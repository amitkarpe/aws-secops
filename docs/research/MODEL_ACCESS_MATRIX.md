# `vagent` Bedrock model-access matrix

Status: Phase 0B.1 discovery plus Phase 0B.2 live Harness evidence, checked
2026-09-09

Region: Asia Pacific (Singapore), `ap-southeast-1`

Phase 0B.1 used Bedrock control-plane discovery only. Phase 0B.2 added the one
live Nova 2 Lite Harness invocation described below. Neither pass exposed the
account identity. “Candidate” means the control-plane gates support a later
tiny invocation; it is not runtime or quality proof.

## Result

All three candidates were visible in account discovery. Nova 2 Lite is a
benchmark candidate (**YES**, cost baseline); Nova Pro is a benchmark candidate
(**YES**, quality comparison); Claude Sonnet 4.6 is **NO** until its agreement
state is resolved. The model IDs below are the relevant agent-use context; the
Bedrock pricing page is the official pricing source, with the Price List API
used for the numeric Nova baseline in the cost model.

| Candidate | Model ID | Inference route | Authorization | Entitlement | Region | Agreement | Conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Amazon Nova 2 Lite | `amazon.nova-2-lite-v1:0` | `global.amazon.nova-2-lite-v1:0` | Authorized | Available | Available | Available | **LIVE Harness model call PASS; requested final text BLOCKED** |
| Amazon Nova Pro | `amazon.nova-pro-v1:0` | `apac.amazon.nova-pro-v1:0` | Authorized | Available | Available | Available | **PASS candidate** |
| Anthropic Claude Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | `global.anthropic.claude-sonnet-4-6` | Authorized | Available | Available | Not available | **BLOCKED pending one runtime probe / agreement clarification** |

## Interpretation

- Nova 2 Lite is the default benchmark candidate because every discovered
  access gate passes and its current inference price is lowest among these
  candidates.
- Nova Pro is the quality comparison candidate, not the default bulk-check
  engine.
- Claude Sonnet 4.6 is visible and authorized, but its agreement gate did not
  report available. Do not claim it works until a minimal paid invocation is
  explicitly run in a later benchmark.
- Cross-Region inference profiles may route requests outside Singapore within
  their documented geography. A company pilot must review data residency and
  SCP compatibility before choosing a global or APAC profile.
- Deterministic compliance checks should use provider APIs or native findings.
  Models should explain, prioritize and propose bounded remediation primarily
  for exceptions.

## Phase 0B.2 live result

After Amit selected local profile `amit` because the `vagent` quota request was
still pending, one Nova 2 Lite invocation was sent through an AgentCore Harness
in Singapore. The native stream reported 1,243 input tokens, 54 output tokens
and 980 ms model latency, proving model access through Harness. The model chose
Harness's default `file_operations` tool and the one-iteration cap then stopped
before a final assistant message. See
[`HARNESS_NOVA2_LITE_LIVE_PROOF.md`](HARNESS_NOVA2_LITE_LIVE_PROOF.md).

This changes Nova 2 Lite from “control-plane candidate” to **live model-call
proof**, but the requested end-to-end response remains BLOCKED pending one
corrected tool-allowlist invocation.

Read-only comparison also found a broader model catalog in Sydney than
Singapore (70 versus 31 catalog entries at the time of checking). Nova 2 Lite
was available in both. Phase 0B.2 remains a Singapore deployment; the broader
Sydney catalog is a later benchmark option, not a reason to move this POC.

## Reproducible read-only method

The Phase 0B.1 account-specific matrix was produced from these API families
with local profile `vagent` and Region `ap-southeast-1`:

```text
bedrock:ListFoundationModels
bedrock:ListInferenceProfiles
bedrock:GetFoundationModelAvailability
```

Private raw output remains outside the public repository. It must not be used as
proof of successful inference. The Phase 0B.2 live call used local profile
`amit` after Amit changed the approved test context.

## Official sources

- [Access Amazon Bedrock foundation models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Supported Regions and models for cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html)
- [Amazon Nova 2 Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
