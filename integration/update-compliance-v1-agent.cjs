/* Update the existing Compliance Agent v1 LibreChat record from the repo-owned spec.
 *
 * Usage:
 *   node integration/update-compliance-v1-agent.cjs /path/to/compliance-agent-v1.json
 *
 * Safety:
 * - updates exactly one existing agent named Compliance Agent v1;
 * - preserves _id, public agent id, author and ACL records;
 * - accepts only the three reviewed v1 tools;
 * - does not create users/agents or widen ACLs.
 */
const fs = require('node:fs');
const { execFileSync } = require('node:child_process');

const specPath = process.argv[2];
const database = process.env.LIBRECHAT_MONGO_DB || 'LibreChat';
if (!specPath || !fs.existsSync(specPath)) throw Error('existing v1 agent spec path required');
if (!/^[A-Za-z0-9_-]{1,64}$/.test(database)) throw Error('invalid LibreChat Mongo database name');

const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const expectedTools = [
  'ask_compliance_agent_v1_mcp_compliance_agent_v1',
  'prepare_multi_account_remediation_mcp_aws_compliance_planner',
  'execute_multi_account_remediation_mcp_aws_compliance_planner',
];
if (spec?.name !== 'Compliance Agent v1') throw Error('unexpected agent name');
if (spec?.provider !== 'bedrock' || spec?.model !== 'global.amazon.nova-2-lite-v1:0') throw Error('unexpected v1 model');
if (JSON.stringify(spec?.tools) !== JSON.stringify(expectedTools)) throw Error('unexpected v1 tool set');
if (typeof spec?.instructions !== 'string' || !spec.instructions.includes('native Approve/Reject')) throw Error('governed approval instructions required');
if (!Array.isArray(spec?.conversation_starters) || spec.conversation_starters.length < 1 || spec.conversation_starters.length > 4) throw Error('1-4 conversation starters required');
if (spec.conversation_starters.some((x) => typeof x !== 'string' || x.length < 1 || x.length > 80)) throw Error('invalid conversation starter');

const update = {
  name: spec.name,
  description: spec.description,
  provider: spec.provider,
  model: spec.model,
  model_parameters: spec.model_parameters,
  instructions: spec.instructions,
  tools: spec.tools,
  conversation_starters: spec.conversation_starters,
};
const js = String.raw`
const update = ${JSON.stringify(update)};
if (db.agents.countDocuments({name:'Compliance Agent v1'}) !== 1) {
  throw new Error('expected exactly one existing Compliance Agent v1');
}
const before = db.agents.findOne({name:'Compliance Agent v1'});
const result = db.agents.updateOne(
  {_id:before._id, name:'Compliance Agent v1'},
  {$set:{...update, updatedAt:new Date()}}
);
if (result.matchedCount !== 1) throw new Error('v1 agent update did not match exactly one record');
const after = db.agents.findOne({_id:before._id});
if (String(after.author) !== String(before.author) || after.id !== before.id) {
  throw new Error('v1 agent identity changed unexpectedly');
}
if (JSON.stringify(after.tools) !== JSON.stringify(update.tools)) {
  throw new Error('v1 agent tools not updated exactly');
}
if (JSON.stringify(after.conversation_starters) !== JSON.stringify(update.conversation_starters)) {
  throw new Error('v1 conversation starters not updated exactly');
}
print(JSON.stringify({status:'READY', id:after.id, toolCount:after.tools.length, starterCount:after.conversation_starters.length}));
`;

const output = execFileSync('mongosh', [database, '--quiet', '--eval', js], {
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 30000,
}).trim();
const line = output.split(/\r?\n/).filter(Boolean).at(-1);
const result = JSON.parse(line);
if (result?.status !== 'READY' || result?.toolCount !== 3 || result?.starterCount !== 4) throw Error('v1 agent update verification failed');
console.log('COMPLIANCE_AGENT_V1_RECORD=READY TOOLS=3 STARTERS=4');
