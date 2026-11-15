import { test, expect } from './fixtures.js';

// Offline API fixtures: these tests never need a database or an AI service.
test('cached interpretation and original-only issues remain understandable and accessible', async ({ page }, info) => {
  const quote = 'The map cannot be used with a keyboard. Fix focus movement.';
  const original = {
    id: 901, title: 'Map controls', description: `## Problem\n${quote}`,
    repository: 'civic/maps', project: { name: 'Community maps', mission: 'Public geographic information.' },
    status: 'open', url: 'https://github.com/civic/maps/issues/1',
    upstream: { number: 1, assignees: [] }, source_enabled: true,
    metadata: { skills: [], topics: [], difficulty: null, effort: null },
    labels: [], explanations: [], score: null,
  };
  const enhanced = {
    ...original, id: 902, title: 'Interpreted map controls', search_match: 'inferred_concept', clarifications: { questions: ['The affected component is not specified.'], review_notes: ['This review did not inspect the screenshot.'] },
    metadata: { ...original.metadata, interpretation: {
      summary: { text: 'Make the map usable without a mouse.', source_quote: quote },
      objective: { text: 'Let people navigate using keys.', source_quote: quote },
      activities: [{ text: 'Repair focus movement.', source_quote: 'Fix focus movement.' }],
      concepts: [{ text: 'accessible navigation', basis: 'inferred', source_quote: quote }],
      uncertainties: ['The affected component is not specified.'],
    } },
  };
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    const responses = {
      '/api/me': { id: 1, roles: ['contributor'], profile: { name: 'Test Contributor' } },
      '/api/me/unread': { notifications: 0, messages: 0 },
      '/api/projects': [],
      '/api/recommendations': { items: [enhanced, original, { ...original, id: 903, title: 'Missing description', description: '' }], total: 3 },
      '/api/tasks/902': enhanced,
    };
    return route.fulfill({ json: responses[path] ?? {} });
  });
  await page.goto('/#/home');
  await expect(page.getByLabel('Maximum estimated hours', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Experience level', { exact: true })).toHaveCount(0);
  const ai = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Interpreted map controls', exact: true }) });
  const plain = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Map controls', exact: true }) });
  await expect(ai.getByText('Make the map usable without a mouse.', { exact: true })).toBeVisible();
  await expect(ai.getByText('This review did not inspect the screenshot.', { exact: true })).not.toBeVisible();
  await expect(ai.getByRole('heading', { name: 'What this task aims to achieve' })).toBeVisible();
  await expect(ai.getByText('The affected component is not specified.', { exact: true })).toBeVisible();
  await expect(ai.getByText(/Found through AI-inferred related terminology/)).toBeVisible();
  await expect(plain.locator('.issueExcerpt')).toHaveText(`Problem ${quote}`);
  await expect(plain.getByRole('heading', { name: 'Confirm with the project' })).toHaveCount(0);
  const missing = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Missing description', exact: true }) });
  await expect(ai.getByRole('region', { name: 'Task overview' }).getByRole('heading')).toHaveText([
    'Task summary', 'What this task aims to achieve', 'Work described in the issue', 'Confirm with the project',
  ]);
  for (const card of [plain, missing]) {
    await expect(card.getByRole('region', { name: 'Task overview' }).getByRole('heading')).toHaveText(['Task summary']);
  }
  await ai.getByText('Match details and source metadata', { exact: true }).click();
  await expect(ai.getByText('This review did not inspect the screenshot.', { exact: true })).toBeVisible();
  await expect(missing.locator('.issueExcerpt')).toHaveText('No description supplied.');
  await expect(plain.getByText('Not enough information to score', { exact: true })).toBeVisible();
  await expect(plain.locator('.issueFacts')).not.toContainText('Estimated effort');
  await expect(plain.locator('.issueFacts')).not.toContainText('Experience');
  const scoring = plain.getByRole('region', { name: 'Match score', exact: true });
  await scoring.getByText('What this match is based on', { exact: true }).click();
  await expect(scoring.getByText('This issue has no assessed skills yet, so we cannot compare it with your profile.', { exact: true })).toBeVisible();
  const details = ai.locator('summary').filter({ hasText: 'Original issue text' });
  await details.focus();
  await page.keyboard.press('Enter');
  await expect(ai.locator('pre')).toHaveText(original.description);
  await expect(ai.getByRole('link', { name: 'Open on GitHub' })).toHaveAttribute('href', original.url);
  await ai.getByRole('button', { name: 'Interpreted map controls', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Interpreted map controls', exact: true })).toBeFocused();
  await expect(page.getByText('Let people navigate using keys.', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(info.project.use.viewport.width);
  expect(errors).toEqual([]);
});

test('main discovery combines saved context, suggested skills and the signed-in profile', async ({ page }) => {
  const item = {
    id: 91, title: 'Clarify selected map features', description: 'Please mention that the point is part of something.',
    repository: 'openstreetmap/iD', project: { name: 'OpenStreetMap iD' },
    status: 'open', url: 'https://github.com/openstreetmap/iD/issues/8695',
    upstream: { number: 8695 }, source_enabled: true, labels: [], explanations: [], score: 100,
    search_match: 'suggested_skill', metadata: { skills: ['frontend development'], topics: ['open mapping'], skill_weights: { 'frontend development': 0.5 }, research_evidence: [{ skill: 'frontend development', rationale: 'Changes the feature display.', quote: 'mention that the point is part of something' }] },
    reviewed_context: { summary: 'Explain how a point belongs to a map feature.', project: 'A community map editor.', background: 'Nodes can belong to larger mapped objects.', purpose: 'Avoid accidental deletions.', work: 'Clarify the selected feature display.', uncertainty: 'The wording needs confirmation.', sources: ['https://wiki.openstreetmap.org/wiki/Elements'], project_url: 'https://github.com/openstreetmap/iD', provenance: 'Saved public research.' },
  };
  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const responses = {
      '/api/me': { id: 1, roles: ['contributor'], profile: { name: 'Tester', skills: ['frontend development'], interests: ['open mapping'] } },
      '/api/me/unread': { notifications: 0, messages: 0 },
      '/api/projects': [],
      '/api/recommendations': { items: url.searchParams.get('include_suggested') === 'false' && url.searchParams.get('q') ? [] : [item], total: url.searchParams.get('include_suggested') === 'false' && url.searchParams.get('q') ? 0 : 1 },
      '/api/tasks/91': item,
    };
    return route.fulfill({ json: responses[url.pathname] ?? {} });
  });
  await page.goto('/#/home');
  await expect(page.getByRole('region', { name: 'Your matching profile' })).toContainText('frontend development');
  await expect(page.getByText('Nodes can belong to larger mapped objects.', { exact: true })).toBeVisible();
  await expect(page.getByText('Matched skills: frontend development. Not in your profile: none.', { exact: true })).toBeVisible();
  await page.getByText('Why these skills are suggested', { exact: true }).click();
  await expect(page.getByText('Changes the feature display.', { exact: true })).toBeVisible();
  await page.getByLabel('Search', { exact: true }).fill('frontend');
  await expect(page.getByText('1 matching issues', { exact: true })).toBeVisible();
  const filtered = page.waitForResponse(r => r.url().includes('/api/recommendations?') && new URL(r.url()).searchParams.get('include_suggested') === 'false');
  await page.getByLabel('Include suggested skills and inferred concepts in search').uncheck();
  await filtered;
  await expect(page.getByRole('heading', { name: 'No issues found' })).toBeVisible();
  await page.getByLabel('Include suggested skills and inferred concepts in search').check();
  await expect(page.getByRole('heading', { name: item.title, exact: true })).toBeVisible();
  await page.getByRole('button', { name: item.title, exact: true }).click();
  await expect(page.getByRole('heading', { name: item.title, exact: true })).toBeFocused();
  await expect(page.getByText(item.reviewed_context.background, { exact: true })).toBeVisible();
});
