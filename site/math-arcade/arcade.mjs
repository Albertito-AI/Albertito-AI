import { games, levels, todaySG, dailyPuzzle, parseRoute, readWins, addWin, stats, createSudokuDealer, sudokuResumeLink } from './arcade-state.mjs?v=20261128m1';
import { mountMatchRoom, matchLink } from './match-room.mjs';

const loaders = {
  lattice: () => import('./lattice.mjs?v=20261128m1'),
  forge: () => import('./forge.mjs'),
  parity: () => import('./parity.mjs?v=20261128m1'),
  sudoku: () => import('./sudoku.mjs?v=20261128b'),
  nim: () => import('./nim.mjs'),
  reversi: () => import('./reversi.mjs')
};
const byId = id => document.getElementById(id);
const storageKey = 'atlas-maths-arcade-wins-v1';
let wins = [];
let persistent = true;
let current;
let unmount;
let revision = 0;

function readRecord() {
  try {
    const stored = readWins(localStorage.getItem(storageKey));
    wins = readWins(JSON.stringify([...stored, ...wins]));
  } catch {
    persistent = false;
  }
}

function saveWin(puzzle) {
  readRecord();
  wins = addWin(wins, { ...puzzle, solvedOn: todaySG() });
  try {
    localStorage.setItem(storageKey, JSON.stringify(wins));
    persistent = true;
  } catch {
    persistent = false;
  }
}

function randomSeed() {
  return crypto.getRandomValues(new Uint32Array(1))[0];
}

const nextSudokuSeed = createSudokuDealer(() => window.indexedDB, randomSeed);

function practiceLink(game, level, seed) {
  return '#play/' + game + '/' + level + '/' + seed;
}

function freshLink(game, level) {
  // An unseeded Sudoku URL requests a new deal. Shared URLs already have a seed.
  return game === 'sudoku' ? '#play/sudoku/' + level : practiceLink(game, level, randomSeed());
}

function prettyDay(day) {
  return new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(day + 'T12:00:00Z'));
}

function recordScreen() {
  readRecord();
  const { total, streak, days, byGame } = stats(wins, todaySG());
  byId('record-total').textContent = total;
  byId('record-streak').textContent = streak;
  byId('record-days').textContent = days;
  byId('record-games').replaceChildren(...Object.entries(games).map(([key, game]) => {
    const { count, bestLevel } = byGame[key];
    const row = document.createElement('div');
    row.className = 'record-row';
    const link = document.createElement('a');
    link.href = '#play/' + key;
    link.textContent = game.name;
    const score = document.createElement('span');
    score.textContent = count + ' solved' + (bestLevel === null ? '' : ' · Highest: ' + levels[bestLevel]);
    row.append(link, score);
    return row;
  }));
  byId('storage-note').textContent = persistent
    ? 'Your record is saved on this browser. Daily challenges change at midnight in Singapore. Complete one on its date to extend your streak.'
    : 'This browser cannot save your record. Solves are kept for this visit. Daily challenges change at midnight in Singapore.';
}

function updateDailyCTA() {
  byId('daily-cta').textContent = wins.some(win => win.day === todaySG()) ? 'Replay today’s challenge' : 'Play today’s challenge';
}

const sudokuResumeKey = 'atlas-sudoku-resume-v1';
function updateSudokuResume() {
  const link = byId('sudoku-resume');
  if (!link) return;
  let target;
  try {
    target = sudokuResumeLink(localStorage.getItem(sudokuResumeKey));
  } catch { /* Persistent storage may be unavailable. */ }
  link.hidden = !target;
  if (target) link.href = target;
  else link.removeAttribute('href');
}

function gameWin(puzzle, result) {
  saveWin(puzzle);
  updateDailyCTA();
  byId('win-heading').textContent = puzzle.day ? 'Daily challenge complete' : 'Puzzle complete';
  byId('win-details').textContent = result.details;
  byId('win-explanation').textContent = result.explanation;
  const panel = byId('win-panel');
  panel.hidden = false;
  panel.focus({ preventScroll: true });
  panel.scrollIntoView({ block: 'nearest', behavior: 'instant' });
}

