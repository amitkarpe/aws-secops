#!/usr/bin/env python3
"""Explicit same-account Gateway/Policy/Lambda deployment; private resumable state.

No bucket creation/reset/write here. Creation is recorded after every step; a
failed or ambiguous operation stops, never deletes resources or broadens IAM.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_v1.bulk import digest
from pilot_v1.bulk_s3 import S3Provider

ERROR_FILE = None


def aws(service, operation, **arguments):
    cmd = ['aws', '--profile', 'vagent', '--region', 'ap-southeast-1', '--cli-connect-timeout', '5', '--cli-read-timeout', '30', service, operation]
    for key, value in arguments.items():
        cmd += ['--'+key.replace('_', '-'), json.dumps(value) if isinstance(value, (list, dict)) else str(value)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                            env={**os.environ, 'AWS_MAX_ATTEMPTS': '1', 'AWS_PAGER': ''})
    if result.returncode:
        if ERROR_FILE:
            ERROR_FILE.write_text(result.stderr)
        import re
        code = re.search(r'\((\w+)\)', result.stderr)
        raise RuntimeError(f'{service}:{operation}: {code.group(1) if code else "FAILED"}; inspect private provider state before retry')
    return json.loads(result.stdout or '{}')


def wait(read, field, ready, expected=None):
    for _ in range(30):
        value = read()
        if value.get(field) == ready and all(value.get(k) == v for k,v in (expected or {}).items()):
            return value
        if value.get(field) in {'FAILED', 'CREATE_FAILED', 'UPDATE_FAILED'}:
            raise RuntimeError('resource failed; retained for review')
        time.sleep(2)
    raise RuntimeError('bounded readiness timeout; retained for review')


def main():
    global ERROR_FILE
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--ttl', required=True)
    p.add_argument('--create', action='store_true', help='explicit approved deployment, otherwise plan only')
    p.add_argument('--replace-scope', action='store_true', help='after terminal batch and gated fleet growth only')
    a = p.parse_args(); os.umask(0o077)
    ERROR_FILE = a.state.with_suffix('.error.txt')
    if datetime.strptime(a.ttl, '%d-%m-%y').date() < datetime.now(timezone.utc).date():
        p.error('expired TTL')
    provider = S3Provider(a.manifest)
    m = provider.manifest; account = m['account']; scope_hash = digest(m)
    state = json.loads(a.state.read_text()) if a.state.exists() else {'account': account, 'scope_hash': scope_hash, 'name': 'aws-secops-bpa-dev-'+scope_hash[:10]}
    name = state['name']
    replacing = state['scope_hash'] != scope_hash
    if (state['account'] != account or not name.startswith('aws-secops-bpa-dev-')
            or (replacing and not a.replace_scope)):
        p.error('existing deployment differs')
    print('PLAN=2 roles, 1 Lambda/log group, 1 Gateway/target, 1 Policy engine/policy; exact manifest only', flush=True)
    if not a.create:
        return
    a.state.parent.mkdir(parents=True, exist_ok=True)
    def save():
        temp = a.state.with_suffix('.new')
        with temp.open('w') as out:
            json.dump(state, out); out.flush(); os.fsync(out.fileno())
        temp.replace(a.state)
    def record(key, value):
        state[key] = value; save(); print('RECORDED='+key, flush=True)
    tags = dict(Name=name, owner='amit', dev='amit', project='aws-secops', environment='dev',
                purpose='exact governed S3 BPA demo', phase='inline-bpa', version='r01',
                created=datetime.now(timezone.utc).date().isoformat(), TTL=a.ttl, tools='cdx', cleanup='review')
    for role, principal in [('lambdaRole', 'lambda.amazonaws.com'), ('gatewayRole', 'bedrock-agentcore.amazonaws.com')]:
        if role not in state:
            trust = {'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Principal': {'Service': principal}, 'Action': 'sts:AssumeRole'}]}
            if role == 'gatewayRole':
                trust['Statement'][0]['Condition'] = {'StringEquals': {'aws:SourceAccount': account}}
            record(role, aws('iam', 'create-role', role_name=name+'-'+role, assume_role_policy_document=trust,
                            tags=[{'Key': k, 'Value': v} for k, v in tags.items()])['Role']['Arn'])
    log_name = '/aws/lambda/'+name
    if 'logGroup' not in state:
        aws('logs', 'create-log-group', log_group_name=log_name, tags=tags)
        record('logGroup', log_name)
    aws('logs', 'put-retention-policy', log_group_name=log_name, retention_in_days=7)
    policy = {'Version': '2012-10-17', 'Statement': [
        {'Effect': 'Allow', 'Action': ['s3:GetBucketLocation', 's3:GetBucketTagging', 's3:ListBucketVersions', 's3:ListBucketMultipartUploads',
                                     's3:GetBucketOwnershipControls', 's3:GetBucketPolicy', 's3:GetBucketPublicAccessBlock', 's3:PutBucketPublicAccessBlock'],
         'Resource': ['arn:aws:s3:::'+b for b in m['buckets']]},
        {'Effect': 'Allow', 'Action': ['logs:CreateLogStream', 'logs:PutLogEvents'],
         'Resource': f'arn:aws:logs:ap-southeast-1:{account}:log-group:{log_name}:*'}]}
    aws('iam', 'put-role-policy', role_name=name+'-lambdaRole', policy_name='ExactScope', policy_document=policy)
    if 'lambdaArn' not in state or replacing:
        archive = a.state.with_suffix('.lambda.zip')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
            out.write(Path(__file__).resolve().parents[1]/'pilot_v1/bulk_lambda.py', 'bulk_lambda.py')
            out.writestr('scope.json', json.dumps({**m, 'scope_hash': scope_hash}))
        if replacing:
            aws('lambda', 'update-function-code', function_name=name, zip_file='fileb://'+str(archive.resolve()))
            wait(lambda: aws('lambda', 'get-function-configuration', function_name=name), 'LastUpdateStatus', 'Successful')
        else:
            time.sleep(10)  # new role propagation; no retry of an ambiguous create
            record('lambdaArn', aws('lambda', 'create-function', function_name=name, role=state['lambdaRole'],
                               runtime='python3.12', handler='bulk_lambda.lambda_handler', timeout=60, memory_size=128,
                               zip_file='fileb://'+str(archive.resolve()), tags=tags)['FunctionArn'])
    wait(lambda: aws('lambda', 'get-function-configuration', function_name=name), 'State', 'Active')
    if 'policyEngineId' not in state:
        engine = aws('bedrock-agentcore-control', 'create-policy-engine', name=name.replace('-', '_'), tags=tags)
        state.update({k: engine[k] for k in ('policyEngineId', 'policyEngineArn')}); save()
    wait(lambda: aws('bedrock-agentcore-control', 'get-policy-engine', policy_engine_id=state['policyEngineId']), 'status', 'ACTIVE')
    gateway_policy = {'Version': '2012-10-17', 'Statement': [
        {'Effect': 'Allow', 'Action': 'lambda:InvokeFunction', 'Resource': state['lambdaArn']},
        {'Effect': 'Allow', 'Action': ['bedrock-agentcore:GetPolicyEngine', 'bedrock-agentcore:AuthorizeAction', 'bedrock-agentcore:PartiallyAuthorizeActions'],
         'Resource': [state['policyEngineArn']]+([state['gatewayArn']] if 'gatewayArn' in state else [])}]}
    aws('iam', 'put-role-policy', role_name=name+'-gatewayRole', policy_name='ExactScope', policy_document=gateway_policy)
    if 'gatewayId' not in state:
        gateway = aws('bedrock-agentcore-control', 'create-gateway', name=name, role_arn=state['gatewayRole'],
                      protocol_type='MCP', authorizer_type='AWS_IAM', tags=tags)
        state.update({k: gateway[k] for k in ('gatewayId', 'gatewayArn', 'gatewayUrl')}); save()
        gateway_policy['Statement'][1]['Resource'].append(state['gatewayArn'])
        aws('iam', 'put-role-policy', role_name=name+'-gatewayRole', policy_name='ExactScope', policy_document=gateway_policy)
    wait(lambda: aws('bedrock-agentcore-control', 'get-gateway', gateway_identifier=state['gatewayId']), 'status', 'READY')
    # Empty Gateway first resolves its exact ARN without wildcard IAM. No target
    # exists until exact-role permission and ENFORCE are read back successfully.
    current = aws('bedrock-agentcore-control', 'get-gateway', gateway_identifier=state['gatewayId'])
    enforced = {'arn': state['policyEngineArn'], 'mode': 'ENFORCE'}
    if current.get('policyEngineConfiguration') != enforced:
        aws('bedrock-agentcore-control', 'update-gateway', gateway_identifier=state['gatewayId'], name=name,
            role_arn=state['gatewayRole'], protocol_type='MCP', authorizer_type='AWS_IAM', policy_engine_configuration=enforced)
        current = wait(lambda: aws('bedrock-agentcore-control', 'get-gateway', gateway_identifier=state['gatewayId']), 'status', 'READY')
    if current.get('policyEngineConfiguration') != enforced:
        raise RuntimeError('ENFORCE missing; no target will be created')
    schema = {'name': 'apply_bucket_bpa', 'description': 'Enable all four BPA flags on exactly one allowlisted empty demo bucket.',
              'inputSchema': {'type': 'object', 'properties': {'scope_hash': {'type': 'string'}, 'resource_index': {'type': 'integer'},
                                                             'batch_id': {'type': 'string'}, 'environment': {'type': 'string'}},
                              'required': ['scope_hash', 'resource_index', 'batch_id', 'environment']}}
    if 'targetId' not in state:
        target = aws('bedrock-agentcore-control', 'create-gateway-target', gateway_identifier=state['gatewayId'], name='ExactBpa',
                     target_configuration={'mcp': {'lambda': {'lambdaArn': state['lambdaArn'], 'toolSchema': {'inlinePayload': [schema]}}}},
                     credential_provider_configurations=[{'credentialProviderType': 'GATEWAY_IAM_ROLE'}])
        record('targetId', target['targetId'])
    wait(lambda: aws('bedrock-agentcore-control', 'get-gateway-target', gateway_identifier=state['gatewayId'], target_id=state['targetId']), 'status', 'READY')
    state['toolName'] = 'ExactBpa___apply_bucket_bpa'
    statement = ('permit(principal, action == AgentCore::Action::"'+state['toolName']+'", resource == AgentCore::Gateway::"'+state['gatewayArn']+'") '
                 'when { context.input.environment == "dev" && context.input.scope_hash == "'+scope_hash+'" && '
                 'context.input.resource_index >= 0 && context.input.resource_index < '+str(len(m['buckets']))+' };')
    state['definition'] = {'cedar': {'statement': statement}}; save()
    if 'policyId' not in state:
        record('policyId', aws('bedrock-agentcore-control', 'create-policy', policy_engine_id=state['policyEngineId'], name='exact_bpa_dev',
                              definition=state['definition'], validation_mode='FAIL_ON_ANY_FINDINGS', enforcement_mode='ACTIVE')['policyId'])
    elif replacing:
        aws('bedrock-agentcore-control', 'update-policy', policy_engine_id=state['policyEngineId'], policy_id=state['policyId'],
            definition=state['definition'], validation_mode='FAIL_ON_ANY_FINDINGS', enforcement_mode='ACTIVE')
    wait(lambda: aws('bedrock-agentcore-control', 'get-policy', policy_engine_id=state['policyEngineId'], policy_id=state['policyId']), 'status', 'ACTIVE', {'definition': state['definition']})
    state['scope_hash'] = scope_hash; save()
    print('DEPLOYMENT=READY; no S3 remediation invoked')


if __name__ == '__main__':
    main()
