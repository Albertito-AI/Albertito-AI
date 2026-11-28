const SIDE = 9;
const CELLS = 81;
const ALL = 0b1111111110;
const indices = Array.from({length: CELLS}, (_, index) => index);
const units = Array.from({length: 27}, () => []);
const rows = [], columns = [], boxes = [];
for (const i of indices) {
  const row = Math.floor(i / SIDE);
  const column = i % SIDE;
  const box = Math.floor(row / 3) * 3 + Math.floor(column / 3);
  rows[i] = row;
  columns[i] = 9 + column;
  boxes[i] = 18 + box;
  for (const unit of [rows[i], columns[i], boxes[i]]) units[unit].push(i);
}
const sizes = new Uint8Array(1024);
for (let mask = 1; mask < sizes.length; mask++) sizes[mask] = sizes[mask >>> 1] + (mask & 1);

function stateFrom(grid) {
  if (!grid || grid.length !== CELLS) return null;
  const used = new Uint16Array(27);
  const cells = new Uint8Array(CELLS);
  for (const i of indices) {
    const digit = grid[i];
    if (!Number.isInteger(digit) || digit < 0 || digit > SIDE) return null;
    if (digit === 0) continue;
    const bit = 1 << digit;
    if ((used[rows[i]] | used[columns[i]] | used[boxes[i]]) & bit) return null;
    used[rows[i]] |= bit;
    used[columns[i]] |= bit;
    used[boxes[i]] |= bit;
    cells[i] = digit;
  }
  return {cells, used};
}

const bitDigit = bit => 31 - Math.clz32(bit);
const available = (s, i) => ALL & ~(s.used[rows[i]] | s.used[columns[i]] | s.used[boxes[i]]);

// Every caller removes exactly the digit it just placed. Toggling also undoes its unit masks.
function toggle(s, index, digit) {
  const bit = 1 << digit;
  s.cells[index] ^= digit;
  s.used[rows[index]] ^= bit;
  s.used[columns[index]] ^= bit;
  s.used[boxes[index]] ^= bit;
}

export function candidateMask(grid, index) {
  if (!Number.isInteger(index) || index < 0 || index >= CELLS) return 0;
  const state = stateFrom(grid);
  return state && !state.cells[index] ? available(state, index) : 0;
}