function showDifficulties(puzzle) {
  const group = byId('levels');
  if (puzzle.day) {
    const active = document.createElement('span');
    active.className = 'daily-level';
    active.textContent = 'Daily level · ' + levels[puzzle.level];
    group.replaceChildren(active);
    return;
  }
  group.replaceChildren(...levels.map((name, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = name;
    button.setAttribute('aria-pressed', String(puzzle.level === index));
    button.addEventListener('click', () => {
      if (index !== puzzle.level) location.hash = freshLink(puzzle.game, index);
    });
    return button;
  }));
}

function focusPage(id, scroll) {
  if (!scroll) return;
  byId(id).focus({ preventScroll: true });
  if (id === 'games') byId(id).scrollIntoView({ block: 'start' });
  else window.scrollTo({ top: 0, behavior: 'instant' });
}

async function render(navigated = true) {
  const turn = ++revision;
  if (unmount) unmount();
  unmount = null;
  const previous = current;
  current = null;
  const board = byId('game-board');
  board.replaceChildren();
  byId('win-panel').hidden = true;
  for (const status of document.querySelectorAll('.share-status')) status.replaceChildren();
  const route = parseRoute(location.hash, todaySG());
  if (route.day && location.hash !== '#daily/' + route.day) {
    history.replaceState(null, '', '#daily/' + route.day);
  }
  const playing = route.view === 'play';
  const records = route.view === 'record';
  const matching = route.view === 'match' || route.view === 'match-setup';
  byId('match-room').hidden = !matching;
  byId('lobby').hidden = playing || records || matching;
  byId('player').hidden = !playing;
  byId('records').hidden = !records;
  for (const [id, selected] of [['nav-games', !records], ['nav-record', records]]) {
    if (selected) byId(id).setAttribute('aria-current', 'page');
    else byId(id).removeAttribute('aria-current');
  }
  document.title = (playing ? games[route.game].name + ' | ' : records ? 'My record | ' : '') + 'Maths Arcade · Albert Tan Sin Hon';
  if (matching) {
    unmount = mountMatchRoom(route, { randomSeed, sharePuzzle, focusPage, navigated });
    return;
  }
  if (records) {
    recordScreen();
    focusPage('records-title', navigated);
    return;
  }
  if (!playing) {
    updateDailyCTA();
    updateSudokuResume();
    if (route.view === 'games') focusPage('games', true);
    else if (location.hash === '#main') byId('main').focus();
    else focusPage('main', navigated);
    return;
  }
  const game = games[route.game];
  const matchEntry = byId('practice-match');
  matchEntry.href = '#match/' + route.game;
  matchEntry.textContent = route.game === 'reversi' ? 'Play a full Reversi match against the agent' : 'Play ' + game.name.replace(' Lab', '') + ' against the agent';
  byId('play-mode').textContent = (route.day ? 'Daily challenge' : 'Practice') + ' / ' + game.genre;
  byId('player-title').textContent = game.name;
  byId('puzzle-label').textContent = '';
  showDifficulties(route);
  focusPage('player-title', navigated);
  board.setAttribute('aria-busy', 'true');
  try {
    let prepared;
    if (route.seed === null) {
      if (route.game === 'sudoku') {
        const { makeSudoku } = await import('./sudoku-engine.mjs');
        if (turn !== revision) return;
        const previousSeed = previous?.game === route.game && previous.level === route.level ? previous.seed : undefined;
        route.seed = await nextSudokuSeed(route.level, previousSeed, seed => {
          prepared = makeSudoku(route.level, seed);
          return prepared.puzzle.join('');
        });
        if (turn !== revision) return;
        if (route.seed === null) {
          board.textContent = 'Those grids were recently dealt. ';
          const retry = document.createElement('button');
          retry.type = 'button';
          retry.textContent = 'Deal another set';
          retry.addEventListener('click', () => render());
          board.append(retry);
          return;
        }
      } else {
        route.seed = randomSeed();
      }
      history.replaceState(null, '', practiceLink(route.game, route.level, route.seed));
    }
    current = route;
    byId('puzzle-label').textContent = route.day ? prettyDay(route.day) + ' · Singapore' : 'Puzzle ' + route.seed.toString(36).toUpperCase();
    const { mount } = await loaders[route.game]();
    if (turn !== revision) return;
    unmount = mount(board, {
      level: route.level,
      seed: route.seed,
      puzzle: prepared,
      onWin: result => {
        if (turn === revision) gameWin(route, result);
      }
    });
  } catch {
    if (turn === revision) {
      board.textContent = 'The puzzle could not load. ';
      const reload = document.createElement('button');
      reload.type = 'button';
      reload.textContent = 'Try again';
      reload.addEventListener('click', () => location.reload());
      board.append(reload);
    }
  } finally {
    if (turn === revision) board.removeAttribute('aria-busy');
  }
}

