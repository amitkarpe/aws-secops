// Exact upstream and retained-runtime source/seam pins for LibreChat v0.8.8-rc1.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const expectedDigest = '6f0f53afbaa06dd65e9558e1595060433e37952ef9b0ad1d4ad57781bcbcf025';
const patchedDigest = '311b925b5157aa22fff9fd846ed7075a043579d1ad1f4201ac5e4517dc12a77a';
const retainedDigest = '54dad95a0e143f5d72857d98c8398743e68e101cab527b38382a7c0d51f10e43';
const retainedPatchedDigest = '9a5ea6723b0daddf7812fba7fb03f47f76183889c3e96a6ad827972f2ad9e0a7';
const backupSuffix = '.before-issue193-native-receipt';
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
const retainedMarker = "    if (\n      !(await GenerationJobManager.beginProviderExecution(\n";
const retainedInsertion = [
  "    // Issue #193: persist the exact final native decision after CAS/schedule validation,",
  "    // but before provider execution or resumeCompletion. Other tools are unchanged.",
  "    try {",
  "      const bounded = await require('/opt/aws-secops/integration/native-decision-receipt.cjs')",
  "        .recordIfRejectOnly({ req, job, pendingAction });",
  "      if (bounded) mapped.resumeValue = bounded.resumeValue;",
  "    } catch (receiptError) {",
  "      logger.error('[ResumeAgentController] Native decision receipt failed closed', getSafeErrorMetadata(receiptError));",
  "      throw Object.assign(new Error('Native decision receipt unavailable; no tool dispatched'), {",
  "        code: 'NATIVE_DECISION_RECEIPT_FAILED',",
  "      });",
  "    }",
  "",
].join("\n");

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

function patchRetainedSource(raw) {
  if (raw.split(retainedMarker).length !== 2) throw Error('unique retained resume boundary missing');
  if (!raw.includes('GenerationJobManager.approvals.resolve(') ||
      !raw.includes('GenerationJobManager.beginProviderExecution(') ||
      !raw.includes('client.resumeCompletion({')) {
    throw Error('retained resume transaction contract differs');
  }
  return raw.replace(retainedMarker, retainedInsertion + retainedMarker);
}

function patchInstalledSource(raw) {
  const digest = crypto.createHash('sha256').update(raw).digest('hex');
  if (digest === patchedDigest || digest === retainedPatchedDigest) {
    return {updated: raw, alreadyPatched: true};
  }
  if (digest === expectedDigest) {
    return {...patchSource(raw), originalDigest: expectedDigest};
  }
  if (digest === retainedDigest) {
    const updated = patchRetainedSource(raw);
    if (crypto.createHash('sha256').update(updated).digest('hex') !== retainedPatchedDigest) {
      throw Error('retained resume patch differs from reviewed insertion');
    }
    return {updated, alreadyPatched: false, originalDigest: retainedDigest};
  }
  throw Error('LibreChat resume source differs from both reviewed v0.8.8-rc1 pins');
}

function check(root) {
  if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (packageJson.version !== 'v0.8.8-rc1') throw Error('unsupported LibreChat version');
  const raw = fs.readFileSync(path.join(root, 'api/server/controllers/agents/resume.js'), 'utf8');
  const currentDigest = crypto.createHash('sha256').update(raw).digest('hex');
  const patch = patchInstalledSource(raw);
  const nextDigest = crypto.createHash('sha256').update(patch.updated).digest('hex');
  if (!patch.alreadyPatched && !patch.originalDigest) throw Error('resume source has no reviewed pin');
  return {alreadyPatched: patch.alreadyPatched, currentDigest, nextDigest};
}

function install(root) {
  if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (packageJson.version !== 'v0.8.8-rc1') throw Error('unsupported LibreChat version');
  const target = path.join(root, 'api/server/controllers/agents/resume.js');
  const raw = fs.readFileSync(target, 'utf8');
  const {updated, alreadyPatched, originalDigest} = patchInstalledSource(raw);
  if (alreadyPatched) return;
  const backup = target + backupSuffix;
  if (!fs.existsSync(backup)) {
    fs.copyFileSync(target, backup, fs.constants.COPYFILE_EXCL);
    fs.chmodSync(backup, 0o600);
    fs.writeFileSync(backup + '.mode', `${(fs.statSync(target).mode & 0o777).toString(8).padStart(3, '0')}\n`, {mode: 0o600, flag: 'wx'});
  } else {
    const backupDigest = crypto.createHash('sha256').update(fs.readFileSync(backup)).digest('hex');
    if (backupDigest !== originalDigest) throw Error('existing LibreChat resume backup differs from source pin');
    const modePath = backup + '.mode';
    if (!fs.existsSync(modePath) || !/^[0-7]{3,4}\n$/.test(fs.readFileSync(modePath, 'utf8'))) {
      throw Error('existing LibreChat resume backup mode record is missing or invalid');
    }
  }
  const staged = target + '.issue193-new';
  fs.writeFileSync(staged, updated, {mode: fs.statSync(target).mode & 0o777, flag: 'wx'});
  fs.renameSync(staged, target);
}

if (require.main === module) {
  if (process.argv[2] === '--check') {
    const result = check(process.argv[3]);
    console.log(`NATIVE_DECISION_RECEIPT_PATCH=${result.alreadyPatched ? 'ALREADY_READY' : 'READY'} SOURCE=${result.currentDigest} NEXT=${result.nextDigest}`);
  } else {
    install(process.argv[2]);
    console.log('NATIVE_DECISION_RECEIPT_PATCH=READY');
  }
}
module.exports = {patchSource, patchRetainedSource, patchInstalledSource, check, install,
  expectedDigest, patchedDigest, retainedDigest, retainedPatchedDigest, backupSuffix};
