import { candidateMask, countSolutions, findLogicalHint, makeSudoku } from './sudoku-engine.mjs';

const settings = [
  { goal: 5, moves: [0, 1], pace: 'one placement every second turn' },
  { goal: 7, moves: [1, 0, 1], pace: 'two placements every three turns (turns 1 and 3 of each cycle)' },
  { goal: 9, moves: [1], pace: 'one placement every turn' }
];
const digits = [1, 2, 3, 4, 5, 6, 7, 8, 9];
const row = index => Math.floor(index / 9);
const col = index => index % 9;
const box = index => 3 * Math.floor(row(index) / 3) + Math.floor(col(index) / 3);
const coordinate = index => `row ${row(index) + 1}, column ${col(index) + 1}`;

// Both boards start with identical clues. The rival solves its own position and never reads the answer key.
export function nextRivalPlacement(board) {
  const single = findLogicalHint(board);
  if (single) return { index: single.index, digit: single.digit,
    reason: single.kind === 'naked' ? 'a cell with only one candidate' : `the only place for a digit in a ${single.unit}` };
  let choices;
  let index;
  for (let i = 0; i < board.length; i++) {
    if (board[i]) continue;
    const mask = candidateMask(board, i);
    const candidates = digits.filter(digit => mask & (1 << digit));
    if (!choices || candidates.length < choices.length) {
      index = i;
      choices = candidates;
    }
  }
  for (const digit of choices || []) {
    const trial = board.slice();
    trial[index] = digit;
    // On these certified unique boards, a completed trial proves this digit is forced.
    if (countSolutions(trial, 1)) return { index, digit, reason: 'a candidate verified by searching for a complete solution' };
  }
  return null;
}