function puzzleURL(puzzle) {
  const website = ['alberttansinhon.com', 'www.alberttansinhon.com'].includes(location.hostname);
  const url = new URL(website ? 'https://alberttansinhon.com/math-arcade/' : 'https://albertito-ai.github.io/Albertito-AI/math-arcade/');
  if (puzzle.view === 'match') url.hash = matchLink(puzzle.game, puzzle.level, puzzle.seed);
  else url.hash = puzzle.day ? '#daily/' + puzzle.day : practiceLink(puzzle.game, puzzle.level, puzzle.seed);
  return url.href;
}

// Keep the active puzzle URL and its in-progress moves when skipping navigation.
document.querySelector('.skip').addEventListener('click', event => {
  event.preventDefault();
  byId('main').focus();
});

const challengePrompts = {
  lattice: 'Which first jump brings the beacon within reach?',
  forge: 'Which two numbers would you combine first, and why?',
  parity: 'Pick one square. Which lights would change if you pressed it?',
  sudoku: 'Find one empty cell and rule out a digit. What clue rules it out?',
  nim: 'Choose a pile. How many counters would you leave?',
  reversi: 'Which legal move would you try first? Count the discs it flips.'
};

async function sharePuzzle(puzzle, status, useShareSheet) {
  if (!puzzle) return;
  const turn = revision;
  const url = puzzleURL(puzzle);
  const isMatch = puzzle.view === 'match';
  status.replaceChildren();
  if (useShareSheet && typeof navigator.share === 'function') {
    try {
      await navigator.share({ title: (isMatch ? 'Play against the agent' : games[puzzle.game].name) + ' | Maths Arcade', text: isMatch ? 'Try the same starting position and opponent difficulty.' : challengePrompts[puzzle.game], url });
      return;
    } catch (error) {
      if (turn !== revision) return;
      if (error.name === 'AbortError') {
        status.textContent = 'Sharing cancelled.';
        return;
      }
    }
  }
  try {
    await navigator.clipboard.writeText(url);
    if (turn === revision) status.textContent = isMatch ? 'Match link copied. It opens the same position and difficulty.' : 'Link copied. Your friend will get the same starting puzzle.';
  } catch {
    if (turn !== revision) return;
    const field = document.createElement('input');
    field.type = 'text';
    field.readOnly = true;
    field.value = url;
    field.setAttribute('aria-label', isMatch ? 'Match link to copy' : 'Puzzle link to copy');
    status.replaceChildren(isMatch ? 'Select and copy the link to this match.' : 'Select and copy the link to this starting puzzle.', field);
    field.focus();
    field.select();
  }
}

byId('share-daily')?.addEventListener('click', () => sharePuzzle(dailyPuzzle(todaySG()), byId('daily-share-status'), true));
const shareButton = byId('share-puzzle');
if (shareButton && typeof navigator.share === 'function') {
  shareButton.hidden = false;
  shareButton.addEventListener('click', () => sharePuzzle(current, byId('status'), true));
}
byId('copy-link').addEventListener('click', () => sharePuzzle(current, byId('status'), false));
byId('share-win')?.addEventListener('click', () => sharePuzzle(current, byId('win-share-status'), true));
function fresh() {
  if (current) location.hash = freshLink(current.game, current.level);
}
byId('again').addEventListener('click', fresh);
byId('shuffle').addEventListener('click', fresh);
window.addEventListener('hashchange', () => render());
window.addEventListener('storage', event => {
  if (event.key === sudokuResumeKey || event.key === null) updateSudokuResume();
  if (event.key === storageKey) {
    wins = readWins(event.newValue);
    if (!byId('records').hidden) recordScreen();
    updateDailyCTA();
  }
});
readRecord();
render(false);
