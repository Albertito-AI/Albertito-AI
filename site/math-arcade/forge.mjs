const marks = { '+': '+', '-': '−', '*': '×', '/': '÷' };
const names = { '+': 'Add', '-': 'Subtract', '*': 'Multiply', '/': 'Divide' };
const allOps = Object.keys(marks);

export function fraction(n, d = 1) {
  if (!Number.isSafeInteger(n) || !Number.isSafeInteger(d) || d === 0) return null;
  let a = Math.abs(n);
  let b = Math.abs(d);
  while (b) [a, b] = [b, a % b];
  return { n: n === 0 ? 0 : n * Math.sign(d) / a, d: Math.abs(d) / a };
}

export function calculate(left, op, right) {
  const { n: a, d: b } = left;
  const { n: c, d } = right;
  switch (op) {
    case '+': return fraction(a * d + b * c, b * d);
    case '-': return fraction(a * d - b * c, b * d);
    case '*': return fraction(a * c, b * d);
    case '/': return fraction(a * d, b * c);
    default: return null;
  }
}

function readable(value) {
  const n = String(value.n).replace('-', '−');
  return value.d === 1 ? n : n + '/' + value.d;
}

function seeded(seed) {
  let x = seed >>> 0;
  return function next(max) {
    x = (x + 0x6D2B79F5) >>> 0;
    let z = Math.imul(x ^ (x >>> 15), 1 | x);
    z = (z + Math.imul(z ^ (z >>> 7), z | 61)) ^ z;
    return Math.floor(((z ^ (z >>> 14)) >>> 0) / 4294967296 * max);
  };
}

