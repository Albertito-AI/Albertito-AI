import { makeSudoku, findLogicalHint } from './sudoku-engine.mjs';

const digits = [1, 2, 3, 4, 5, 6, 7, 8, 9];
const savePrefix = 'atlas-sudoku-progress-v1:';
const resumeKey = 'atlas-sudoku-resume-v1';
const row = i => Math.floor(i / 9);
const col = i => i % 9;
const box = i => 3 * Math.floor(row(i) / 3) + Math.floor(col(i) / 3);
const coordinate = i => 'row ' + (row(i) + 1) + ', column ' + (col(i) + 1);
const peers = Array.from({ length: 81 }, (_, i) => Array.from({ length: 81 }, (_, j) => j)
  .filter(j => i !== j && (row(i) === row(j) || col(i) === col(j) || box(i) === box(j))));
const pencilDigits = mask => digits.filter(n => (mask & (1 << n)) !== 0);

function restore(key, givens) {
  try {
    const state = JSON.parse(localStorage.getItem(key));
    if (state?.opening !== givens.join('') || !/^[0-9]{81}$/.test(state.values) ||
      !Array.isArray(state.notes) || state.notes.length !== 81) return null;
    const values = Array.from(state.values, Number);
    if (givens.some((n, i) => n !== 0 && n !== values[i])) return null;
    if (state.notes.some(mask => !Number.isInteger(mask) || mask < 0 || mask > 1022 || mask % 2 !== 0)) return null;
    return {
      values,
      notes: state.notes.map((mask, i) => values[i] ? 0 : mask),
      selected: Number.isInteger(state.selected) && state.selected >= 0 && state.selected < 81 ? state.selected : givens.indexOf(0),
      pencil: state.pencil === true
    };
  } catch {
    return null;
  }
}

function storeProgress(key, state) {
  try {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const item = localStorage.key(i);
      if (item?.startsWith(savePrefix) && item !== key) keys.push(item);
    }
    const time = k => {
      try { return Number(JSON.parse(localStorage.getItem(k))?.updated) || 0; } catch { return 0; }
    };
    function pointTo(k) {
      const [level, seed] = k.slice(savePrefix.length).split(':').map(Number);
      localStorage.setItem(resumeKey, JSON.stringify({ level, seed }));
    }
    if (!state) {
      localStorage.removeItem(key);
      if (keys.length) pointTo(keys.sort((a, b) => time(b) - time(a))[0]);
      else localStorage.removeItem(resumeKey);
      return;
    }
    // One key per board keeps concurrent games independent. Bound old drafts.
    if (keys.length >= 12) {
      keys.sort((a, b) => time(a) - time(b)).slice(0, keys.length - 11)
        .forEach(k => localStorage.removeItem(k));
    }
    localStorage.setItem(key, JSON.stringify({ ...state, updated: Date.now() }));
    pointTo(key);
  } catch { /* Play remains available when browser storage is disabled or full. */ }
}

