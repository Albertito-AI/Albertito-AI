// A jump can cross an obstacle. Only its landing point is tested.
const LEVELS = [
  { size: 6, blocked: 0, min: 3, max: 5, bases: [[[1, 0], [1, 1]], [[1, 0], [0, 1]], [[1, 1], [0, 1]]] },
  { size: 7, blocked: 5, min: 5, max: 8, bases: [[[1, 0], [1, 1]], [[1, 1], [1, -1]], [[1, 0], [2, 1]]] },
  { size: 9, blocked: 14, min: 7, max: 13, bases: [[[2, 1], [1, 1]], [[2, 1], [1, -1]], [[1, 2], [1, 1]], [[1, 2], [1, -1]]] }
];

function randomGenerator(seed) {
  let state = seed >>> 0;
  return function random() {
    state = (state + 0x6D2B79F5) >>> 0;
    let value = Math.imul(state ^ (state >>> 15), state | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

const point = (id, size) => [id % size, Math.floor(id / size)];
const signed = value => value > 0 ? '+' + value : String(value).replace('-', '−');
const coordText = (id, size) => '(' + point(id, size).join(', ') + ')';
const vectorText = ([x, y]) => '(' + signed(x) + ', ' + signed(y) + ')';

export function landing(board, from, index) {
  const [x, y] = point(from, board.size);
  const [dx, dy] = board.vectors[index];
  const nx = x + dx;
  const ny = y + dy;
  if (nx < 0 || ny < 0 || nx >= board.size || ny >= board.size) return -1;
  const to = nx + ny * board.size;
  return board.blocked.has(to) ? -1 : to;
}

// Every edge costs one move. Breadth-first search gives the minimum jump count.
function search(board, from) {
  const n = board.size ** 2;
  const distance = new Int16Array(n).fill(-1);
  const parent = new Int16Array(n).fill(-1);
  const move = new Int8Array(n).fill(-1);
  const queue = [from];
  distance[from] = 0;
  for (let head = 0; head < queue.length; head++) {
    const at = queue[head];
    for (let j = 0; j < board.vectors.length; j++) {
      const next = landing(board, at, j);
      if (next < 0 || distance[next] >= 0) continue;
      distance[next] = distance[at] + 1;
      parent[next] = at;
      move[next] = j;
      queue.push(next);
    }
  }
  return { distance, parent, move };
}

export function shortestRoute(board, from = board.start, to = board.goal) {
  const { distance, parent, move } = search(board, from);
  if (distance[to] < 0) return null;
  const route = [];
  for (let cell = to; cell !== from; cell = parent[cell]) route.push(move[cell]);
  return route.reverse();
}

export function makeBoard(level, seed) {
  const config = LEVELS[level];
  const random = randomGenerator(seed);
  const index = count => Math.floor(random() * count);
  const size = config.size;
  const n = size ** 2;
  for (let attempt = 0; attempt < 80; attempt++) {
    const pair = config.bases[index(config.bases.length)];
    const reflect = random() < 0.5 ? -1 : 1;
    const transpose = random() < 0.5;
    const [a, b] = pair.map(([x, y]) => transpose ? [reflect * y || 0, x] : [x, reflect * y || 0]);
    const opposite = ([x, y]) => [-x || 0, -y || 0];
    const start = index(n);
    const blocked = new Set();
    while (blocked.size < config.blocked) {
      const cell = index(n);
      if (cell !== start) blocked.add(cell);
    }
    const board = { size, start, goal: -1, blocked, vectors: [a, b, opposite(a), opposite(b)] };
    const { distance } = search(board, start);
    const goals = [];
    for (let i = 0; i < n; i++) {
      if (distance[i] >= config.min && distance[i] <= config.max) goals.push(i);
    }
    if (goals.length) {
      board.goal = goals[index(goals.length)];
      board.par = distance[board.goal];
      return board;
    }
  }
  // A deterministic, always-reachable board if every sampled component was too small.
  const goalY = level + 1;
  const goalX = Math.min(size - 1, config.max - goalY);
  const goal = goalX + size * goalY;
  const blocked = new Set();
  for (let cell = n - 1; blocked.size < config.blocked; cell--) blocked.add(cell);
  return { size, start: 0, goal, blocked, vectors: [[1, 0], [0, 1], [-1, 0], [0, -1]], par: goalX + goalY };
}

export function mount(root, { level, seed, onWin, onMove, competitive = false }) {
  const board = makeBoard(level, seed);
  const history = [board.start];
  const moves = [];
  let hintStage = 0;
  let highlighted = -1;
  let finished = false;
  let mounted = true;
  const events = new AbortController();
  const unique = 'ld-' + Math.random().toString(36).slice(2, 9);
  root.innerHTML = `
    <section class="ld-game" aria-label="Lattice Dash" tabindex="-1">
      <p class="ld-instruction">Land on the gold beacon in as few jumps as possible. Each key moves you by a fixed vector.</p>
      <div class="ld-main">
        <div class="ld-plot-wrap"><svg class="ld-plot" role="img" viewBox="0 0 370 350"></svg></div>
        <div class="ld-console">
          <div class="ld-score"><span>Moves <strong data-ld="moves">0</strong></span><span>Par <strong>${board.par}</strong></span></div>
          <div class="ld-coords"><span><i class="ld-player-swatch"></i>You <b data-ld="you"></b></span><span><i class="ld-goal-swatch"></i>Beacon <b>${coordText(board.goal, board.size)}</b></span></div>
          <p class="ld-key-label">Choose a jump <small>(Δx, Δy)</small></p>
          <div class="ld-jumps"></div>
          <p class="ld-axis-help">Positive x goes right. Positive y goes up.${board.blocked.size ? ' Landings marked × are blocked.' : ''}</p>
          <div class="ld-tools"><button type="button" data-ld="undo">Undo</button><button type="button" data-ld="reset">Reset</button><button type="button" data-ld="hint">Hint</button></div>
          <p class="ld-message" data-ld="status" role="status" aria-live="polite" aria-atomic="true"></p>
        </div>
      </div>
    </section>`;
  const section = root.querySelector('.ld-game');
  if (competitive) root.querySelector('.ld-tools').style.display = 'none';
  const get = name => root.querySelector('[data-ld="' + name + '"]');
  const plot = root.querySelector('.ld-plot');
  const jumpContainer = root.querySelector('.ld-jumps');
  const status = get('status');
  const controls = board.vectors.map((vec, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ld-jump';
    btn.innerHTML = '<kbd>' + (i + 1) + '</kbd><span>' + vectorText(vec) + '</span>';
    btn.setAttribute('aria-label', 'Jump ' + (i + 1) + ': x ' + signed(vec[0]) + ', y ' + signed(vec[1]));
    btn.addEventListener('click', () => jump(i), {signal: events.signal});
    jumpContainer.append(btn);
    return btn;
  });
  const slot = 288 / (board.size - 1);
  const px = x => 48 + slot * x;
  const py = y => 307 - slot * y;
  const screen = cell => {
    const [x, y] = point(cell, board.size);
    return [px(x), py(y)];
  };
  let grid = '';
  for (let i = 0; i < board.size; i++) {
    grid += '<path class="ld-axis-line" d="M ' + px(i) + ' ' + py(0) + ' V ' + py(board.size - 1) + ' M ' + px(0) + ' ' + py(i) + ' H ' + px(board.size - 1) + '"/>';
    grid += '<text x="' + px(i) + '" y="328" class="ld-label">' + i + '</text><text x="29" y="' + (py(i) + 4) + '" class="ld-label">' + i + '</text>';
  }
  grid += '<text x="353" y="310" class="ld-axis-name">x</text><text x="28" y="10" class="ld-axis-name">y</text>';
  let dots = '';
  for (let i = 0; i < board.size ** 2; i++) {
    const [x, y] = screen(i);
    if (board.blocked.has(i)) {
      dots += '<path class="ld-blocked" d="M ' + (x-4) + ' ' + (y-4) + ' l 8 8 m 0 -8 l -8 8"/>';
    } else {
      dots += '<circle class="ld-node" cx="' + x + '" cy="' + y + '" r="2.25"/>';
    }
  }
  function redraw() {
    const cell = history.at(-1);
    const [x, y] = screen(cell);
    const [sx, sy] = screen(board.start);
    const [gx, gy] = screen(board.goal);
    let dynamic = '<polyline class="ld-trail" points="' + history.map(id => screen(id).join(',')).join(' ') + '"/>';
    dynamic += '<circle class="ld-start" cx="' + sx + '" cy="' + sy + '" r="8"/>';
    dynamic += '<g class="ld-star" transform="translate(' + gx + ' ' + gy + ')"><circle r="14"/><path d="M0 -10 L2.6 -2.6 L10 0 L2.6 2.6 L0 10 L-2.6 2.6 L-10 0 L-2.6 -2.6Z"/></g>';
    controls.forEach((button, i) => {
      const next = landing(board, cell, i);
      const disabled = finished || next < 0;
      // aria-disabled keeps the activated key focusable when the next jump hits a wall.
      button.setAttribute('aria-disabled', String(disabled));
      if (disabled) return;
      const [nx, ny] = screen(next);
      dynamic += '<circle class="ld-reachable' + (i === highlighted ? ' ld-hinted' : '') + '" cx="' + nx + '" cy="' + ny + '" r="11"/>';
      dynamic += '<circle data-ld-jump="' + i + '" class="ld-hit" cx="' + nx + '" cy="' + ny + '" r="16"><title>Jump ' + (i+1) + ' to ' + coordText(next, board.size) + '</title></circle>';
    });
    dynamic += '<g class="ld-player" transform="translate(' + x + ' ' + y + ')"><circle r="12"/><path d="M0 -7 L6 0 L0 7 L-6 0Z"/></g>';
    plot.innerHTML = '<title id="' + unique + '">Coordinate grid. You are at ' + coordText(cell, board.size) + '. Beacon at ' + coordText(board.goal, board.size) + '.</title>' + grid + dots + dynamic;
    plot.setAttribute('aria-labelledby', unique);
    get('you').textContent = coordText(cell, board.size);
    get('moves').textContent = moves.length;
    get('undo').disabled = finished || !moves.length;
    get('reset').disabled = finished || !moves.length;
    get('hint').disabled = finished;
  }

  function jump(index) {
    if (finished || !mounted) return;
    const next = landing(board, history.at(-1), index);
    if (next < 0) {
      status.textContent = 'That jump lands outside the grid or on a blocked point.';
      return;
    }
    history.push(next);
    moves.push(index);
    hintStage = 0;
    highlighted = -1;
    finished = next === board.goal;
    redraw();
    onMove?.(moves.length);
    if (finished) {
      const [x0, y0] = point(board.start, board.size);
      const [x1, y1] = point(board.goal, board.size);
      const score = moves.length === board.par ? 'You matched par.' : 'Shortest route: ' + board.par + ' jumps.';
      const explanation = 'Your jump vectors sum to ' + vectorText([x1-x0, y1-y0]) + ', the displacement from ' + coordText(board.start, board.size) + ' to ' + coordText(board.goal, board.size) + '. Searching all reachable points one jump at a time first reaches the beacon after ' + board.par + ' jumps.';
      const details = moves.length + ' jumps · par ' + board.par + '. ' + score;
      status.textContent = 'Beacon reached! ' + details;
      onWin({ explanation, details });
    } else {
      status.textContent = 'Landed at ' + coordText(next, board.size) + '.';
    }
  }
  get('undo').addEventListener('click', () => {
    if (finished || !moves.length) return;
    moves.pop(); history.pop(); hintStage = 0; highlighted = -1;
    redraw();
    status.textContent = 'Last jump undone. You are at ' + coordText(history.at(-1), board.size) + '.';
  }, {signal:events.signal});
  get('reset').addEventListener('click', () => {
    if (finished || !moves.length) return;
    moves.length = 0; history.length = 1; hintStage = 0; highlighted = -1;
    redraw(); status.textContent = 'Back at the starting point.';
  }, {signal:events.signal});
  get('hint').addEventListener('click', () => {
    if (finished) return;
    const current = history.at(-1);
    const [x,y] = point(current, board.size);
    const [gx,gy] = point(board.goal, board.size);
    const route = shortestRoute(board, current);
    if (!hintStage) {
      status.textContent = 'The remaining displacement is ' + vectorText([gx-x, gy-y]) + '. A shortest route from here takes ' + route.length + (route.length === 1 ? ' jump.' : ' jumps.') + ' Ask again for its first jump.';
      hintStage = 1;
    } else {
      highlighted = route[0];
      const next = landing(board, current, highlighted);
      status.textContent = 'Try jump ' + (highlighted + 1) + ' ' + vectorText(board.vectors[highlighted]) + ' to ' + coordText(next, board.size) + '.';
      redraw();
    }
  }, {signal:events.signal});
  plot.addEventListener('click', event => {
    const node = event.target.closest('[data-ld-jump]');
    if (node) jump(Number(node.dataset.ldJump));
  }, {signal:events.signal});
  section.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.repeat) return;
    if (/^[1-4]$/.test(event.key)) {
      event.preventDefault();
      jump(Number(event.key) - 1);
    }
  }, {signal:events.signal});
  redraw();
  return () => { mounted = false; events.abort(); };
}
