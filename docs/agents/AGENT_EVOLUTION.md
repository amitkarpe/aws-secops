# Agent Evolution

Owning Issue: #123

## Product family

### Compliance Agent v1

Specialist AWS compliance agent.

Scope:

- four registered LAB aliases;
- S3 Block Public Access;
- restricted SSH;
- status / explain / plan;
- automated acceptance;
- no generic AWS administration.

### AWS Ops Agent v1

Preferred next generic product name because current scope is AWS-only.

Read-first operations assistant:

- inventory/status;
- compliance evidence;
- EC2/ECS/Lambda operations evidence;
- CloudWatch/log evidence;
- troubleshooting and explanation;
- no broad mutation.

### AWS Ops Agent v2

Governed operational actions:

- everything in v1;
- bounded runbooks;
- frozen plans;
- human approval;
- exact tool execution;
- provider verification;
- audit trail.

No generic shell or model-accessible AWS administrator.

### AWS Ops Agent v3

Composable operations platform:

- compliance/security/operations specialist capabilities;
- shared tool/MCP contracts;
- reusable acceptance datasets and harness;
- memory/context boundaries;
- policy, approval and audit integration;
- multi-service orchestration with explicit safety boundaries.

## Naming boundary

Do not call the product `DevOps Agent` or `DevSecOps Agent` until it genuinely includes broader CI/CD, IaC, repository/code, runtime and security lifecycle capabilities.

## Migration principle

Prove stable contracts in Compliance Agent v1 first.

Future AWS Ops Agent versions should consume those proven contracts rather than copy legacy agent code.
