// Usage: node screens.js <url> <outdir> <labels.json>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [url, out, labf] = process.argv.slice(2);
  const L = JSON.parse(fs.readFileSync(labf, 'utf8'));
  const plain = (t) => t.replace(/^[^\p{L}\p{N}]+/u, '');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 950 } });
  const idle = async (extra = 1500) => {
    await p.waitForTimeout(1200);
    for (let i = 0; i < 300; i++) { if (!(await p.locator('[data-testid="stStatusWidget"]').count())) break; await p.waitForTimeout(1000); }
    await p.waitForTimeout(extra);
  };
  const shot = async (name, full = false) => { await p.screenshot({ path: `${out}/${name}.png`, fullPage: full }); };
  const tab = async (i) => { await p.getByRole('tab').nth(i).click(); await idle(); await p.evaluate(() => window.scrollTo(0, 0)); };
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.waitForSelector('[role="dialog"]', { timeout: 120000 }); await idle(500);
  await shot('00_beta');
  await p.locator('[role="dialog"] button').last().click(); await idle();
  await shot('01_wizard');
  await p.getByRole('button', { name: L.find }).click();
  await p.waitForSelector(`text=${L.use}`, { timeout: 240000 }); await idle();
  await shot('02_wizard_result');
  await p.getByRole('button', { name: L.use }).click(); await idle();
  await tab(1);
  await p.getByRole('combobox', { name: L.ftype }).first().click();
  await p.getByRole('option', { name: /Pickett-Potter/ }).first().click(); await idle(3000);
  await shot('03_design');
  await tab(2);
  await p.getByText(plain(L.tolhead)).first().waitFor({ timeout: 300000 }); await idle(3000);
  await p.evaluate(() => window.scrollTo(0, 0)); await shot('04_lab');
  const tb = p.locator('button', { hasText: plain(L.tol) }).first();
  await tb.scrollIntoViewIfNeeded(); await tb.click(); await p.getByText(plain(L.crit)).first().waitFor({ timeout: 300000 }); await idle(3000);
  await p.waitForTimeout(1000); await p.getByText(plain(L.tolhead)).first().scrollIntoViewIfNeeded(); await p.evaluate(() => window.scrollBy(0, -60));
  await shot('05_tolerances');
  await tab(3); await idle(3000); await shot('06_simulation');
  await tab(4); await idle(3000); await shot('07_lobe3d');
  await tab(5); await idle(3000); await shot('08_model3d');
  await tab(6); await shot('09_drawing');
  await tab(7);
  const hc = p.getByText(L.holes).first(); if (await hc.count()) { await hc.click(); await idle(6000); }
  await shot('10_plate');
  await tab(8); await shot('11_openems');
  const sub = p.getByRole('tab', { name: /⑤/ }); if (await sub.count()) { await sub.click(); await idle(); await shot('12_spacemap'); }
  await tab(9); await shot('13_credits');
  await b.close();
})();
