import { combine, findRoute, fraction, initialTiles, makeForge } from './forge.mjs';

const signs = { '+': '+', '-': '−', '*': '×', '/': '÷' };
const verbs = { '+': 'Add', '-': 'Subtract', '*': 'Multiply', '/': 'Divide' };
const plans = [
  'Atlas follows the single most promising continuation.',
  'Atlas compares up to eight promising continuations at each step, alongside the Easy line.',
  'Atlas also searches for an exact expression. You can beat an exact line with smaller working numbers.'
];

function display(value) {
  const numerator = String(value.n).replace('-', '−');
  return value.d === 1 ? numerator : numerator + '/' + value.d;
}

function distance(value, target) {
  return fraction(Math.abs(value.n - target * value.d), value.d);
}

function compareFraction(a, b) {
  return Math.sign(a.n * b.d - b.n * a.d);
}

export function startRound(numbers) {
  return { tiles: initialTiles(numbers), steps: [], peak: 0 };
}

export function forgeStep(state, a, op, b) {
  const tiles = combine(state.tiles, a, op, b);
  if (!tiles) return null;
  const value = tiles.at(-1);
  const peak = tiles.length === 1 ? state.peak : Math.max(state.peak, Math.abs(value.n), value.d);
  const line = display(state.tiles[a]) + ' ' + signs[op] + ' ' + display(state.tiles[b]) + ' = ' + display(value);
  return { tiles, peak, steps: [...state.steps, { a, b, op, line }] };
}

// Lower distance, then lower peak. An unfinished hand is ineligible for scoring.
export function compareRounds(a, b, target) {
  if (a.tiles.length !== 1 || b.tiles.length !== 1) throw new Error('Complete both hands before scoring');
  return compareFraction(distance(a.tiles[0], target), distance(b.tiles[0], target)) || Math.sign(a.peak - b.peak);
}

function comparePrefixes(a, b, target) {
  const difference = compareFraction(distance(a.tiles.at(-1), target), distance(b.tiles.at(-1), target));
  return difference || a.peak - b.peak;
}

function searchBeam(numbers, target, width) {
  let states = [startRound(numbers)];
  while (states[0].tiles.length > 1) {
    const next = [];
    for (const state of states) {
      for (let a = 0; a < state.tiles.length; a++) {
        for (let b = 0; b < state.tiles.length; b++) {
          if (a === b) continue;
          for (const op of Object.keys(signs)) {
            if (a > b && (op === '+' || op === '*')) continue;
            const result = forgeStep(state, a, op, b);
            if (result) next.push(result);
          }
        }
      }
    }
    next.sort((a, b) => comparePrefixes(a, b, target));
    states = next.slice(0, width);
  }
  return states[0];
}

export function agentRound(numbers, target, difficulty) {
  const easy = searchBeam(numbers, target, 1);
  if (difficulty === 0) return easy;
  const medium = searchBeam(numbers, target, 8);
  let best = compareRounds(medium, easy, target) < 0 ? medium : easy;
  if (difficulty === 2) {
    let exact = startRound(numbers);
    const route = findRoute(exact.tiles, target);
    if (route !== null) {
      for (const { a, b, op } of route) exact = forgeStep(exact, a, op, b);
      if (compareRounds(exact, best, target) < 0) best = exact;
    }
  }
  return best;
}

