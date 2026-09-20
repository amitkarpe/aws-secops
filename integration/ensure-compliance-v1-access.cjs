/* Ensure Compliance Agent v1 is visible to an already-authorized LibreChat user.
 *
 * Usage:
 *   node integration/ensure-compliance-v1-access.cjs user@example.com
 *
 * Safety:
 * - fixed source agent: AWS Compliance Agent
 * - fixed target agent: Compliance Agent v1
 * - target user must already have access to the source agent
 * - role IDs and permission bits are derived from existing source-agent ACLs
 * - idempotent; conflicting target ACLs fail closed
 */
const { execFileSync } = require('node:child_process');

const viewerEmail = process.argv[2];
const database = process.env.LIBRECHAT_MONGO_DB || 'LibreChat';

if (!viewerEmail || viewerEmail.length > 320 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(viewerEmail)) {
  throw Error('valid existing LibreChat user email required');
}
if (!/^[A-Za-z0-9_-]{1,64}$/.test(database)) {
  throw Error('invalid LibreChat Mongo database name');
}

const sourceName = 'AWS Compliance Agent';
const targetName = 'Compliance Agent v1';
const js = String.raw`
const sourceName = ${JSON.stringify(sourceName)};
const targetName = ${JSON.stringify(targetName)};
const viewerEmail = ${JSON.stringify(viewerEmail)};

if (db.agents.countDocuments({name: sourceName}) !== 1 ||
    db.agents.countDocuments({name: targetName}) !== 1 ||
    db.users.countDocuments({email: viewerEmail}) !== 1) {
  throw new Error('LibreChat source, target, or user identity is missing or ambiguous');
}
const source = db.agents.findOne({name: sourceName});
const target = db.agents.findOne({name: targetName});
const viewer = db.users.findOne({email: viewerEmail});
if (String(source.author) !== String(target.author)) {
  throw new Error('source/target agent authors differ; manual review required');
}

const ownerTemplate = db.aclentries.findOne({
  resourceId: source._id,
  resourceType: 'agent',
  principalType: 'user',
  principalId: source.author,
  permBits: 15,
});
const viewerTemplate = db.aclentries.findOne({
  resourceId: source._id,
  resourceType: 'agent',
  principalType: 'user',
  principalId: viewer._id,
  permBits: {$in: [1, 15]},
});
if (!ownerTemplate) throw new Error('source-agent owner ACL missing');
if (!viewerTemplate) throw new Error('target user must already have source-agent access');

function ensure(template, principalId) {
  const query = {
    resourceId: target._id,
    resourceType: 'agent',
    principalType: 'user',
    principalId,
  };
  const existing = db.aclentries.findOne(query);
  if (existing) {
    if (existing.permBits !== template.permBits || String(existing.roleId) !== String(template.roleId)) {
      throw new Error('conflicting target ACL; manual review required');
    }
    return 'existing';
  }
  const now = new Date();
  db.aclentries.insertOne({
    ...query,
    principalModel: template.principalModel || 'User',
    roleId: template.roleId,
    permBits: template.permBits,
    grantedBy: target.author,
    grantedAt: now,
    createdAt: now,
    updatedAt: now,
    __v: 0,
  });
  return 'created';
}

const owner = ensure(ownerTemplate, target.author);
const viewerResult = ensure(viewerTemplate, viewer._id);
print(JSON.stringify({status: 'READY', owner, viewer: viewerResult}));
`;

const output = execFileSync('mongosh', [database, '--quiet', '--eval', js], {
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 30000,
}).trim();

let result;
try {
  result = JSON.parse(output.split(/\r?\n/).filter(Boolean).at(-1));
} catch {
  throw Error('LibreChat access helper returned unexpected output');
}
if (result?.status !== 'READY') throw Error('LibreChat access helper did not verify READY');
console.log('COMPLIANCE_AGENT_V1_ACCESS=READY');
