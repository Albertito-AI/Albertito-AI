'use strict';
// Unit-level interaction checks using the actual inline script and a minimal DOM.
// This is not a browser, layout or assistive-technology test.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = process.argv[2] || require('node:path').join(__dirname, '../../site/ibol/activities/study-lab.html');
const html = fs.readFileSync(path, 'utf8');
const blocks = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
const dataBlock = blocks.find(b => b[1].includes('study-card-data'));
const script = blocks.find(b => !b[1].includes('application/'))[2];
const cards = JSON.parse(dataBlock[2]);
let focused = null;
const elements = new Map();
for (const match of html.matchAll(/<([a-z0-9-]+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
 const attrs = Object.fromEntries([...match[2].matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
 const node = { id: match[3], tag: match[1], attrs, hidden:/\bhidden(?:\s|$)/.test(match[2]), disabled:false, textContent:'', listeners:{},
  setAttribute(k,v){this.attrs[k]=v;},
  addEventListener(k,fn){this.listeners[k]=fn;},
  focus(){focused=this.id;},
  click(){if(!this.disabled && this.listeners.click)this.listeners.click();}
 };
 elements.set(node.id,node);
}
elements.get('study-card-data').textContent = dataBlock[2];
const document = {getElementById(id){assert(elements.has(id),'missing element '+id); return elements.get(id);}};
const node = id=>document.getElementById(id);
vm.runInNewContext(script,{document}, {timeout:1000});
assert.equal(node('interactive').hidden,false);
assert.equal(node('progress').textContent,'Card 1 of 8');
assert.equal(node('previous').disabled,true);
assert.equal(node('answer').hidden,true);
assert.equal(focused,null,'initial load must not steal focus');
for (let i=0;i<cards.length;i++) {
 assert.equal(node('card-title').textContent,cards[i].title);
 assert.equal(node('question').textContent,cards[i].question);
 assert.equal(node('source-link').href,cards[i].source_url);
 assert.equal(node('answer').hidden,true,'each card begins with answer hidden');
 assert.equal(node('reveal').attrs['aria-expanded'],'false');
 node('reveal').click();
 assert.equal(node('answer').hidden,false);
 assert.equal(node('answer-text').textContent,cards[i].answer);
 assert.equal(node('reveal').attrs['aria-expanded'],'true');
 assert.match(node('status').textContent,/Commentary shown/);
 node('reveal').click();
 assert.equal(node('answer').hidden,true);
 assert.match(node('status').textContent,/Commentary hidden/);
 if(i<cards.length-1){node('next').click();assert.equal(focused,'card-title');}
}
assert.equal(node('next').disabled,true);
node('next').click();
assert.equal(node('progress').textContent,'Card 8 of 8','last card cannot overflow');
node('previous').click();
assert.equal(node('progress').textContent,'Card 7 of 8');
assert.equal(node('next').disabled,false);
node('reveal').click();
node('restart').click();
assert.equal(node('progress').textContent,'Card 1 of 8');
assert.equal(node('answer').hidden,true);
assert.equal(node('previous').disabled,true);
assert.equal(node('next').disabled,false);
assert.equal(node('reveal').attrs['aria-expanded'],'false');
assert.equal(focused,'card-title');
assert.match(node('status').textContent,/Restarted at card 1/);
node('previous').click();
assert.equal(node('progress').textContent,'Card 1 of 8','first card cannot underflow');
for(const id of ['reveal','previous','next','restart']){assert.equal(node(id).tag,'button');assert.equal(node(id).attrs.type,'button');}
assert.equal(node('status').attrs.role,'status');
assert.equal(node('status').attrs['aria-live'],'polite');
assert.equal(node('status').attrs['aria-atomic'],'true');
assert.equal(node('card-title').attrs.tabindex,'-1');
assert.equal(node('card-title').attrs['aria-describedby'],'progress');
assert.equal(node('interactive').attrs['aria-describedby'],'keyboard-help');
assert(!/keydown|keypress|keyup/.test(script),'native keyboard behaviour must not be intercepted');
console.log('PASS: eight-card reveal/hide sequence, source correspondence, bounds, backwards navigation, restart, focus policy, native button semantics and status attributes.');