export function mount(root, { difficulty = 0, seed = 0, onFinish = () => {} } = {}) {
  const level = [0, 1, 2].includes(difficulty) ? difficulty : 0;
  const { numbers, target } = makeForge(level, seed >>> 0);
  const rival = agentRound(numbers, target, level);
  const board = document.createElement('section');
  board.className = 'tf-game';
  board.setAttribute('aria-label', 'Target Forge match');
  board.innerHTML = `
    <div class="tf-display">
      <div class="tf-goal"><span>Target</span><strong></strong></div>
      <div class="tf-display-copy"><b>One hand, two expressions</b><p>Use all four tiles once. Closest to the target wins. You can undo before you submit.</p></div>
    </div>
    <details><summary>Scoring and opponent strategy</summary>
    <p>Both players use the same four tiles. Equal distances are settled by the lower working peak. For each of your first two results, take the greater of its absolute numerator and positive denominator in lowest terms. Your peak is the larger of those two scores. The final result is excluded. Matching both scores is a draw.</p>
    <p data-plan></p></details>
    <div class="tf-tiles" role="group" aria-label="Number tiles"></div>
    <div class="tf-operations" role="group" aria-label="Arithmetic operations"></div>
    <p class="tf-message" role="status" aria-live="polite" aria-atomic="true"></p>
    <div class="tf-bottom"><div class="tf-actions"><button type="button" data-action="undo">Undo</button>
    <button type="button" data-action="submit">Submit expression</button>
    <button type="button" data-action="concede">Concede round</button></div></div>
    <p data-peak></p><ol aria-label="Your calculations"></ol><section data-reveal hidden aria-label="Atlas result"><h3>Atlas’s calculations</h3><ol></ol><p></p></section>`;
  root.replaceChildren(board);
  board.querySelector('.tf-goal strong').textContent = String(target);
  board.querySelector('[data-plan]').textContent = plans[level];
  const tileBox = board.querySelector('.tf-tiles');
  const opBox = board.querySelector('.tf-operations');
  const status = board.querySelector('[role=status]');
  const reveal = board.querySelector('[data-reveal]');
  const undo = board.querySelector('[data-action=undo]');
  const submit = board.querySelector('[data-action=submit]');
  const concede = board.querySelector('[data-action=concede]');
  const history = [];
  let state = startRound(numbers);
  let selected = null;
  let operation = null;
  let finished = false;
  let confirming = false;
  const remove = new AbortController();

  function drawList(list, steps) {
    list.replaceChildren(...steps.map(step => {
      const item = document.createElement('li');
      item.textContent = step.line;
      return item;
    }));
  }

  function draw() {
    tileBox.replaceChildren(...state.tiles.map((value, index) => {
      const tile = document.createElement('button');
      tile.type = 'button';
      tile.className = 'tf-tile';
      tile.dataset.tile = String(index);
      tile.textContent = display(value);
      tile.setAttribute('aria-label', 'Tile ' + (index + 1) + ', value ' + display(value));
      tile.setAttribute('aria-pressed', String(index === selected));
      tile.disabled = finished || state.tiles.length === 1;
      return tile;
    }));
    opBox.replaceChildren(...Object.entries(signs).map(([op, sign]) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.op = op;
      button.textContent = sign;
      button.setAttribute('aria-label', verbs[op]);
      button.setAttribute('aria-pressed', String(op === operation));
      button.disabled = finished || selected === null;
      return button;
    }));
    undo.disabled = finished || !history.length;
    submit.disabled = finished || state.tiles.length !== 1;
    concede.disabled = finished;
    concede.textContent = confirming ? 'Confirm concession' : 'Concede round';
    board.querySelector('[data-peak]').textContent = state.steps.length ? 'Your working peak: ' + state.peak : '';
    drawList(board.querySelector('ol[aria-label]'), state.steps);
  }

  function finish(conceded) {
    if (finished || (!conceded && state.tiles.length !== 1)) return;
    finished = true;
    const comparison = conceded ? 1 : compareRounds(state, rival, target);
    const outcome = comparison < 0 ? 'win' : comparison > 0 ? 'loss' : 'draw';
    const describe = hand => display(hand.tiles[0]) + ' (distance ' + display(distance(hand.tiles[0], target)) + ', working peak ' + hand.peak + ')';
    const summary = (conceded ? 'You conceded.' : 'You made ' + describe(state) + '.') + ' Atlas made ' + describe(rival) + '.';
    selected = null;
    operation = null;
    confirming = false;
    draw();
    reveal.hidden = false;
    drawList(reveal.querySelector('ol'), rival.steps);
    reveal.querySelector('p').textContent = rival.tiles[0].expr + ' = ' + display(rival.tiles[0]);
    status.textContent = (outcome === 'win' ? 'You win. ' : outcome === 'draw' ? 'Draw. ' : 'Atlas wins. ') + summary;
    onFinish({ outcome, summary });
  }

  board.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button || button.disabled || finished || !board.contains(button)) return;
    if (button.dataset.action === 'concede') {
      if (confirming) return finish(true);
      confirming = true;
      concede.textContent = 'Confirm concession';
      status.textContent = 'Confirm to concede, or keep playing.';
      return;
    }
    confirming = false;
    if (button.dataset.action === 'submit') return finish(false);
    if (button.dataset.action === 'undo') {
      state = history.pop();
      selected = null;
      operation = null;
      status.textContent = 'Last combination undone.';
    } else if (button.dataset.op) {
      operation = button.dataset.op;
      status.textContent = display(state.tiles[selected]) + ' ' + signs[operation] + ' … Select a second tile.';
    } else if (button.dataset.tile !== undefined) {
      const index = Number(button.dataset.tile);
      if (selected !== null && operation && selected !== index) {
        const next = forgeStep(state, selected, operation, index);
        if (!next) {
          status.textContent = 'Division by zero is undefined. Choose a different tile or operation.';
          return;
        }
        history.push(state);
        state = next;
        selected = null;
        operation = null;
        status.textContent = state.steps.at(-1).line + (state.tiles.length === 1 ? '. Submit this expression or undo to revise it.' : '. Choose your next pair.');
      } else {
        selected = selected === index ? null : index;
        operation = null;
        status.textContent = selected === null ? 'Choose a tile.' : 'Starting with ' + display(state.tiles[selected]) + '. Choose an operation.';
      }
    }
    draw();
    if (event.detail === 0) {
      const nextFocus = state.tiles.length === 1 ? submit : selected === null ? tileBox.firstElementChild : operation ? tileBox.children[selected === 0 ? 1 : 0] : opBox.firstElementChild;
      nextFocus?.focus({ preventScroll: true });
    }
  }, { signal: remove.signal });
  draw();
  status.textContent = 'Choose a tile, an operation, then a second tile. Atlas’s line is hidden until the result.';
  return () => { remove.abort(); };
}
