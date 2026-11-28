const games = {
  reversi: {
    name: 'Reversi',
    description: 'Start with four discs. Play to the last legal move and finish with more discs than the agent.',
    load: () => import('./match-reversi.mjs')
  },
  nim: {
    name: 'Nim',
    description: 'Face the agent across fresh heaps. On your turn, take any number of counters from one heap. Whoever takes the last counter wins.',
    load: () => import('./match-nim.mjs')
  },
  sudoku: {
    name: 'Sudoku',
    description: 'Race the agent to complete your copy of the same Sudoku. Choose a short checkpoint if you only have time for a few deductions.',
    load: () => import('./match-sudoku.mjs')
  },
  lattice: {
    name: 'Lattice Dash',
    description: 'Start on the same square as the agent. Reach the beacon and compare how many jumps each of you needed.',
    load: () => import('./match-lattice.mjs')
  },
  forge: {
    name: 'Target Forge',
    description: 'You each get the same four numbers. Use all of them to get as close as possible to the target, then compare your arithmetic.',
    load: () => import('./match-forge.mjs')
  },
  parity: {
    name: 'Parity Lights',
    description: 'You and the agent get the same lights. Turn yours off and see who needed fewer presses.',
    load: () => import('./match-parity.mjs')
  }
};
const strengths = ['Easy', 'Medium', 'Hard'];

export function matchLink(game, level, seed) {
  return '#match/' + game + '/' + level + '/' + seed;
}

export function mountMatchRoom(route, { randomSeed, sharePuzzle, focusPage, navigated }) {
  const byId = id => document.getElementById(id);
  const setup = route.view === 'match-setup';
  const game = games[route.game];
  const room = byId('match-room');
  const board = byId('match-board');
  const result = byId('match-result');
  const controller = new AbortController();
  const { signal } = controller;
  let disposeGame;
  const listen = (node, event, handler) => node.addEventListener(event, handler, { signal });

  byId('match-setup').hidden = !setup;
  byId('match-play').hidden = setup;
  room.setAttribute('aria-labelledby', setup ? 'match-title' : 'match-game-title');
  result.hidden = true;
  board.replaceChildren();
  board.removeAttribute('aria-busy');
  if (setup) {
    document.title = 'Play against the agent | Maths Arcade';
    const select = byId('match-game');
    const form = byId('match-form');
    select.value = route.game;
    byId('match-description').textContent = game.description;
    listen(select, 'change', () => {
      byId('match-description').textContent = games[select.value].description;
      history.replaceState(null, '', '#match/' + select.value);
    });
    listen(form, 'submit', event => {
      event.preventDefault();
      const level = Number(new FormData(form).get('difficulty'));
      location.hash = matchLink(select.value, level, randomSeed());
    });
    focusPage('match-title', navigated);
  } else {
    if (route.seed === null) {
      route.seed = randomSeed();
      history.replaceState(null, '', matchLink(route.game, route.level, route.seed));
    }
    const title = game.name + ' vs the agent';
    document.title = title + ' | Maths Arcade';
    byId('match-game-title').textContent = title;
    byId('match-mode').textContent = strengths[route.level] + ' opponent';
    byId('match-change').href = '#match/' + route.game;
    byId('match-form').elements.difficulty.value = String(route.level);
    listen(byId('match-share'), 'click', () => sharePuzzle(route, byId('match-share-status'), true));
    listen(byId('match-rematch'), 'click', () => { location.hash = matchLink(route.game, route.level, randomSeed()); });
    focusPage('match-game-title', navigated);
    board.setAttribute('aria-busy', 'true');
    let finished = false;
    function onFinish({ outcome, summary }) {
      if (signal.aborted || finished) return;
      finished = true;
      byId('match-result-title').textContent = { win: 'You won', loss: 'The agent won', draw: 'A draw' }[outcome];
      byId('match-summary').textContent = summary;
      result.hidden = false;
      result.focus({ preventScroll: true });
      result.scrollIntoView({ block: 'nearest' });
    }
    game.load().then(({ mount }) => {
      if (signal.aborted) return;
      disposeGame = mount(board, { difficulty: route.level, seed: route.seed, onFinish });
    }).catch(() => {
      if (signal.aborted) return;
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.textContent = 'Reload match';
      listen(retry, 'click', () => location.reload());
      board.replaceChildren('The match could not load. ', retry);
    }).finally(() => {
      if (!signal.aborted) board.removeAttribute('aria-busy');
    });
  }

  return () => {
    controller.abort();
    if (disposeGame) disposeGame();
    board.replaceChildren();
  };
}
