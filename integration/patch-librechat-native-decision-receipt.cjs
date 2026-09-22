// Exact source and seam pin for the retained LibreChat v0.8.8-rc1 build.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const expectedDigest = '6f0f53afbaa06dd65e9558e1595060433e37952ef9b0ad1d4ad57781bcbcf025';
const patchedDigest = '311b925b5157aa22fff9fd846ed7075a043579d1ad1f4201ac5e4517dc12a77a';
const marker = `  /**
   * An interrupt steer enqueued just before the pause survives durably with`;
const insertion = `  // Issue #193: exact reject-only tool receipt, after the winning approval CAS.
  // A failed durable receipt terminalizes this generation before any continuation.
  try {
    const bounded = await require('/opt/aws-secops/integration/native-decision-receipt.cjs')
      .recordIfRejectOnly({ req, job, pendingAction });
    if (bounded) mapped.resumeValue = bounded.resumeValue;
  } catch (receiptError) {
    logger.error('[ResumeAgentController] Native decision receipt failed closed', receiptError);
    try {
      await GenerationJobManager.completeJob(streamId, 'Native decision receipt unavailable; no tool dispatched', job.createdAt);
    } catch (finalizeError) {
      logger.error('[ResumeAgentController] Failed to terminalize receipt failure', finalizeError);
    }
    await decrementPendingRequest(userId);
    return sendGenerationJson(res, 503, { error: 'Native decision receipt unavailable; no tool dispatched' }, generationProtocolVersion);
  }

`;
function patchSource(raw) {
  const digest = crypto.createHash('sha256').update(raw).digest('hex');
  if (digest === patchedDigest) return {updated: raw, alreadyPatched: true};
  if (digest !== expectedDigest) throw Error('LibreChat resume source differs from pinned v0.8.8-rc1');
  if (raw.split(marker).length !== 2) throw Error('unique resume seam missing');
  const updated = raw.replace(marker, insertion + marker);
  if (crypto.createHash('sha256').update(updated).digest('hex') !== patchedDigest) {
    throw Error('LibreChat resume patch differs from reviewed insertion');
  }
  return {updated, alreadyPatched: false};
}

function install(root) {
  if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (packageJson.version !== 'v0.8.8-rc1') throw Error('unsupported LibreChat version');
  const target = path.join(root, 'api/server/controllers/agents/resume.js');
  const raw = fs.readFileSync(target, 'utf8');
  const {updated, alreadyPatched} = patchSource(raw);
  if (alreadyPatched) return;
  const staged = target + '.issue193-new';
  fs.writeFileSync(staged, updated, {mode: fs.statSync(target).mode & 0o777, flag: 'wx'});
  fs.renameSync(staged, target);
}

if (require.main === module) {
  install(process.argv[2]);
  console.log('NATIVE_DECISION_RECEIPT_PATCH=READY');
}
module.exports = {patchSource, install, expectedDigest};