export function mount(root, { level, seed, onWin, puzzle: prepared }) {
  const { puzzle, solution } = prepared ?? makeSudoku(level, seed);
  const saveKey = savePrefix + level + ':' + seed;
  const saved = restore(saveKey, puzzle);
  const recovered = saved && !saved.values.every((n, i) => n === solution[i]) ? saved : null;
  let values = recovered?.values ?? puzzle.slice();
  let notes = recovered?.notes ?? Array(81).fill(0);
  let selected = recovered?.selected ?? puzzle.indexOf(0);
  let pencil = recovered?.pencil ?? false;
  let finished = false;
  let suggestion = null;
  const history = [];
  const controller = new AbortController();
  const listen = (el, type, fn) => el.addEventListener(type, fn, { signal: controller.signal });

  const panel = document.createElement('section');
  panel.className = 'sdk-game';
  panel.setAttribute('aria-label', 'Sudoku puzzle');
  panel.innerHTML = `
    <p class="sdk-intro">Fill every row, column and 3 × 3 box with the digits 1–9, once each.</p>
    <div class="sdk-layout">
      <div class="sdk-board-wrap">
        <div class="sdk-grid" role="grid" aria-label="Sudoku. Use arrow keys to select a cell." aria-rowcount="9" aria-colcount="9"></div>
        <div class="sdk-progress"><span class="sdk-bar" aria-hidden="true"><i></i></span><span class="sdk-progress-text"></span></div>
      </div>
      <div class="sdk-tools">
        <p class="sdk-location"></p>
        <div class="sdk-pad" role="group" aria-label="Number pad"></div>
        <div class="sdk-actions">
          <button type="button" data-operation="pencil" aria-pressed="false">Pencil marks</button>
          <button type="button" data-operation="erase">Erase</button>
          <button type="button" data-operation="undo">Undo</button>
          <button type="button" data-operation="hint">Hint</button>
        </div>
        <div class="sdk-help"><p class="sdk-message" role="status" aria-live="polite"></p>
          <button class="sdk-apply" type="button" hidden></button></div>
        <details class="sdk-keys"><summary>Keyboard controls</summary><p>Use the arrow keys to move and 1–9 to write. Press N for pencil marks, Backspace or Delete to erase, and Ctrl/⌘ + Z to undo. Home and End jump across a row.</p></details>
      </div>
    </div>`;
  const get = selector => panel.querySelector(selector);
  const grid = get('.sdk-grid');
  const pad = get('.sdk-pad');
  const message = get('.sdk-message');
  const apply = get('.sdk-apply');
  const buttons = {};
  panel.querySelectorAll('[data-operation]').forEach(button => { buttons[button.dataset.operation] = button; });
  const cells = [];
  for (let r = 0; r < 9; r++) {
    const group = document.createElement('div');
    group.className = 'sdk-row';
    group.setAttribute('role', 'row');
    group.setAttribute('aria-rowindex', String(r + 1));
    for (let c = 0; c < 9; c++) {
      const i = r * 9 + c;
      const slot = document.createElement('div');
      slot.className = 'sdk-slot';
      slot.setAttribute('role', 'gridcell');
      slot.setAttribute('aria-colindex', String(c + 1));
      slot.setAttribute('aria-readonly', String(Boolean(puzzle[i])));
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'sdk-cell';
      button.dataset.i = i;
      const glyph = document.createElement('span');
      glyph.className = 'sdk-glyph';
      glyph.setAttribute('aria-hidden', 'true');
      button.append(glyph);
      slot.append(button);
      group.append(slot);
      cells.push({ slot, button, glyph, lastFace: '' });
    }
    grid.append(group);
  }
  for (const n of digits) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.digit = n;
    button.textContent = n;
    pad.append(button);
  }
  root.replaceChildren(panel);

  function save() {
    if (finished || (values.every((v, i) => v === puzzle[i]) && !notes.some(Boolean))) {
      storeProgress(saveKey, null);
    } else {
      storeProgress(saveKey, { opening: puzzle.join(''), values: values.join(''), notes, selected, pencil });
    }
  }

  function render() {
    const duplicate = values.map((v, i) => v && peers[i].some(j => values[j] === v));
    for (let i = 0; i < 81; i++) {
      const { slot, button, glyph } = cells[i];
      const v = values[i];
      const mask = notes[i];
      button.classList.toggle('sdk-given', Boolean(puzzle[i]));
      button.classList.toggle('sdk-related', peers[selected].includes(i));
      button.classList.toggle('sdk-matching', Boolean(v && v === values[selected]));
      button.classList.toggle('sdk-selected', i === selected);
      button.classList.toggle('sdk-conflict', Boolean(duplicate[i]));
      button.tabIndex = selected === i ? 0 : -1;
      slot.setAttribute('aria-selected', String(i === selected));
      const marks = !v && mask ? pencilDigits(mask) : [];
      const face = v + '/' + mask;
      if (face !== cells[i].lastFace) {
        glyph.className = marks.length ? 'sdk-glyph sdk-marks' : 'sdk-glyph';
        glyph.replaceChildren();
        if (v) glyph.textContent = String(v);
        else if (marks.length) for (const n of digits) {
          const mark = document.createElement('span');
          mark.textContent = mask & (1 << n) ? String(n) : '';
          glyph.append(mark);
        }
        cells[i].lastFace = face;
      }
      const description = v ? String(v) + (puzzle[i] ? ', given' : ', your entry') :
        (marks.length ? 'pencil marks ' + marks.join(', ') : 'empty');
      button.setAttribute('aria-label', coordinate(i) + ', ' + description + (duplicate[i] ? ', duplicate' : ''));
    }
    const count = values.filter(Boolean).length;
    get('.sdk-progress-text').textContent = count + ' / 81 filled';
    get('.sdk-bar i').style.width = (count / 81 * 100) + '%';
    get('.sdk-location').textContent = 'Row ' + (row(selected) + 1) + ' · Column ' + (col(selected) + 1) + (puzzle[selected] ? ' · Given' : '');
    for (const button of pad.children) {
      button.disabled = finished || Boolean(puzzle[selected]);
      button.setAttribute('aria-label', (pencil ? 'Toggle pencil mark ' : 'Enter ') + button.dataset.digit);
    }
    buttons.pencil.setAttribute('aria-pressed', String(pencil));
    buttons.pencil.disabled = finished;
    buttons.erase.disabled = finished || Boolean(puzzle[selected]) || (!values[selected] && !notes[selected]);
    buttons.undo.disabled = finished || !history.length;
    buttons.hint.disabled = finished;
    apply.hidden = !suggestion || finished;
    if (suggestion) apply.textContent = suggestion.revealed ? 'Place hinted digit' :
      suggestion.kind === 'checked' ? 'Reveal checked digit' : 'Explain the digit';
  }

  function select(i, focus = false) {
    if (i !== selected) {
      selected = i;
      suggestion = null;
      message.textContent = '';
      render();
    }
    if (focus) cells[i].button.focus({ preventScroll: true });
  }

  function remember() {
    history.push({ values: values.slice(), notes: notes.slice(), selected });
    if (history.length > 120) history.shift();
  }

  function complete() {
    if (!values.every((n, i) => n === solution[i])) return false;
    finished = true;
    suggestion = null;
    save();
    render();
    message.textContent = 'Sudoku complete. Every row, column and box contains all nine digits.';
    onWin({ details: 'All 81 cells complete · ' + puzzle.filter(Boolean).length + ' starting clues',
      explanation: 'Each row, each column and each 3 × 3 box contains the digits 1–9 exactly once. The starting clues admit exactly one completed grid.' });
    return true;
  }

  function write(n, asNote = false) {
    if (finished || puzzle[selected]) return;
    if (asNote && values[selected]) {
      message.textContent = 'Erase this entry first to add pencil marks.';
      return;
    }
    if (!asNote && values[selected] === n && !notes[selected]) return;
    remember();
    suggestion = null;
    if (asNote) {
      notes[selected] ^= 1 << n;
      message.textContent = (notes[selected] & (1 << n) ? 'Added' : 'Removed') + ' pencil mark ' + n + '.';
    } else {
      values[selected] = n;
      notes[selected] = 0;
      if (n) for (const j of peers[selected]) notes[j] &= ~(1 << n);
      const duplicate = n && peers[selected].some(j => values[j] === n);
      message.textContent = duplicate ? 'This digit repeats in its row, column or box. You can change either editable entry.' :
        n ? 'Entered ' + n + ' in ' + coordinate(selected) + '.' : 'Cell cleared.';
      if (n && complete()) return;
    }
    render();
    save();
  }

  function togglePencil() {
    if (finished) return;
    pencil = !pencil;
    suggestion = null;
    message.textContent = pencil ? 'Pencil marks on. Pick a digit to add or remove it.' : 'Pencil marks off. Pick a digit to enter an answer.';
    render();
    save();
  }

  function undo() {
    const old = history.pop();
    if (!old || finished) return;
    values = old.values;
    notes = old.notes;
    selected = old.selected;
    suggestion = null;
    message.textContent = 'Last edit undone.';
    render();
    save();
  }

  function hint() {
    if (finished) return;
    const error = values.findIndex((n, i) => n && n !== solution[i]);
    if (error !== -1) {
      select(error);
      suggestion = null;
      const duplicate = peers[error].find(i => values[i] === values[error]);
      message.textContent = 'Revisit ' + coordinate(error) + '. ' + (duplicate === undefined ?
        'A check against the unique solution shows that this entry cannot be correct. Try erasing it and checking the clues.' :
        'The same digit appears at ' + coordinate(duplicate) + '. Erase the selected entry and check the clues.');
    } else {
      const logical = findLogicalHint(values);
      const index = logical?.index ?? (!values[selected] ? selected : values.indexOf(0));
      if (index < 0) return;
      select(index);
      suggestion = { index, digit: logical?.digit ?? solution[index],
        kind: logical?.kind ?? 'checked', unit: logical?.unit, revealed: false };
      const place = coordinate(index);
      if (logical?.kind === 'naked') message.textContent = 'Look at ' + place + '. Cross out the digits already present in its row, column and box. Which digit remains?';
      else if (logical?.kind === 'hidden') message.textContent = 'Look at ' + place + '. Compare the empty squares in this ' + logical.unit + '. Which missing digit can go only here?';
      else message.textContent = 'Try ' + place + '. No naked or hidden single is available. You can work on the puzzle or reveal this cell from the unique solution.';
    }
    render();
  }

  function useHint() {
    if (!suggestion || suggestion.index !== selected || finished) return;
    const { digit, index, kind, unit } = suggestion;
    if (suggestion.revealed) {
      write(digit);
      if (!finished) cells[index].button.focus({ preventScroll: true });
      return;
    }
    suggestion.revealed = true;
    const place = coordinate(index);
    if (kind === 'naked') message.textContent = 'At ' + place + ', its row, column and box rule out every digit except ' + digit + '.';
    else if (kind === 'hidden') message.textContent = 'In this ' + unit + ', every other square is filled or ruled out for ' + digit + '. Only ' + place + ' can hold it.';
    else message.textContent = 'The unique solution has ' + digit + ' at ' + place + '. This value comes from checking the solution.';
    render();
  }

  listen(grid, 'click', event => {
    const target = event.target.closest('[data-i]');
    if (target) select(Number(target.dataset.i), true);
  });
  listen(grid, 'focusin', event => {
    const target = event.target.closest('[data-i]');
    if (target) select(Number(target.dataset.i));
  });
  listen(pad, 'click', event => {
    const target = event.target.closest('[data-digit]');
    if (target) write(Number(target.dataset.digit), pencil);
  });
  listen(buttons.pencil, 'click', togglePencil);
  listen(buttons.erase, 'click', () => write(0));
  listen(buttons.undo, 'click', undo);
  listen(buttons.hint, 'click', hint);
  listen(apply, 'click', useHint);
  listen(grid, 'keydown', event => {
    if (event.altKey) return;
    const key = event.key;
    if ((event.ctrlKey || event.metaKey) && key.toLowerCase() === 'z' && !event.shiftKey) {
      event.preventDefault();
      undo();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && key !== 'Home' && key !== 'End') return;
    let next = selected;
    switch (key) {
      case 'ArrowLeft': next = row(selected) * 9 + Math.max(0, col(selected) - 1); break;
      case 'ArrowRight': next = row(selected) * 9 + Math.min(8, col(selected) + 1); break;
      case 'ArrowUp': next = selected >= 9 ? selected - 9 : selected; break;
      case 'ArrowDown': next = selected < 72 ? selected + 9 : selected; break;
      case 'Home': next = event.ctrlKey || event.metaKey ? 0 : row(selected) * 9; break;
      case 'End': next = event.ctrlKey || event.metaKey ? 80 : row(selected) * 9 + 8; break;
      case 'Backspace': case 'Delete': case '0': write(0); break;
      case 'n': case 'N': togglePencil(); break;
      default:
        if (!/^[1-9]$/.test(key)) return;
        write(Number(key), pencil);
    }
    event.preventDefault();
    if (next !== selected) select(next, true);
  });

  render();
  message.textContent = recovered ? 'Your unfinished puzzle has been restored.' : 'Choose an empty square, then a digit.';
  return () => { controller.abort(); };
}
