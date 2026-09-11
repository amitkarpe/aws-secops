// Trusted hook narrows one native ASK to the current immutable SG batch.
// It performs no AWS or state mutation.
module.exports = () => () => async (input) => {
  const args = input?.toolInput ?? {};
  if (Object.keys(args).sort().join(',') !== 'approval_hash,batch_id' ||
      !/^[a-f0-9]{64}$/.test(args.batch_id ?? '') || args.batch_id !== args.approval_hash)
    return {decision: 'deny', reason: 'DENY — invalid or edited Security Group batch scope. No dispatch.'};
  try {
    const response = await fetch('http://localhost:4455/api/v1/list_sg_batches', {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw Error('unavailable');
    const data = await response.json();
    const batch = data.items?.find(b => b.batch_id === args.batch_id && b.approval_hash === args.approval_hash);
    if (!batch || batch.execution_active || ['UNKNOWN','RUNNING'].some(k => batch.counts?.[k]) ||
        batch.decision !== 'PENDING' || !batch.counts?.PENDING)
      return {decision: 'deny', reason: 'DENY — stale, terminal, active or uncertain Security Group batch. Read progress; no dispatch.'};
    return {
      decision: 'ask',
      reason: `ASK — Approve & Execute this exact frozen batch of ${batch.total} unattached demo Security Groups once. Fix: remove only TCP/22 from 0.0.0.0/0. Reject + Submit = zero dispatch. Approve + Submit starts durable execution; AgentCore Gateway Policy must independently ALLOW each fix. Success requires direct EC2 readback. This does not approve S3 or future batches.`
    };
  } catch {
    return {decision: 'deny', reason: 'BLOCKED — exact Security Group batch preview unavailable. No dispatch.'};
  }
};
