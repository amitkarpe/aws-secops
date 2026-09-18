// Native LibreChat ASK hook for the exact four-account CodeBuild executor.
// This hook performs no AWS mutation. It validates that the submitted
// control+batch_id exactly matches the current short-lived frozen preview.
const CONTROLS = new Set([
  's3-bucket-level-public-access-prohibited',
  'restricted-ssh',
]);

module.exports = () => () => async (input) => {
  const args = input?.toolInput ?? {};
  if (Object.keys(args).sort().join(',') !== 'batch_id,control' ||
      !CONTROLS.has(args.control) ||
      !/^[a-f0-9]{20}$/.test(args.batch_id ?? '')) {
    return {decision: 'deny', reason: 'DENY — invalid or edited four-account execution scope. No dispatch.'};
  }
  try {
    const url = 'http://localhost:4444/api/operator/multi-account-execution-preview?' +
      new URLSearchParams({control: args.control});
    const response = await fetch(url, {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw Error('unavailable');
    const preview = await response.json();
    if (preview?.version !== 1 ||
        preview?.scope !== 'four-account-live-config' ||
        preview?.control !== args.control ||
        preview?.batch_id !== args.batch_id ||
        JSON.stringify(preview?.pending_aliases) !== JSON.stringify(['lab-dev','lab-poc','lab-qa','lab-sec']) ||
        typeof preview?.age_seconds !== 'number' ||
        preview.age_seconds < 0 ||
        preview.age_seconds > 900) {
      return {decision: 'deny', reason: 'DENY — stale or changed frozen four-account batch. Prepare a new plan; no dispatch.'};
    }
    const title = args.control === 's3-bucket-level-public-access-prohibited'
      ? 'S3 Block Public Access'
      : 'restricted SSH';
    const action = args.control === 's3-bucket-level-public-access-prohibited'
      ? 'enable all four bucket-level Block Public Access settings'
      : 'remove only TCP/22 ingress from 0.0.0.0/0 on the exact unattached demo Security Group';
    return {
      decision: 'ask',
      reason: `ASK — Approve ${title} remediation across exactly lab-dev, lab-poc, lab-qa and lab-sec. Action: ${action}. Reject + Submit = zero CodeBuild dispatch and zero remediation. Approve + Submit runs only this frozen batch through the fixed CodeBuild project and existing G/O controller role. Direct provider readback must prove success; AWS Config may converge later. This does not approve the other control or future batches.`
    };
  } catch {
    return {decision: 'deny', reason: 'BLOCKED — exact four-account execution preview unavailable. No dispatch.'};
  }
};
