const tiers = [
  { size: 3, min: 2, max: 4 },
  { size: 4, min: 5, max: 7 },
  { size: 5, min: 9, max: 12 }
];

export function bitCount(bits) {
  let count = 0;
  while (bits) {
    bits &= bits - 1;
    count += 1;
  }
  return count;
}

export function toggleMask(size, index) {
  const row = Math.floor(index / size);
  const col = index % size;
  let mask = 1 << index;
  if (row > 0) mask |= 1 << (index - size);
  if (row + 1 < size) mask |= 1 << (index + size);
  if (col > 0) mask |= 1 << (index - 1);
  if (col + 1 < size) mask |= 1 << (index + 1);
  return mask;
}

export function applyPresses(size, board, presses) {
  for (let i = 0; i < size * size; i += 1) {
    if (presses & (1 << i)) board ^= toggleMask(size, i);
  }
  return board;
}

// Once the first row of presses is chosen, each lit cell forces the press
// directly beneath it. All remaining choices follow, including on an edge.
export function minimumSolution(size, board) {
  const rowMask = (1 << size) - 1;
  let best = null;
  let minimum = Infinity;
  for (let first = 0; first <= rowMask; first += 1) {
    let presses = 0;
    let previous = 0;
    let current = first;
    for (let r = 0; r < size; r += 1) {
      presses |= current << (size * r);
      const row = (board >>> (size * r)) & rowMask;
      const lightFromThisRow = current ^ (current << 1) ^ (current >>> 1);
      const next = (row ^ previous ^ lightFromThisRow) & rowMask;
      previous = current;
      current = next;
    }
    if (current !== 0) continue;
    const weight = bitCount(presses);
    if (weight < minimum) {
      best = presses;
      minimum = weight;
    }
  }
  return best;
}

