export const games = {
  lattice: { name: 'Lattice Dash', genre: 'Geometry' },
  forge: { name: 'Target Forge', genre: 'Arithmetic' },
  parity: { name: 'Parity Lights', genre: 'Logic' },
  sudoku: { name: 'Sudoku', genre: 'Number logic' },
  nim: { name: 'Nim Lab', genre: 'Combinatorial games' },
  reversi: { name: 'Reversi Endgame Lab', genre: 'Board strategy' }
};

export const levels = ['Warm-up', 'Tricky', 'Expert'];

const gameKeys = Object.keys(games);
// Shared daily URLs have used this rotation since the arcade launched.
const dailyGames = ['lattice', 'forge', 'parity'];
const dayLength = 86400000;
const singaporeDate = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Singapore', year: 'numeric', month: '2-digit', day: '2-digit'
});

// Deal every game once per round. A hand-picked game also counts for this round.
export function createGameShuffle(random = Math.random) {
  let remaining = new Set(gameKeys);
  return function nextGame(currentGame) {
    remaining.delete(currentGame);
    if (!remaining.size) remaining = new Set(gameKeys);
    const choices = [...remaining].filter(game => game !== currentGame);
    const game = choices[Math.floor(random() * choices.length)];
    remaining.delete(game);
    return game;
  };
}

