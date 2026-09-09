# Pilot v1 cost and retention notes

Checked: 2026-09-09. USD, before tax/support/discounts. Recheck AWS pricing
before a budget decision; the detailed formulas and official links are in
`docs/research/COST_MODEL_V0.md`.

## Current small-lab shape

- Harness: no additional Harness fee.
- Nova 2 Lite: pay per input/output token only when a prompt runs.
- Gateway: `$0.005 / 1,000` invocations.
- Policy: `$0.000025` per authorization request.
- Gateway indexing: `$0.02 / 100 tools / month`; four retained tools are about
  **$0.0008/month** before billing behavior or pricing changes.
- Lambda: no idle compute charge; the demo calls fit comfortably within the
  standard free tier if it is otherwise unused.
- S3: the dedicated bucket is empty; only tiny request charges are expected.
- Security Group and IAM: no direct idle charge.
- CloudWatch: variable ingestion/storage only; Pilot Lambda logs retain 1 day
  and Harness Runtime logs retain 7 days.

A normal demonstration uses a handful of Nova, Gateway, Policy, Lambda, EC2
read, and S3 read requests. Its exact total depends on tokens, cold starts,
request class, shared free tier, and logs; do not replace those measured billing
dimensions with a false fixed total.

## Cost controls

- Run the model only for manager-facing interpretation; deterministic provider
  reads remain the source of truth.
- Keep the Harness allowlist to the two exact read tools; remediation is called
  only by the service after a human decision.
- Keep the bucket empty and the demo Security Group unattached.
- Stop local UI processes and finish Runtime sessions after use.
- Retain inexpensive control-plane resources; do not repeatedly deploy/delete
  them for every demo.
- Review Cost Explorer after the first week and first month using the
  `aws-secops` project tags where the service supports tags.

Cleanup is an explicit Pilot-retirement activity, not a post-demo action. See
`RETAINED_RESOURCES.md` for the exact order and safety gates.
