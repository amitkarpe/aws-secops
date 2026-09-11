"""Same-account exact Gateway adapter; no direct remediation fallback."""
import json
from pathlib import Path
from .bulk import PolicyDenied, digest
from .bulk_s3 import S3Provider
from .gateway import call_tool, result_text


class GovernedS3Provider(S3Provider):
    concurrency = 3

    def __init__(self, manifest, deployment):
        super().__init__(manifest, sdk=True)
        self.deployment = json.loads(Path(deployment).read_text())
        if (self.deployment['scope_hash'] != digest(self.manifest)
                or self.deployment['account'] != self.manifest['account']):
            raise ValueError('governed deployment/manifest mismatch')
        self.context['governance_hash'] = digest(self.deployment)
        self.batch_id = None
        self.metrics.update(gateway_calls=0, policy_denied=0, target_success=0)

    def authorize(self, batch_id):
        self.verify_identity()
        d = self.deployment
        gateway = self.call('bedrock-agentcore-control', 'get-gateway', gateway_identifier=d['gatewayId'])
        if (gateway.get('status') != 'READY' or gateway.get('authorizerType') != 'AWS_IAM'
                or gateway.get('gatewayUrl') != d['gatewayUrl']
                or gateway.get('policyEngineConfiguration') != {'arn': d['policyEngineArn'], 'mode': 'ENFORCE'}):
            raise PermissionError('Gateway enforcement prerequisites differ')
        policy = self.call('bedrock-agentcore-control', 'get-policy', policy_engine_id=d['policyEngineId'], policy_id=d['policyId'])
        if (policy.get('status') != 'ACTIVE' or policy.get('definition') != d['definition']
                or policy.get('enforcementMode', 'ACTIVE') != 'ACTIVE'):
            raise PermissionError('Policy prerequisites differ')
        policies = self.call('bedrock-agentcore-control', 'list-policies', policy_engine_id=d['policyEngineId'])
        if policies.get('nextToken') or [p['policyId'] for p in policies.get('policies', [])] != [d['policyId']]:
            raise PermissionError('unexpected additional Policy scope')
        self.batch_id = batch_id

    def invoke(self, resource, environment='dev'):
        if not self.batch_id or resource not in self.resources:
            raise PermissionError('no exact approved execution context')
        d = self.deployment
        self.metrics['gateway_calls'] += 1
        response = call_tool(d['gatewayUrl'], 'ap-southeast-1', 'vagent', d['toolName'],
                             dict(scope_hash=d['scope_hash'], resource_index=self.resources.index(resource),
                                  batch_id=self.batch_id, environment=environment))
        error = response.get('error', {})
        if error.get('code') == -32002 and 'Tool Execution Denied' in error.get('message', '') and 'denied by default' in error.get('message', ''):
            self.metrics['policy_denied'] += 1
            raise PolicyDenied('independent Gateway Policy DENY')
        if error or response.get('result', {}).get('isError'):
            raise RuntimeError('Gateway/target error; not Policy DENY')
        value = json.loads(result_text(response))
        if value.get('scope_hash') != d['scope_hash'] or value.get('result') not in {'BPA_APPLIED', 'ALREADY_COMPLIANT'}:
            raise RuntimeError('unexpected target result')
        self.metrics['target_success'] += 1
        return dict(gateway_decision='ALLOW', target_result=value['result'], target_calls=1)

    def apply(self, resource, before):
        from .bulk import TARGET
        if before != {**TARGET, 'BlockPublicAcls': False}:
            raise PermissionError('unexpected approved precondition')
        # BulkStore pre-reads; Lambda independently repeats ownership and exact
        # precondition checks immediately before its single write.
        return self.invoke(resource)