function shuffled(items, random) {
  for (let end = items.length - 1; end > 0; end--) {
    const j = Math.floor(random() * (end + 1));
    [items[end], items[j]] = [items[j], items[end]];
  }
  return items;
}

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let x = Math.imul(state ^ (state >>> 15), state | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

// Branch on the empty square with the fewest candidates. A random digit order creates
// full grids from scratch. Counting uses a fixed digit order and stops at the requested limit.
function search(s, limit, random, solution) {
  let best = -1, options = 0, least = 10;
  for (const i of indices) {
    if (s.cells[i]) continue;
    const candidates = available(s, i);
    if (!candidates) return 0;
    const size = sizes[candidates];
    if (size < least) {
      best = i;
      options = candidates;
      least = size;
      if (least === 1) break;
    }
  }
  if (best < 0) {
    if (solution) solution.set(s.cells);
    return 1;
  }
  const choices = [];
  while (options) {
    const bit = options & -options;
    choices.push(bitDigit(bit));
    options ^= bit;
  }
  if (random) shuffled(choices, random);
  let found = 0;
  for (const digit of choices) {
    toggle(s, best, digit);
    found += search(s, limit - found, random, solution);
    toggle(s, best, digit);
    if (found >= limit) break;
  }
  return found;
}

export function countSolutions(grid, limit = 2) {
  if (!Number.isSafeInteger(limit) || limit < 1) throw new RangeError('The limit must be a positive integer.');
  const state = stateFrom(grid);
  return state ? search(state, limit, null, null) : 0;
}

function single(s, allowHidden, candidates) {
  for (const i of indices) {
    if (s.cells[i]) { candidates[i] = 0; continue; }
    const mask = available(s, i);
    if (!mask) return null;
    if (sizes[mask] === 1) return {index: i, digit: bitDigit(mask), kind: 'naked'};
    candidates[i] = mask;
  }
  if (!allowHidden) return null;
  for (let u = 0; u < units.length; u++) {
    let seen = 0, repeated = 0;
    for (const i of units[u]) {
      repeated |= seen & candidates[i];
      seen |= candidates[i];
    }
    const unique = seen & ~repeated;
    if (!unique) continue;
    const bit = unique & -unique;
    const unit = u < 9 ? 'row' : u < 18 ? 'column' : 'box';
    return {
      index: units[u].find(i => candidates[i] & bit),
      digit: bitDigit(bit), kind: 'hidden', unit, unitIndex: u % 9
    };
  }
  return null;
}

export function findLogicalHint(grid) {
  const state = stateFrom(grid);
  return state ? single(state, true, new Uint16Array(CELLS)) : null;
}

// If legal singles fill a grid, every written digit was forced, which also proves uniqueness.
function singlesResult(grid, allowHidden) {
  const state = stateFrom(grid);
  const candidates = new Uint16Array(CELLS);
  let hidden = false;
  for (;;) {
    const hint = single(state, allowHidden, candidates);
    if (!hint) return {solved: !state.cells.includes(0), hidden};
    if (hint.kind === 'hidden') hidden = true;
    toggle(state, hint.index, hint.digit);
  }
}

function generate(level, random) {
  const solution = new Uint8Array(CELLS);
  search(stateFrom(new Uint8Array(CELLS)), 1, random, solution);
  const puzzle = solution.slice();
  const target = [40, 31, 25][level] + Math.floor(random() * 4);
  const order = shuffled([...indices], random);
  let givens = CELLS;
  let qualifies = level === 0;
  for (const i of order) {
    puzzle[i] = 0;
    const deductions = level < 2 ? singlesResult(puzzle, level === 1) : null;
    const unique = deductions ? deductions.solved : countSolutions(puzzle) === 1;
    if (!unique) {
      puzzle[i] = solution[i];
      continue;
    }
    givens--;
    if (level === 1) qualifies = deductions.hidden;
    if (level === 2 && givens <= target) qualifies = !singlesResult(puzzle, true).solved;
    if (givens <= target && qualifies) break;
    if (level === 1 && givens <= 29) break;
  }
  // A sparsely clued Expert may run out of removable clues just above its random target.
  if (level === 2 && !qualifies && givens <= 31) qualifies = !singlesResult(puzzle, true).solved;
  return qualifies ? {puzzle: Array.from(puzzle), solution: Array.from(solution), givens, level} : null;
}

// Very rarely, repeated carving attempts can miss the requested reasoning tier. These two
// verified examples provide a bounded escape; their symmetries preserve the reasoning tier.
const rescue = [
  null,
  ['080504001503078090004000000020000000040800125136209000090005640400010500007080009',
   '682594371513678492974321856825147963749863125136259784291735648468912537357486219'],
  ['080504001503070000004000000020000000000800120136209000090005640400010500007080009',
   '682594371513678492974321856825147963749863125136259784291735648468912537357486219']
];
function sudokuPermutation(random) {
  const bands = shuffled([0, 1, 2], random);
  return bands.flatMap(band => shuffled([0, 1, 2], random).map(offset => 3 * band + offset));
}
function rescued(level, random) {
  const pair = rescue[level];
  if (!pair) throw new Error('No suitable puzzle was generated.');
  const rowOrder = sudokuPermutation(random), columnOrder = sudokuPermutation(random);
  const digits = [0, ...shuffled([1, 2, 3, 4, 5, 6, 7, 8, 9], random)];
  const transpose = random() < .5;
  const convert = grid => indices.map(i => {
    const r = rowOrder[rows[i]], c = columnOrder[i % 9];
    return digits[Number(grid[transpose ? c * 9 + r : r * 9 + c])];
  });
  const puzzle = convert(pair[0]);
  return {puzzle, solution: convert(pair[1]), givens: puzzle.filter(Boolean).length, level};
}

export function makeSudoku(level, seed) {
  if (!Number.isInteger(level) || level < 0 || level > 2) throw new RangeError('Choose Sudoku level 0, 1 or 2.');
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) throw new RangeError('Use an unsigned 32-bit puzzle seed.');
  const random = seededRandom(seed);
  for (let attempt = 0; attempt < 8; attempt++) {
    const puzzle = generate(level, random);
    if (puzzle) return puzzle;
  }
  return rescued(level, random);
}
