# Pilot v1 status

## PROVEN

- Nova 2 Lite runs through AgentCore Harness in Singapore.
- Harness built-ins are unavailable; its allowlist has exactly the fixed SG
  read and S3 read Gateway tools.
- A real unattached Security Group finding is provider-grounded.
- Reject makes no Gateway/remediation call.
- Synthetic PROD is denied by native Gateway Policy with no provider change.
- DEV approval reaches one exact remediation and provider verification becomes
  COMPLIANT.
- The manager UI visibly reports finding, recommendation, human decision,
  Policy decision, exact tool, provider verification, and AWS change.
- One fixed S3 bucket returns five deterministic provider controls through one
  read-only Gateway tool with no mutation.

## PROPOSED NEXT

- Let management review the 3–5 minute Pilot and decide whether a limited
  internal user trial is valuable.
- Measure one week of actual model, Gateway, Policy, Lambda, and CloudWatch
  usage before revising the cost estimate.
- If approved later, replace private state-file configuration with a reviewed
  deployment/configuration source while preserving server-owned resource IDs.

## LATER / OUT OF SCOPE

Multi-user auth, multi-account onboarding, Organizations/StackSets, generic AWS
write tools, Security Hub/Config/Inspector enablement, Registry, Temporal Policy,
EKS, Supervisor/A2A, broad observability, and production operation.
