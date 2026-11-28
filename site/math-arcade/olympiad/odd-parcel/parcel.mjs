import { createRound, identify, optimalBudget, suggestWeighing, weigh } from './engine.mjs';

const $ = id => document.getElementById(id);
const presets = [8, 12, 27];
const labels = { left: 'Left', right: 'Right', off: 'Off' };
const readings = { left: 'Left pan is heavier', right: 'Right pan is heavier', balance: 'The pans balance' };
const parcelName = id => 'P' + String(id).padStart(2, '0');
const parcelList = ids => ids.map(parcelName).join(', ');
const noun = (n, one, plural) => `${n} ${n === 1 ? one : plural}`;
const inspections = n => noun(n, 'inspection', 'inspections');
const possibleParcels = n => noun(n, 'possible parcel', 'possible parcels');
let round;
let mode;
let pans;
let hintStage;
let certified;

function randomSeed() {
  return crypto.getRandomValues(new Uint32Array(1))[0];
}

function readSettings() {
  const params = new URLSearchParams(location.hash.slice(1));
  const size = params.get('n') ?? '';
  const digits = params.get('seed') ?? '';
  const kind = params.get('mode');
  if (!/^\d{1,2}$/.test(size) || !/^\d{1,10}$/.test(digits)) return null;
  const count = Number(size);
  const seed = Number(digits);
  if (count < 1 || count > 36 || seed > 0xffffffff || !['free', 'challenge'].includes(kind)) return null;
  if (kind === 'challenge' && !presets.includes(count)) return null;
  return { count, seed, mode: kind };
}

function signature() {
  return `#n=${round.count}&seed=${round.seed}&mode=${mode}`;
}

function load(settings) {
  round = createRound(settings.count, settings.seed);
  mode = settings.mode;
  pans = Array(round.count + 1).fill('off');
  certified = false;
  hintStage = 0;
  $('batch-size').value = mode === 'free' ? 'free' : String(round.count);
  $('custom-label').hidden = mode !== 'free';
  $('custom-count').disabled = mode !== 'free';
  if (mode === 'free') $('custom-count').value = String(round.count);
  $('seed').textContent = String(round.seed);
  $('batch-link').href = signature();
  $('group-size').value = '1';
  $('left-tool').checked = true;
  $('reading').textContent = 'Ready for inspection.';
  document.querySelector('.scale').dataset.reading = '';
  $('budget-insight').hidden = true;
  $('share-status').replaceChildren();
  $('hint-text').textContent = '';
  $('verdict').textContent = round.count === 1 ? 'Only one parcel is possible. You can identify it immediately.' : 'A valid identification must explain every reading.';
  $('history').replaceChildren();
  $('empty-history').hidden = false;
  $('parcels').replaceChildren();
  $('guess').replaceChildren(new Option('Choose a parcel', ''));
  for (const id of round.candidates) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'parcel';
    button.dataset.id = id;
    const name = document.createElement('b');
    name.textContent = parcelName(id);
    button.append(name, document.createElement('small'));
    $('parcels').append(button);
    $('guess').add(new Option(parcelName(id), String(id)));
  }
  if (location.hash !== signature()) history.replaceState(null, '', signature());
  draw();
}

