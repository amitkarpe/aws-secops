# Phase 0B — AgentCore feasibility, models and cost lab

Issue: https://github.com/amitkarpe/aws-secops/issues/3

Status: planned / research PR seed

## Objective

Use the isolated standalone personal AWS lab account selected locally through `vagent` to replace assumptions with small measured evidence before a company pilot.

This is not the full AWS Copilot implementation.

## Required outputs

1. AgentCore feature/Region matrix.
2. Minimal Harness experiment.
3. Minimal Gateway + Policy + harmless exact tool experiment.
4. Bedrock model access/quality/cost benchmark.
5. Hosting recommendation.
6. Official-source-backed scale/cost estimates.
7. Retained-resource and cleanup report.
8. Recommendation for the first company non-production pilot.

## Cost scenarios

### S3 compliance

```text
1,000 buckets x 5 controls = 5,000 checks / assessment
20,000 buckets x 5 controls = 100,000 checks / assessment
```

Compare daily / weekly / monthly and direct provider APIs vs provider-native compliance findings where applicable.

Prefer deterministic/provider-native bulk evaluation and spend model tokens mainly on exceptions, explanation and remediation.

### EC2 vulnerability/remediation

Baseline:

- 20 EC2 instances/month;
- consume existing Inspector/provider findings where possible;
- triage/compare;
- recommendation;
- human approval;
- bounded remediation/patch workflow;
- provider verification.

Separate security-service, model, AgentCore, execution and logging costs.

## Experiment rules

- Confirm `vagent` identity and Region before AWS work.
- Direct AWS CLI first for simple setup/readback.
- Small experiment -> exact proof -> cleanup/readback.
- Do not commit private AWS environment identity.
- Do not touch company/production/Organizations-management environments.
- Workload/deployed tests use workload IAM, not embedded IAM-user credentials.
- Do not enable broad account-wide paid services merely to explore them.
- Record retained resources, billing dimension and cleanup plan.

## Suggested first sequence

```text
1. Region/service matrix
2. model-access matrix
3. minimal Harness hello-world
4. minimal Gateway/Policy harmless tool
5. inspect native logs/observability
6. cost model from official pricing
7. hosting recommendation
8. company-pilot recommendation
```

## References

- Phase 0A proposal: https://github.com/amitkarpe/aws-secops/issues/1
- R&D architecture research: https://github.com/mytestlab123/AgentCore/tree/main/docs/research/aws-copilot
- Existing working governance demo: https://github.com/mytestlab123/AgentCore
