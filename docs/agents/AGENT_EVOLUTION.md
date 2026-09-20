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
- Amazon Bedrock AgentCore Harness as the primary agent reasoning/tool layer;
- automated backend + Harness + LibreChat acceptance;
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


## Knowledge and memory progression

Keep operational truth separate from semantic knowledge.

### Compliance Agent v1
- structured operational event ledger first;
- KISS storage: S3 JSON event objects;
- exact actor/resource/time/before/after/provider-verification queries use the ledger;
- no RAG required.

### Later
- add AgentCore Memory for conversation continuity and episodic/user context;
- add Bedrock Knowledge Bases/RAG for growing runbooks, SOPs, policies, architecture and incident documentation;
- move operational event storage to DynamoDB when indexed/queryable history needs outgrow simple S3 JSON.

RAG supplements operational truth; it does not replace the change ledger or CloudTrail evidence.
