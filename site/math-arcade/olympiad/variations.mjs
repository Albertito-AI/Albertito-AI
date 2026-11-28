function seededChoice(seed) {
  // Mix nearby seed numbers before choosing the first parameter.
  let state = Math.imul(seed ^ (seed >>> 16), 0x85ebca6b);
  state = Math.imul(state ^ (state >>> 13), 0xc2b2ae35);
  state ^= state >>> 16;
  return function choose(low, high) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return low + Math.floor((state / 4294967296) * (high - low + 1));
  };
}

function lastCounter(choose) {
  const benches = choose(3, 11);
  const start = choose(1, benches);
  const rounds = choose(3, 12);
  const pile = 2 ** rounds;
  const prefix = `Number ${benches} benches clockwise from 1 to ${benches}, with bench 1 after bench ${benches}. Put ${pile} counters at bench ${start} and none elsewhere. A trade spends two counters to put one at the next bench.`;
  const finish = 1 + (start - 1 + rounds) % benches;
  if (choose(0, 1) === 0) {
    return {
      prompt: prefix + ' What is the largest possible number of trades?',
      answer: String(pile - 1),
      explanation: `Each trade reduces the total by one and leaves at least one counter. Pair the entire pile, then pair the resulting pile at the next bench. In ${rounds} rounds the pile shrinks from ${pile} to 1, attaining ${pile - 1} trades.`
    };
  }
  return {
    prompt: prefix + ' Pair the whole pile in each round before advancing to the next bench. On which numbered bench does the final counter land?',
    answer: String(finish),
    explanation: `The pile halves after each round. Since ${pile} = 2^${rounds}, there are ${rounds} advances from bench ${start}. Wrapping around the ${benches} benches gives bench ${finish}.`
  };
}

function shiftedSquares(choose) {
  const degree = choose(6, 90);
  let triples = 0;
  const counts = [];
  for (let a = Math.ceil(degree / 5); a <= Math.floor(degree / 3); a++) {
    const low = Math.max(a, degree - 3 * a);
    const high = Math.floor((degree - a) / 2);
    const count = Math.max(0, high - low + 1);
    triples += count;
    counts.push(count);
  }
  const quadratic = Number(degree % 2 === 0);
  const quartic = Number(degree % 4 === 0);
  const total = triples + quadratic + quartic;
  return {
    prompt: `In The Shifted Squares, how many distinct admissible pairs (c, P) have P of degree exactly ${degree}? Count each shift together with its polynomial.`,
    answer: String(total),
    explanation: `For shift −1 count exponents a ≤ b ≤ d ≤ 2a with a+b+d = ${degree}. For each a from ${Math.ceil(degree / 5)} to ${Math.floor(degree / 3)}, b ranges from max(a, ${degree}−3a) to floor((${degree}−a)/2). The resulting counts are ${counts.join(', ')}, totalling ${triples}. The quadratic family contributes ${quadratic} and the quartic family contributes ${quartic}, for ${total} pairs.`
  };
}

function threeTurnTriangle(choose) {
  const b = choose(1, 4);
  const q = choose(2, 30);
  const numerator = 12 * b * b - 1;
  const area = choose(0, 1) === 1;
  const original = (area ? 64 : 8) * q;
  const answer = q * (area ? numerator * numerator : numerator);
  const quantity = area ? 'triangle area' : 'distance from the centroid to vertex A';
  const units = area ? 'square units' : 'units';
  return {
    prompt: `Apply three passes of the Three-Turn Triangle with settings 0, ${b}, then −${b}. The original ${quantity} is ${original} ${units}. What is the final ${quantity}, in ${units}?`,
    answer: String(answer),
    explanation: `About the unchanged centroid a pass is −I/2 + sK, with K² = 3I. The opposite settings cancel the K terms. Including the zero pass, lengths scale by (12 × ${b}² − 1)/8 = ${numerator}/8. ${area ? 'Area scales by the square of this factor.' : 'Apply the length factor to the original distance.'} The result is ${answer} ${units}.`
  };
}

// Count linear k-subspaces by dividing ordered independent bases by bases per subspace.
function binarySubspaces(dimension, k) {
  let bases = 1;
  let perSubspace = 1;
  for (let i = 0; i < k; i++) {
    bases *= 2 ** dimension - 2 ** i;
    perSubspace *= 2 ** k - 2 ** i;
  }
  return bases / perSubspace;
}

function twoMissingLamps(choose) {
  const dimension = choose(4, 7);
  const k = choose(2, 3);
  const meetingOne = choose(0, 1) === 1;
  const directions = binarySubspaces(dimension, k);
  const throughBoth = binarySubspaces(dimension - 1, k - 1);
  const all = directions * 2 ** (dimension - k);
  const answer = meetingOne ? 2 * (directions - throughBoth) : all - 2 * directions + throughBoth;
  const name = k === 2 ? 'affine planes (four points each)' : 'affine cubes (eight points each)';
  return {
    prompt: `In a binary space of dimension ${dimension}, two distinct lamps are switched off and every other lamp is on. How many ${name} ${meetingOne ? 'contain exactly one of the two switched-off lamps' : 'are entirely lit'}?`,
    answer: String(answer),
    explanation: `Counting independent ordered bases of ${k} vectors and dividing by the number of bases per direction gives ${directions} directions. Each direction has exactly one translate through a given point, so ${directions} flats pass through either specified lamp. The directions containing the difference of the two lamps correspond to ${k-1}-dimensional subspaces of a ${dimension-1}-dimensional quotient, giving ${throughBoth}. ${meetingOne ? `For each lamp, subtract flats containing both and double: 2 × (${directions} − ${throughBoth}) = ${answer}.` : `There are ${all} translates altogether. Inclusion and exclusion gives ${all} − 2 × ${directions} + ${throughBoth} = ${answer}.`}`
  };
}

const variations = new Map([
  ['last-counter', lastCounter],
  ['shifted-squares', shiftedSquares],
  ['three-turn-triangle', threeTurnTriangle],
  ['two-missing-lamps', twoMissingLamps]
]);

export function makeVariation(problemId, seed) {
  if (!Number.isInteger(seed) || seed < 0 || seed > 0x7fffffff) {
    throw new RangeError('Use an integer variation seed from 0 to 2147483647.');
  }
  const generate = variations.get(problemId);
  if (!generate) throw new RangeError('Unknown Olympiad problem.');
  return generate(seededChoice(seed));
}