function draw() {
  const possible = new Set(round.candidates);
  const singleton = possible.size === 1;
  const locked = certified || singleton;
  const left = pans.filter(p => p === 'left').length;
  const right = pans.filter(p => p === 'right').length;
  $('possible-count').textContent = String(possible.size);
  $('used-count').textContent = String(round.history.length);
  $('allowance').textContent = mode === 'free' ? ' · free play' : ` / ${optimalBudget(round.count)}`;
  $('load-counts').textContent = `Left ${left} · Right ${right}`;
  $('selection-state').textContent = locked ? 'The readings identify a single parcel.' : left === 0 && right === 0 ? 'Load the same positive number on both pans.' : left === right ? `${noun(left, 'parcel', 'parcels')} on each pan. Ready to weigh.` : `Pans need equal counts. ${noun(Math.abs(left - right), 'more parcel', 'more parcels')} needed on the ${left < right ? 'left' : 'right'}.`;
  for (const button of $('parcels').children) {
    const id = Number(button.dataset.id);
    const side = pans[id];
    button.dataset.pan = side;
    button.classList.toggle('cleared', !possible.has(id));
    button.querySelector('small').textContent = labels[side];
    button.setAttribute('aria-label', `${parcelName(id)}, ${side === 'off' ? 'off the balance' : side + ' pan'}, ${possible.has(id) ? 'possible' : 'cleared'}`);
    button.disabled = locked;
  }
  for (const input of document.querySelectorAll('input[name=tool]')) input.disabled = locked;
  $('group-size').max = String(Math.max(1, Math.floor(possible.size / 2)));
  $('group-size').disabled = locked;
  $('fill').disabled = locked;
  $('clear-pans').disabled = locked || !(left + right);
  $('weigh').disabled = locked || left === 0 || left !== right;
  $('guess').disabled = certified;
  $('identify').disabled = certified || !$('guess').value;
  $('hint').disabled = certified;
}

function record(entry) {
  const item = document.createElement('li');
  const headline = document.createElement('strong');
  headline.textContent = `${readings[entry.outcome]}. ${entry.before} → ${entry.after} possible.`;
  const detail = document.createElement('small');
  detail.textContent = `Left ${parcelList(entry.left)} · Right ${parcelList(entry.right)}.`;
  item.append(headline, detail);
  $('history').append(item);
  $('empty-history').hidden = true;
}

function updateBudget() {
  const insight = $('budget-insight');
  if (mode === 'free') {
    insight.hidden = true;
    return;
  }
  const remaining = Math.max(0, optimalBudget(round.count) - round.history.length);
  const capacity = 3 ** remaining;
  const count = round.candidates.length;
  insight.hidden = count === 1;
  if (count === 1) return;
  const room = `${inspections(remaining)} can distinguish at most ${noun(capacity, 'label', 'labels')}.`;
  insight.textContent = count > capacity ? `${possibleParcels(count)} remain. ${room} From here the original budget is out of reach. You can still finish.` : `${possibleParcels(count)} remain. ${room} The budget is still attainable.`;
}

