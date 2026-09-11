// Add one exact ASK entry, preserving existing reader, agents and SG policy.
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');
const root = process.argv[2];
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat root required');
const yaml = require(path.join(root,'node_modules/js-yaml'));
const file = path.join(root,'librechat.yaml');
const raw = fs.readFileSync(file,'utf8');
const original = yaml.load(raw), config = structuredClone(original);
const approval = config.endpoints?.agents?.toolApproval;
if (!approval?.enabled || approval.mode !== 'default' || !Array.isArray(approval.ask) || !Array.isArray(approval.allow))
  throw Error('expected existing native approval configuration');
const names = ['start_batch_execution_mcp_aws_secops_executor','mcp:aws_secops_executor:start_batch_execution'];
// This field is endpoint-wide, not agent-specific. Never put SG or S3
// instructions here: native static ASK can supply this text before tool hooks.
const neutralReason = 'ASK - Review {tool}. Review the exact parameters and the selected agent\'s recommendation. Reject + Submit = do not run this request. Approve + Submit = run only this exact request, subject to independent policy checks. Approval is not proof of success; read the verified result afterward.';
if (approval.reason !== neutralReason) {
  if (typeof approval.reason !== 'string' || !approval.reason.includes('action=remove_unrestricted_ssh, target=demo-security-group'))
    throw Error('unrecognized shared approval reason; review before replacing');
  approval.reason = neutralReason;
}
if (approval.allow.some(x=>names.includes(x) || /[*]/.test(x))) throw Error('execution must not be statically allowed');
const entry = {type:'stdio', command:'/opt/aws-secops/.venv-mcp/bin/python', args:['-m','pilot_v1.mcp_executor'],
  env:{PYTHONPATH:'/opt/aws-secops',SECOPS_BULK_BACKEND_URL:'http://localhost:4444'},
  timeout:35000,initTimeout:15000,chatMenu:false,serverInstructions:true};
if (config.mcpServers.aws_secops_executor && !isDeepStrictEqual(config.mcpServers.aws_secops_executor,entry))
  throw Error('existing executor differs');
config.mcpServers.aws_secops_executor = entry;
approval.hooks ??= [];
for (const name of names) {
  if (!approval.ask.includes(name)) approval.ask.push(name);
  const hook = {matcher:name,module:'/opt/aws-secops/integration/bulk-approval-hook.cjs'};
  const existing = approval.hooks.find(h=>h.matcher===name);
  if (existing && !isDeepStrictEqual(existing,hook)) throw Error('existing hook differs');
  if (!existing) approval.hooks.push(hook);
}
if (!isDeepStrictEqual(original, config)) {
  const wordingBackup = file+'.before-neutral-approval-wording';
  if (!fs.existsSync(wordingBackup)) fs.writeFileSync(wordingBackup,raw,{mode:0o600,flag:'wx'});
  const backup = file+'.before-inline-bulk';
  if (!fs.existsSync(backup)) fs.writeFileSync(backup,raw,{mode:0o600,flag:'wx'});
  const rendered = yaml.dump(config,{lineWidth:-1,noRefs:true});
  if (!isDeepStrictEqual(yaml.load(rendered),config)) throw Error('YAML round trip differs');
  fs.writeFileSync(file+'.bulk-new',rendered,{mode:fs.statSync(file).mode&0o777,flag:'wx'});
  fs.renameSync(file+'.bulk-new',file);
}
console.log('EXACT_EXECUTOR=ASK READERS_AND_SG=PRESERVED');
