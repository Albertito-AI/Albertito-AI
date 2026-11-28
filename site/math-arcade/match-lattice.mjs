import { landing, makeBoard, mount as mountLattice, shortestRoute } from './lattice.mjs?v=20261128m1';
import { mountRace } from './match-paths.mjs';

const strategies = [
  'Scout explores up to four nearby landings before finding a shortest route from there.',
  'Navigator scouts up to two landings, then finds a shortest route from its position.',
  'Pathfinder searches the whole grid for a shortest route. Matching that route’s length earns a draw.'
];

export function latticePlan(board, difficulty, seed) {
  const moves = [];
  const visited = new Set([board.start]);
  let cell = board.start;
  const scouting = [4, 2, 0][difficulty];
  for (let step = 0; step < scouting && cell !== board.goal; step++) {
    const options = board.vectors.map((_, key) => ({ key, next: landing(board, cell, key) }));
    const beacon = options.find(option => option.next === board.goal);
    const fresh = options.filter(option => option.next >= 0 && !visited.has(option.next));
    if (!beacon && !fresh.length) break;
    const rotation = ((seed >>> 0) + Math.imul(cell + 1, 2654435761) + step) >>> 0;
    const choice = beacon ?? fresh[rotation % fresh.length];
    moves.push(choice.key);
    cell = choice.next;
    visited.add(cell);
  }
  return moves.concat(shortestRoute(board, cell));
}

function coords(board, cell) {
  return `(${cell % board.size}, ${Math.floor(cell / board.size)})`;
}

function latticeRival(board) {
  const trail = [board.start];
  const side = 22 * (board.size - 1) + 28;
  function point(cell) {
    return [14 + 22 * (cell % board.size), side - 14 - 22 * Math.floor(cell / board.size)];
  }
  const dots = Array.from({ length: board.size ** 2 }, (_, cell) => {
    const [x, y] = point(cell);
    if (board.blocked.has(cell)) return `<path d="M${x - 2} ${y - 2}l4 4m-4 0l4 -4" stroke="#e9a995" stroke-width="2"/>`;
    return `<circle cx="${x}" cy="${y}" r="1.7" fill="#65877c"/>`;
  }).join('');
  const [gx, gy] = point(board.goal);
  return {
    play(move) {
      const from = trail.at(-1);
      const next = landing(board, from, move);
      trail.push(next);
      return `Jump ${move + 1}, ${coords(board, from)} to ${coords(board, next)}`;
    },
    position() {
      const current = trail.at(-1);
      return current === board.goal ? `Beacon reached at ${coords(board, current)}.` : `Rival at ${coords(board, current)}. Beacon at ${coords(board, board.goal)}.`;
    },
    draw(target) {
      const current = trail.at(-1);
      const [x, y] = point(current);
      target.innerHTML = `<svg class="mp-lattice-map" viewBox="0 0 ${side} ${side}" role="img" aria-label="${this.position()}">${dots}
        <polyline points="${trail.map(cell => point(cell).join(',')).join(' ')}" fill="none" stroke="#b8a3ff" stroke-width="2"/>
        <path d="M${gx} ${gy - 8}l3 5 5 3-5 3-3 5-3-5-5-3 5-3z" fill="#ffd778"/>
        <circle cx="${x}" cy="${y}" r="6" fill="#c2abff" stroke="#1d1636" stroke-width="2"/></svg>`;
    }
  };
}

export function mount(root, { difficulty, seed, onFinish }) {
  const board = makeBoard(difficulty, seed);
  return mountRace(root, {
    game: 'Lattice Dash', unit: 'jump', strategy: strategies[difficulty],
    route: latticePlan(board, difficulty, seed), rival: latticeRival(board), onFinish,
    mountPlayer: (target, onMove, onWin) => mountLattice(target, { level: difficulty, seed, competitive: true, onMove, onWin })
  });
}