$('parcels').addEventListener('click', event => {
  const button = event.target.closest('button[data-id]');
  if (!button || button.disabled) return;
  const id = Number(button.dataset.id);
  const selected = document.querySelector('input[name=tool]:checked').value;
  pans[id] = pans[id] === selected ? 'off' : selected;
  draw();
});
$('parcels').addEventListener('keydown', event => {
  if (!event.target.matches('button[data-id]')) return;
  const grid = $('parcels');
  const columns = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
  const i = Number(event.target.dataset.id) - 1;
  const shifts = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -columns, ArrowDown: columns, Home: -i, End: round.count - 1 - i };
  if (!Object.hasOwn(shifts, event.key)) return;
  event.preventDefault();
  grid.children[Math.max(0, Math.min(round.count - 1, i + shifts[event.key]))].focus();
});
$('clear-pans').addEventListener('click', () => { pans.fill('off'); draw(); });
$('fill').addEventListener('click', () => {
  if (!$('group-size').reportValidity()) return;
  const k = $('group-size').valueAsNumber;
  if (!Number.isInteger(k) || k < 1 || k * 2 > round.candidates.length) {
    $('selection-state').textContent = 'Choose a positive whole number that fits on both pans.';
    return;
  }
  pans.fill('off');
  round.candidates.slice(0, k).forEach(id => { pans[id] = 'left'; });
  round.candidates.slice(k, 2 * k).forEach(id => { pans[id] = 'right'; });
  draw();
});
$('weigh').addEventListener('click', () => {
  const assigned = side => pans.flatMap((value, index) => value === side ? [index] : []);
  round = weigh(round, assigned('left'), assigned('right'));
  const entry = round.history.at(-1);
  record(entry);
  document.querySelector('.scale').dataset.reading = entry.outcome;
  $('reading').textContent = `Reading ${round.history.length}. ${readings[entry.outcome]}. ${possibleParcels(entry.after)} ${entry.after === 1 ? 'remains' : 'remain'}.`;
  pans.fill('off');
  hintStage = 0;
  $('hint-text').textContent = '';
  $('verdict').textContent = entry.after === 1 ? 'One label explains every reading. Choose it and select Identify.' : 'Choose the next inspection or identify a parcel when the evidence is sufficient.';
  $('group-size').value = '1';
  draw();
  updateBudget();
  if (entry.after === 1) $('guess').focus({ preventScroll: true });
});
$('guess').addEventListener('change', draw);
$('guess-form').addEventListener('submit', event => {
  event.preventDefault();
  if (certified || !$('guess').value) return;
  const id = Number($('guess').value);
  const verdict = identify(round, id);
  const name = parcelName(id);
  if (verdict.status === 'ruled-out') {
    $('verdict').textContent = `${name} was ruled out by inspection ${verdict.inspection}. Its position would have produced a different reading.`;
  } else if (verdict.status === 'ambiguous') {
    $('verdict').textContent = `${name} is possible, but ${noun(verdict.remaining - 1, 'other parcel also fits', 'other parcels also fit')} the evidence. Keep testing.`;
  } else {
    certified = true;
    const used = round.history.length;
    const target = optimalBudget(round.count);
    const budgetText = mode === 'free' ? `The guaranteed budget for this batch size is ${inspections(target)}.` : used <= target ? 'You met the inspection budget.' : `The budget was ${inspections(target)}. Replay to try a different opening.`;
    $('verdict').textContent = `Certified. ${name} is the heavier parcel. You used ${inspections(used)}. ${budgetText}`;
    draw();
  }
});
$('hint').addEventListener('click', () => {
  const ids = round.candidates;
  if (ids.length === 1) { $('hint-text').textContent = `Only ${parcelName(ids[0])} fits every recorded reading.`; return; }
  const suggestion = suggestWeighing(round);
  const k = suggestion.left.length;
  const hints = [
    'Imagine each of the three readings before you weigh. Which possible labels would survive the least useful reading?',
    `You have ${possibleParcels(ids.length)}. Try keeping the numbers of possible labels on the left, on the right and off the balance as close together as you can.`,
    `One efficient inspection puts ${parcelList(suggestion.left)} on the left and ${parcelList(suggestion.right)} on the right. You can load these with ${k} possible ${k === 1 ? 'parcel' : 'parcels'} per pan.`
  ];
  $('hint-text').textContent = hints[Math.min(hintStage, hints.length - 1)];
  hintStage++;
});
$('batch-size').addEventListener('change', () => {
  const free = $('batch-size').value === 'free';
  $('custom-label').hidden = !free;
  $('custom-count').disabled = !free;
});
$('batch-form').addEventListener('submit', event => {
  event.preventDefault();
  const free = $('batch-size').value === 'free';
  const count = free ? $('custom-count').valueAsNumber : Number($('batch-size').value);
  if (!Number.isInteger(count) || count < 1 || count > 36) { $('custom-count').reportValidity(); return; }
  load({ count, seed: randomSeed(), mode: free ? 'free' : 'challenge' });
});
document.querySelector('.skip').addEventListener('click', event => {
  event.preventDefault();
  $('main').focus();
});
$('batch-link').addEventListener('click', event => { event.preventDefault(); load({ count: round.count, seed: round.seed, mode }); });
$('share').addEventListener('click', async () => {
  const link = $('batch-link').href;
  try { await navigator.clipboard.writeText(link); $('share-status').textContent = 'Starting batch link copied.'; }
  catch {
    const field = document.createElement('input');
    field.readOnly = true;
    field.setAttribute('aria-label', 'Starting batch URL');
    field.value = link;
    $('share-status').replaceChildren('Select and copy this link. ', field);
    field.select();
  }
});
window.addEventListener('hashchange', () => { const settings = readSettings(); if (settings) load(settings); });
load(readSettings() ?? { count: 8, seed: randomSeed(), mode: 'challenge' });
