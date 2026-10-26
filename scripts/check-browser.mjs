import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { chromium } from "playwright";

const output = path.resolve(process.argv[2] || "dist");
const prefix = "/niri-plus/";
const routes = ["", "story/", "tour/", "design/", "design/contrast/", "architecture/", "setup/", "recipes/notifications/", "recipes/clipboard/", "recipes/session/", "recipes/terminal/", "recipes/desktop-utilities/", "recipes/appearance/", "reference/"];
const mime = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json", ".woff2": "font/woff2" };
const server = http.createServer(async (request, response) => {
  try {
    let url = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    if (!url.startsWith(prefix)) { response.writeHead(404).end(); return; }
    url = url.slice(prefix.length);
    if (!url || url.endsWith("/")) url += "index.html";
    const file = path.resolve(output, url);
    if (!file.startsWith(output + path.sep)) { response.writeHead(404).end(); return; }
    const bytes = await fs.readFile(file);
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "text/plain" });
    response.end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}${prefix}`;
const browser = await chromium.launch({ headless: true });
const errors = [];
let checks = 0;
try {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  for (const width of [375, 768, 1280, 1600]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of routes) {
      const response = await page.goto(origin + route);
      assert.equal(response.status(), 200);
      assert.equal(await page.locator("main").count(), 1);
      assert.equal(await page.locator("h1").count(), 1);
      assert.ok(await page.locator("main").innerText());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `horizontal overflow at ${width}: ${route}`);
      assert.equal(await page.locator("img").evaluateAll((images) => images.filter((image) => !image.complete || image.naturalWidth === 0).length), 0, `broken image: ${route}`);
      checks += 6;
      if (process.env.NIRI_SCREENSHOTS && ["", "design/", "design/contrast/", "recipes/terminal/"].includes(route) && [375, 1280].includes(width)) {
        await page.evaluate(() => document.fonts.ready);
        await fs.mkdir(process.env.NIRI_SCREENSHOTS, { recursive: true });
        await page.screenshot({ path: path.join(process.env.NIRI_SCREENSHOTS, `${route.replaceAll("/", "-") || "home"}-${width}.png`), fullPage: true });
      }
    }
  }
  await page.goto(origin + "design/");
  const identity = await (await page.request.get(origin + "data/identity.json")).json();
  assert.equal(identity.selected_candidate, "neutral-slate");
  assert.equal(identity.direction.id, "neutral-slate");
  assert.equal(identity.direction.ui_font, "Noto Sans");
  assert.equal(identity.direction.mono_font, "MesloLGS Nerd Font");
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()), identity.direction.colors.canvas);
  assert.equal(await page.locator("[data-surface-button]").count(), 4);
  assert.equal(await page.locator("[data-surface-panel]:visible").count(), 1);
  await page.locator('[data-surface-button="launch"]').focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.locator('[data-surface-button="information"]').getAttribute("aria-pressed"), "true");
  assert.equal(await page.locator('[data-surface-panel="information"]:visible').count(), 1);
  await page.locator('[data-surface-button="terminal"]').click();
  await page.evaluate(() => document.fonts.ready);
  const terminalFont = await page.locator(".terminal-transcript").evaluate(node => getComputedStyle(node).fontFamily);
  assert.match(terminalFont, /MesloLGS Nerd Font/);
  assert.ok(await page.locator(".terminal-transcript").evaluate(node => parseFloat(getComputedStyle(node).fontSize) >= 14), "Terminal specimen should use the selected 11pt size on desktop");
  assert.equal(await page.locator(".terminal-ansi-preview [role=listitem]").count(), 16);
  assert.equal(await page.locator(".ansi-reference-grid [role=listitem]").count(), 16);
  assert.ok(await page.evaluate(() => document.fonts.check('14px "Noto Sans"')));
  assert.ok(await page.evaluate(() => document.fonts.check('14px "MesloLGS Nerd Font"')));
  checks += 12;
  await page.locator('[data-surface-button="launch"]').click();
  const filter = page.getByLabel("Filter sample windows");
  await filter.fill("claude");
  assert.equal(await page.locator("[data-launch-row]:visible").count(), 1);
  assert.match(await page.locator("[data-launch-message]").innerText(), /1 sample row match/);
  await page.locator("[data-launch-row]:visible").click();
  await page.locator('[data-launch-action="new"]').click();
  assert.equal(await page.locator('[data-launch-action="new"]').getAttribute("aria-pressed"), "true");
  assert.match(await page.locator("[data-launch-message]").innerText(), /New window/);
  await filter.fill("no-such-window");
  assert.equal(await page.locator("[data-launch-row]:visible").count(), 0);
  assert.match(await page.locator("[data-launch-message]").innerText(), /No sample rows match/);
  await filter.fill("");
  await page.locator('[data-surface-button="login-lock"]').click();
  await page.locator("[data-login-error-toggle]").click();
  assert.equal(await page.locator("[data-login-error]").isVisible(), true);
  assert.equal(await page.locator("[data-login-error-toggle]").getAttribute("aria-expanded"), "true");
  checks += 10;
  await page.locator('[data-surface-button="launch"]').focus();
  await page.keyboard.press("End");
  assert.equal(await page.locator('[data-surface-button="login-lock"]').getAttribute("aria-pressed"), "true");
  checks += 1;
  await page.goto(origin + "design/contrast/");
  assert.equal(await page.locator("[data-desktop-card]:visible").count(), 2);
  assert.equal(await page.locator("[data-terminal-card]:visible").count(), 3);
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()), identity.direction.colors.canvas);
  assert.deepEqual(await page.locator(".study-desktop").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).backgroundColor)), ["rgb(21, 23, 25)", "rgb(17, 18, 19)"]);
  const desktopText = await page.locator(".study-desktop").allInnerTexts();
  assert.equal(desktopText[0], desktopText[1]);
  const transcriptText = await page.locator(".study-transcript").allInnerTexts();
  assert.deepEqual(transcriptText, Array(3).fill(transcriptText[0]));
  const terminalBackgrounds = await page.locator(".study-terminal").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).backgroundColor));
  assert.deepEqual(terminalBackgrounds, ["rgb(32, 35, 38)", "rgb(0, 0, 0)", "rgb(0, 0, 0)"]);
  assert.equal(await page.locator(".study-ansi [role=listitem]").count(), 48);
  assert.deepEqual(await page.locator(".t-rgb").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).color)), Array(3).fill("rgb(180, 168, 250)"));
  for (const state of ["warning", "error", "success"]) {
    await page.locator(`[data-study-state="${state}"]`).click();
    assert.deepEqual(await page.locator(".study-desktop").evaluateAll(nodes => nodes.map(node => node.dataset.state)), [state, state]);
    assert.equal(await page.locator(`[data-study-state="${state}"]`).getAttribute("aria-pressed"), "true");
    checks += 2;
  }
  for (const view of ["current", "proposal", "all"]) {
    const button = page.locator(`[data-desktop-view="${view}"]`);
    await button.focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.locator("[data-desktop-card]:visible").count(), view === "all" ? 2 : 1);
    if (view !== "all") assert.equal(await page.locator("[data-desktop-card]:visible").getAttribute("data-desktop-card"), view);
    checks += 2;
  }
  for (const view of ["current", "black-only", "black-vivid", "all"]) {
    await page.locator(`[data-terminal-view="${view}"]`).click();
    assert.equal(await page.locator("[data-terminal-card]:visible").count(), view === "all" ? 3 : 1);
    if (view !== "all") assert.equal(await page.locator("[data-terminal-card]:visible").getAttribute("data-terminal-card"), view);
    checks += 2;
  }
  await page.locator('[data-terminal-size="larger"]').click();
  assert.deepEqual(await page.locator(".study-transcript").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).fontSize)), Array(3).fill("16px"));
  await page.locator('[data-terminal-size="standard"]').click();
  assert.ok(await page.locator(".study-transcript").first().evaluate(node => Math.abs(parseFloat(getComputedStyle(node).fontSize) - 14.6667) < .01));
  for (const details of await page.locator(".study-details").all()) {
    await details.locator("summary").click();
    assert.ok(await details.getAttribute("open") !== null);
    checks += 1;
  }
  checks += 11;
  await page.setViewportSize({ width: 1280, height: 1000 });
  for (const route of ["", "tour/"]) {
    await page.goto(origin + route);
    for (const scene of ["terminal", "panel", "remote", "browser"]) {
      const button = page.locator(`[data-scene-button="${scene}"]`);
      await button.focus();
      await page.keyboard.press("Enter");
      assert.equal(await button.getAttribute("aria-pressed"), "true");
      assert.equal(await page.locator(".desktop-stage").getAttribute("data-scene"), scene);
      assert.equal(await page.locator('[data-scene-button][aria-pressed="true"]').count(), 1);
      checks += 3;
    }
    assert.equal(await page.locator(".desktop-stage .window").first().evaluate((node) => getComputedStyle(node).transitionDuration), "0s");
  }
  await page.goto(origin + "reference/");
  const input = page.getByLabel("Find a key or task");
  await input.fill("clipboard");
  assert.equal(await page.locator("[data-key-table] tbody tr:visible").count(), 1);
  assert.match(await page.locator("[data-key-count]").innerText(), /1 of/);
  await input.fill("no-such-binding");
  assert.equal(await page.locator("[data-key-table] tbody tr:visible").count(), 0);
  assert.match(await page.locator("[data-key-count]").innerText(), /No matching/);
  await input.fill("");
  assert.equal(await page.locator("[data-key-table] tbody tr:visible").count(), 18);
  checks += 5;
  await page.goto(origin);
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "Skip to content");
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(":focus").getAttribute("id"), "main");
  checks += 2;
  const noScript = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 375, height: 900 } });
  const staticPage = await noScript.newPage();
  for (const route of ["", "story/", "tour/", "design/", "design/contrast/", "recipes/terminal/", "recipes/desktop-utilities/", "setup/", "reference/"]) {
    await staticPage.goto(origin + route);
    assert.ok((await staticPage.locator("main").innerText()).length > 400);
    assert.equal(await staticPage.locator("[data-scene-controls]:visible").count(), 0);
    assert.equal(await staticPage.locator("[data-surface-switcher]:visible").count(), 0);
    assert.ok(await staticPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    checks += 4;
  }
  await staticPage.goto(origin + "design/");
  assert.equal(await staticPage.locator("[data-surface-panel]:visible").count(), 4);
  assert.equal(await staticPage.locator("[data-surface-button]:visible").count(), 0);
  assert.ok(await staticPage.locator("[data-surface-panel=terminal]").innerText());
  checks += 3;
  await staticPage.goto(origin + "design/contrast/");
  assert.equal(await staticPage.locator("[data-desktop-card]:visible").count(), 2);
  assert.equal(await staticPage.locator("[data-terminal-card]:visible").count(), 3);
  assert.equal(await staticPage.locator("[data-study-controls]:visible").count(), 0);
  assert.ok((await staticPage.locator("main").innerText()).includes("Proposal"));
  checks += 4;
  await staticPage.goto(origin + "reference/");
  assert.equal(await staticPage.locator(".table-scroll tbody tr").first().count(), 1);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ checks, routes: routes.length, widths: [375, 768, 1280, 1600], javascript: "interactive + disabled", browser_errors: errors.length }));
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
