import { BLACK, WHITE, coordinate, discMargin, flipsFor, legalMoves, playMove, startBoard } from './reversi.mjs';

const corners = [[0, 1, 8, 9], [7, 6, 15, 14], [56, 48, 57, 49], [63, 55, 62, 54]];
const colour = side => side === BLACK ? 'Black' : 'White';
const levelNotes = ['Easy chooses a random legal move.', 'Medium takes the most discs it can flip this turn.', 'Hard looks three placements ahead and searches the final six empty squares to the end.'];

function randomSource(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

// Search scores are from the side to move. Forced passes consume no placement.
function search(board, side, depth, empty, alpha, beta) {
  const moves = legalMoves(board, side);
  if (!moves.length) {
    if (legalMoves(board, -side).length) return -search(board, -side, depth, empty, -beta, -alpha);
    const margin = discMargin(board, side);
    return Math.sign(margin) * 10000 + margin;
  }
  if (depth === 0) {
    // A corner cannot be flipped. Its neighbours are risky while it is still open.
    let value = discMargin(board, side) * (empty < 16 ? 4 : 1);
    value += 8 * (moves.length - legalMoves(board, -side).length);
    for (const [corner, edgeA, edgeB, diagonal] of corners) {
      value += 75 * side * board[corner];
      if (!board[corner]) value -= side * (12 * (board[edgeA] + board[edgeB]) + 25 * board[diagonal]);
    }
    return value;
  }
  let best = -Infinity;
  for (const square of moves) {
    const value = -search(playMove(board, square, side), -side, depth - 1, empty - 1, -beta, -alpha);
    best = Math.max(best, value);
    alpha = Math.max(alpha, best);
    if (alpha >= beta) break;
  }
  return best;
}

function agentMove(board, side, moves, difficulty, random) {
  const choose = choices => choices[Math.floor(random() * choices.length)];
  if (moves.length === 1) return moves[0];
  if (difficulty === 0) return choose(moves);
  const empty = board.reduce((sum, cell) => sum + (cell === 0), 0);
  const depth = empty <= 6 ? empty : 3;
  let best = -Infinity;
  let candidates = [];
  for (const square of moves) {
    const value = difficulty === 1 ? flipsFor(board, square, side).length
      : -search(playMove(board, square, side), -side, depth - 1, empty - 1, -Infinity, Infinity);
    if (value > best) {
      best = value;
      candidates = [square];
    } else if (value === best) candidates.push(square);
  }
  return choose(candidates);
}

export function mount(root, { difficulty = 0, seed = 0, onFinish = () => {} } = {}) {
  const level = [0, 1, 2].includes(difficulty) ? difficulty : 0;
  const game = document.createElement('section');
  game.className = 'rev-game';
  game.setAttribute('aria-label', 'Full Reversi match');
  game.innerHTML = `
    <div class="rev-goal"><div><strong class="rev-title"></strong><p class="rev-task"></p></div></div>
    <p class="rev-score" aria-label="Disc counts"></p>
    <p class="rev-message" role="status" aria-atomic="true"></p>
    <div class="rev-frame"><div class="rev-files" aria-hidden="true"></div><div class="rev-ranks" aria-hidden="true"></div><div class="rev-board" role="grid" aria-label="Reversi board. Arrow keys explore squares. Enter or Space plays a legal move."></div></div>
    <div class="rev-controls"><button type="button" data-action="colour"></button><button type="button" data-action="restart">Restart this match</button></div>
    <details class="rev-help"><summary>Rules and strategy</summary><p>Black moves first. Place a disc on a dotted square to trap a continuous line of opposing discs between two of yours. Every trapped line flips, including diagonals. A colour with no legal move must pass. When neither colour can move, the larger disc count wins. Equal counts draw.</p><p class="rev-opponent"></p></details>
    <details class="rev-help"><summary>Move history</summary><p class="rev-history"></p></details>`;
  root.append(game);
  const get = selector => game.querySelector(selector);
  const grid = get('.rev-board');
  const score = get('.rev-score');
  const status = get('.rev-message');
  const historyText = get('.rev-history');
  const colourButton = get('[data-action="colour"]');
  const restart = get('[data-action="restart"]');
  get('.rev-task').textContent = 'Finish with more discs than the computer. Dots show where you can play.';
  get('.rev-opponent').textContent = levelNotes[level];

  for (const [selector, symbols] of [['.rev-files', 'ABCDEFGH'], ['.rev-ranks', '12345678']]) {
    for (const symbol of symbols) {
      const label = document.createElement('span');
      label.textContent = symbol;
      get(selector).append(label);
    }
  }
  const cells = [];
  for (let rowIndex = 0; rowIndex < 8; rowIndex++) {
    const row = document.createElement('div');
    row.className = 'rev-row';
    row.setAttribute('role', 'row');
    grid.append(row);
    for (let col = 0; col < 8; col++) {
      const cell = document.createElement('div');
      cell.setAttribute('role', 'gridcell');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'rev-cell';
      button.dataset.square = String(cells.length);
      button.append(document.createElement('span'));
      cell.append(button);
      row.append(cell);
      cells.push(button);
    }
  }

  let human = BLACK, board, side, moves, random, history, hasPlayed, finished;
  let focus = 19, timer, active = true;
  const events = new AbortController();

  function select(square, moveFocus = false) {
    cells[focus].tabIndex = -1;
    focus = square;
    cells[focus].tabIndex = 0;
    if (moveFocus) cells[focus].focus({ preventScroll: true });
  }

  function refresh(note) {
    const available = side === human && !finished ? moves : [];
    const black = board.reduce((n, v) => n + (v === BLACK), 0);
    const white = board.reduce((n, v) => n + (v === WHITE), 0);
    score.textContent = 'Black ' + black + ' · White ' + white + ' · ' + (64 - black - white) + ' empty';
    get('.rev-title').textContent = 'You play ' + colour(human);
    colourButton.textContent = 'Play as ' + colour(-human);
    colourButton.disabled = hasPlayed || finished;
    restart.disabled = finished || (!history.length && side === human);
    status.textContent = note;
    historyText.textContent = history.length ? history.join(' · ') : 'The opening four discs are on the board.';
    for (const [index, button] of cells.entries()) {
      const legal = available.includes(index);
      const state = board[index] ? colour(board[index]).toLowerCase() : legal ? 'legal' : 'empty';
      button.dataset.state = state;
      button.setAttribute('aria-label', coordinate(index) + ', ' + (legal ? 'legal move' : state));
      button.setAttribute('aria-disabled', String(!legal));
      button.tabIndex = index === focus ? 0 : -1;
    }
    if (available.length && !available.includes(focus)) select(available[0], grid.contains(document.activeElement));
  }

  function advance(note = '') {
    moves = legalMoves(board, side);
    if (!moves.length) {
      const otherMoves = legalMoves(board, -side);
      if (!otherMoves.length) {
        finished = true;
        const margin = discMargin(board, human);
        const outcome = margin === 0 ? 'draw' : margin > 0 ? 'win' : 'loss';
        const black = board.filter(cell => cell === BLACK).length;
        const white = board.filter(cell => cell === WHITE).length;
        const summary = (outcome === 'draw' ? 'Draw' : outcome === 'win' ? 'You win' : 'Computer wins')
          + '. Black ' + black + ', White ' + white + '. You played ' + colour(human) + '.';
        refresh(note + 'Neither colour can move. ' + summary);
        onFinish({ outcome, summary });
        return;
      }
      const pass = colour(side) + ' passes';
      history.push(pass);
      note += pass + '. ';
      side = -side;
      moves = otherMoves;
    }
    if (side === human) {
      refresh(note + 'Your move as ' + colour(human) + '.');
      return;
    }
    refresh(note + 'Computer to move as ' + colour(side) + '.');
    timer = setTimeout(() => {
      if (!active || finished || side === human) return;
      place(agentMove(board, side, moves, level, random));
    }, 140);
  }

  function place(square) {
    const label = colour(side) + ' ' + coordinate(square);
    board = playMove(board, square, side);
    history.push(label);
    side = -side;
    advance(label + '. ');
  }

  function reset() {
    clearTimeout(timer);
    random = randomSource(seed);
    board = startBoard();
    side = BLACK;
    history = [];
    hasPlayed = false;
    finished = false;
    focus = 19;
    advance();
  }

  game.addEventListener('click', event => {
    if (!active || finished) return;
    if (event.target === restart) return reset();
    if (event.target === colourButton && !hasPlayed) {
      human = -human;
      return reset();
    }
    const cell = event.target.closest('.rev-cell');
    if (!cell || side !== human) return;
    const square = Number(cell.dataset.square);
    select(square);
    if (!moves.includes(square)) return;
    hasPlayed = true;
    place(square);
  }, { signal: events.signal });

  grid.addEventListener('keydown', event => {
    const cell = event.target.closest('.rev-cell');
    if (!cell) return;
    const square = Number(cell.dataset.square), row = square >> 3, col = square % 8;
    const next = {
      ArrowLeft: 8 * row + Math.max(0, col - 1), ArrowRight: 8 * row + Math.min(7, col + 1),
      ArrowUp: 8 * Math.max(0, row - 1) + col, ArrowDown: 8 * Math.min(7, row + 1) + col,
      Home: event.ctrlKey ? 0 : 8 * row, End: event.ctrlKey ? 63 : 8 * row + 7
    };
    if (Object.hasOwn(next, event.key)) {
      event.preventDefault();
      select(next[event.key], true);
    }
  }, { signal: events.signal });

  reset();
  return () => {
    active = false;
    clearTimeout(timer);
    events.abort();
    game.remove();
  };
}
