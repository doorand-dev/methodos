// The full snapshot may lose every control after a long source packet.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function fixture() {
  let value = '';
  const ui = {stop: false, done: false};
  const editor = {count: async () => 1, fill: async text => {value = text;},
    evaluate: async fn => fn({value})};
  const page = {
    url: () => 'https://aistudio.google.com/prompts/new_chat',
    getByRole: (role, options = {}) => {
      if (role === 'main') return {evaluate: async () => []};
      if (role === 'textbox' && options.name === 'Enter a prompt') return editor;
      if (role === 'combobox' && options.name === 'Thinking Level') return {innerText: async () => 'Medium'};
      if (role === 'textbox' && options.name === 'Maximum output tokens') return {inputValue: async () => '65536'};
      if (role === 'button' && options.name === 'No API key selected') return {count: async () => 1};
      if (role === 'button' && options.name === 'Good response') return {count: async () => Number(ui.done)};
      if (role === 'button' && typeof options.name?.test === 'function') return {count: async () => Number(ui.stop)};
      throw Error(`Unexpected control ${role} ${options.name}`);
    },
    locator: ref => ref === 'footer' ? {evaluate: async () => ui.stop} : ({innerText: async () => {assert.equal(ref, 'thinking'); return 'Medium';},
      inputValue: async () => {assert.equal(ref, 'max'); return '65536';},
      getAttribute: async () => 'false'}),
  };
  const context = {snapshot: async (_, options) => ({tree: options.selector === 'ms-run-settings'
    ? '- button "Gemini 3.8 Flash gemini-3.8-flash description" [ref=model]\n' +
      '- combobox "Thinking Level" [ref=thinking]\n- textbox "Maximum output tokens" [ref=max]'
    : 'Temporary chat\n... [snapshot truncated at 16 KiB]', diff: ''})};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(require.resolve('./web_generation_browser.js'), 'utf8'), context);
  const driver = context.webgen;
  driver.page = page;
  driver.service = 'aistudio';
  return {driver, ui};
}

test('a 43K prompt can be filled and verified with a truncated snapshot', async () => {
  const {driver} = fixture();
  const prompt = 'source line\n'.repeat(4000);
  const result = await driver.fill(prompt);
  assert.equal(result.input_matches, true);
  assert.equal(result.editor_text, prompt);
});

test('configuration is read from the settings panel after full snapshot truncation', async () => {
  const {driver} = fixture();
  const result = await driver.inspect();
  assert.equal(result.model_id, 'gemini-3.8-flash');
  assert.equal(result.reasoning, 'Medium');
  assert.equal(result.temporary_chat, true);
  assert.equal(result.api_key, 'none');
});

test('completion controls remain authoritative when prompt and answer overflow the snapshot', async () => {
  const {driver, ui} = fixture();
  const prompt = 'p'.repeat(43000);
  driver.history = async () => ({users: [prompt], answers: ['a'.repeat(20000)]});
  ui.done = true;
  ui.stop = true;
  assert.equal((await driver.collect(prompt)).complete, false);
  ui.stop = false;
  const result = await driver.collect(prompt);
  assert.equal(result.complete, true);
  assert.equal(result.prompt_matches, true);
  assert.equal(result.output.length, 20000);
});

test('rendered review packets preserve every source block and all prose', () => {
  const {driver} = fixture();
  const prompt = '# 검토 요청\n질문\n\n# 세부 자료\n\n## file.py\n\n```\n  code = "# literal"\n```\n';
  const history = {users: ['rendered Markdown'], user_packets: [{
    prose: '검토 요청 질문 세부 자료 file.py', codes: ['  code = "# literal"\n'],
  }]};
  assert.equal(driver.promptMatches(history, prompt), true);
  history.user_packets[0].codes[0] = 'code = "# literal"\n';
  assert.equal(driver.promptMatches(history, prompt), false);
  history.user_packets[0].codes[0] = '  code = "# literal"\n';
  history.user_packets[0].prose = '검토 요청 세부 자료 file.py';
  assert.equal(driver.promptMatches(history, prompt), false);
  assert.equal(driver.promptMatches(history, '# arbitrary Markdown'), false);
});
