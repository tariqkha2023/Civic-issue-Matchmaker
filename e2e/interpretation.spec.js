import { test, expect } from '@playwright/test';

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
    ...original, id: 902, title: 'Interpreted map controls', search_match: 'inferred_concept',
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
  await expect(ai.getByText('Summary source: AI interpretation. Check the original issue before starting.', { exact: true })).toBeVisible();
  await expect(ai.getByRole('heading', { name: 'What this task aims to achieve' })).toBeVisible();
  await expect(ai.getByText('The affected component is not specified.', { exact: true })).toBeVisible();
  await expect(ai.getByText(/Found through AI-inferred related terminology/)).toBeVisible();
  await expect(plain.locator('.issueExcerpt')).toHaveText(`Problem ${quote}`);
  await expect(plain.getByText('Summary source: original issue excerpt. Check the original issue before starting.', { exact: true })).toBeVisible();
  const missing = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Missing description', exact: true }) });
  for (const card of [ai, plain, missing]) {
    await expect(card.getByRole('region', { name: 'Task overview' }).getByRole('heading')).toHaveText([
      'Task summary', 'What this task aims to achieve', 'Work described in the issue', 'Still unclear',
    ]);
  }
  await expect(plain.getByText('No separate objective available. Check the original issue for its purpose.', { exact: true })).toBeVisible();
  await expect(plain.getByText('No separate work breakdown available. Check the original issue for activities and deliverables.', { exact: true })).toBeVisible();
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
