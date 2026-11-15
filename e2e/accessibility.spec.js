import AxeBuilder from '@axe-core/playwright';
import { test, expect } from './fixtures.js';

async function check(page) {
  const result = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(result.violations.map(v => ({
    rule: v.id, impact: v.impact,
    elements: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })),
  }))).toEqual([]);
}

test('public account forms meet automated accessibility checks', async ({ page }) => {
  await page.goto('/#/login');
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await check(page);
  await page.goto('/#/register');
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();
  await check(page);
});

test('contributor workspaces meet automated accessibility checks', async ({ page }) => {
  test.setTimeout(90000);
  await page.goto('/#/login');
  await page.getByLabel('Email', { exact: true }).fill('volunteer@civic.demo');
  await page.getByLabel('Password', { exact: true }).fill('fixture demo password');
  await page.getByRole('button', { name: 'Login', exact: true }).last().click();
  await expect(page.getByRole('heading', { name: 'Discover civic-tech issues' })).toBeVisible();
  await expect(page.locator('.resultCount')).toBeVisible();
  await check(page);
  for (const [route, heading] of [
    ['repository', 'Civic projects'], ['profile', 'Contributor profile'],
    ['saved', 'Saved issues'], ['participation', 'My contributions'],
    ['account', 'Account settings'],
  ]) {
    await page.goto('/#/' + route);
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
    await expect(page.getByText(/Loading/)).toHaveCount(0);
    await check(page);
  }
});
