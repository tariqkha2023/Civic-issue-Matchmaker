import test from 'node:test';
import assert from 'node:assert/strict';
import { issueSummary } from './issueSummary.js';

test('source excerpts remove Markdown noise while preserving prose', () => {
  assert.equal(issueSummary('<!-- template -->\n## Fix map\nPlease **repair** [keyboard navigation](https://example.org).\n```js\nthrow error;\n```\n- [ ] Keep `focus` visible.'), 'Fix map Please repair keyboard navigation. Keep focus visible.');
});
test('empty and code-only descriptions do not invent a summary', () => {
  assert.equal(issueSummary(), '');
  assert.equal(issueSummary('```js\nconst x = 1;\n```'), '');
  assert.equal(issueSummary('![screenshot](https://example.org/image.png)'), '');
});
test('long descriptions truncate on a word boundary and indicate omission', () => {
  assert.equal(issueSummary('One two three four five six seven', 20), 'One two three four…');
});
test('technical identifiers retain their literal underscores', () => {
  assert.equal(issueSummary('Fix `user_id` and update *keyboard support*.'), 'Fix user_id and update keyboard support.');
});
