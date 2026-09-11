/* Add the reader without changing existing LibreChat endpoints or MCP entries.
 * Run on the retained host: node /path/install-reader.cjs /opt/LibreChat
 * Restart only the verified LibreChat backend afterwards.
 */
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');
const root = process.argv[2];
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
const yaml = require(path.join(root, 'node_modules/js-yaml'));
const file = path.join(root, 'librechat.yaml');
const before = fs.readFileSync(file, 'utf8');
const config = yaml.load(before);
const entry = {
  type: 'stdio', command: '/opt/aws-secops/.venv-mcp/bin/python',
  args: ['-m', 'pilot_v1.mcp_bridge'],
  env: {PYTHONPATH: '/opt/aws-secops', SECOPS_BACKEND_URL: 'http://localhost:3340'},
  timeout: 105000, initTimeout: 15000, chatMenu: false, serverInstructions: true,
};
const reviewOrigin = process.env.SECOPS_REVIEW_ORIGIN;
if (reviewOrigin) {
  const u = new URL(reviewOrigin);
  if (u.protocol !== 'https:' || u.origin !== reviewOrigin || u.port || u.username || u.password)
    throw Error('SECOPS_REVIEW_ORIGIN must be an HTTPS origin');
  entry.env.SECOPS_REVIEW_ORIGIN = reviewOrigin;
}
const readTools = ['list_findings','get_finding','get_source_health','explain_finding','list_jobs','get_job','list_batches','get_batch'];
const bulkOrigin = process.env.SECOPS_BULK_BACKEND_URL;
if (bulkOrigin) {
  if (bulkOrigin !== 'http://localhost:4444') throw Error('bulk bridge must use fixed loopback port 4444');
  entry.env.SECOPS_BULK_BACKEND_URL = bulkOrigin;
}
const allowNames = readTools.map(name => name + '_mcp_aws_secops_reader');
if (!config.mcpServers) throw Error('existing mcpServers mapping required');
let after = before;
if (config.mcpServers.aws_secops_reader) {
  const previous = structuredClone(entry);
  delete previous.env.SECOPS_REVIEW_ORIGIN;
  delete previous.env.SECOPS_BULK_BACKEND_URL;
  const withReview = structuredClone(previous);
  if (reviewOrigin) withReview.env.SECOPS_REVIEW_ORIGIN = reviewOrigin;
  if (!isDeepStrictEqual(config.mcpServers.aws_secops_reader, entry)) {
    if (!isDeepStrictEqual(config.mcpServers.aws_secops_reader, previous) &&
        !isDeepStrictEqual(config.mcpServers.aws_secops_reader, withReview))
      throw Error('existing reader differs; review before replacing');
    const additions = [];
    if (reviewOrigin && !config.mcpServers.aws_secops_reader.env.SECOPS_REVIEW_ORIGIN)
      additions.push('      SECOPS_REVIEW_ORIGIN: ' + reviewOrigin);
    if (bulkOrigin) additions.push('      SECOPS_BULK_BACKEND_URL: ' + bulkOrigin);
    after = before.replace(/^      SECOPS_BACKEND_URL: http:\/\/localhost:3340[ \t]*$/m,
      '$&\n' + additions.join('\n'));
  }
} else {
  if (!/^mcpServers:\s*$/m.test(before)) throw Error('unsupported YAML layout');
  after = before.replace(/^mcpServers:\s*$/m, 'mcpServers:\n' +
    yaml.dump({aws_secops_reader: entry}).trimEnd().split('\n').map(l => '  ' + l).join('\n'));
}
const allow = config.endpoints?.agents?.toolApproval?.allow;
if (!Array.isArray(allow) || !/^      allow:\s*$/m.test(before))
  throw Error('expected explicit native tool approval allow list');
const missing = allowNames.filter(name => !allow.includes(name));
if (missing.length) after = after.replace(/^      allow:\s*$/m,
  '      allow:\n' + missing.map(name => '        - ' + name).join('\n'));
const expected = structuredClone(config);
expected.mcpServers.aws_secops_reader = entry;
expected.endpoints.agents.toolApproval.allow = [...missing,...allow];
if (!isDeepStrictEqual(yaml.load(after), expected))
  throw Error('unrelated config changed');
if (after !== before) {
  if (!fs.existsSync(file + '.before-secops-reader'))
    fs.writeFileSync(file + '.before-secops-reader', before, {mode: 0o600, flag: 'wx'});
  fs.writeFileSync(file + '.secops-new', after, {mode: fs.statSync(file).mode & 0o777, flag: 'wx'});
  fs.renameSync(file + '.secops-new', file);
  console.log('READER_CONFIG=UPDATED READ_TOOLS=8 EXISTING_CONFIG=PRESERVED');
} else {
  console.log('READER_CONFIG=UNCHANGED');
}
if (process.argv.includes('--native-bedrock')) {
  const envFile = path.join(root, '.env');
  const original = fs.readFileSync(envFile, 'utf8');
  const dotenv = require(path.join(root, 'node_modules/dotenv'));
  const env = dotenv.parse(original);
  if (env.BEDROCK_AWS_DEFAULT_REGION && env.BEDROCK_AWS_DEFAULT_REGION !== 'ap-southeast-1')
    throw Error('existing Bedrock Region differs');
  if (['BEDROCK_AWS_ACCESS_KEY_ID','BEDROCK_AWS_BEARER_TOKEN','BEDROCK_AWS_PROFILE'].some(k=>env[k]))
    throw Error('existing Bedrock authentication requires separate review');
  let updated = original;
  const values = {
    ENDPOINTS: [...new Set([...(env.ENDPOINTS || '').split(',').filter(Boolean), 'bedrock'])].join(','),
    BEDROCK_AWS_DEFAULT_REGION: 'ap-southeast-1',
    BEDROCK_AWS_MODELS: [...new Set([...(env.BEDROCK_AWS_MODELS || '').split(',').filter(Boolean), 'global.amazon.nova-2-lite-v1:0'])].join(','),
  };
  for (const [key,value] of Object.entries(values)) {
    const pattern = new RegExp('^'+key+'=.*$', 'm');
    updated = pattern.test(updated) ? updated.replace(pattern,key+'='+value) : updated+'\n'+key+'='+value+'\n';
  }
  if (updated !== original) {
    if (!fs.existsSync(envFile+'.before-secops-bedrock'))
      fs.writeFileSync(envFile+'.before-secops-bedrock',original,{mode:0o600,flag:'wx'});
    fs.writeFileSync(envFile+'.secops-new',updated,{mode:0o600,flag:'wx'});
    fs.renameSync(envFile+'.secops-new',envFile);
  }
  console.log('NATIVE_BEDROCK=ENABLED INSTANCE_ROLE_AUTH=REQUIRED');
}