export function todaySG(now = new Date()) {
  const parts = Object.fromEntries(singaporeDate.formatToParts(now).map(({ type, value }) => [type, value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function dayNumber(day) {
  if (typeof day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return null;
  const time = Date.parse(`${day}T00:00:00Z`);
  if (!Number.isFinite(time) || new Date(time).toISOString().slice(0, 10) !== day) return null;
  return time / dayLength;
}

function cycle(index, length) {
  return ((index % length) + length) % length;
}

export function dailyPuzzle(day) {
  const ordinal = dayNumber(day);
  if (ordinal === null) throw new RangeError('Expected a calendar date in YYYY-MM-DD format.');
  const game = dailyGames[cycle(ordinal, dailyGames.length)];
  const level = cycle(ordinal + Math.floor(ordinal / dailyGames.length), levels.length);
  // This reversible 32-bit mix gives each supported calendar day its own seed.
  let seed = ordinal >>> 0;
  seed = Math.imul(seed ^ (seed >>> 16), 0x7feb352d);
  seed = Math.imul(seed ^ (seed >>> 15), 0x846ca68b);
  seed = (seed ^ (seed >>> 16)) >>> 0;
  return { game, level, seed, day };
}

function isSeed(value) {
  return Number.isInteger(value) && value >= 0 && value <= 0xffffffff;
}

// An odd step visits every uint32 exactly once before returning to its start.
export function advanceSudokuStream(previous, randomUint32, avoidSeed, fingerprint) {
  const valid = previous && isSeed(previous.next) && isSeed(previous.step) && (previous.step & 1);
  const step = valid ? previous.step : (randomUint32() | 1) >>> 0;
  let next = valid ? previous.next : randomUint32() >>> 0;
  const recent = Array.isArray(previous?.recent)
    ? previous.recent.slice(-64).filter(value => typeof value === 'string' && /^[0-9]{81}$/.test(value))
    : [];
  // Different seeds can produce the same grid. Compare the 81 actual clues, not a hash.
  // Even a degenerate generator must yield the UI thread after a bounded number of attempts.
  for (let attempt = 0; attempt < 32; attempt++) {
    const seed = next;
    next = (seed + step) >>> 0;
    if (seed === avoidSeed) continue;
    if (!fingerprint) return { seed, state: { step, next } };
    const grid = fingerprint(seed);
    if (!recent.includes(grid)) {
      return { seed, state: { step, next, recent: [...recent.slice(-63), grid] } };
    }
  }
  return { seed: null, state: { step, next, recent } };
}

function openDealDatabase(indexedDB) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('atlas-maths-arcade-deals-v1', 1);
    let blocked = false;
    request.onupgradeneeded = () => request.result.createObjectStore('sudoku');
    request.onerror = () => reject(request.error);
    request.onblocked = () => {
      blocked = true;
      reject(new Error('Sudoku deal storage is blocked.'));
    };
    request.onsuccess = () => {
      const db = request.result;
      if (blocked) db.close();
      else {
        db.onversionchange = () => db.close();
        resolve(db);
      }
    };
  });
}

function dealInTransaction(db, level, randomUint32, avoidSeed, fingerprint) {
  return new Promise((resolve, reject) => {
    // Read and advance inside one write transaction so two tabs cannot draw the same seed.
    const transaction = db.transaction('sudoku', 'readwrite');
    const store = transaction.objectStore('sudoku');
    const read = store.get(level);
    let deal;
    let calculationError;
    read.onsuccess = () => {
      try {
        deal = advanceSudokuStream(read.result, randomUint32, avoidSeed, fingerprint);
        store.put(deal.state, level);
      } catch (error) {
        calculationError = error;
        transaction.abort();
      }
    };
    transaction.onabort = () => reject(calculationError || transaction.error || new Error('Sudoku deal was not saved.'));
    transaction.oncomplete = () => resolve(deal);
  });
}

export function createSudokuDealer(getIndexedDB, randomUint32) {
  const memory = new Map();
  let connection;
  let storageAvailable = true;
  return async function nextSudokuSeed(level, avoidSeed, fingerprint) {
    if (!Number.isInteger(level) || level < 0 || level >= levels.length) {
      throw new RangeError('Invalid Sudoku difficulty.');
    }
    if (storageAvailable) {
      try {
        connection ??= openDealDatabase(getIndexedDB());
        const deal = await dealInTransaction(await connection, level, randomUint32, avoidSeed, fingerprint);
        memory.set(level, deal.state);
        return deal.seed;
      } catch {
        storageAvailable = false;
      }
    }
    const deal = advanceSudokuStream(memory.get(level), randomUint32, avoidSeed, fingerprint);
    memory.set(level, deal.state);
    return deal.seed;
  };
}

export function sudokuResumeLink(raw) {
  try {
    const saved = JSON.parse(raw);
    if (saved && Number.isInteger(saved.level) && saved.level >= 0 && saved.level < levels.length && isSeed(saved.seed)) {
      return '#play/sudoku/' + saved.level + '/' + saved.seed;
    }
  } catch { /* An unavailable or obsolete save leaves the resume link hidden. */ }
  return null;
}

export function parseRoute(hash, today = todaySG()) {
  const fallback = { view: 'home' };
  if (typeof hash !== 'string') return fallback;
  const [page, ...args] = hash.replace(/^#/, '').split('/');
  if ((page === 'games' || page === 'record') && !args.length) return { view: 'games' };
  if (page === 'daily' && args.length <= 1) {
    const requestedDay = args.length ? args[0] : today;
    if (dayNumber(requestedDay) === null || dayNumber(today) === null) return fallback;
    return { view: 'play', ...dailyPuzzle(requestedDay > today ? today : requestedDay) };
  }
  if (page === 'match' && args.length === 0) return { view: 'match-setup', game: 'reversi' };
  if (!['play', 'match'].includes(page) || !Object.hasOwn(games, args[0]) || args.length > 3) return fallback;
  if (page === 'match' && args.length === 1) return { view: 'match-setup', game: args[0] };
  const [game, rawLevel, rawSeed] = args;
  if (rawLevel !== undefined && !/^[0-2]$/.test(rawLevel)) return fallback;
  if (rawSeed !== undefined && (!/^\d{1,10}$/.test(rawSeed) || !isSeed(Number(rawSeed)))) return fallback;
  return { view: page, game, level: Number(rawLevel ?? 0), seed: rawSeed === undefined ? null : Number(rawSeed), day: null };
}
