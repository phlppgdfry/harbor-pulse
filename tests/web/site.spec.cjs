const { test, expect } = require('@playwright/test');
const evidence = require('../../docs/assets/sensitivity.json');

test('reviewer page loads without script errors, missing images or horizontal overflow', async ({ page }, testInfo) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('#recommendation')).toContainText('Under these assumptions:');
  await expect(page.locator('h1')).toBeVisible();
  await page.locator('footer').scrollIntoViewIfNeeded();
  await expect.poll(() => page.locator('img').evaluateAll(images => images.every(i => i.complete && i.naturalWidth > 0))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath('reviewer-page.png'), fullPage: true });
  await testInfo.attach('reviewer-page', { path: testInfo.outputPath('reviewer-page.png'), contentType: 'image/png' });
});

test('all 32 assumption combinations agree with committed analytical evidence', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#results tr')).toHaveCount(3);
  const fractions = [0, .03, .05, .075, .10, .125, .15, .20];
  const euro = new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
  for (const row of evidence.grid) {
    await page.locator('#fraction').fill(String(fractions.indexOf(row.fraction)));
    await page.locator('#value').selectOption(String(row.hour_value));
    await expect(page.locator('#recommendation')).toHaveText(`Under these assumptions: ${row.preferred}`);
    await expect(page.locator('#results tr')).toHaveText(row.options.map(o => [o.option, euro.format(o.annual_net), euro.format(o.year_one_cash), `${(o.break_even_realizable_fraction*100).toFixed(1)}%`].join('')));
  }
});

test('report gallery supports keyboard navigation and full-resolution links', async ({ page }) => {
  await page.goto('/');
  const buttons = page.locator('#report-tabs button');
  await expect(buttons).toHaveCount(5);
  for (const button of await buttons.all()) {
    await button.focus();
    await page.keyboard.press('Enter');
    await expect(button).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#report-tabs [aria-pressed="true"]')).toHaveCount(1);
    const image = page.locator('#report-image');
    await expect.poll(() => image.evaluate(i => i.complete && i.naturalWidth > 0)).toBe(true);
    await expect(page.locator('#report-full')).toHaveAttribute('href', await image.getAttribute('src'));
    await expect(image).toHaveAttribute('alt', `Actual Power BI ${await button.getAttribute('data-label')} page`);
  }
});

test('unavailable evidence produces an explicit fallback', async ({ page }) => {
  await page.route('**/assets/sensitivity.json', route => route.fulfill({ status: 503, body: '{}' }));
  await page.goto('/');
  await expect(page.locator('#recommendation')).toHaveText('Interactive evidence unavailable. Read the repository sensitivity JSON.');
});

test('two-minute video and captions are served locally', async ({ page, request }) => {
  await page.goto('/');
  await expect.poll(() => page.locator('video').evaluate(v => Number.isFinite(v.duration) ? v.duration : 0)).toBeGreaterThan(119);
  expect(await page.locator('video').evaluate(v => v.duration)).toBeLessThan(121);
  const captions = await request.get('/assets/walkthrough-en.vtt');
  expect(captions.ok()).toBe(true);
  expect(await captions.text()).toMatch(/^WEBVTT/);
});
