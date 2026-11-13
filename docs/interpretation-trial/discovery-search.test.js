import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {discover, searchIssue} from './discovery-search.js';
const read = name => JSON.parse(readFileSync(new URL(name, import.meta.url), 'utf8'));
const data = read('context-review.json').issues;
const meta = read('sample-metadata.json').issues;
const skills = read('suggested-skills.json');
const issues = data.map(x => ({...x,...meta[x.id],suggestedSkills:skills[x.id]}));
const get = id => issues.find(x => x.id === id);

test('all 20 originals have explicit filter metadata and source-supported suggestions', () => {
  assert.equal(issues.length, 20);
  assert.equal(new Set(issues.map(x => x.id)).size, 20);
  for (const x of issues) {
    assert.ok(meta[x.id]); assert.ok(Array.isArray(x.suggestedSkills));
    for (const s of x.suggestedSkills) {
      assert.ok(s.name && s.reason && s.quote);
      assert.ok(`${x.title} ${x.description}`.includes(s.quote), `${x.id}: ${s.quote}`);
    }
  }
});
test('new skills broaden discovery and the toggle removes them', () => {
  const yes = discover(issues, {skill:'Frontend development'});
  assert.ok(yes.some(x => x.issue.id === 9079));
  assert.ok(yes.every(x => x.reason.includes('Suggested skill match')));
  assert.equal(discover(issues, {skill:'Frontend development',includeSuggested:false}).length,0);
  assert.ok(searchIssue(get(9079), 'frontend').reason.includes('Suggested skill'));
  assert.equal(searchIssue(get(9079), 'frontend', false), null);
});
test('background can surface civic purpose without becoming a direct task match', () => {
  const match = searchIssue(get(9080), 'potholes');
  assert.equal(match.rank, 3);
  assert.equal(match.reason, 'Related through project background');
});
test('direct work outranks background even when original sample order is reversed', () => {
  const base = get(9080);
  const indirect = {...base,id:1,title:'Other task',summary:'Other task',purpose:'',work:'',description:'',background:'Potholes',suggestedSkills:[]};
  const direct = {...indirect,id:2,work:'Display potholes on the map',background:''};
  assert.deepEqual(discover([indirect,direct],{q:'potholes'}).map(x=>x.issue.id),[2,1]);
});
test('related wording and all-word matching work without loose substrings', () => {
  const x = get(9079);
  assert.ok(searchIssue(x,'login spaces'));
  assert.ok(searchIssue(x,'spaces sign-in'));
  assert.equal(searchIssue(x,'login nonexistentword'),null);
  assert.equal(searchIssue(x,'spa'),null);
});
test('uncertainty, provenance and speculative rationales do not produce matches', () => {
  const x = {...get(13463),uncertainty:'rust',fields:'rust',sources:['https://example.com/rust'],suggestedSkills:[{name:'Writing',reason:'rust',quote:'rust'}]};
  assert.equal(searchIssue(x,'rust'),null);
  assert.equal(searchIssue(get(13463),'python'),null);
});
test('filters combine and unknown assignment is not treated as unassigned', () => {
  const found = discover(issues,{topic:'food transparency',assignment:'assigned',skill:'Statistical analysis',status:'open'});
  assert.deepEqual(found.map(x=>x.issue.id),[13467]);
  assert.equal(discover([{...get(13467),assignment:'unknown'}],{assignment:'unassigned'}).length,0);
  assert.equal(discover(issues,{status:'closed'}).length,0);
  assert.equal(discover(issues,{project:'OpenStreetMap iD'}).length,4);
});
test('search does not mutate issue metadata or create personal scores', () => {
  const before = JSON.stringify(issues);
  discover(issues,{q:'mapping'});
  assert.equal(JSON.stringify(issues),before);
  assert.ok(discover(issues).every(x => !('score' in x) && !('score' in x.issue)));
});
