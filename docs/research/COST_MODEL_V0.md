# Phase 0B.1 cost model v0

Status: planning estimate, checked 2026-09-09

Currency: USD. Taxes, Enterprise Discount Program terms, data transfer and
support are excluded. Prices can change; recheck the linked AWS pages before a
budget decision.

## Executive result

The economical design is deterministic/provider-native checking plus model use
only for exceptions. At the largest scenario, sending all 3,000,000 monthly
checks to a model would be unnecessary; sending only 1%-10% exceptions keeps
the modeled Nova 2 Lite inference spend at approximately **$75.45-$754.50 per
month** under the stated token assumption.

## Workload definitions

| Estate | Checks per assessment | Monthly run | Weekly, 4 runs | Daily, 30 runs |
| --- | ---: | ---: | ---: | ---: |
| 1,000 S3 buckets × 5 controls | 5,000 | 5,000 | 20,000 | 150,000 |
| 20,000 S3 buckets × 5 controls | 100,000 | 100,000 | 400,000 | 3,000,000 |

“Weekly” and “daily” use explicit planning factors of 4 and 30, rather than an
average calendar month.

## Provider-native security-service costs

### AWS Config rule evaluations

AWS public-Region tiers are $0.001 for the first 100,000 evaluations, $0.0008
for the next 400,000, and $0.0005 above 500,000.

| Estate | Monthly | Weekly | Daily |
| --- | ---: | ---: | ---: |
| 1,000 buckets | $5.00 | $20.00 | $140.00 |
| 20,000 buckets | $100.00 | $340.00 | $1,670.00 |

Formula: `min(N,100000)*0.001 + min(max(N-100000,0),400000)*0.0008 + max(N-500000,0)*0.0005`.

Configuration-item recording, conformance packs, S3 delivery and notifications
are separate and depend on resource changes, not merely the assessment count.

### Security Hub CSPM

AWS's current examples use the same AWS security-check tiers: $0.001 for the
first 100,000 checks, $0.0008 for the next 400,000 and $0.0005 thereafter.
Therefore the isolated security-check totals for the two workload tables are
the same as the Config rule-evaluation table above.

Do **not** add both tables automatically. Security Hub service-linked Config
rules are not separately charged as Config rule evaluations, although Config
configuration-item recording is still billed. Findings produced by Security
Hub's own checks do not incur finding-ingestion charges. External finding
ingestion has 10,000 events/month free, then $0.00003/event.

### Amazon Inspector for 20 EC2 instances/month

Inspector is priced by average instances scanned and varies by Region. AWS's
official pricing-page example for US East (N. Virginia) is $1.258 per average
EC2 instance-month for agent-based scanning and $1.75 for agentless scanning:

| Reference mode | Formula | Illustrative monthly total |
| --- | --- | ---: |
| Agent-based | `20 × $1.258` | $25.16 |
| Agentless | `20 × $1.75` | $35.00 |

These are official example rates, **not a claimed Singapore quote**. Exact
Singapore Inspector pricing is BLOCKED in v0 and must be captured from AWS
Pricing Calculator or a measured bill before the company pilot.

### Direct AWS API checks

Direct provider reads avoid a separate AgentCore or model fee, but individual
AWS service request prices depend on each API and Region. Five controls are not
necessarily five identically priced S3 requests. Preserve the formula
`request_count / 1,000 × applicable API rate` per request class and measure the
actual API mix in the next experiment; do not pretend all controls are `GET`
requests.

## Model inference for exceptions

Baseline: Nova 2 Lite global cross-Region Standard pricing observed through the
official AWS Price List API on 2026-09-09:

- input: $0.41 per million tokens;
- output: $3.39 per million tokens;
- one exception: 2,000 input + 500 output tokens;
- cost per exception: `(2,000/1,000,000 × 0.41) + (500/1,000,000 × 3.39)` =
  **$0.002515**.

| Checks/month | 1% exceptions | 5% exceptions | 10% exceptions |
| ---: | ---: | ---: | ---: |
| 5,000 | 50 / $0.13 | 250 / $0.63 | 500 / $1.26 |
| 20,000 | 200 / $0.50 | 1,000 / $2.52 | 2,000 / $5.03 |
| 150,000 | 1,500 / $3.77 | 7,500 / $18.86 | 15,000 / $37.73 |
| 100,000 | 1,000 / $2.52 | 5,000 / $12.58 | 10,000 / $25.15 |
| 400,000 | 4,000 / $10.06 | 20,000 / $50.30 | 40,000 / $100.60 |
| 3,000,000 | 30,000 / $75.45 | 150,000 / $377.25 | 300,000 / $754.50 |

