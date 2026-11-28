import { bitCount, generate, minimumSolution, mount as mountParity, toggleMask } from './parity.mjs?v=20261128m1';
import { mountRace } from './match-paths.mjs';

const strategies = [
  'Spark first tries up to three presses that leave the fewest lamps lit, then solves the remaining grid.',
  'Tracker first tries one press that leaves the fewest lamps lit, then finds a shortest solution from there.',
  'Analyst compares every first-row pattern and uses a shortest solution. Match its press count to draw.'
];

function tileName(size, cell) {
  return String.fromCharCode(65 + Math.floor(cell / size)) + (1 + cell % size);
}

export function parityPlan(puzzle, difficulty, seed) {
  const { size } = puzzle;
  const count = size * size;
  const moves = [];
  let board = puzzle.board;
  let used = 0;
  const masks = Array.from({ length: count }, (_, i) => toggleMask(size, i));
  const rotation = (seed >>> 0) % count;
  function bestPress(eligible) {
    let best = -1;
    let fewest = Infinity;
    for (let j = 0; j < count; j++) {
      const tile = (j + rotation) % count;
      if (!(eligible & (1 << tile))) continue;
      const lights = bitCount(board ^ masks[tile]);
      if (lights < fewest) {
        best = tile;
        fewest = lights;
      }
    }
    return best;
  }
  const lookAhead = [3, 1, 0][difficulty];
  for (let i = 0; i < lookAhead && board; i++) {
    const tile = bestPress(~used);
    used |= 1 << tile;
    board ^= masks[tile];
    moves.push(tile);
  }
  // Presses commute. Among tiles in the optimal continuation choose the one
  // extinguishing the most lamps now; its order never changes the final count.
  let remaining = minimumSolution(size, board);
  while (remaining) {
    const tile = bestPress(remaining);
    board ^= masks[tile];
    remaining ^= 1 << tile;
    moves.push(tile);
  }
  return moves;
}

function parityRival(puzzle) {
  const { size } = puzzle;
  let board = puzzle.board;
  let last = -1;
  return {
    play(tile) {
      last = tile;
      board ^= toggleMask(size, tile);
      return `Press ${tileName(size, tile)}, ${bitCount(board)} lights on`;
    },
    position() {
      if (!board) return 'Rival grid cleared.';
      const current = `${bitCount(board)} lights on.`;
      return last < 0 ? current : `Last press ${tileName(size, last)}. ${current}`;
    },
    draw(target) {
      const cells = Array.from({ length: size * size }, (_, i) => {
        const lit = Boolean(board & (1 << i));
        return `<span class="mp-light${lit ? ' is-on' : ''}${last === i ? ' just-pressed' : ''}" aria-hidden="true">${lit ? '✦' : '·'}</span>`;
      });
      const lit = Array.from({ length: size * size }, (_, i) => i).filter(i => board & (1 << i)).map(i => tileName(size, i));
      const description = lit.length ? `Lit squares ${lit.join(', ')}.` : 'All lights off.';
      target.innerHTML = `<div class="mp-lights" role="img" aria-label="${description}" style="--mp-size:${size}">${cells.join('')}</div>`;
    }
  };
}

export function mount(root, { difficulty, seed, onFinish }) {
  const board = generate(difficulty, seed);
  return mountRace(root, {
    game: 'Parity Lights', unit: 'press', strategy: strategies[difficulty],
    route: parityPlan(board, difficulty, seed), rival: parityRival(board), onFinish,
    mountPlayer: (target, onMove, onWin) => mountParity(target, { level: difficulty, seed, competitive: true, onMove, onWin })
  });
}
