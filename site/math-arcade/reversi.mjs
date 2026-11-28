export const BLACK = 1;
export const WHITE = -1;
export const EMPTY_COUNTS = [3, 5, 6];
const letters = 'ABCDEFGH';
const directions = [-1, 0, 1].flatMap(dr => [-1, 0, 1].map(dc => [dr, dc])).filter(([dr, dc]) => dr || dc);
const rays = Array.from({ length: 64 }, (_, square) => directions.map(([dr, dc]) => {
  const ray = [];
  for (let r = (square >> 3) + dr, c = (square % 8) + dc; r >= 0 && r < 8 && c >= 0 && c < 8; r += dr, c += dc) {
    ray.push(r * 8 + c);
  }
  return ray;
}));

export function coordinate(square) {
  return letters[square % 8] + (1 + (square >> 3));
}

export function startBoard() {
  const board = new Int8Array(64);
  board[27] = board[36] = WHITE;
  board[28] = board[35] = BLACK;
  return board;
}

function captures(board, square, side, stopEarly) {
  const result = [];
  if (!Number.isInteger(square) || square < 0 || square > 63 || board[square] !== 0) return result;
  for (const ray of rays[square]) {
    let n = 0;
    while (n < ray.length && board[ray[n]] === -side) n++;
    if (n && n < ray.length && board[ray[n]] === side) {
      if (stopEarly) return [ray[0]];
      for (let i = 0; i < n; i++) result.push(ray[i]);
    }
  }
  return result;
}

export function flipsFor(board, square, side) {
  return captures(board, square, side, false);
}

export function legalMoves(board, side) {
  const moves = [];
  for (let square = 0; square < 64; square++) {
    if (!board[square] && captures(board, square, side, true).length) moves.push(square);
  }
  return moves;
}

export function playMove(board, square, side) {
  const flips = flipsFor(board, square, side);
  if (!flips.length) throw new RangeError('A legal placement must enclose at least one opposing disc.');
  const next = board.slice();
  next[square] = side;
  for (const index of flips) next[index] = side;
  return next;
}

export function discMargin(board, side) {
  return board.reduce((sum, cell) => sum + cell * side, 0);
}

// Called on the final six empty squares or fewer. Each branch is evaluated to terminal.
export function solve(board, side) {
  const moves = legalMoves(board, side);
  if (!moves.length) {
    if (!legalMoves(board, -side).length) return discMargin(board, side);
    return -solve(board, -side) || 0;
  }
  let best = -65;
  for (const square of moves) best = Math.max(best, -solve(playMove(board, square, side), -side));
  return best || 0;
}

export function rankMoves(board, side) {
  return legalMoves(board, side).map(square => ({
    square, score: -solve(playMove(board, square, side), -side) || 0
  })).sort((a, b) => b.score - a.score || a.square - b.square);
}

