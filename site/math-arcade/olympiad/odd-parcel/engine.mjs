const directions = ['left', 'right', 'balance'];
const maxParcels = 36;

function checkCount(count) {
  if (!Number.isInteger(count) || count < 1 || count > maxParcels) {
    throw new RangeError('Choose between 1 and 36 parcels.');
  }
}

function checkId(id, count) {
  if (!Number.isInteger(id) || id < 1 || id > count) {
    throw new RangeError('Choose a parcel from this batch.');
  }
}

export function optimalBudget(count) {
  checkCount(count);
  let capacity = 1;
  let inspections = 0;
  while (capacity < count) {
    capacity *= 3;
    inspections++;
  }
  return inspections;
}

export function createRound(count, seed = 0) {
  checkCount(count);
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) {
    throw new RangeError('Batch seed must be an unsigned 32-bit integer.');
  }
  return { count, seed, candidates: Array.from({ length: count }, (_, i) => i + 1), history: [] };
}

export function outcomeGroups(round, left, right) {
  if (!Array.isArray(left) || !Array.isArray(right) || !left.length || left.length !== right.length) {
    throw new RangeError('Put the same positive number of parcels on each pan.');
  }
  const sides = new Map();
  for (const [side, batch] of [['left', left], ['right', right]]) {
    for (const id of batch) {
      checkId(id, round.count);
      if (sides.has(id)) throw new RangeError('Each parcel can occupy only one place.');
      sides.set(id, side);
    }
  }
  const groups = { left: [], right: [], balance: [] };
  for (const id of round.candidates) groups[sides.get(id) ?? 'balance'].push(id);
  return groups;
}

// The rank belongs to the labelled parcel, independent of which pan it occupies.
// Swapping all left and right assignments therefore mirrors a tied reading.
function tieRank(id, seed) {
  let x = (seed ^ id) >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x7feb352d);
  x = Math.imul(x ^ (x >>> 15), 0x846ca68b);
  return (x ^ (x >>> 16)) >>> 0;
}

export function weigh(round, left, right) {
  if (round.candidates.length === 1) throw new RangeError('One parcel remains possible. Identify it.');
  const groups = outcomeGroups(round, left, right);
  const branchSizes = Object.fromEntries(directions.map(side => [side, groups[side].length]));
  const largest = Math.max(...Object.values(branchSizes));
  const branches = directions.filter(side => branchSizes[side] === largest);
  let outcome = branches[0];
  let rank = Infinity;
  for (const branch of branches) {
    for (const id of groups[branch]) {
      const candidateRank = tieRank(id, round.seed);
      if (candidateRank < rank) {
        outcome = branch;
        rank = candidateRank;
      }
    }
  }
  const candidates = groups[outcome];
  const entry = { left: [...left], right: [...right], outcome, before: round.candidates.length, after: candidates.length, branchSizes };
  return { ...round, candidates, history: [...round.history, entry] };
}

export function identify(round, id) {
  checkId(id, round.count);
  if (!round.candidates.includes(id)) {
    const index = round.history.findIndex(row => {
      const side = row.left.includes(id) ? 'left' : row.right.includes(id) ? 'right' : 'balance';
      return row.outcome !== side;
    });
    return { status: 'ruled-out', inspection: index + 1 };
  }
  if (round.candidates.length > 1) return { status: 'ambiguous', remaining: round.candidates.length };
  return { status: 'proved' };
}

export function suggestWeighing(round) {
  const groupSize = Math.round(round.candidates.length / 3);
  if (!groupSize) return null;
  return { left: round.candidates.slice(0, groupSize), right: round.candidates.slice(groupSize, 2 * groupSize) };
}
