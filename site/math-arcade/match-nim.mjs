import { legalMoves, makeNim, optimalMove, playMove } from './nim.mjs';

const profiles = [
  'Atlas varies its moves, choosing at random from legal plays.',
  'Atlas tries to pair large heaps. With two heaps left, it knows the mirroring strategy.',
  'Atlas plays perfectly, leaving a zero nim-sum whenever possible.'
];

const letter = index => String.fromCharCode(65 + index);
const quantity = n => n + (n === 1 ? ' counter' : ' counters');

export function agentMove(heaps, difficulty, random = Math.random) {
  if (difficulty === 2) return optimalMove(heaps);
  if (!heaps.some(Boolean)) return null;
  if (difficulty === 0) {
    const moves = legalMoves(heaps);
    return moves[Math.floor(random() * moves.length)];
  }
  if (difficulty !== 1) throw new RangeError('Choose a difficulty from 0 to 2.');
  const ranked = heaps.map((count, heap) => ({ count, heap }))
    .filter(pile => pile.count > 0).sort((a, b) => b.count - a.count);
  const [largest, next, third] = ranked;
  if (!next) return { heap: largest.heap, take: largest.count };
  if (largest.count !== next.count) return { heap: largest.heap, take: largest.count - next.count };
  // Preserve the two equal leaders by clearing a third heap if available.
  return third ? { heap: third.heap, take: third.count } : { heap: largest.heap, take: 1 };
}

export function mount(root, { difficulty, seed, onFinish }) {
  let heaps = makeNim(difficulty, seed);
  let randomState = seed >>> 0;
  let selected = 0;
  let started = false;
  let finished = false;
  let disposed = false;
  const events = new AbortController();
  const view = document.createElement('section');
  view.className = 'nim-game';
  view.setAttribute('aria-label', 'Nim match');
  view.innerHTML = `
    <p class="nim-rules">Take one or more counters from a single heap. The player taking the last counter wins.</p>
    <p data-el="profile"></p>
    <div class="nim-table">
      <div class="nim-caption"><strong data-el="turn"></strong><span data-el="total"></span></div>
      <div class="nim-heaps" role="group" aria-label="Choose a heap" data-el="heaps"></div>
    </div>
    <div class="nim-controls">
      <label>Number to take <select data-el="count"></select></label>
      <button type="button" class="nim-take" data-el="take">Take counters</button>
    </div>
    <p class="nim-report" role="status" data-el="report"></p>
    <div class="nim-small-actions"><button type="button" data-el="second">Let Atlas move first</button></div>`;
  const el = Object.fromEntries(Array.from(view.querySelectorAll('[data-el]'), e => [e.dataset.el, e]));
  el.profile.textContent = profiles[difficulty];
  root.replaceChildren(view);
  const buttons = heaps.map((_, i) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'nim-heap';
    const tag = document.createElement('strong');
    tag.textContent = letter(i);
    const counters = document.createElement('span');
    counters.className = 'nim-tokens';
    counters.setAttribute('aria-hidden', 'true');
    const number = document.createElement('span');
    number.className = 'nim-count';
    button.append(tag, counters, number);
    button.addEventListener('click', () => {
      if (disposed || finished || heaps[i] === 0) return;
      selected = i;
      paint();
    }, { signal: events.signal });
    el.heaps.append(button);
    return { button, counters, number };
  });

  function random() {
    randomState = (Math.imul(1664525, randomState) + 1013904223) >>> 0;
    return randomState / 4294967296;
  }

  function preview() {
    const amount = Number(el.count.value);
    buttons.forEach(({ counters }, i) => {
      Array.from(counters.children).forEach((dot, j) => {
        dot.className = i === selected && j >= heaps[i] - amount ? 'nim-removing' : '';
      });
    });
  }

  function paint() {
    if (!heaps[selected]) selected = Math.max(0, heaps.findIndex(Boolean));
    buttons.forEach(({ button, counters, number }, i) => {
      const n = heaps[i];
      button.disabled = finished || !n;
      button.setAttribute('aria-pressed', String(!finished && i === selected));
      button.setAttribute('aria-label', 'Heap ' + letter(i) + ', ' + quantity(n));
      number.textContent = String(n);
      counters.replaceChildren(...Array.from({ length: n }, () => document.createElement('i')));
    });
    el.count.replaceChildren(...Array.from({ length: heaps[selected] }, (_, i) => new Option(String(i + 1), String(i + 1))));
    el.count.disabled = el.take.disabled = finished;
    el.second.hidden = started;
    el.turn.textContent = finished ? 'Match complete' : 'Your turn';
    el.total.textContent = quantity(heaps.reduce((a, b) => a + b, 0)) + ' left';
    preview();
  }

  function move(actor, choice) {
    heaps = playMove(heaps, choice.heap, choice.take);
    const line = actor + ' took ' + quantity(choice.take) + ' from ' + letter(choice.heap) + '.';
    if (heaps.some(Boolean)) return line;
    finished = true;
    return line + (actor === 'You' ? ' You win.' : ' Atlas wins.');
  }

  function endTurn(lines, outcome) {
    paint();
    el.report.textContent = lines.join(' ');
    if (finished) onFinish({ outcome, summary: lines.at(-1) });
  }

  el.take.addEventListener('click', () => {
    if (disposed || finished) return;
    started = true;
    const own = move('You', { heap: selected, take: Number(el.count.value) });
    if (finished) { endTurn([own], 'win'); return; }
    const reply = move('Atlas', agentMove(heaps, difficulty, random));
    endTurn([own, reply], 'loss');
  }, { signal: events.signal });
  el.second.addEventListener('click', () => {
    if (disposed || started) return;
    started = true;
    const reply = move('Atlas', agentMove(heaps, difficulty, random));
    endTurn([reply], 'loss');
    if (!finished) buttons[selected].button.focus();
  }, { signal: events.signal });
  el.count.addEventListener('change', preview, { signal: events.signal });
  el.report.textContent = 'You have the opening move. You can also choose to play second.';
  paint();
  return () => { disposed = true; events.abort(); view.remove(); };
}
