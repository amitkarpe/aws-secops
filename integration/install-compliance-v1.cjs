/* Install the isolated Compliance Agent v1 MCP without modifying legacy MCP servers. */
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');

const root = process.argv[2];
const harnessArn = process.argv[3] || process.env.COMPLIANCE_AGENT_V1_HARNESS_ARN;
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
if (!/^arn:aws[a-zA-Z-]*:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:harness\/compliance_agent_v1-[A-Za-z0-9]+$/.test(harnessArn || ''))
  throw Error('exact Compliance Agent v1 Harness ARN required');

const yaml = require(path.join(root,'node_modules/js-yaml'));
const file = path.join(root,'librechat.yaml');
const raw = fs.readFileSync(file,'utf8');
const config = yaml.load(raw), updated = structuredClone(config);
if (!updated.mcpServers) throw Error('existing mcpServers mapping required');
const approval = updated.endpoints?.agents?.toolApproval;
if (!approval?.enabled || approval.mode !== 'default' || !Array.isArray(approval.allow) || !Array.isArray(approval.ask))
  throw Error('expected native tool approval configuration');
if (approval.allow.some(x => /[*]/.test(x)) || approval.ask.some(x => /[*]/.test(x)))
  throw Error('wildcard tool approval is not accepted');

const server = {
  type:'stdio',
  command:'/opt/compliance-agent-v1/.venv/bin/python',
  args:['-m','compliance_agent_v1.mcp_server'],
  env:{
    PYTHONPATH:'/opt/compliance-agent-v1/src',
    CONFIG_BACKEND_URL:'http://127.0.0.1:1111',
    COMPLIANCE_AGENT_V1_HARNESS_ARN:harnessArn,
    AWS_REGION:'ap-southeast-1',
  },
  timeout:120000,
  initTimeout:15000,
  chatMenu:false,
  serverInstructions:true,
};
const existing = updated.mcpServers.compliance_agent_v1;
if (existing && !isDeepStrictEqual(existing,server))
  throw Error('existing compliance_agent_v1 MCP differs; review before replacing');
updated.mcpServers.compliance_agent_v1 = server;

const tool='ask_compliance_agent_v1_mcp_compliance_agent_v1';
if (!approval.allow.includes(tool)) approval.allow.push(tool);
approval.ask = approval.ask.filter(name => name !== tool);

const rendered=yaml.dump(updated,{lineWidth:-1,noRefs:true});
if(!isDeepStrictEqual(yaml.load(rendered),updated)) throw Error('YAML round trip differs');
if(rendered!==raw){
  const backup=file+'.before-compliance-agent-v1';
  if(!fs.existsSync(backup)) fs.writeFileSync(backup,raw,{mode:0o600,flag:'wx'});
  const temp=file+'.compliance-v1-new';
  fs.writeFileSync(temp,rendered,{mode:fs.statSync(file).mode&0o777,flag:'wx'});
  fs.renameSync(temp,file);
}
console.log('COMPLIANCE_AGENT_V1_MCP=READY TOOL=ALLOW LEGACY_MCP=PRESERVED');
