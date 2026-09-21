// Native LibreChat ASK hook for the exact four-account CodeBuild executor.
// This hook performs no AWS mutation. It validates that the submitted
// control+batch_id exactly matches the current short-lived frozen preview.
const CONTROLS = new Set([
  's3-bucket-level-public-access-prohibited',
  'restricted-ssh',
]);

module.exports = () => (context) => async (input) => {
  if (typeof context?.userId !== 'string' || context.userId.length < 1) {
    return {decision: 'deny', reason: 'DENY — authenticated LibreChat user context is required. No execution.'};
  }
  const args = input?.toolInput ?? {};
  if (Object.keys(args).sort().join(',') !== 'batch_id,control,scope_hash' ||
      !CONTROLS.has(args.control) ||
      !/^[a-f0-9]{20}$/.test(args.batch_id ?? '') ||
      !/^[a-f0-9]{24}$/.test(args.scope_hash ?? '')) {
    return {decision: 'deny', reason: 'DENY — invalid or edited four-account execution scope. No dispatch.'};
  }
  try {
    const url = 'http://localhost:4444/api/operator/multi-account-execution-preview?' +
      new URLSearchParams({control: args.control});
    const response = await fetch(url, {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw Error('unavailable');
    const preview = await response.json();
    const pending = preview?.pending_aliases;
    const selectedAccounts = preview?.selected_accounts ?? [];
    const unselectedAccounts = preview?.unselected_accounts ?? [];
    const excludedAliases = preview?.excluded_aliases ?? [];
    const excludedResources = preview?.excluded_resources ?? [];
    const allAliases = [...(pending ?? []), ...excludedAliases].sort();
    const allowed = ['lab-dev','lab-poc','lab-qa','lab-sec'];
    if (preview?.version !== 1 ||
        preview?.scope !== 'four-account-live-config' ||
        preview?.control !== args.control ||
        preview?.batch_id !== args.batch_id ||
        preview?.scope_hash !== args.scope_hash ||
        !Array.isArray(pending) ||
        !Array.isArray(selectedAccounts) ||
        !Array.isArray(unselectedAccounts) ||
        !Array.isArray(excludedAliases) ||
        !Array.isArray(excludedResources) ||
        excludedAliases.length !== excludedResources.length ||
        selectedAccounts.length < 1 ||
        selectedAccounts.length > 4 ||
        selectedAccounts.some((x) => !allowed.includes(x)) ||
        new Set(selectedAccounts).size !== selectedAccounts.length ||
        JSON.stringify([...selectedAccounts].sort()) !== JSON.stringify(allAliases) ||
        unselectedAccounts.some((x) => !allowed.includes(x) || selectedAccounts.includes(x)) ||
        new Set([...selectedAccounts, ...unselectedAccounts]).size !== 4 ||
        pending.length < 1 ||
        typeof preview?.age_seconds !== 'number' ||
        preview.age_seconds < 0 ||
        preview.age_seconds > 900) {
      return {decision: 'deny', reason: 'DENY — stale or changed frozen four-account batch. Prepare a new plan; no dispatch.'};
    }
    const title = args.control === 's3-bucket-level-public-access-prohibited'
      ? 'S3 Block Public Access'
      : 'restricted SSH';
    const action = args.control === 's3-bucket-level-public-access-prohibited'
      ? 'enable all four bucket-level Block Public Access settings on each included bucket'
      : 'remove only TCP/22 ingress from 0.0.0.0/0 on each included exact unattached demo Security Group';
    const includedText = pending.join(', ');
    const unselectedText = unselectedAccounts.length
      ? ` Accounts outside requested scope: ${unselectedAccounts.join(', ')}.`
      : '';
    const exception = preview?.exception ?? null;
    const scopeHash = preview?.scope_hash;
    if (excludedResources.length && (
        !exception ||
        typeof exception.reason !== 'string' ||
        exception.reason.length < 3 ||
        (exception.reference !== null && typeof exception.reference !== 'string') ||
        (exception.expires_at !== null && typeof exception.expires_at !== 'string') ||
        typeof exception.requested_at !== 'string' ||
        typeof scopeHash !== 'string' ||
        !/^[a-f0-9]{24}$/.test(scopeHash)
    )) {
      return {decision: 'deny', reason: 'DENY — frozen exception metadata is invalid. Prepare a new plan; no dispatch.'};
    }
    const metadataText = excludedResources.length
      ? ` Reason: ${exception.reason}.${exception.reference ? ` Reference: ${exception.reference}.` : ''}${exception.expires_at ? ` Expires: ${exception.expires_at}.` : ''}`
      : '';
    const excludedText = excludedResources.length
      ? ` Excluded by this one-time exception: ${excludedResources.join(', ')} (${excludedAliases.join(', ')}).${metadataText} These excluded findings remain non-compliant and are not reported as fixed.`
      : '';
    return {
      decision: 'ask',
      reason: `Allow Compliance Agent v1 to apply ${title} remediation? Selected accounts: ${includedText}. Change: ${action}.${unselectedText}${excludedText} Choose Approve or Reject, then Submit. Approve applies only this frozen scope; Reject makes zero remediation execution dispatch and zero AWS resource writes. AWS service verification runs after the change; AWS Config evaluation may update later.`,
      allowedDecisions: ['approve', 'reject'],
    };
  } catch {
    return {decision: 'deny', reason: 'BLOCKED — exact four-account execution preview unavailable. No dispatch.'};
  }
};