function shuffle(values, pick) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i--) {
    const j = pick(i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

function moves(values, ops = allOps, integerOnly = false) {
  const possible = [];
  for (let a = 0; a < values.length; a++) {
    for (let b = 0; b < values.length; b++) {
      if (a === b) continue;
      for (const op of ops) {
        if ((op === '+' || op === '*') && a > b) continue;
        const value = calculate(values[a], op, values[b]);
        if (value && (!integerOnly || value.d === 1)) possible.push({ a, b, op, value });
      }
    }
  }
  return possible;
}

function replacePair(values, step) {
  return [...values.filter((_, i) => i !== step.a && i !== step.b), step.value];
}

function stateKey(values) {
  return values.map(x => x.n + '/' + x.d).sort().join(',');
}

export function findRoute(values, target, { ops = allOps, integerOnly = false } = {}) {
  const dead = new Set();
  function visit(state) {
    if (state.length === 1) return state[0].n === target && state[0].d === 1 ? [] : null;
    const key = stateKey(state);
    if (dead.has(key)) return null;
    for (const step of moves(state, ops, integerOnly)) {
      const rest = visit(replacePair(state, step));
      if (rest !== null) return [step, ...rest];
    }
    dead.add(key);
    return null;
  }
  return visit(values);
}

function targetCandidates(numbers, ops, integerOnly = false) {
  const found = new Set();
  const seen = new Set();
  function visit(values) {
    if (values.length === 1) {
      const { n, d } = values[0];
      if (d === 1 && n >= 12 && n <= 84) found.add(n);
      return;
    }
    const key = stateKey(values);
    if (seen.has(key)) return;
    seen.add(key);
    for (const step of moves(values, ops, integerOnly)) visit(replacePair(values, step));
  }
  visit(numbers.map(n => fraction(n)));
  return found;
}

export function makeForge(level, seed) {
  const pick = seeded(seed);
  if (level === 0) {
    const a = 1 + pick(5), b = 1 + pick(5), c = 2 + pick(4), d = 2 + pick(6);
    return { numbers: shuffle([a, b, c, d], pick), target: (a + b) * c + d };
  }
  for (let attempt = 0; attempt < 12; attempt++) {
    const nums = Array.from({ length: 4 }, () => 2 + pick(level === 2 ? 11 : 8));
    const attainable = targetCandidates(nums, allOps, level !== 2);
    const easier = targetCandidates(nums, level === 2 ? allOps : ['+', '*'], true);
    const targets = [...attainable].filter(t => !easier.has(t)).sort((a, b) => a - b);
    if (targets.length) return { numbers: nums, target: targets[pick(targets.length)] };
  }
  // Both fallbacks retain the mathematical difficulty guarantee of their tier.
  if (level === 2) return { numbers: shuffle([3, 3, 8, 8], pick), target: 24 };
  return { numbers: shuffle([2, 3, 5, 8], pick), target: 14 };
}

export function initialTiles(numbers) {
  return numbers.map(n => ({ ...fraction(n), expr: String(n) }));
}

export function combine(tiles, a, op, b) {
  if (a === b || !tiles[a] || !tiles[b] || !Object.hasOwn(marks, op)) return null;
  const value = calculate(tiles[a], op, tiles[b]);
  if (!value) return null;
  const expr = '(' + tiles[a].expr + ' ' + marks[op] + ' ' + tiles[b].expr + ')';
  return replacePair(tiles, { a, b, value: { ...value, expr } });
}

export function mount(root, { level = 0, seed = 0, onWin = () => {} } = {}) {
  const { numbers, target } = makeForge(level, seed);
  let tiles = initialTiles(numbers);
  let past = [];
  let selected = null;
  let operation = null;
  let hintStage = 0;
  let won = false;
  const instruction = 'Choose a tile, an operation, then a second tile.';
  const board = document.createElement('section');
  board.className = 'tf-game';
  board.setAttribute('aria-label', 'Target Forge board');
  board.innerHTML = `
    <div class="tf-display">
      <div class="tf-goal"><span>Target</span><strong></strong></div>
      <div class="tf-display-copy"><b>Use all four numbers</b><p></p></div>
    </div>
    <div class="tf-tiles" role="group" aria-label="Number tiles"></div>
    <div class="tf-operations" role="group" aria-label="Arithmetic operations"></div>
    <p class="tf-message" role="status" aria-live="polite" aria-atomic="true"></p>
    <div class="tf-bottom">
      <div class="tf-actions"><button type="button" data-action="undo">Undo</button><button type="button" data-action="restart">Reset</button><button type="button" data-action="hint">Hint</button></div>
      <ol class="tf-history" aria-label="Calculations"></ol>
    </div>`;
  root.replaceChildren(board);
  const tileList = board.querySelector('.tf-tiles');
  const operations = board.querySelector('.tf-operations');
  const trail = board.querySelector('.tf-history');
  const message = board.querySelector('.tf-message');
  board.querySelector('.tf-goal strong').textContent = String(target);
  board.querySelector('.tf-display-copy p').textContent = [
    'Three combinations will get you there. Try adding a pair first.',
    'At least one subtraction or division is needed.',
    'Every solution passes through a fraction before it returns to a whole number.'
  ][level] || 'Each move combines two tiles into one.';

  function draw() {
    tileList.replaceChildren();
    for (let i = 0; i < 4; i++) {
      const tile = tiles[i];
      if (!tile) {
        const slot = document.createElement('span');
        slot.className = 'tf-empty';
        slot.setAttribute('aria-hidden', 'true');
        tileList.append(slot);
        continue;
      }
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'tf-tile';
      button.dataset.tile = String(i);
      button.setAttribute('aria-label', 'Tile ' + (i + 1) + ', value ' + readable(tile));
      button.setAttribute('aria-pressed', String(i === selected));
      button.disabled = tiles.length === 1;
      if (tile.d === 1) button.textContent = readable(tile);
      else {
        const frac = document.createElement('span');
        frac.className = 'tf-fraction';
        for (const n of [tile.n, tile.d]) {
          const part = document.createElement('span');
          part.textContent = String(n).replace('-', '−');
          frac.append(part);
        }
        button.append(frac);
      }
      tileList.append(button);
    }
    operations.replaceChildren();
    for (const [op, name] of Object.entries(names)) {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.operation = op;
      button.textContent = marks[op];
      button.title = name;
      button.setAttribute('aria-label', name);
      button.setAttribute('aria-pressed', String(operation === op));
      button.disabled = selected === null || tiles.length === 1;
      operations.append(button);
    }
    board.querySelector('[data-action="undo"]').disabled = past.length === 0 || won;
    board.querySelector('[data-action="restart"]').disabled = (!past.length && selected === null) || won;
    const hintButton = board.querySelector('[data-action="hint"]');
    hintButton.disabled = won;
    hintButton.textContent = hintStage === 1 ? 'More hint' : 'Hint';
    trail.replaceChildren();
    for (const old of past) {
      const li = document.createElement('li');
      li.textContent = old.line;
      trail.append(li);
    }
  }

  function announce(text) {
    message.textContent = text;
  }

  function focusTile(id) {
    const button = tileList.querySelector('[data-tile="' + id + '"]');
    if (button && !button.disabled) button.focus({ preventScroll: true });
  }

  function chooseTile(i, keyboard) {
    if (won || tiles.length < 2 || !tiles[i]) return;
    if (selected === null || operation === null || i === selected) {
      selected = selected === i ? null : i;
      operation = null;
      draw();
      announce(selected === null ? instruction : 'Starting with ' + readable(tiles[i]) + '. Choose an operation.');
      if (keyboard && selected !== null) operations.querySelector('button').focus({ preventScroll: true });
      else if (keyboard) focusTile(i);
      return;
    }
    const left = tiles[selected], right = tiles[i];
    const next = combine(tiles, selected, operation, i);
    if (!next) {
      announce('Division by zero is undefined. Choose another tile or operation.');
      return;
    }
    const result = next.at(-1);
    const line = readable(left) + ' ' + marks[operation] + ' ' + readable(right) + ' = ' + readable(result);
    past.push({ tiles, line });
    tiles = next;
    selected = null;
    operation = null;
    hintStage = 0;
    won = tiles.length === 1 && result.n === target && result.d === 1;
    draw();
    if (won) {
      const proof = result.expr.slice(1, -1) + ' = ' + target + '.';
      announce(proof);
      onWin({ explanation: proof + ' All four original numbers are used once.', details: 'Three combinations' });
    } else if (tiles.length === 1) {
      announce(line + '. The target is ' + target + '. Undo a move to try a different route.');
      if (keyboard) board.querySelector('[data-action="undo"]').focus({ preventScroll: true });
    } else {
      announce(line + '. Choose your next pair.');
      if (keyboard) focusTile(0);
    }
  }

  function chooseOperation(op, keyboard) {
    if (selected === null || won || !Object.hasOwn(marks, op)) return;
    operation = op;
    draw();
    announce(readable(tiles[selected]) + ' ' + marks[op] + ' … Choose the second tile.');
    if (keyboard) focusTile(selected === 0 ? 1 : 0);
  }

  function hint() {
    const route = findRoute(tiles, target);
    if (!route || !route.length) {
      announce('This position has no route to ' + target + '. Undo your last combination to recover.');
      return;
    }
    const step = route[0];
    const left = readable(tiles[step.a]);
    const right = readable(tiles[step.b]);
    hintStage = Math.min(2, hintStage + 1);
    const hintButton = board.querySelector('[data-action="hint"]');
    hintButton.textContent = hintStage === 1 ? 'More hint' : 'Hint';
    announce(hintStage === 1
      ? 'A solution from here starts by combining ' + left + ' and ' + right + '.'
      : 'Try ' + left + ' ' + marks[step.op] + ' ' + right + ' = ' + readable(step.value) + ' next.');
  }

  function action(kind, keyboard) {
    if (won) return;
    if (kind === 'hint') { hint(); return; }
    if (kind === 'undo') {
      if (!past.length) return;
      tiles = past.pop().tiles;
    } else if (kind === 'restart') {
      tiles = initialTiles(numbers);
      past = [];
    } else return;
    selected = null;
    operation = null;
    hintStage = 0;
    draw();
    announce(kind === 'undo' ? 'Last combination undone. ' + instruction : 'Tiles reset. ' + instruction);
    if (keyboard) focusTile(0);
  }

  function click(event) {
    const button = event.target.closest('button');
    if (!button || button.disabled || !board.contains(button)) return;
    const keyboard = event.detail === 0;
    if (Object.hasOwn(button.dataset, 'tile')) chooseTile(Number(button.dataset.tile), keyboard);
    else if (button.dataset.operation) chooseOperation(button.dataset.operation, keyboard);
    else action(button.dataset.action, keyboard);
  }

  function keydown(event) {
    if (event.altKey || event.ctrlKey || event.metaKey || event.repeat || won) return;
    if (/^[1-4]$/.test(event.key)) {
      event.preventDefault();
      chooseTile(Number(event.key) - 1, true);
    } else if (allOps.includes(event.key)) {
      event.preventDefault();
      chooseOperation(event.key, true);
    } else if (event.key === 'Escape') {
      selected = null;
      operation = null;
      draw();
      announce(instruction);
      focusTile(0);
    }
  }

  board.addEventListener('click', click);
  board.addEventListener('keydown', keydown);
  draw();
  announce(instruction);
  return () => {
    board.removeEventListener('click', click);
    board.removeEventListener('keydown', keydown);
  };
}
