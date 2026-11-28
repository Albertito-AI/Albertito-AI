const baseline = { own: 80, supplier: 20 };
const plans = {
  A: { own: 68, supplier: 20 },
  B: { own: 50, supplier: 65 }
};

function measuredTotal(plan, boundary) {
  if (boundary === 'own') return plan.own;
  if (boundary === 'combined') return plan.own + plan.supplier;
  throw new RangeError('Unknown emissions boundary');
}

export function evaluateRule(boundary, threshold, evidence) {
  if (!Number.isFinite(threshold) || threshold < 0.1 || threshold > 100) {
    throw new RangeError('Use a threshold between 0.1 and 100 per cent.');
  }
  const start = measuredTotal(baseline, boundary);
  const evaluations = Object.entries(plans).map(([id, plan]) => {
    const reduction = 100 * (start - measuredTotal(plan, boundary)) / start;
    return { id, reduction, pays: reduction >= threshold };
  });
  const aligned = evaluations[0].pays && !evaluations[1].pays;
  return { evaluations, aligned, verified: evidence === 'reconciled', passed: aligned && evidence === 'reconciled' };
}

function begin() {
  const get = id => document.getElementById(id);
  const choice = get('choice');
  const designer = get('designer');
  const title = get('decision-title');
  const instructions = document.querySelector('.instruction');
  const next = get('next');
  const result = get('result');
  const progress = Array.from(document.querySelectorAll('.steps li'));
  let stage = 0;
  let accepted = false;
  let finalRule = '';

  function message(titleText, body, positive = false) {
    const heading = document.createElement('strong');
    heading.textContent = titleText;
    const paragraph = document.createElement('p');
    paragraph.textContent = body;
    result.dataset.state = positive ? 'good' : 'retry';
    result.replaceChildren(heading, paragraph);
  }

  function clearResult() {
    result.replaceChildren();
    delete result.dataset.state;
    accepted = false;
    next.hidden = true;
  }

  function highlight(id) {
    for (const row of document.querySelectorAll('.data-row')) {
      row.classList.toggle('selected', row.dataset.proposal === id);
    }
  }

  function showStage(index, focus = true) {
    stage = index;
    clearResult();
    highlight('');
    progress.forEach((item, number) => {
      if (number === index) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
      item.classList.toggle('done', number < index);
    });
    get('turn').hidden = index === 3;
    get('finished').hidden = index !== 3;
    get('transfer').hidden = index !== 3;
    if (index === 3) {
      get('final-rule').textContent = finalRule;
      if (focus) get('finish-title').focus();
      return;
    }
    const headings = ['Earn the bonus', 'Take the board’s seat', 'Write a better rule'];
    const prompts = [
      'You manage the company. Which proposal earns your bonus under the current contract?',
      'You chair the board. Your objective is to reduce emissions across own operations and suppliers for the same output. Which proposal do you approve?',
      'Set a bonus that rewards the upgrade and declines outsourcing. Choose what counts, how much improvement qualifies and the evidence a reviewer needs.'
    ];
    title.textContent = headings[index];
    instructions.textContent = prompts[index];
    choice.hidden = index === 2;
    designer.hidden = index !== 2;
    choice.reset();
    if (focus) title.focus();
  }

  choice.addEventListener('change', () => {
    clearResult();
    highlight(choice.elements.plan.value);
  });

  choice.addEventListener('submit', event => {
    event.preventDefault();
    const selected = choice.elements.plan.value;
    if (!selected) return;
    if (stage === 0) {
      accepted = selected === 'B';
      message(accepted ? 'The contract pays B.' : 'The upgrade misses the bonus.',
        accepted ? 'Own emissions fall from 80 to 50, a 37.5% reduction. The contract ignores the rise in supplier emissions.' : 'Own emissions fall by 12 out of 80, or 15%. The contract requires a reduction of at least 25%. Try the other proposal.', accepted);
      next.textContent = 'Take the board’s seat';
    } else if (stage === 1) {
      accepted = selected === 'A';
      message(accepted ? 'The board approves A.' : 'Outsourcing raises combined emissions.',
        accepted ? 'A brings the total down from 100 to 88, a 12% reduction. B moves the total up to 115, a 15% increase. The board and the manager have different reasons to choose.' : 'Own operations fall to 50, but suppliers emit 65. The new total is 115, up 15% at the same output. Try the other proposal.', accepted);
      next.textContent = 'Design the new rule';
    }
    next.hidden = !accepted;
  });

  designer.addEventListener('input', clearResult);
  designer.addEventListener('change', clearResult);
  designer.addEventListener('submit', event => {
    event.preventDefault();
    const boundary = get('boundary').value;
    const threshold = get('threshold').valueAsNumber;
    const evidence = get('evidence').value;
    if (!designer.reportValidity()) return;
    const rule = evaluateRule(boundary, threshold, evidence);
    const [a, b] = rule.evaluations;
    const outcomes = 'A ' + (a.pays ? 'earns' : 'misses') + ' the bonus. B ' + (b.pays ? 'earns' : 'misses') + ' the bonus.';
    if (!rule.aligned) {
      const reason = boundary === 'own'
        ? 'Under this boundary B’s measured reduction (37.5%) exceeds A’s (15%). Any threshold that rewards A would also reward B. Try a different boundary.'
        : 'Across both sources, A reduces emissions by 12% and B increases them by 15%. Try a positive threshold that A can meet.';
      message(outcomes, reason);
      return;
    }
    if (!rule.verified) {
      message(outcomes, 'The choices fit the objective. To verify them, the reviewer still needs records that cover both sources and confirm comparable output and periods.');
      return;
    }
    finalRule = 'Pay a bonus when combined own and supplier emissions fall by at least ' + threshold + '% from baseline, for the same output and period. Reconcile the operating and supplier records and check output before awarding the bonus.';
    message(outcomes, 'A meets your ' + threshold + '% threshold with a 12% cut. B’s emissions rise by 15%. Your evidence covers both sources and the output being compared.', true);
    accepted = true;
    next.textContent = 'See my final rule';
    next.hidden = false;
  });

  next.addEventListener('click', () => {
    if (accepted && stage < 3) showStage(stage + 1);
  });
  get('reset').addEventListener('click', () => {
    designer.reset();
    get('transfer-answer').open = false;
    finalRule = '';
    showStage(0);
  });
  get('handout-link').addEventListener('click', () => { get('handout').open = true; });
  get('print-handout').addEventListener('click', () => window.print());
  window.addEventListener('beforeprint', () => { get('handout').open = true; });
  get('transfer-link').addEventListener('click', () => get('transfer-title').focus());
  showStage(0, false);
}

if (typeof document !== 'undefined') begin();
