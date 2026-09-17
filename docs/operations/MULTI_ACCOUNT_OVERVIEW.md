# Multi-account SecOps overview

Authority: Issue #76

This is a public-safe, read-only overview for three or four explicitly
registered personal LAB accounts. It reuses the same
`ChatGPTCrossAccountReadRole` role contract that the Platform hub proves for
each approved target.

## Evidence shape

Each overview row contains only:

- a public-safe LAB alias;
- a hashed account reference, never an account ID or ARN;
- VPC count as bounded inventory evidence;
- the two supported AWS Config control states as security evidence;
- IAM account-summary counts as IAM evidence;
- read-only authority and principal-kind assertions.

The overview deliberately does not collect resource identifiers, credentials,
role ARNs, private finding details, or any mutation result.

## Drill-down path

```text
overview
  -> public-safe LAB alias
     -> supported Config control
        -> Config state + evidence boundary + recommendation
```

For `NON_COMPLIANT`, the recommendation is to use the existing single-account
human-approved remediation flow. The cross-account overview cannot remediate.
For every other state, it says that no cross-account action is available.
If a selected account cannot return the supported Config controls, the overview
shows `UNAVAILABLE` and the drill-down recommends only account-local Config
investigation; it never treats absence of evidence as a clear result.

## Runtime boundary

The local role runner may use short-lived STS credentials to create this
evidence after every assume-role hop verifies target identity. The current AWS
MCP runtime cannot carry those assumed credentials into later MCP calls, so
the MCP UI must not claim dynamic account switching. That runtime limitation
does not weaken the separate CLI role proof.

## Validation

`pilot_v1.multi_account_read.read_security_overview` requires exactly three or
four distinct runtime scopes in the Singapore lab Region and permits only STS,
Config compliance-summary, EC2 VPC inventory, and IAM account-summary reads.
`drill_down_control` accepts only a returned account alias and one of the two
supported controls. Both outputs keep raw identifiers hidden and state
`mutation=false`.