function randomSource(seed) {
  let state = seed >>> 0;
  return function random() {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = Math.imul(state ^ (state >>> 15), state | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function candidate(random, target) {
  let board = startBoard();
  let side = BLACK;
  const history = [];
  for (let empty = 60; empty >= target;) {
    const moves = legalMoves(board, side);
    if (!moves.length) {
      if (!legalMoves(board, -side).length) return null;
      history.push(-1);
      side = -side;
      continue;
    }
    if (empty === target) {
      if (moves.length < 2) return null;
      const analysis = rankMoves(board, side);
      if (analysis[0].score === analysis.at(-1).score) return null;
      return { board, side, history, analysis };
    }
    const square = moves[Math.floor(random() * moves.length)];
    board = playMove(board, square, side);
    history.push(square);
    side = -side;
    empty--;
  }
}

export function makeEndgame(level = 0, seed = 0) {
  const target = EMPTY_COUNTS[level] ?? EMPTY_COUNTS[0];
  const random = randomSource(seed);
  for (let attempt = 0; attempt < 12; attempt++) {
    const result = candidate(random, target);
    if (result) return result;
  }
  // The first twelve opening playouts of seed 7 contain a qualifying board in each tier.
  const rescue = randomSource(7);
  for (let attempt = 0; attempt < 12; attempt++) {
    const result = candidate(rescue, target);
    if (result) return result;
  }
  throw new Error('Endgame fallback invariant failed.');
}

const colour = side => side === BLACK ? 'Black' : 'White';
const signed = value => value > 0 ? '+' + value : String(value);

export function mount(root, { level = 0, seed = 0, onWin = () => {} } = {}) {
  const initial = makeEndgame(level, seed);
  const player = initial.side;
  const target = initial.analysis[0].score;
  const game = document.createElement('section');
  game.className = 'rev-game';
  game.setAttribute('aria-label', 'Reversi Endgame Lab');
  game.innerHTML = '<div class="rev-goal"><div><strong class="rev-title"></strong><p class="rev-task"></p></div><div class="rev-target"><small>Target margin</small><strong></strong></div></div><div class="rev-score" aria-label="Disc counts"></div><div class="rev-frame"><div class="rev-files" aria-hidden="true"></div><div class="rev-ranks" aria-hidden="true"></div><div class="rev-board" role="grid" aria-label="Reversi board. Use arrow keys to explore. Enter or Space places a disc."></div></div><p class="rev-message" role="status" aria-live="polite" aria-atomic="true"></p><div class="rev-controls"><button type="button" class="rev-undo">Undo turn</button><button type="button" class="rev-reset">Replay position</button><button type="button" class="rev-compare" aria-expanded="false">Compare moves</button></div><div class="rev-analysis" hidden></div><details class="rev-help"><summary>Rules and scoring</summary><p>Place a disc to bracket one or more opposing discs in a straight line. All bracketed discs flip. Dotted squares are legal. A player without a move must pass. Play ends when neither colour can move. Your margin is your discs minus the other colour’s discs. A negative target means holding the smallest possible loss.</p></details>';
  root.append(game);
  const get = selector => game.querySelector(selector);
  const grid = get('.rev-board');
  const score = get('.rev-score');
  const message = get('.rev-message');
  const undo = get('.rev-undo');
  const reset = get('.rev-reset');
  const compare = get('.rev-compare');
  const analysisPanel = get('.rev-analysis');
  get('.rev-title').textContent = 'You play ' + colour(player);
  get('.rev-task').textContent = 'Choose each move to reach the target against perfect replies.';
  get('.rev-target strong').textContent = signed(target);
  function axis(parent, symbols) {
    for (const symbol of symbols) {
      const item = document.createElement('span');
      item.textContent = symbol;
      parent.append(item);
    }
  }
  axis(get('.rev-files'), letters);
  axis(get('.rev-ranks'), '12345678');
  const cells = [];
  for (let r = 0; r < 8; r++) {
    const row = document.createElement('div');
    row.className = 'rev-row';
    row.setAttribute('role', 'row');
    grid.append(row);
    for (let c = 0; c < 8; c++) {
      const cell = document.createElement('div');
      cell.setAttribute('role', 'gridcell');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'rev-cell';
      button.dataset.square = String(r * 8 + c);
      button.append(document.createElement('span'));
      cell.append(button);
      row.append(cell);
      cells.push(button);
    }
  }
  let board = initial.board, side = player, history = [], turns = [], terminal = false, credited = false, showing = false;
  let focus = initial.analysis.map(move => move.square).sort((a, b) => a - b)[0];

  function setFocus(square, moveFocus = false) {
    cells[focus].tabIndex = -1;
    focus = square;
    cells[focus].tabIndex = 0;
    if (moveFocus) cells[focus].focus();
  }

  function render(note) {
    const legal = terminal ? [] : legalMoves(board, player);
    const black = board.filter(cell => cell === BLACK).length;
    const white = board.filter(cell => cell === WHITE).length;
    for (let i = 0; i < 64; i++) {
      const available = legal.includes(i);
      const state = board[i] === BLACK ? 'black' : board[i] === WHITE ? 'white' : available ? 'legal' : 'empty';
      const cell = cells[i];
      cell.dataset.state = state;
      cell.tabIndex = i === focus ? 0 : -1;
      cell.setAttribute('aria-label', coordinate(i) + ', ' + (available ? 'legal move' : state));
      cell.setAttribute('aria-disabled', String(!available));
    }
    score.textContent = 'Black ' + black + '  ·  White ' + white + '  ·  ' + (64 - black - white) + ' empty';
    undo.disabled = !history.length;
    reset.disabled = !history.length;
    analysisPanel.hidden = !showing;
    compare.setAttribute('aria-expanded', String(showing));
    compare.textContent = showing ? 'Hide analysis' : 'Compare moves';
    if (showing) {
      const ranked = terminal ? initial.analysis : rankMoves(board, player);
      const title = terminal ? 'Opening alternatives' : 'Available moves';
      analysisPanel.replaceChildren();
      const heading = document.createElement('strong');
      heading.textContent = title + ' · final margins with perfect play';
      const list = document.createElement('ul');
      for (const move of ranked) {
        const item = document.createElement('li');
        item.textContent = coordinate(move.square) + '  ' + signed(move.score);
        list.append(item);
      }
      analysisPanel.append(heading, list);
      if (terminal && turns.length) {
        const record = document.createElement('p');
        record.textContent = 'Your line: ' + turns.join(', ') + '.';
        analysisPanel.append(record);
      }
    }
    if (note !== undefined) message.textContent = note;
  }
  function place(square) {
    if (terminal || !legalMoves(board, side).includes(square)) return;
    history.push({ board, logLength: turns.length });
    board = playMove(board, square, player);
    const played = [colour(player) + ' ' + coordinate(square)];
    side = -player;
    while (true) {
      const moves = legalMoves(board, side);
      if (!moves.length) {
        if (!legalMoves(board, -side).length) {
          terminal = true;
          break;
        }
        played.push(colour(side) + ' passes');
        side = -side;
        continue;
      }
      if (side === player) break;
      const best = rankMoves(board, side)[0].square;
      board = playMove(board, best, side);
      played.push(colour(side) + ' ' + coordinate(best));
      side = -side;
    }
    turns.push(...played);
    let note = played.join(', ') + '. ';
    if (terminal) {
      const margin = discMargin(board, player);
      note += 'Final margin ' + signed(margin) + '. ';
      note += margin === target ? 'Target reached.' : 'The best attainable margin was ' + signed(target) + '. Try another line.';
      showing = true;
      render(note);
      if (margin === target && !credited) {
        credited = true;
        onWin({ details: 'Optimal endgame margin ' + signed(target), explanation: 'You achieved ' + colour(player) + '’s best guaranteed disc margin against perfect replies.' });
      }
    } else {
      const next = legalMoves(board, player)[0];
      setFocus(next, game.contains(document.activeElement) && grid.contains(document.activeElement));
      render(note + 'Your move.');
    }
  }

  function handleClick(event) {
    const cell = event.target.closest('.rev-cell');
    if (cell && grid.contains(cell)) {
      setFocus(Number(cell.dataset.square));
      place(focus);
    } else if (event.target === compare) {
      showing = !showing;
      render();
    } else if (event.target === undo && history.length) {
      const prior = history.pop();
      board = prior.board;
      side = player;
      turns.length = prior.logLength;
      terminal = false;
      setFocus(legalMoves(board, player)[0]);
      render('Turn undone. Your move.');
    } else if (event.target === reset) {
      board = initial.board;
      side = player;
      history = [];
      turns = [];
      terminal = false;
      showing = false;
      setFocus(legalMoves(board, player)[0]);
      render('Starting position restored. Your move.');
    }
  }
  function handleKey(event) {
    const cell = event.target.closest('.rev-cell');
    if (!cell) return;
    const square = Number(cell.dataset.square), r = square >> 3, c = square % 8;
    const next = {
      ArrowLeft: 8 * r + Math.max(0, c - 1), ArrowRight: 8 * r + Math.min(7, c + 1),
      ArrowUp: 8 * Math.max(0, r - 1) + c, ArrowDown: 8 * Math.min(7, r + 1) + c,
      Home: event.ctrlKey ? 0 : 8 * r, End: event.ctrlKey ? 63 : 8 * r + 7
    };
    if (Object.hasOwn(next, event.key)) {
      event.preventDefault();
      setFocus(next[event.key], true);
    }
  }
  game.addEventListener('click', handleClick);
  game.addEventListener('keydown', handleKey);
  render('Your move. Choose a dotted square.');
  return () => {
    game.removeEventListener('click', handleClick);
    game.removeEventListener('keydown', handleKey);
    game.remove();
  };
}
