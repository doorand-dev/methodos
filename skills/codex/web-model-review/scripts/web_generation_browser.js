/* Loaded only inside `aside repl`. DOM UI only; no provider/network APIs. */
const CHAT_REASONING = ['Low', 'Medium', 'High', 'Extra High', 'Pro'];
const CHAT_PICKER = '[data-model-picker-view-toggle="true"]';
const CHAT_SLIDER = '[data-reasoning-slider="true"]';
const CHAT_PICKER_BUTTON = /^(ChatGPT 모델 선택|ChatGPT model selector)$/;

globalThis.webgen = {
  page: null,
  service: null,
  tree: '',
  async snap(selector) {
    const s = await snapshot(this.page, {interactive: true, ...(selector ? {selector} : {})});
    this.tree = s.tree;
    return s;
  },
  async attach(service, target) {
    const host = service === 'chatgpt' ? 'chatgpt.com' : 'aistudio.google.com';
    const matches = (await listBrowserTabs()).filter(t => new URL(t.url).hostname === host && (!target || t.targetId === target));
    if (matches.length !== 1) throw Error(`Expected one ${host} tab; found ${matches.length}. Open a blank temporary chat, or pass --tab.`);
    this.page = await attachBrowserTab(matches[0].targetId);
    this.service = service;
    await this.snap();
    return {tab_id: matches[0].targetId, url: this.page.url()};
  },
  ref(role, name) {
    for (const line of this.tree.split('\n')) {
      const m = line.match(/^\s*- ([\w]+) "([^"]*)" \[ref=([^\]]+)\]/);
      if (m && m[1] === role && (typeof name === 'string' ? m[2] === name : name.test(m[2]))) return m[3];
    }
    return null;
  },
  async click(role, name) {
    const ref = this.ref(role, name);
    if (!ref) throw Error(`Missing UI control: ${role} ${name}`);
    await this.page.locator(ref).click();
    await this.snap();
  },
  async waitRef(role, name) {
    for (let i = 0; i < 10; i++) {
      const ref = this.ref(role, name);
      if (ref) return ref;
      // A post-action snapshot already showed an unfinished transition.
      await sleep(250);
      await this.snap();
    }
    throw Error(`UI transition did not reveal ${role} ${name}`);
  },
  async editor() {
    // Long source packets exceed Aside's snapshot text limit. This exact
    // visible textarea was verified in the AI Studio UI; do not depend on its
    // value (or the controls after it) fitting inside a full-page snapshot.
    if (this.service === 'aistudio') {
      const field = this.page.getByRole('textbox', {name: 'Enter a prompt', exact: true});
      if (await field.count() === 1) return field;
      throw Error('Prompt editor unavailable; login, loading, or UI change');
    }
    const ref = this.ref('textbox', this.service === 'chatgpt' ? /^(ChatGPT에게 물어보세요|Ask anything)$/ : 'Enter a prompt');
    if (!ref) throw Error('Prompt editor unavailable; login, loading, or UI change');
    return this.page.locator(ref);
  },
  async editorText() {
    return (await this.editor()).evaluate(el => 'value' in el ? el.value : el.innerText);
  },
  norm(s) { return s.replace(/\s+/g, ' ').trim(); },
  promptMatches(history, prompt) {
    if (history.users.length !== 1) return false;
    if (this.norm(history.users[0]) === this.norm(prompt)) return true;
    // AI Studio renders our generated Markdown packet instead of displaying
    // its delimiters. Verify every code block exactly and all remaining text;
    // never strip Markdown-like characters from the source code itself.
    const raw = prompt.replace(/\r\n/g, '\n');
    if (this.service !== 'aistudio' || !raw.startsWith('# 검토 요청\n') || !raw.includes('\n# 세부 자료\n')) return false;
    const packet = history.user_packets?.[0];
    if (!packet) return false;
    const fences = /^(`{3,})[^\n]*\n([\s\S]*?)\n\1(?=\n|$)/gm;
    const codes = Array.from(raw.matchAll(fences), m => m[2]);
    const normalizeCode = s => s.replace(/\r\n/g, '\n').replace(/\n+$/, '');
    if (!codes.length || codes.length !== packet.codes.length ||
        codes.some((code, i) => normalizeCode(code) !== normalizeCode(packet.codes[i]))) return false;
    const prose = raw.replace(fences, '').replace(/^(?:#{1,6} |- )/gm, '');
    return prose.replace(/\s/g, '') === packet.prose.replace(/\s/g, '');
  },
  async gate() {
    // Match actual access UI, never keywords inside the user's prompt or output.
    if (/^\s*- heading "Upgrade to unlock /m.test(this.tree)) return {blocked: 'blocked_paid_access', reason: 'Upgrade to unlock model'};
    if (this.ref('button', /^(Log in|Sign in|로그인)$/)) return {blocked: 'blocked_login', reason: 'Login control displayed'};
    const root = this.service === 'chatgpt' ? this.page.locator('main').first() : this.page.getByRole('main');
    const messages = await root.evaluate(main =>
      Array.from(main.querySelectorAll('[role="alert"], [role="status"]'))
        .filter(n => !n.closest('[data-user-message-bubble], [data-markdown-text-style], [data-turn-role]') && n.getClientRects().length)
        .map(n => n.innerText).filter(Boolean));
    for (const reason of messages) {
      if (/usage limit|quota exceeded|rate limit|사용 한도|사용량.*(소진|초과)/i.test(reason)) return {blocked: 'blocked_usage_limit', reason};
      if (/upgrade|billing|payment|paid plan|결제|업그레이드/i.test(reason)) return {blocked: 'blocked_paid_access', reason};
      if (/error|failed|오류|실패/i.test(reason)) return {blocked: 'blocked_provider_error', reason};
    }
    return {};
  },
  async openChatPicker() {
    // Snapshot omits this popover's descendants. These DOM attributes were
    // verified against the visible menu on 2026-11-04, not app internal state.
    if (!(await this.page.locator(CHAT_PICKER).count())) {
      await this.click('button', CHAT_PICKER_BUTTON);
    }
    return this.page.locator(`[role="menu"]:has(${CHAT_PICKER})`);
  },
  async readChatPicker(menu) {
    return menu.evaluate((el, selectors) => {
      const items = Array.from(el.querySelectorAll('[role="menuitemradio"]')).map(n => ({
        label: n.innerText.trim(), selected: n.getAttribute('aria-checked') === 'true',
        disabled: n.getAttribute('aria-disabled') === 'true',
        description: (n.getAttribute('aria-describedby') || '').split(' ').map(id => el.ownerDocument.getElementById(id)?.textContent || '').join(' ').trim(),
      }));
      const toggle = el.querySelector(selectors.picker);
      const row = el.querySelector(selectors.slider);
      const thumb = row?.querySelector('[role="slider"]');
      const position = attr => {
        const value = thumb?.getAttribute(attr);
        return /^\d+$/.test(value ?? '') ? Number(value) : null;
      };
      const effort_label = toggle?.innerText.trim() || 'unknown';
      const text = el.innerText;
      return {
        models: items, effort_label, reasoning: effort_label.split('\n').at(-1).trim(),
        slider: thumb ? {
          min: position('aria-valuemin'), max: position('aria-valuemax'), value: position('aria-valuenow'),
          disabled: row.getAttribute('aria-disabled') === 'true',
          quota_notice: /사용 한도에 도달|usage limit|limit reached/i.test(text),
        } : null,
      };
    }, {picker: CHAT_PICKER, slider: CHAT_SLIDER});
  },
  async closeChatPicker(menu) {
    if (await menu.count()) await menu.press('Escape');
    await this.snap();
  },
  async chatModel() {
    const menu = await this.openChatPicker();
    try { return await this.readChatPicker(menu); }
    finally { await this.closeChatPicker(menu); }
  },
  reasoningMatches(info, target) {
    const slider = info.slider;
    return slider?.min === 0 && slider.max === CHAT_REASONING.length - 1 &&
      slider.value === CHAT_REASONING.indexOf(target) && info.reasoning === target;
  },
  async setChatReasoning(model, target) {
    const index = CHAT_REASONING.indexOf(target);
    if (index < 0) return {blocked: 'blocked_reasoning_unavailable', supported_reasoning: CHAT_REASONING};
    const menu = await this.openChatPicker();
    const row = menu.locator(CHAT_SLIDER);
    let issue = null;
    try {
      let current = await this.readChatPicker(menu);
      for (let step = 0; step <= CHAT_REASONING.length; step++) {
        if (current.models.find(m => m.selected)?.label !== model) {
          issue = 'blocked_model_mismatch';
          break;
        }
        if (!this.reasoningMatches(current, current.reasoning)) {
          issue = 'blocked_reasoning_ui';
          break;
        }
        if (target === 'Pro' && current.reasoning === target && (current.slider.disabled || current.slider.quota_notice)) {
          issue = current.slider.quota_notice ? 'blocked_usage_limit' : 'blocked_reasoning_unavailable';
          break;
        }
        if (current.reasoning === target) break;
        const direction = index > current.slider.value ? 1 : -1;
        const expected = CHAT_REASONING[current.slider.value + direction];
        await row.press(direction > 0 ? 'ArrowRight' : 'ArrowLeft');
        await this.snap();
        if (!(await menu.count())) break;
        current = await this.readChatPicker(menu);
        if (!this.reasoningMatches(current, expected)) {
          issue = target === 'Pro' && current.slider?.quota_notice ?
            'blocked_usage_limit' : 'blocked_reasoning_mismatch';
          break;
        }
      }
    } finally {
      await this.closeChatPicker(menu);
    }
    // Reopen the picker and check the persisted UI state before allowing a send.
    const verified = await this.inspect();
    if (issue) return {...verified, blocked: issue, required: target};
    if (verified.model !== model) return {...verified, blocked: 'blocked_model_mismatch'};
    if (!this.reasoningMatches(verified, target)) return {...verified, blocked: 'blocked_reasoning_mismatch', required: target};
    if (target === 'Pro' && (verified.slider.disabled || verified.slider.quota_notice)) return {
      ...verified, required: target, blocked: verified.slider.quota_notice ? 'blocked_usage_limit' : 'blocked_reasoning_unavailable',
    };
    return verified;
  },
  async inspect() {
    await this.snap();
    if (this.service === 'chatgpt') {
      const model = await this.chatModel();
      return {...model, model: model.models.find(m => m.selected)?.label || 'unknown',
        personalization: this.ref('button', /^(개인화되지 않음|Not personalized)$/) ? 'off' : this.ref('button', /^(개인화됨|Personalized)$/) ? 'on' : 'unknown',
        temporary_chat: Boolean(this.ref('button', /^(임시 채팅 끄기|Turn off temporary chat)$/)),
        system_instruction: 'unknown (provider system prompt not exposed)', tools: 'unknown',
      };
    }
    const pageTree = this.tree;
    // Keep configuration readable even when the prompt or response is large.
    await this.snap('ms-run-settings');
    const modelLine = this.tree.split('\n').find(l => /- button ".* gemini-[\w.-]+ /.test(l));
    const model = modelLine?.match(/- button "(.*?) (gemini-[\w.-]+) /);
    const thinking = this.ref('combobox', 'Thinking Level');
    const max = this.ref('textbox', 'Maximum output tokens');
    const switches = [];
    for (const line of this.tree.split('\n')) {
      const m = line.match(/- switch "([^"]+)" \[ref=([^\]]+)\]/);
      if (m) switches.push({name: m[1], checked: await this.page.getByRole('switch', {name: m[1], exact: true}).getAttribute('aria-checked')});
    }
    return {model: model?.[1] || 'unknown', model_id: model?.[2] || 'unknown',
      reasoning: thinking ? (await this.page.getByRole('combobox', {name: 'Thinking Level', exact: true}).innerText()).trim() : 'unknown',
      max_output_tokens: max ? await this.page.getByRole('textbox', {name: 'Maximum output tokens', exact: true}).inputValue() : 'unknown',
      temporary_chat: pageTree.includes('Temporary chat'),
      api_key: await this.page.getByRole('button', {name: 'No API key selected', exact: true}).count() === 1 ? 'none' : 'unknown',
      tools: switches, system_instruction: 'unknown', temperature: 'unknown', top_p: 'unknown',
      blocked: this.tree.includes('Upgrade to unlock') ? 'blocked_paid_access' : null,
    };
  },
  async prepare(model, reasoning, personalization, prompt) {
    await this.snap();
    const gate = await this.gate();
    if (gate.blocked) return gate;
    let info = await this.inspect();
    if (!info.temporary_chat) return {...info, blocked: 'blocked_not_temporary_chat'};
    const existing = await this.history();
    if (existing.users.length || existing.answers.length) return {...info, blocked: 'blocked_existing_conversation'};
    const current = await this.editorText();
    if (this.norm(current) && this.norm(current) !== this.norm(prompt)) return {...info, blocked: 'blocked_existing_draft'};
    if (this.service === 'chatgpt') {
      if (!CHAT_REASONING.includes(reasoning)) return {
        ...info, blocked: 'blocked_reasoning_unavailable', supported_reasoning: CHAT_REASONING,
      };
      const choice = info.models.find(m => m.label === model);
      if (!choice) return {...info, blocked: 'blocked_model_unavailable', reason: 'Requested exact name not in UI; no model substitution'};
      if (choice.disabled || /사용 한도|usage limit|잠김|locked/i.test(choice.description)) {
        return {...info, blocked: 'blocked_usage_or_access', reason: choice.description};
      }
      if (!choice.selected) {
        await this.openChatPicker();
        await this.page.locator(CHAT_PICKER).click();
        await this.snap();
        await this.page.getByRole('menuitemradio', {name: model, exact: true}).click();
        await this.snap();
      }
      info = await this.setChatReasoning(model, reasoning);
      if (info.blocked) return info;
      if (personalization === 'off' && info.personalization === 'on') {
        await this.click('button', /^(개인화됨|Personalized)$/);
        await this.click('menuitemradio', /^(개인화되지 않음 |Not personalized )/);
        info = await this.inspect();
      }
      if (personalization === 'off' && info.personalization !== 'off') return {...info, blocked: 'blocked_personalization_unknown'};
    } else {
      if (info.model_id !== model && info.model !== model) return {...info, blocked: 'blocked_model_mismatch', reason: 'Select the exact model in the AI Studio UI, then run again'};
      if (info.blocked) return info;
      if (info.api_key !== 'none') return {...info, blocked: 'blocked_paid_or_unknown_key'};
      if (info.reasoning !== reasoning) return {...info, blocked: 'blocked_reasoning_mismatch', required: reasoning};
      const requiredTools = ['Structured outputs', 'Code execution', 'Function calling', 'Grounding with Google Search', 'Browse the url context'];
      if (requiredTools.some(n => !info.tools.some(t => t.name === n)) || info.tools.some(t => t.checked !== 'false')) return {...info, blocked: 'blocked_tools_enabled_or_unknown'};
      await this.page.getByRole('button', {name: 'System instructions', exact: true}).click();
      await this.snap('mat-dialog-container');
      // Inspect the UI editor; never read hidden model reasoning or app stores.
      const field = this.page.getByRole('textbox', {name: 'System instructions', exact: true});
      if (await field.count() !== 1) return {...info, blocked: 'blocked_system_instruction_unknown'};
      info.system_instruction = await field.inputValue();
      // Finish the modal interaction in a separate REPL request. Scoped
      // snapshots and a close in the same request can leave its UI open.
      return {...info, close_system_instruction_panel: true,
        ...(info.system_instruction ? {blocked: 'blocked_nonempty_system_instruction'} : {})};
    }
    return info;
  },
  async closeInstructions() {
    await this.snap('mat-dialog-container');
    await this.page.getByRole('textbox', {name: 'System instructions', exact: true}).press('Escape');
    await this.snap();
    return {};
  },
  async readyAfterInstructions() {
    for (let i = 0; i < 10; i++) {
      await this.snap();
      if (!(await this.page.locator('mat-dialog-container').count())) {
        await this.editor();
        return {};
      }
      await sleep(250);
    }
    return {blocked: 'blocked_system_instruction_panel'};
  },
  async fill(prompt) {
    await this.snap();
    let warning = null;
    try { await (await this.editor()).fill(prompt); }
    catch (e) { warning = String(e); }
    await this.snap();
    const text = await this.editorText();
    if (this.norm(text) !== this.norm(prompt)) throw Error('Editor input differs from prompt');
    return {input_matches: true, editor_text: text, fill_warning: warning,
      comparison: text === prompt ? 'exact' : 'whitespace_normalized'};
  },
  async submit(prompt) {
    await this.snap();
    const existing = await this.history();
    if (existing.users.length || existing.answers.length) throw Error('Existing conversation; refusing duplicate submit');
    if (this.norm(await this.editorText()) !== this.norm(prompt)) throw Error('Editor changed before submission');
    if (this.service === 'aistudio') {
      const run = this.page.locator('footer button.ctrl-enter-submits');
      if (await run.count() !== 1 || !/^Run\s/.test(await run.innerText())) throw Error('Run control unavailable');
      await run.click();
      await this.snap();
    } else {
      await this.click('button', /^(보내기|Send prompt|Send)$/);
    }
    return {clicked: true};
  },
  async history() {
    // The service-specific final response selectors are verified before use.
    // Initial empty conversations can be established by the visible UI.
    if (this.service === 'chatgpt') {
      if (!this.ref('region', /^(대화|Conversation)$/)) {
        if (/heading \[level=1\]: "(임시 채팅|Temporary Chat)"/.test(this.tree)) return {users: [], answers: []};
        throw Error('Unrecognized conversation UI');
      }
      return this.page.locator(this.ref('region', /^(대화|Conversation)$/)).evaluate(region => {
      const users = Array.from(region.querySelectorAll('[data-user-message-bubble] [data-search-result-target]')).map(n => n.textContent);
      const answers = Array.from(region.querySelectorAll('[data-markdown-text-style="assistant-message"]')).map(n => {
        const blocks = n.querySelectorAll('[data-oai-writing-block-surface]');
        if (blocks.length === 1) {
          const block = blocks[0];
          const raw = block.getAttribute('data-markdown-copy-text');
          const visible = block.querySelector('[role="textbox"]')?.innerText;
          if (raw && visible && raw.replace(/\s+/g,' ').trim() === visible.replace(/\s+/g,' ').trim()) return raw;
          return null;
        }
        if (blocks.length) return null;
        return n.innerText;
      });
      return {users, answers};
      });
    }
    return this.page.getByRole('main').evaluate(main => {
      const renderedPrompt = n => {
        let text = n.innerText;
        for (const list of n.querySelectorAll('ol')) {
          const items = Array.from(list.querySelectorAll('li')).filter(li => li.closest('ol') === list);
          const start = list.start || 1;
          text = text.replace(list.innerText, items.map((li, i) => `${li.getAttribute('value') || start + i}. ${li.innerText}`).join('\n'));
        }
        return text;
      };
      const userTurns = Array.from(main.querySelectorAll('[data-turn-role="User"]'));
      const users = userTurns.map(turn =>
        Array.from(turn.querySelectorAll(':scope > .turn-content > ms-prompt-chunk > ms-text-chunk')).map(renderedPrompt).join('\n'));
      const user_packets = userTurns.map(turn => {
        const chunks = turn.querySelectorAll(':scope > .turn-content > ms-prompt-chunk > ms-text-chunk');
        if (chunks.length !== 1) return null;
        const prose = chunks[0].cloneNode(true);
        prose.querySelectorAll('ms-code-block').forEach(n => n.remove());
        return {prose: prose.textContent,
          codes: Array.from(chunks[0].querySelectorAll('ms-code-block pre code')).map(n => n.textContent)};
      });
      const answers = Array.from(main.querySelectorAll('[data-turn-role="Model"]')).map(turn =>
        // Explicit direct children exclude .thought-panel, even when its hidden
        // descendants have layout boxes. Never read or expand that content.
        Array.from(turn.querySelectorAll(':scope > .turn-content > ms-prompt-chunk > ms-text-chunk')).map(n => n.innerText).join('\n')).filter(Boolean);
      return {users, answers, user_packets};
    });
  },
  async collect(prompt) {
    await this.snap();
    const gate = await this.gate();
    if (gate.blocked) return {...gate, url: this.page.url()};
    const history = await this.history();
    const stop = this.service === 'aistudio'
      ? await this.page.locator('footer').evaluate(el => Array.from(el.querySelectorAll('button'))
        .some(n => n.getClientRects().length && /^Stop(?:\s|$)/.test(n.innerText.trim())))
      : this.ref('button', /^(중지|Stop|Stop generating|Stop response)$/);
    const done = this.service === 'aistudio'
      ? await this.page.getByRole('button', {name: 'Good response', exact: true}).count()
      : this.ref('button', /^(응답 다시 생성|Regenerate|Regenerate response)$/);
    return {url: this.page.url(), prompt_matches: this.promptMatches(history, prompt),
      output: history.answers.length === 1 ? history.answers[0] : null,
      user_count: history.users.length, answer_count: history.answers.length,
      complete: Boolean(done && !stop), extraction: this.service === 'chatgpt' ? 'visible assistant DOM; writing-block clipboard text checked against visible editor' : 'Model turn > .turn-content > ms-prompt-chunk > ms-text-chunk.innerText; thought-panel excluded',
    };
  },
};
