/* Restore only the fields changed by the Issue #191 v1-agent updater. */
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

const backupPath = process.argv[2];
const database = process.env.LIBRECHAT_MONGO_DB || 'LibreChat';
if (!backupPath || !path.isAbsolute(backupPath) || !fs.existsSync(backupPath)) throw Error('private v1 agent backup required');
if (!/^[A-Za-z0-9_-]{1,64}$/.test(database)) throw Error('invalid LibreChat Mongo database name');
const snapshotText = fs.readFileSync(backupPath, 'utf8');
const snapshot = JSON.parse(snapshotText);
const fields = ['description', 'provider', 'model', 'model_parameters', 'instructions', 'tools', 'conversation_starters', 'updatedAt'];
if (!snapshot?._id || !snapshot?.id || !snapshot?.author || snapshot?.name !== 'Compliance Agent v1' ||
    !Array.isArray(snapshot.tools) || !Array.isArray(snapshot.conversation_starters)) {
  throw Error('private v1 agent backup is invalid');
}
const js = String.raw`
const snapshot = EJSON.parse(${JSON.stringify(snapshotText)});
if (db.agents.countDocuments({name:'Compliance Agent v1'}) !== 1) {
  throw new Error('expected exactly one existing Compliance Agent v1');
}
const before = db.agents.findOne({_id:snapshot._id, name:'Compliance Agent v1'});
if (!before || String(before.author) !== String(snapshot.author) || before.id !== snapshot.id) {
  throw new Error('existing v1 agent identity differs from private backup');
}
const fields = ${JSON.stringify(fields)};
const restore = {};
for (const field of fields) {
  if (Object.prototype.hasOwnProperty.call(snapshot, field)) restore[field] = snapshot[field];
  else throw new Error('private v1 agent backup is incomplete');
}
const result = db.agents.updateOne({_id:snapshot._id}, {$set:restore});
if (result.matchedCount !== 1) throw new Error('v1 agent rollback did not match exactly one record');
const after = db.agents.findOne({_id:snapshot._id});
for (const field of fields) {
  if (EJSON.stringify(after[field]) !== EJSON.stringify(restore[field])) throw new Error('v1 agent rollback verification failed');
}
print(JSON.stringify({status:'RESTORED', toolCount:after.tools.length}));
`;
const output = execFileSync('mongosh', [database, '--quiet', '--eval', js], {
  encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000,
}).trim();
const result = JSON.parse(output.split(/\r?\n/).filter(Boolean).at(-1));
if (result?.status !== 'RESTORED') throw Error('v1 agent rollback failed');
console.log(`COMPLIANCE_AGENT_V1_RECORD=RESTORED TOOLS=${result.toolCount}`);
