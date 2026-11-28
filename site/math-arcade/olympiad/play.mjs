import counter from './algebra.mjs';
import square from './arithmetic.mjs';
import triangle from './geometry.mjs';
import lamps from './combinatorics.mjs';
import investigations from './investigations.mjs';
import cases from './applications.mjs';
import {makeVariation} from './variations.mjs';

const problems = [counter, triangle, square, lamps];
const connections = {
  'last-counter': ['nim', 'Nim Lab', 'Two positions with the same number of counters can behave differently. Find an example in Nim.'],
  'three-turn-triangle': ['lattice', 'Lattice Dash', 'Try describing a route with vectors. Which distances change when you rotate the whole grid?'],
  'shifted-squares': ['forge', 'Target Forge', 'Try representing a sequence of operations by an expression. Which restrictions survive each operation?'],
  'two-missing-lamps': ['parity', 'Parity Lights', 'Write a board as a string of bits. Which parts of the cube argument still make sense for a single tap?']
};
const accents = ['#b5edc4','#ccbaff','#8ddcf4','#ffd077'];
const github = 'https://github.com/Albertito-AI/atlas-open-mathematics/blob/main/research/olympiad/problems/';
const landing = document.getElementById('landing');
const article = document.getElementById('problem');
const local = new Map();
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function anchor(label, href, className) {
  const node = el('a', label, className); node.href = href; return node;
}
function button(label, onClick, className) {
  const node = el('button', label, className);
  node.type = 'button'; node.addEventListener('click', onClick); return node;
}
function section(title, className) {
  const node = el('section', undefined, className); node.append(el('h2',title)); return node;
}
function readState(id) {
  if (local.has(id)) return local.get(id);
  let value = {};
  try { const saved = JSON.parse(localStorage.getItem('atlas-olympiad-v1:' + id)); if (saved && typeof saved === 'object') value = saved; } catch {}
  local.set(id,value); return value;
}
function save(id) {
  try { localStorage.setItem('atlas-olympiad-v1:' + id, JSON.stringify(readState(id))); return true; } catch { return false; }
}
function details(title) {
  const box=el('details'); box.append(el('summary',title)); return box;
}
function list(items,ordered=false) {
  const node=el(ordered?'ol':'ul'); for(const item of items) node.append(el('li',item)); return node;
}
function question(q, key, reveal=false) {
  const form=el('form',undefined,'task');
  const label=el('label',q.prompt); label.htmlFor=key;
  const field=el('input'); field.id=key; field.type='text'; field.autocomplete='off'; field.spellcheck=false;
  const submit=el('button','Check answer'); submit.type='submit';
  const row=el('div',undefined,'row'); row.append(field,submit);
  const result=el('p',undefined,'feedback'); result.setAttribute('role','status');
  form.append(label,row,result);
  form.addEventListener('submit',e=>{
    e.preventDefault(); const raw=field.value.trim().replace(/^−/,'-');
    if (!/^[+-]?\d{1,100}$/.test(raw)) { result.textContent='Enter a whole number, including a minus sign if needed.'; return; }
    const matches = BigInt(raw)===BigInt(q.answer);
    result.textContent = matches ? 'Correct. '+q.explanation : 'Try again. Look for a small case you can calculate by hand.';
  });
  if (reveal) {
    const worked=details('Show the worked answer');
    worked.addEventListener('toggle',()=>{
      if(worked.open && worked.children.length===1) worked.append(el('p',q.answer+'. '+q.explanation));
    });
    form.append(worked);
  }
  return form;
}
function renderCards() {
  const cards=document.getElementById('cards');
  problems.forEach((p,i)=>{
    const card=anchor('', '#'+p.id,'card'); card.style.setProperty('--accent',accents[i]);
    card.append(el('span',p.level+' / '+p.subject,'label'),el('h3',p.title),el('p',p.intro),el('span','Open challenge','card-action')); cards.append(card);
  });
}
function route(focus=false) {
  const id=location.hash.slice(1);
  const p=problems.find(x=>x.id===id); landing.hidden=!!p; article.hidden=!p; article.replaceChildren();
  document.title=(p?p.title+' | ':'')+'Atlas Math Olympiad | Albert Tan Sin Hon';
  if (!p) {
    if (focus) {const h=document.getElementById('list-heading');h.tabIndex=-1;h.focus({preventScroll:true});h.scrollIntoView({block:'start'});}
    return;
  }
  const state=readState(p.id); const keep=()=>save(p.id);
  const top=el('header',undefined,'problem-head');
  const h1=el('h1',p.title); h1.tabIndex=-1;
  top.append(el('p',p.level+' / '+p.subject,'label'),h1,el('p',p.intro,'dek'));
  article.append(anchor('All four challenges','#challenges','back'),top);
  const work=el('div',undefined,'work'); article.append(work);
  const statement=section('The challenge','statement');
  for(const text of p.statement) statement.append(el('p',text));
  if (p.diagram) {const fig=el('figure');const img=el('img');img.src=p.diagram;img.alt=p.diagramAlt;fig.append(img);statement.append(fig);}
  const proofUrl=github+p.id+'.md';
  const scratch=section('Your proof notebook');
  const note=el('label','Try an example, state a conjecture, or draft your proof.');note.htmlFor='notebook';
  const area=el('textarea');area.id='notebook';area.rows=5;area.value=typeof state.draft==='string'?state.draft:'';
  const storage=el('small','Your notes stay in this browser.');storage.id='notebook-storage';area.setAttribute('aria-describedby',storage.id);
  area.addEventListener('input',()=>{state.draft=area.value;storage.textContent=keep()?'Draft saved in this browser.':'Notes are available for this visit. This browser could not save them.';});scratch.append(note,area,storage);
  const help=section('Find a way in'); const count=Number(state.hints);
  let visible=Number.isInteger(count)?Math.min(Math.max(count,0),p.hints.length):0;
  const hints=el('ol',undefined,'hints');hints.setAttribute('aria-live','polite');
  const hint=button('',()=>{if(visible<p.hints.length){visible++;state.hints=visible;keep();hints.append(el('li',p.hints[visible-1]));updateHint();}});
  function updateHint(){hint.textContent=visible===p.hints.length?'All hints shown':'Show hint '+(visible+1)+' of '+p.hints.length;hint.disabled=visible===p.hints.length;}
  for(const item of p.hints.slice(0,visible)) hints.append(el('li',item)); updateHint();
  help.append(hint,hints);
  const cp=details('Try the numerical checkpoints');
  for(const [i,q] of p.checkpoints.entries()) cp.append(question(q,'checkpoint-'+i,true));help.append(cp);
  const proof=section('Compare your proof','proof');
  const official=details('Reveal the worked proof and self-check rubric');
  function fillProof() {
    if (!official.open || official.children.length>1) return;
    const steps=el('ol');
    for(const step of p.proof){const item=el('li');item.append(el('h3',step.title),el('p',step.body));steps.append(item);}
    official.append(steps,el('h3','Check your reasoning'),list(p.rubric),el('p',p.credit,'credit'));
  }
  official.open=state.proof===true;fillProof();official.addEventListener('toggle',()=>{fillProof();state.proof=official.open;keep();});
  proof.append(official,anchor('Read this full solution and its verification on GitHub (spoilers)',proofUrl));
  const app=cases[p.id];
  const applied=section('Use it in the world','case');
  applied.append(el('h3',app.title,'prompt-title'),el('p',app.scenario),el('p',app.question));
  const prediction=el('label','Record your prediction or observations');prediction.htmlFor='field-notes';
  const observation=el('textarea');observation.id='field-notes';observation.rows=2;observation.value=typeof state.observation==='string'?state.observation:'';
  const privateNote=el('small','Saved in this browser when storage is available.');privateNote.id='case-storage';observation.setAttribute('aria-describedby',privateNote.id);
  observation.addEventListener('input',()=>{state.observation=observation.value;privateNote.textContent=keep()?'Observation saved in this browser.':'Observation available for this visit only.';});
  applied.append(prediction,observation,privateNote);
  const modelling=details('Compare your decision with the worked model');
  modelling.addEventListener('toggle',()=>{
    if (!modelling.open || modelling.children.length>1) return;
    for(const step of app.model) modelling.append(el('p',step));
    modelling.append(el('strong','Where the model stops'),el('p',app.limitation));
  });applied.append(modelling,el('strong','Test it yourself'),el('p',app.investigate));
  const transfer=section('Change the problem');transfer.append(question(p.transfer,'transfer',true));
  const lab=section('Try another example');
  const labBody=el('div');let seed=Number.isSafeInteger(state.seed)?state.seed:(Math.floor(Date.now()/86400000)%2147483647);
  function renderVariant(){labBody.replaceChildren(question(makeVariation(p.id,seed),'variation',true));}
  const fresh=button('Give me a different example',()=>{const old=makeVariation(p.id,seed).prompt;
    for(let attempt=0;attempt<512;attempt++){seed=(seed+1)%2147483647;if(makeVariation(p.id,seed).prompt!==old)break;}
    state.seed=seed;keep();renderVariant();const field=labBody.querySelector('input');field.focus();
  });renderVariant();lab.append(labBody,fresh);
  const exploration=section('Take the investigation further');
  exploration.append(el('p',investigations[p.id]),el('h3','Try a related arcade game'));
  const [game,name,connection]=connections[p.id];exploration.append(el('p',connection),anchor('Play '+name,'../#play/'+game));
  const next=problems[(problems.indexOf(p)+1)%problems.length];
  exploration.append(el('h3','Another question to explore'),anchor(next.title,'#'+next.id));
  const jumps=el('nav',undefined,'anchor-nav');jumps.setAttribute('aria-label','Within this challenge');
  for (const [label,target] of [['Try the problem',statement],['Get a hint',help],['Explore the application',applied],['Try a variation',lab]]) {
    const jump=button(label,()=>{const heading=target.firstElementChild;heading.tabIndex=-1;heading.focus({preventScroll:true});target.scrollIntoView();});jumps.append(jump);
  }
  work.append(jumps,statement,scratch,help,proof,applied,transfer,lab,exploration);
  if (focus) {h1.focus({preventScroll:true});window.scrollTo(0,0);}
}
document.querySelector('.skip').addEventListener('click',event=>{event.preventDefault();document.getElementById('main').focus();});
renderCards();route();window.addEventListener('hashchange',()=>route(true));
