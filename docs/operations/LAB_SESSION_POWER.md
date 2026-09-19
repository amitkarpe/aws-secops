# Personal LAB session power

Authority: Amit's explicit request in Issue #110. Applies only to the retained personal-LAB host serving Ops Operator Center and LibreChat, not the four remediation target accounts or any work/office host.

## During active personal-LAB demo work

Keep the retained LAB instance running. Do not proactively ask Amit to stop it at each validation checkpoint.

A stop is considered only when Amit explicitly requests a cost-saving shutdown. Never terminate the instance.

Before an explicitly requested stop:

1. Select the intended AWS MCP connection and verify its account with STS, using `ap-southeast-1`; use the personal-LAB account gate from Issue #106.
2. Re-discover the exact retained host, verify ownership and state, and confirm that no deployment, CodeBuild execution, remediation, tests or other active host work would be interrupted. Stop if the target or activity is ambiguous.
3. Explain that Ops, Config Console and LibreChat will be unavailable while the host is stopped. Preserve MongoDB data, EBS volumes, journals, manifests and configuration.
4. Use normal EC2 `StopInstances` only after Amit has explicitly requested that shutdown, with no force or skip-OS-shutdown options. Verify the final `stopped` state and record it.

Never use `TerminateInstances`, delete disks, clean up resources, resize, migrate, or change IAM/network/DNS under this authority. Stop is a reversible power action, not cleanup. This rule does not authorize bypassing a validation or safety failure.

## When work resumes

Amit authorizes starting the **same** retained host when resumed work actually needs its runtime. Repository-only edits do not require a start.

Validate GitHub context and STS first, re-discover and verify the exact host, then use `StartInstances` only if its current state is `stopped`. If already running, do not restart it. Wait for instance health and SSM availability; verify MongoDB, LibreChat, Operator and endpoint/auth health before claiming the demo is ready. A failed endpoint check is not permission to modify DNS or security settings.

Do not auto-enroll another host or account. Unexpected, stopping, shutting-down, terminated, ambiguous or unsupported state requires investigation rather than a replacement instance.

## Reminder behavior

Do not prompt for shutdown merely because validation completed. Mention shutdown only when Amit asks about cost-saving or explicitly requests a stop. A reminder never performs an AWS power action itself.