For the EC2 path, assuming one 4,000-input/1,000-output-token triage per
instance: `20 × ((4,000/1M × 0.41) + (1,000/1M × 3.39))` = **$0.10/month**.
This excludes embeddings, retries and cache effects and must be calibrated with
measured token counts.

## AgentCore and execution costs

| Layer | Current official rate | Cost implication |
| --- | --- | --- |
| Harness | No additional charge | Pay for models, tools and underlying resources |
| Gateway invocation | $0.005 / 1,000 API calls | $0.000005 per exception tool call |
| Gateway Search | $0.025 / 1,000 searches | Excluded; no search required in this design |
| Gateway tool indexing | $0.02 / 100 tools/month | Effectively $0.0002 for one indexed tool before rounding/billing behavior |
| Policy authorization | $0.000025/request | One request per controlled tool action |
| Runtime microVM | $0.0895/vCPU-hour + $0.00945/GB-hour, active time | Avoid unless Harness/Lambda cannot meet lifecycle needs |
| Identity through Runtime/Gateway | No additional charge | External identity providers may have their own charges |
| Evaluations | Built-in: $0.0024/1K input and $0.012/1K output tokens | Use for a bounded test set, not every production check |

Assuming one Gateway invocation and one Policy authorization per exception,
the combined charge is `$0.000030 × exception_count`: from less than one cent
at 50 exceptions to **$9.00/month** at 300,000 exceptions.

### Lambda exact tool

AWS Lambda's free tier includes 1 million requests and 400,000 GB-seconds per
month. Beyond it, the reference x86 on-demand rates are $0.20 per million
requests and $0.00001667 per GB-second. Example only: a 128 MB function running
100 ms once per exception consumes 0.0125 GB-seconds. At the maximum 300,000
exceptions, pre-free-tier cost is approximately **$0.06 requests + $0.0625
compute = $0.1225/month**. Actual duration, architecture, free-tier sharing and
Region determine the bill.

## Logging, observability and hosting

AgentCore Observability is billed through CloudWatch. The AgentCore pricing
page's official example uses $0.35/GB for spans and $0.50/GB for logs: 10 GB of
spans plus 6 GB of logs costs $6.50. Use this as a sizing example, not a fixed
Singapore quote. Set retention and measure actual ingestion before extrapolating.

Hosting recommendation:

- **Agent → Harness:** first choice; no separate Harness fee.
- **Exact tool → Lambda:** scale-to-zero and simplest bounded action.
- **UI → existing LibreChat or thin UI:** reuse retained hosting; incremental
  hosting can be near zero, but the existing host's EC2/storage bill remains.
- **Runtime MCP → only if needed:** pay active Runtime CPU and memory only when a
  long-lived protocol/tool process is justified.
- **EKS → defer:** no Phase 0 requirement warrants a continuously operated
  cluster.

## What is not included

- S3 configuration recording and heterogeneous API request mix;
- exact Singapore Inspector quote;
- retries, prompt growth, cached-token behavior and model quality differences;
- NAT Gateway, data transfer, WAF, third-party UI hosting and support plans;
- production volumes, multi-account aggregation and enterprise discounts.

## Official sources

- [AWS Config pricing](https://aws.amazon.com/config/pricing/)
- [Security Hub CSPM pricing](https://aws.amazon.com/security-hub/cspm/pricing/)
- [Amazon Inspector pricing](https://aws.amazon.com/inspector/pricing/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)

## Phase 0B.3 measured governed-call cost

Phase 0B.3 reused the retained Harness and ran one successful DEV tool call and
one Policy-denied synthetic PROD tool call. Including one failed no-tool
diagnostic, measured model usage was 4,262 input and 114 output tokens:

```text
model                       = $0.00213388
2 Gateway invocations       = $0.00001000
2 Policy authorizations     = $0.00005000
1 Lambda call, 128 MB/96 ms = $0.00000040 before free tier
measured variable total     = $0.00219428
```

Tiny CloudWatch storage is excluded. One retained indexed tool is approximately
$0.0002/month; the retained services have no separate idle compute charge.

## Single next experiment

Run a fixed, no-tool security-task quality benchmark through the retained
Harness using Nova 2 Lite and one stronger Nova model. Record exact
tokens/latency/cost and score both outputs with the same small deterministic
rubric before selecting the Friday-demo model.
