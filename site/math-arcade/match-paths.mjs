// Both puzzle races use the same turn and scoring rules. Each game owns its
// rival's independent state, legal moves and rendering.
export function mountRace(root, { game, strategy, unit, route, rival, mountPlayer, onFinish }) {
  const plural = unit === 'press' ? 'presses' : 'jumps';
  root.innerHTML = `
    <section class="mp-race" aria-label="${game} head-to-head match">
      <p class="mp-rules">You and the rival start with the same puzzle. Each time you move, the rival takes one turn on its own board. Finish in fewer ${plural} to win. Equal counts draw.</p>
      <div class="mp-scores" aria-label="Match score"><span>Your ${plural} <strong data-mp="player-count">0</strong></span><span>Rival ${plural} <strong data-mp="rival-count">0</strong></span></div>
      <div class="mp-layout">
        <div class="mp-player" aria-label="Your board"></div>
        <aside class="mp-rival" aria-label="Rival board">
          <h3>Rival board</h3><p class="mp-strategy"></p>
          <div class="mp-diagram"></div><p class="mp-position"></p>
          <details><summary>Rival move log</summary><ol class="mp-log"></ol></details>
        </aside>
      </div>
      <p class="mp-status" role="status" aria-live="polite" aria-atomic="true"></p>
    </section>`;
  const select = selector => root.querySelector(selector);
  const playerCount = select('[data-mp="player-count"]');
  const rivalCount = select('[data-mp="rival-count"]');
  const diagram = select('.mp-diagram');
  const position = select('.mp-position');
  const log = select('.mp-log');
  const status = select('.mp-status');
  select('.mp-strategy').textContent = strategy;
  let playerMoves = 0;
  let rivalMoves = 0;
  let disposed = false;
  let finished = false;

  function advanceRival() {
    if (rivalMoves === route.length) return '';
    const label = rival.play(route[rivalMoves]);
    rivalMoves++;
    const item = document.createElement('li');
    item.textContent = label;
    log.append(item);
    rivalCount.textContent = String(rivalMoves);
    return label;
  }

  function refreshRival() {
    rival.draw(diagram);
    position.textContent = rival.position();
  }

  function playerTurn(count) {
    if (disposed || finished) return;
    playerMoves = count;
    playerCount.textContent = String(count);
    const move = advanceRival();
    if (!move) return;
    refreshRival();
    status.textContent = rivalMoves === route.length
      ? `The rival finished in ${rivalMoves} ${plural}. You can finish your board to compare scores.`
      : `Rival ${unit} ${rivalMoves}. ${move}.`;
  }

  function playerFinished() {
    if (disposed || finished) return;
    finished = true;
    // Complete the independent route even if the player solved first. The
    // opponent gets the same scoring opportunity whichever board finishes first.
    while (rivalMoves < route.length) advanceRival();
    refreshRival();
    const outcome = playerMoves === rivalMoves ? 'draw' : playerMoves < rivalMoves ? 'win' : 'loss';
    const word = count => `${count} ${count === 1 ? unit : plural}`;
    const summary = `You finished in ${word(playerMoves)}. The rival finished in ${word(rivalMoves)}.`;
    status.textContent = summary;
    onFinish({ outcome, summary });
  }

  refreshRival();
  const stopPlayer = mountPlayer(select('.mp-player'), playerTurn, playerFinished);
  return () => {
    disposed = true;
    stopPlayer();
  };
}
