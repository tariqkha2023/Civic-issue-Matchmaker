import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {profileMatch} from './profile-match.js';

test('19 real samples can score using inferred skills; the broad tracker remains unknown', () => {
  const metadata = JSON.parse(readFileSync(new URL('sample-metadata.json', import.meta.url))).issues;
  const suggestions = JSON.parse(readFileSync(new URL('suggested-skills.json', import.meta.url)));
  for (const [id, issue] of Object.entries(metadata)) {
    const x = {...issue,suggestedSkills:suggestions[id]};
    assert.equal(profileMatch(x,{skills:suggestions[id].map(s=>s.name),interests:issue.topics}).score,id === '13463' ? null : 100);
  }
});
// Synthetic fixtures test the formula; they are never shown as real sample tasks.
test('recorded skills and interests follow the 80/20 split', () => {
  const issue = {recordedSkills:['Python','SQL'],topics:['open mapping']};
  assert.equal(profileMatch(issue,{skills:['python'],interests:['open mapping']}).score,60);
  assert.equal(profileMatch(issue,{skills:['python','sql'],interests:['food transparency']}).score,80);
  assert.equal(profileMatch(issue,{skills:['rust'],interests:['food transparency']}).score,0);
});
test('missing interests renormalize skills; missing profile skills never become zero fit', () => {
  const issue = {recordedSkills:['Python','SQL'],topics:['open mapping']};
  assert.equal(profileMatch(issue,{skills:['python'],interests:[]}).score,50);
  assert.equal(profileMatch(issue,{skills:[],interests:['open mapping']}).score,null);
});
test('inferred skills contribute without duplicates or mutation', () => {
  const issue = {recordedSkills:['Python'],topics:[],suggestedSkills:[{name:'SQL'}]};
  const before = JSON.stringify(issue);
  assert.equal(profileMatch(issue,{skills:['sql'],interests:[]}).score,50);
  assert.equal(JSON.stringify(issue),before);
  assert.equal(profileMatch({...issue,suggestedSkills:[]},{skills:['sql'],interests:[]}).score,0);
  assert.equal(profileMatch({...issue,suggestedSkills:[{name:'python'},{name:'SQL'},{name:'sql'}]},{skills:['sql'],interests:[]}).score,50);
});

test('inferred-only partial matching explains the evidence and follows the 80/20 rule', () => {
  const result = profileMatch({suggestedSkills:[{name:'Frontend development'},{name:'Input validation'}],topics:['public infrastructure']}, {skills:['Frontend development'],interests:['public infrastructure']});
  assert.equal(result.score,60);
  assert.equal(result.inferred,true);
  assert.match(result.explanation,/not confirmed requirements/);
  assert.match(result.explanation,/Not in your profile: input validation/);
});
