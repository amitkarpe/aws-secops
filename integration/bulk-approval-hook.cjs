// Trusted hook only narrows the static ASK decision. No AWS or state writes.
module.exports = () => () => async (input) => {
  const args = input?.toolInput ?? {};
  if (Object.keys(args).sort().join(',') !== 'approval_hash,batch_id' ||
      !/^[a-f0-9]{64}$/.test(args.batch_id ?? '') || args.batch_id !== args.approval_hash)
    return {decision: 'deny', reason: 'DENY — invalid or edited batch scope. No dispatch.'};
  try {
    const response = await fetch('http://localhost:4444/api/v1/list_batches', {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw Error('unavailable');
    const data = await response.json();
    const batch = data.items?.find(b => b.batch_id === args.batch_id && b.approval_hash === args.approval_hash);
    if (!batch || batch.execution_active || ['UNKNOWN','RUNNING'].some(k => batch.counts[k]) ||
        !['PENDING','APPROVE'].includes(batch.decision) || !(batch.counts.PENDING || batch.counts.APPROVED))
      return {decision: 'deny', reason: 'DENY — stale, terminal, active or uncertain batch. Read progress; no dispatch.'};
    return {decision: 'ask', reason: `ASK — Approve & Execute this exact frozen batch of ${batch.total} demo S3 buckets once. Fix: enable all four bucket Block Public Access settings. Reject + Submit = zero dispatch. Approve + Submit starts durable execution; Gateway Policy must independently ALLOW each fix. Success requires S3 readback. No objects, bucket policies or ACLs are changed. This does not approve future batches.`};
  } catch {
    return {decision: 'deny', reason: 'BLOCKED — exact batch preview unavailable. No dispatch.'};
  }
};
