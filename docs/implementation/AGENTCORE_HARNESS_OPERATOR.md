# AgentCore Harness operator — Issue #44

## Goal

Promote AgentCore Harness from historical feasibility work into the real AWS SecOps operator-facing reasoning/read layer.

The first production-shaped slice is intentionally read-only:

```text
operator chat
   -> AgentCore Harness: aws_secops_operator
   -> exact AgentCore Gateway tools
   -> Policy ENFORCE
   -> read-only Lambda
   -> AWS Config
   -> live evidence back to operator
```

The existing governed remediation path remains unchanged:

```text
human approval
   -> exact executor
   -> AgentCore Gateway / Policy
   -> exact remediation tool
   -> AWS API
   -> provider readback
```

The Harness does **not** receive a generic AWS tool and does not bypass the current approval/executor contract.

## Why this shape

The learning lab `mytestlab123/lab1_agent` already proved the useful Harness patterns:

- direct operator chat without requiring a custom product GUI;
- exact live read through Gateway + Policy ENFORCE + Lambda;
- explicit separation between human approval and deterministic authorization;
- no shell or broad AWS mutation capability.

Issue #44 promotes those patterns into this repository without copying lab identities, ARNs, account IDs, resource names, or test-only approval claims.

## Operator Harness

`infra/operator-harness/template.yml` defines one Harness:

`aws_secops_operator`

Properties:

- Nova 2 Lite only;
- managed Memory disabled;
- bounded iterations, tokens, timeout and runtime lifetime;
- two explicit Gateway tools only;
- no shell command tool;
- no generic AWS API/CLI tool;
- explicit execution-role deny for runtime command/shell and role chaining.

### Tool 1 — `get_config_summary`

Takes no input. Reads only the two current controls:

- `s3-bucket-level-public-access-prohibited`
- `restricted-ssh`

Returns bounded AWS Config counts and freshness metadata.

### Tool 2 — `list_config_findings`

Accepts only one enum selecting those same two controls. It returns at most 20 current `NON_COMPLIANT` evaluations. The Lambda itself limits the total Config scan to 250 evaluations and 10 pages, matching the repository's existing bounded Config contract.

Resource names returned by AWS are evidence/data, never instructions or authorization.

## Operator experience

Useful prompts after an authorized deployment:

```text
What security findings need attention in this AWS lab?
```

```text
Show me the current restricted SSH findings and explain the risk.
```

```text
Summarize S3 public-access compliance and recommend what I should do next.
```

For an explicit write request such as:

```text
Fix all restricted SSH findings.
```

this Harness must explain that execution still requires the existing governed human-approval/executor path. It must not claim or attempt remediation.

## Long-term direction

Harness should become the primary operator chat entrypoint while these boundaries stay stable:

- ChatGPT + GitHub + OIDC = engineering control plane;
- Harness = operator reasoning/chat plane;
- Gateway + Policy + exact tools = AWS authorization plane;
- provider readback = remediation truth.

A later milestone may connect Harness approval to the existing exact executor only after an approval token/identity binding is designed that cannot be fabricated or skipped by the model. Directly exposing the existing mutation tools to the Harness would bypass today's batch/approval contract and is therefore out of scope.

## Deployment boundary

This PR adds repo-owned desired state and safety tests only. It does not deploy the Harness or change Demo v1. Live deployment requires a separately reviewed OIDC deployment role/workflow or an explicitly authorized trusted bootstrap followed by independent AWS verification.

## Acceptance for this PR

- CloudFormation template validates in `ap-southeast-1`;
- offline safety tests pass;
- Gateway uses Policy `ENFORCE`;
- the Harness can only invoke the two exact read tools;
- no S3, EC2, SSM or other remediation permission is model-accessible;
- existing Demo v1 behavior remains unchanged.
