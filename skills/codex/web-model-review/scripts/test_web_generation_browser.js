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

test('ChatGPT can verify long input, submit once and require final controls beyond the snapshot', async () => {
  const {driver} = fixture();
  driver.service = 'chatgpt';
  let value = '', clicks = 0, stop = false, done = false;
  const editor = {count: async () => 1, fill: async text => {value = text;}, evaluate: async fn => fn({value})};
  driver.page.getByRole = (role, {name}) => {
    if (role === 'textbox' && name === 'ChatGPT에게 물어보세요') return editor;
    if (role === 'button') return {
      count: async () => name === '보내기' ? 1 : name === 'Stop generating' ? Number(stop) : name === 'Regenerate' ? Number(done) : 0,
      click: async () => {assert.equal(name, '보내기'); clicks++;},
    };
    throw Error('Unexpected ChatGPT control');
  };
  driver.gate = async () => ({});
  driver.history = async () => ({users: [], answers: []});
  const prompt = 'source line\n'.repeat(4000);
  assert.equal((await driver.fill(prompt)).input_matches, true);
  await driver.submit(prompt);
  assert.equal(clicks, 1);
  driver.history = async () => ({users: [prompt], answers: ['answer']});
  assert.equal((await driver.collect(prompt)).complete, false);
  done = true; stop = true;
  assert.equal((await driver.collect(prompt)).complete, false);
  stop = false;
  assert.equal((await driver.collect(prompt)).complete, true);
  await assert.rejects(driver.submit(prompt), /Existing conversation/);
  assert.equal(clicks, 1);
});

test('hidden generic quota descriptions do not block Pro, while a visible quota notice does', async () => {
  const {driver} = fixture();
  const attributes = {};
  const parent = {hidden: false, parentElement: null, getAttribute: key => attributes[key] ?? null,
    classList: {contains: () => false}, style: {display: 'block', visibility: 'visible', opacity: '1'}};
  let srOnly = true;
  const notice = {textContent: '사용 한도에 도달했습니다', children: [], parentElement: parent,
    hidden: false, getClientRects: () => [{}], getAttribute: () => null,
    classList: {contains: name => name === 'sr-only' && srOnly},
    style: {display: 'block', visibility: 'visible', opacity: '1'}};
  const thumb = {getAttribute: attr => ({'aria-valuemin': '0', 'aria-valuemax': '4', 'aria-valuenow': '4'})[attr]};
  const row = {querySelector: () => thumb, getAttribute: () => 'false'};
  const el = {parentElement: null, querySelectorAll: selector => selector === '*' ? [notice] : [],
    querySelector: selector => selector.includes('picker') ? {innerText: 'Pro'} : row,
    ownerDocument: {defaultView: {getComputedStyle: node => node.style}}};
  const menu = {evaluate: async (fn, selectors) => fn(el, selectors)};
  assert.equal((await driver.readChatPicker(menu)).slider.quota_notice, false);
  srOnly = false; attributes['aria-hidden'] = 'true';
  assert.equal((await driver.readChatPicker(menu)).slider.quota_notice, false);
  attributes['aria-hidden'] = 'false'; parent.style.opacity = '0';
  assert.equal((await driver.readChatPicker(menu)).slider.quota_notice, false);
  parent.style.opacity = '1';
  assert.equal((await driver.readChatPicker(menu)).slider.quota_notice, true);
});

test('ChatGPT paragraph input preserves URL literals, indentation and empty lines', async () => {
  const {driver} = fixture();
  driver.service = 'chatgpt';
  const lines = ['line 1', 'url = "https://example.com/"', '', '  indented', ''];
  driver.page.getByRole = () => ({count: async () => 1, evaluate: async fn => fn({
    innerText: 'line 1\n\nurl = "\nhttps://example.com/"\n\n\n\n\n  indented\n\n\n',
    childNodes: lines.map(textContent => ({nodeType: 1, tagName: 'P', textContent})),
  })});
  assert.equal(await driver.editorText(), lines.join('\n'));
});

test('ChatGPT history resolves the observed main DOM when the conversation snapshot ref is missing', async () => {
  const {driver} = fixture();
  driver.service = 'chatgpt';
  driver.tree = '[snapshot truncated at 16 KiB]';
  driver.page.locator = selector => {
    if (selector === '[data-user-message-bubble]') return {count: async () => 1};
    if (selector === '[data-user-message-bubble] button') return {count: async () => 0};
    assert.equal(selector, 'main');
    return {first: () => ({evaluate: async fn => fn({querySelectorAll: query =>
      query === '[data-user-message-bubble]' ? [{querySelector: () => ({nodeType: 1, tagName: 'DIV', hidden: false,
        getAttribute: () => null, childNodes: [{nodeType: 3, textContent: 'exact prompt'}]})}] : []})})};
  };
  const history = await driver.history();
  assert.deepEqual(Array.from(history.users), ['exact prompt\n']);
  assert.equal(history.answers.length, 0);
});

test('code string spaces and indentation cannot be accepted through whitespace normalization', async () => {
  const {driver} = fixture();
  driver.service = 'chatgpt';
  const prompt = 'value = "a  b"\n';
  driver.page.getByRole = () => ({count: async () => 1, fill: async () => {},
    evaluate: async fn => fn({value: 'value = "a b"\n'})});
  await assert.rejects(driver.fill(prompt), /Editor input differs/);
  assert.equal(driver.promptMatches({users: ['value = "a b"\n']}, prompt), false);
  driver.service = 'aistudio';
  const packet = '# 검토 요청\n질문\n\n# 세부 자료\n```\n  value = "a  b"\n```\n';
  assert.equal(driver.promptMatches({users: [packet.replace('a  b', 'a b')],
    user_packets: [{codes: ['  value = "a b"'], prose: '검토 요청 질문 세부 자료'}]}, packet), false);
});

test('only the visible selectable final response is read, excluding hidden copies and progress surfaces', async () => {
  const {driver} = fixture();
  driver.service = 'chatgpt';
  const visible = {closest: () => null, querySelectorAll: () => [], innerText: 'final answer'};
  const hidden = {closest: () => ({hidden: true})};
  Object.defineProperty(hidden, 'innerText', {get() {throw Error('Hidden response was read');}});
  driver.page.locator = selector => {
    if (selector === '[data-user-message-bubble]') return {count: async () => 0};
    assert.equal(selector, 'main');
    return {first: () => ({evaluate: async fn => fn({querySelectorAll: query => {
      if (query === '[data-user-message-bubble]') return [];
      assert.equal(query, '[data-chatgpt-selection-conversation-id] [data-markdown-text-style="assistant-message"]:not([data-markdown-text-tone])');
      return [hidden, visible];
    }})})};
  };
  assert.deepEqual(Array.from((await driver.history()).answers), ['final answer']);
});
