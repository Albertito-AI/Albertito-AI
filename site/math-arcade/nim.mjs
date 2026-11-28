const tiers = [
  { piles: 3, cap: 6 }, { piles: 4, cap: 7 }, { piles: 5, cap: 15 }
];

function randomStream(seed) {
  let n = seed >>> 0;
  return () => {
    n = (n + 0x6d2b79f5) >>> 0;
    let x = Math.imul(n ^ (n >>> 15), n | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

// The arcade uses at most five heaps and fifteen counters per heap.
export function nimSum(heaps) {
  return heaps.reduce((sum, count) => sum ^ count, 0);
}

export function makeNim(level, seed) {
  if (!Number.isInteger(level) || !tiers[level]) throw new RangeError('Choose a level from 0 to 2.');
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) throw new RangeError('Supply a 32-bit unsigned seed.');
  const { piles, cap } = tiers[level];
  const random = randomStream(seed);
  const heaps = Array.from({ length: piles }, () => 1 + Math.floor(random() * cap));
  if (level === 0 && nimSum(heaps) === 0) {
    heaps[0] = heaps[0] === cap ? cap - 1 : heaps[0] + 1;
  }
  if (level > 0 && seed % 4 === 0) {
    const prefix = heaps.slice(0, -1);
    if (nimSum(prefix) === 0) prefix[0] = prefix[0] === cap ? cap - 1 : prefix[0] + 1;
    heaps[0] = prefix[0];
    heaps[piles - 1] = nimSum(prefix);
  }
  return heaps;
}

export function playMove(heaps, heap, take) {
  if (!Number.isInteger(heap) || heap < 0 || heap >= heaps.length ||
      !Number.isInteger(take) || take < 1 || take > heaps[heap]) throw new RangeError('Choose a non-empty heap and a legal number of counters.');
  const next = heaps.slice();
  next[heap] -= take;
  return next;
}

export function legalMoves(heaps) {
  const moves = [];
  heaps.forEach((count, heap) => {
    for (let take = 1; take <= count; take++) moves.push({ heap, take });
  });
  return moves;
}

export function optimalMove(heaps) {
  const sum = nimSum(heaps);
  for (const [heap, count] of heaps.entries()) {
    const after = count ^ sum;
    if (after < count) return { heap, take: count - after };
  }
  // Equal outcome against perfect opposition; break ties by taking one from the first non-empty heap.
  const heap = heaps.findIndex(Boolean);
  return heap === -1 ? null : { heap, take: 1 };
}

const name = index => String.fromCharCode(65 + index);
const counters = n => n === 1 ? '1 counter' : n + ' counters';
const signature = move => move.heap + '/' + move.take;
const moveLabel = move => 'Take ' + move.take + ' from heap ' + name(move.heap);

function setOptions(select, items) {
  select.replaceChildren(...items.map(({value, label}) => new Option(label, value)));
}

export function mount(root, { level, seed, onWin }) {
  const opening = makeNim(level, seed);
  const controller = new AbortController();
  let board = opening.slice();
  let humanFirst = true;
  let chosen = 0;
  let outcome = null;
  let lastNotice = '';
  let priorTurns = [];
  let legal = [];

  const section = document.createElement('section');
  section.className = 'nim-game';
  section.setAttribute('aria-label', 'Nim Lab board');
  section.innerHTML = `
    <p class="nim-rules">Take one or more counters from a single heap. Whoever takes the last counter wins. Atlas plays an optimal reply.</p>
    <div class="nim-table">
      <div class="nim-caption"><strong data-el="turn"></strong><span data-el="remaining"></span></div>
      <div class="nim-heaps" role="group" aria-label="Choose a heap" data-el="heaps"></div>
    </div>
    <div class="nim-controls"><label>Number to take <select data-el="amount"></select></label>
      <button class="nim-take" type="button" data-el="take">Take counters</button></div>
    <p class="nim-report" role="status" data-el="report"></p>
    <div class="nim-small-actions"><button type="button" data-el="undo">Undo my turn</button>
      <button type="button" data-el="restart">Restart</button>
      <button type="button" data-el="switch">Restart with Atlas first</button></div>
    <details class="nim-lab" data-el="lab"><summary>Compare moves using binary</summary>
      <p>Write each heap in binary. In each column, an odd number of ones gives 1 and an even number gives 0. This produces the nim-sum (XOR).</p>
      <p class="nim-binary" data-el="binary"></p>
      <div class="nim-comparisons" data-el="comparisons"></div>
      <p data-el="conclusion"></p>
    </details>`;
  root.replaceChildren(section);
  const refs = Object.fromEntries([...section.querySelectorAll('[data-el]')].map(el => [el.dataset.el, el]));
  const listen = (el, event, fn) => el.addEventListener(event, fn, {signal: controller.signal});

  function report() {
    refs.report.textContent = lastNotice || 'You move first. Select a heap and how many counters to take.';
  }

  function paintHeaps() {
    refs.heaps.replaceChildren(...board.map((count, idx) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'nim-heap';
      button.dataset.heap = String(idx);
      button.disabled = count === 0 || Boolean(outcome);
      button.setAttribute('aria-pressed', String(count > 0 && idx === chosen && !outcome));
      button.setAttribute('aria-label', 'Heap ' + name(idx) + ', ' + counters(count));
      const tag = document.createElement('strong');
      tag.textContent = name(idx);
      const tokens = document.createElement('span');
      tokens.className = 'nim-tokens';
      tokens.setAttribute('aria-hidden','true');
      const take = idx === chosen && !outcome ? Number(refs.amount.value) : 0;
      for (let i = 0; i < count; i++) {
        const token = document.createElement('i');
        if (i >= count - take) token.className = 'nim-removing';
        tokens.append(token);
      }
      const qty = document.createElement('span');
      qty.className = 'nim-count';
      qty.textContent = count;
      button.append(tag, tokens, qty);
      return button;
    }));
  }

  function compare() {
    const sum = nimSum(board);
    const digits = Math.max(1, ...board.map(n => n.toString(2).length));
    const binary = n => n.toString(2).padStart(digits,'0');
    refs.binary.textContent = board.map(binary).join(' ⊕ ') + ' = ' + binary(sum) + ' (' + sum + ')';
    refs.conclusion.textContent = !legal.length ? 'The board is empty. The last player to take a counter won.' :
      sum === 0 ? 'The current nim-sum is zero. Every legal move gives the opponent a winning reply if they play perfectly.' :
      'The current nim-sum is non-zero. Find a move that leaves zero for the opponent.';
    refs.comparisons.replaceChildren();
    if (!legal.length) return;
    const ideas = [legal[0]];
    if (legal.length > 1) {
      const winner = optimalMove(board);
      const alt = legal.find(m => (nimSum(playMove(board, m.heap, m.take)) === 0) !== (nimSum(playMove(board, ideas[0].heap, ideas[0].take)) === 0));
      ideas.push(alt || (signature(winner) !== signature(legal[0]) ? winner : legal[1]));
    }
    for (const [index, initial] of ideas.entries()) {
      const card = document.createElement('div');
      const label = document.createElement('label');
      label.textContent = 'Trial ' + (index + 1);
      const select = document.createElement('select');
      setOptions(select, legal.map(m => ({value: signature(m), label: moveLabel(m)})));
      select.value = signature(initial);
      const output = document.createElement('p');
      output.setAttribute('aria-live','polite');
      function calculate() {
        const m = legal.find(item => signature(item) === select.value);
        const result = playMove(board, m.heap, m.take);
        const nextSum = nimSum(result);
        const end = result.every(n => !n);
        output.textContent = '[' + result.join(', ') + '] · XOR ' + nextSum + '. ' +
          (end ? 'Takes the last counter and wins.' : nextSum === 0 ? 'Leaves the opponent a losing position.' : 'Leaves the opponent a winning position.');
      }
      select.onchange = calculate;
      calculate();
      label.append(select); card.append(label,output); refs.comparisons.append(card);
    }
  }

  function render() {
    if (!board[chosen]) chosen = Math.max(0, board.findIndex(Boolean));
    setOptions(refs.amount, Array.from({length: board[chosen]}, (_,i) => ({value: i+1, label: i+1})));
    paintHeaps();
    legal = legalMoves(board);
    if (refs.lab.open) compare();
    refs.turn.textContent = outcome === 'human' ? 'You win' : outcome === 'atlas' ? 'Atlas wins' : 'Your turn';
    refs.remaining.textContent = counters(board.reduce((a,b) => a+b,0)) + ' left';
    refs.take.disabled = refs.amount.disabled = Boolean(outcome);
    refs.undo.disabled = !priorTurns.length || outcome === 'human';
    refs.restart.disabled = (!priorTurns.length && !outcome) || outcome === 'human';
    refs.switch.disabled = outcome === 'human';
    refs.switch.textContent = humanFirst ? 'Restart with Atlas first' : 'Restart with me first';
    report();
  }

  function computer() {
    const m = optimalMove(board);
    board = playMove(board, m.heap, m.take);
    return 'Atlas took ' + counters(m.take) + ' from ' + name(m.heap) + '.';
  }

  function restart() {
    board = opening.slice();
    chosen = 0; outcome = null; priorTurns = [];
    lastNotice = humanFirst ? '' : computer() + ' Your turn.';
    render();
  }

  listen(refs.heaps,'click', event => {
    const target = event.target.closest('[data-heap]');
    if (!target || outcome) return;
    chosen = Number(target.dataset.heap);
    setOptions(refs.amount, Array.from({length: board[chosen]}, (_,i) => ({value:i+1, label:i+1})));
    paintHeaps();
    refs.heaps.querySelector('[data-heap="' + chosen + '"]').focus({preventScroll:true});
  });
  listen(refs.amount,'change',paintHeaps);
  listen(refs.lab,'toggle',() => { if (refs.lab.open) compare(); });
  listen(refs.take,'click',() => {
    if (outcome || !board[chosen]) return;
    const take = Number(refs.amount.value);
    priorTurns.push({board:board.slice(), chosen, notice:lastNotice});
    board = playMove(board, chosen, take);
    lastNotice = 'You took ' + counters(take) + ' from ' + name(chosen) + '. ';
    if (!board.some(Boolean)) {
      outcome = 'human';
      lastNotice += 'You took the last counter.';
      render();
      onWin({details:'You won in ' + priorTurns.length + (priorTurns.length === 1 ? ' turn.' : ' turns.'),
        explanation:'The empty board has nim-sum zero. From a non-zero nim-sum you can always reduce one heap to leave zero for your opponent.'});
      return;
    }
    lastNotice += computer();
    if (!board.some(Boolean)) { outcome = 'atlas'; lastNotice += ' Atlas took the last counter. Undo to try another line, or switch seats.'; }
    render();
  });
  listen(refs.undo,'click',() => {
    if (!priorTurns.length || outcome === 'human') return;
    const prev = priorTurns.pop();
    board = prev.board; chosen = prev.chosen; outcome = null;
    lastNotice = (prev.notice ? prev.notice + ' ' : '') + 'Your last turn and any reply were undone.';
    render();
  });
  listen(refs.restart,'click',restart);
  listen(refs.switch,'click',() => { humanFirst = !humanFirst; restart(); });
  render();
  return () => {controller.abort(); if (section.parentNode === root) section.remove();};
}