export function mount(root, { difficulty, seed, onFinish }) {
  const { goal: checkpoint, moves, pace } = settings[difficulty];
  const { puzzle, solution } = makeSudoku(difficulty, seed);
  const player = puzzle.slice();
  const rival = puzzle.slice();
  const notes = new Uint16Array(81);
  const emptyCells = puzzle.filter(digit => digit === 0).length;
  let format = 'full';
  let goal = emptyCells;
  let selected = player.indexOf(0);
  let playerScore = 0, rivalScore = 0, turns = 0;
  let pencil = false, ended = false;
  const controller = new AbortController();
  const panel = document.createElement('section');
  panel.className = 'sdk-game';
  panel.setAttribute('aria-label', 'Sudoku race');
  panel.innerHTML = `
    <div class="sdk-actions" role="group" aria-label="Choose race format before your first turn"><button type="button" data-format="full" aria-pressed="true">Full board</button><button type="button" data-format="checkpoint" aria-pressed="false">Short checkpoint · ${checkpoint} digits</button></div>
    <p class="sdk-intro"><strong data-goal></strong> Both players start with identical clues. Choose your format before the first turn. You move first. The rival makes ${pace}. A wrong entry or a pass uses a turn. Take as long as you like to think.</p>
    <div class="sdk-layout"><div class="sdk-board-wrap">
      <div class="sdk-grid" role="grid" aria-label="Your Sudoku board" aria-rowcount="9" aria-colcount="9"></div>
      <div class="sdk-progress"><span class="sdk-progress-text" data-score="player"></span><span class="sdk-bar" aria-hidden="true"><i></i></span></div>
      <div class="sdk-progress"><span class="sdk-progress-text" data-score="rival"></span><span class="sdk-bar" aria-hidden="true"><i></i></span></div>
    </div><div class="sdk-tools">
      <p class="sdk-location"></p><div class="sdk-pad" role="group" aria-label="Number pad"></div>
      <div class="sdk-actions"><button type="button" data-action="pencil" aria-pressed="false">Pencil marks</button><button type="button" data-action="pass">Pass a turn</button></div>
      <p class="sdk-help sdk-message" role="status">Choose a blank square, then enter a digit. Pencil marks are private and cost no turn.</p>
      <details class="sdk-keys"><summary>Keyboard controls</summary><p>Use arrow keys to move on the grid, 1–9 to enter a digit, and N to switch pencil marks on or off. With pencil marks on, enter a digit again to remove its mark.</p></details>
    </div></div>`;
  const goalText = panel.querySelector('[data-goal]');
  const formatButtons = panel.querySelectorAll('[data-format]');
  function selectFormat(choice) {
    if (ended || turns) return;
    format = choice;
    goal = choice === 'full' ? emptyCells : checkpoint;
    goalText.textContent = choice === 'full'
      ? `Complete all ${emptyCells} blank squares before the rival finishes its board.`
      : `Place ${checkpoint} correct digits before the rival reaches that checkpoint.`;
    for (const button of formatButtons) button.setAttribute('aria-pressed', String(button.dataset.format === choice));
  }
  selectFormat(format);
  const grid = panel.querySelector('.sdk-grid');
  const pad = panel.querySelector('.sdk-pad');
  const message = panel.querySelector('.sdk-message');
  const pencilButton = panel.querySelector('[data-action="pencil"]');
  const scores = ['player', 'rival'].map(name => panel.querySelector(`[data-score="${name}"]`));
  const cells = [];
  for (let r = 0; r < 9; r++) {
    const group = document.createElement('div');
    group.className = 'sdk-row';
    group.setAttribute('role', 'row');
    group.setAttribute('aria-rowindex', r + 1);
    for (let c = 0; c < 9; c++) {
      const cell = document.createElement('div');
      cell.className = 'sdk-slot';
      cell.setAttribute('role', 'gridcell');
      cell.setAttribute('aria-colindex', c + 1);
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.cell = r * 9 + c;
      button.className = 'sdk-cell';
      cell.append(button);
      group.append(cell);
      cells.push(button);
    }
    grid.append(group);
  }
  for (const digit of digits) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.digit = digit;
    button.textContent = digit;
    pad.append(button);
  }
  root.replaceChildren(panel);

  function render() {
    cells.forEach((button, i) => {
      const value = player[i];
      const marks = notes[i] ? digits.filter(n => notes[i] & (1 << n)) : [];
      button.classList.toggle('sdk-given', Boolean(puzzle[i]));
      button.classList.toggle('sdk-related', row(i) === row(selected) || col(i) === col(selected) || box(i) === box(selected));
      button.classList.toggle('sdk-selected', i === selected);
      button.tabIndex = i === selected ? 0 : -1;
      const face = value + '/' + notes[i];
      if (button.dataset.face !== face) {
        button.dataset.face = face;
        if (marks.length) {
          const glyph = document.createElement('span');
          glyph.className = 'sdk-glyph sdk-marks';
          glyph.setAttribute('aria-hidden', 'true');
          for (const n of digits) {
            const mark = document.createElement('span');
            if (marks.includes(n)) mark.textContent = n;
            glyph.append(mark);
          }
          button.replaceChildren(glyph);
        } else button.textContent = value || '';
      }
      button.setAttribute('aria-label', `${coordinate(i)}, ${value ? value + (puzzle[i] ? ', given' : ', your placement') : marks.length ? 'pencil marks ' + marks.join(', ') : 'empty'}`);
      button.parentElement.setAttribute('aria-readonly', Boolean(value));
      button.parentElement.setAttribute('aria-selected', i === selected);
    });
    scores.forEach((label, i) => {
      const score = i ? rivalScore : playerScore;
      label.textContent = `${i ? 'Rival' : 'You'}: ${score}/${goal}`;
      label.nextElementSibling.firstElementChild.style.width = `${100 * score / goal}%`;
    });
    panel.querySelector('.sdk-location').textContent = coordinate(selected) + (player[selected] ? ' · filled' : pencil ? ' · pencil marks' : ' · enter a digit');
    pencilButton.setAttribute('aria-pressed', pencil);
    for (const button of pad.children) button.disabled = ended || Boolean(player[selected]);
    for (const button of panel.querySelectorAll('[data-action]')) button.disabled = ended;
  }
  function finish(outcome) {
    ended = true;
    const who = outcome === 'win' ? 'You' : 'The rival';
    const result = format === 'full' ? 'completed the full Sudoku board first.' : 'reached the checkpoint first.';
    const summary = `${who} ${result} You ${playerScore}, rival ${rivalScore}. ${turns} ${turns === 1 ? 'turn' : 'turns'} played.`;
    message.textContent = summary;
    render();
    onFinish({ outcome, summary });
  }
  function takeTurn(feedback) {
    turns++;
    if (turns === 1) for (const button of formatButtons) button.disabled = true;
    if (playerScore === goal) return finish('win');
    if (moves[(turns - 1) % moves.length]) {
      const move = nextRivalPlacement(rival);
      if (!move) throw new Error('Sudoku rival has no valid continuation.');
      rival[move.index] = move.digit;
      rivalScore++;
      if (rivalScore === goal) return finish('loss');
      feedback += ` The rival placed a digit using ${move.reason}.`;
    } else feedback += ' The rival waits this turn.';
    message.textContent = `${feedback} You ${playerScore}, rival ${rivalScore}.`;
    render();
  }
  function enter(digit) {
    if (ended || player[selected]) return;
    if (pencil) {
      notes[selected] ^= 1 << digit;
      message.textContent = `Pencil mark ${digit} ${notes[selected] & (1 << digit) ? 'added' : 'removed'}.`;
      render();
      return;
    }
    if (digit !== solution[selected]) {
      const legal = candidateMask(player, selected) & (1 << digit);
      takeTurn(legal ? 'That digit cannot lead to a completed board.' : 'That digit is already in this row, column or box.');
      return;
    }
    const index = selected;
    player[index] = digit;
    notes[index] = 0;
    playerScore++;
    takeTurn(`Correct. You placed ${digit} in ${coordinate(index)}.`);
  }
  function togglePencil() {
    pencil = !pencil;
    message.textContent = pencil ? 'Pencil marks on. Notes do not use a turn.' : 'Pencil marks off. Your next entry uses a turn.';
    render();
  }
  panel.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button || ended) return;
    if (button.dataset.format) { selectFormat(button.dataset.format); render(); }
    else if (button.hasAttribute('data-cell')) { selected = Number(button.dataset.cell); render(); }
    else if (button.hasAttribute('data-digit')) enter(Number(button.dataset.digit));
    else if (button.dataset.action === 'pencil') togglePencil();
    else if (button.dataset.action === 'pass') takeTurn('You passed.');
  }, { signal: controller.signal });
  panel.addEventListener('keydown', event => {
    if (ended || event.altKey || event.ctrlKey || event.metaKey) return;
    if (/^[1-9]$/.test(event.key)) {
      event.preventDefault();
      if (!event.repeat) enter(Number(event.key));
    } else if (event.key.toLowerCase() === 'n') {
      event.preventDefault();
      if (!event.repeat) togglePencil();
    } else if (grid.contains(event.target)) {
      const positions = { ArrowLeft: row(selected) * 9 + Math.max(0, col(selected) - 1), ArrowRight: row(selected) * 9 + Math.min(8, col(selected) + 1),
        ArrowUp: Math.max(0, row(selected) - 1) * 9 + col(selected), ArrowDown: Math.min(8, row(selected) + 1) * 9 + col(selected) };
      if (!(event.key in positions)) return;
      event.preventDefault();
      selected = positions[event.key];
      render();
      cells[selected].focus();
    }
  }, { signal: controller.signal });
  render();
  return () => { ended = true; controller.abort(); panel.remove(); };
}
