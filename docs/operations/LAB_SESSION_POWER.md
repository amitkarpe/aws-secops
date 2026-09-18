# Personal LAB session power

Authority: Amit's explicit request in Issue #110. Applies only to the retained personal-LAB host serving Ops Operator Center and LibreChat, not the four remediation target accounts or any work/office host.

## After testing or validation

Ask Amit whether to **STOP the LAB instance, never terminate it**. A request for a reminder is not permission to stop immediately. Record the validation checkpoint and whether the shutdown prompt was delivered on the owning Issue/PR.

Before an approved stop:

1. Select the intended AWS MCP connection and verify its account with STS, using `ap-southeast-1`; use the personal-LAB account gate from Issue #106.
2. Re-discover the exact retained host, verify ownership and state, and confirm that no deployment, CodeBuild execution, remediation, tests or other active host work would be interrupted. Stop if the target or activity is ambiguous.
3. Explain that Ops and LibreChat will be unavailable while the host is stopped. Preserve MongoDB data, EBS volumes, journals, manifests and configuration.
4. After Amit confirms that exact stop, use normal EC2 `StopInstances`, with no force or skip-OS-shutdown options. Verify the final `stopped` state and record it.

Never use `TerminateInstances`, delete disks, clean up resources, resize, migrate, or change IAM/network/DNS under this authority. Stop is a reversible power action, not cleanup. This rule does not authorize bypassing a validation or safety failure.

## When work resumes

Amit authorizes starting the **same** retained host when resumed work actually needs its runtime. Repository-only edits do not require a start.

Validate GitHub context and STS first, re-discover and verify the exact host, then use `StartInstances` only if its current state is `stopped`. If already running, do not restart it. Wait for instance health and SSM availability; verify MongoDB, LibreChat, Operator and endpoint/auth health before claiming the demo is ready. A failed endpoint check is not permission to modify DNS or security settings.

Do not auto-enroll another host or account. Unexpected, stopping, shutting-down, terminated, ambiguous or unsupported state requires investigation rather than a replacement instance.

## Reminder behavior

The interactive session should ask at the validation-complete checkpoint. A reminder may check durable completion state later, but it never performs an AWS power action itself. Avoid duplicate reminders for a checkpoint already acknowledged, prompted or recorded as stopped.