function seeded(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6D2B79F5) >>> 0;
    let t = Math.imul(state ^ (state >>> 15), state | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function generate(level, seed) {
  const { size, min, max } = tiers[level];
  const squares = size * size;
  const random = seeded(seed);
  function evaluate(pattern) {
    const board = applyPresses(size, 0, pattern);
    const solution = minimumSolution(size, board);
    const par = bitCount(solution);
    return par >= min && par <= max ? { size, board, par } : null;
  }
  for (let attempt = 0; attempt < 96; attempt += 1) {
    const cells = Array.from({ length: squares }, (_, i) => i);
    const count = min + Math.floor(random() * (max - min + 1));
    let presses = 0;
    for (let i = 0; i < count; i += 1) {
      const j = i + Math.floor(random() * (squares - i));
      [cells[i], cells[j]] = [cells[j], cells[i]];
      presses |= 1 << cells[i];
    }
    const puzzle = evaluate(presses);
    if (puzzle) return puzzle;
  }
  // Each fallback has been checked against the same difficulty gate.
  const fallback = [0x5, 0x1f, 0x1ff][level];
  const puzzle = evaluate(fallback);
  if (!puzzle) throw new Error('Parity Lights fallback failed its difficulty check.');
  return puzzle;
}

function cellName(size, i) {
  return String.fromCharCode(65 + Math.floor(i / size)) + (1 + i % size);
}

function element(tag, cssClass, text) {
  const el = document.createElement(tag);
  el.className = cssClass;
  if (text) el.textContent = text;
  return el;
}

export function mount(root, { level, seed, onWin, onMove, competitive = false }) {
  const { size, board: opening, par } = generate(level, seed);
  let board = opening;
  let history = [];
  let hinted = -1;
  let focused = 0;
  let preview = -1;
  let finished = false;
  const controller = new AbortController();
  const listen = (target, name, fn) => target.addEventListener(name, fn, { signal: controller.signal });

  const panel = element('section', 'parity-play');
  panel.setAttribute('aria-label', 'Parity Lights puzzle');
  const intro = element('p', 'parity-intro', 'Switch every light off. Press a tile to flip it and its neighbours above, below, left and right.');
  const stage = element('div', 'parity-stage');
  const frame = element('div', 'parity-frame');
  frame.style.setProperty('--parity-size', size);
  const columns = element('div', 'parity-columns');
  const rows = element('div', 'parity-rows');
  columns.setAttribute('aria-hidden', 'true');
  rows.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < size; i += 1) {
    columns.append(element('span', '', String(i + 1)));
    rows.append(element('span', '', String.fromCharCode(65 + i)));
  }
  const grid = element('div', 'parity-grid');
  grid.setAttribute('role', 'group');
  grid.setAttribute('aria-label', 'Lights grid. Use arrow keys to select a tile and Enter or Space to press it.');
  const cells = [];
  for (let i = 0; i < size * size; i += 1) {
    const cell = element('button', 'parity-cell');
    cell.type = 'button';
    cell.dataset.index = String(i);
    const lamp = element('span', 'parity-lamp');
    lamp.setAttribute('aria-hidden', 'true');
    cell.append(lamp);
    cells.push(cell);
    grid.append(cell);
  }
  frame.append(columns, rows, grid);
  stage.append(frame);

  const metrics = element('div', 'parity-metrics');
  const moves = element('span', '');
  const lights = element('span', '');
  metrics.append(moves, lights, element('span', '', 'Par ' + par));

  const actions = element('div', 'parity-actions');
  const undo = element('button', 'parity-action', 'Undo');
  const restart = element('button', 'parity-action', 'Restart');
  const hint = element('button', 'parity-action parity-hint', 'Hint');
  for (const button of [undo, restart, hint]) button.type = 'button';
  actions.append(undo, restart, hint);
  const message = element('p', 'parity-message');
  message.setAttribute('role', 'status');
  message.setAttribute('aria-live', 'polite');
  panel.append(intro, stage, metrics);
  if (!competitive) panel.append(actions);
  panel.append(message);
  root.replaceChildren(panel);

  function showPreview() {
    const mask = !finished && preview >= 0 ? toggleMask(size, preview) : 0;
    cells.forEach((cell, i) => cell.classList.toggle('parity-neighbour', i !== preview && !!(mask & (1 << i))));
  }
  function render() {
    for (const [i, cell] of cells.entries()) {
      const lit = !!(board & (1 << i));
      cell.classList.toggle('parity-on', lit);
      cell.classList.toggle('parity-marked', hinted === i);
      cell.setAttribute('aria-pressed', String(lit));
      cell.setAttribute('aria-label', cellName(size, i) + ', ' + (lit ? 'lit' : 'off') + (hinted === i ? ', suggested move' : ''));
      cell.tabIndex = i === focused ? 0 : -1;
    }
    moves.textContent = 'Moves ' + history.length;
    lights.textContent = 'Lights on ' + bitCount(board);
    undo.disabled = finished || !history.length;
    restart.disabled = finished || !history.length;
    hint.disabled = finished;
    showPreview();
  }

  listen(grid, 'click', event => {
    const cell = event.target.closest('button[data-index]');
    if (!cell || finished) return;
    const i = Number(cell.dataset.index);
    board ^= toggleMask(size, i);
    history.push(i);
    focused = i;
    hinted = -1;
    message.textContent = '';
    finished = board === 0;
    render();
    onMove?.(history.length);
    if (finished) {
      const details = history.length + ' moves · shortest solution ' + par;
      message.textContent = 'All lights off. ' + details + '.';
      onWin({ details, explanation: 'A light ends off when its starting state and all its flips add to an even number. Tapping a tile twice cancels out, so the order of your taps never changes the result.' });
    }
  });
  listen(grid, 'keydown', event => {
    const cell = event.target.closest('button[data-index]');
    if (!cell) return;
    const i = Number(cell.dataset.index);
    let next = i;
    const col = i % size;
    const row = Math.floor(i / size);
    switch (event.key) {
      case 'ArrowLeft': next = row * size + Math.max(0, col - 1); break;
      case 'ArrowRight': next = row * size + Math.min(size - 1, col + 1); break;
      case 'ArrowUp': next = Math.max(0, row - 1) * size + col; break;
      case 'ArrowDown': next = Math.min(size - 1, row + 1) * size + col; break;
      case 'Home': next = row * size; break;
      case 'End': next = row * size + size - 1; break;
      default: return;
    }
    event.preventDefault();
    cells[next].focus();
  });
  listen(grid, 'focusin', event => {
    const cell = event.target.closest('button[data-index]');
    if (!cell) return;
    cells[focused].tabIndex = -1;
    focused = Number(cell.dataset.index);
    cells[focused].tabIndex = 0;
    preview = focused;
    showPreview();
  });
  listen(grid, 'focusout', () => { preview = -1; showPreview(); });
  listen(grid, 'pointerover', event => {
    if (event.pointerType !== 'mouse') return;
    const cell = event.target.closest('button[data-index]');
    if (!cell) return;
    preview = Number(cell.dataset.index);
    showPreview();
  });
  listen(grid, 'pointerleave', () => { preview = -1; showPreview(); });
  listen(undo, 'click', () => {
    if (!history.length || finished) return;
    board ^= toggleMask(size, history.pop());
    hinted = -1;
    render();
    message.textContent = 'Last move undone. ' + bitCount(board) + ' lights remain.';
  });
  listen(restart, 'click', () => {
    if (finished) return;
    board = opening;
    history = [];
    hinted = -1;
    render();
    message.textContent = 'Opening grid restored.';
  });
  listen(hint, 'click', () => {
    if (finished) return;
    const solution = minimumSolution(size, board);
    hinted = 31 - Math.clz32(solution & -solution);
    render();
    const remaining = bitCount(solution);
    message.textContent = 'Press ' + cellName(size, hinted) + '. You can clear the current grid in ' + remaining + (remaining === 1 ? ' move.' : ' moves.');
  });
  render();
  return () => controller.abort();
}
