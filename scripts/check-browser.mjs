import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { chromium } from "playwright";

const output = path.resolve(process.argv[2] || "dist");
const prefix = "/niri-plus/";
const routes = ["", "story/", "tour/", "architecture/", "setup/", "recipes/notifications/", "recipes/clipboard/", "recipes/session/", "reference/"];
const mime = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json" };
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
      if (process.env.NIRI_SCREENSHOTS && ["", "story/", "tour/", "architecture/", "setup/"].includes(route) && [375, 1280].includes(width)) {
        await fs.mkdir(process.env.NIRI_SCREENSHOTS, { recursive: true });
        await page.screenshot({ path: path.join(process.env.NIRI_SCREENSHOTS, `${route.replaceAll("/", "-") || "home"}-${width}.png`), fullPage: true });
      }
    }
  }
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
  for (const route of ["", "story/", "tour/", "setup/", "reference/"]) {
    await staticPage.goto(origin + route);
    assert.ok((await staticPage.locator("main").innerText()).length > 400);
    assert.equal(await staticPage.locator("[data-scene-controls]:visible").count(), 0);
    assert.ok(await staticPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    checks += 3;
  }
  assert.equal(await staticPage.locator(".table-scroll tbody tr").first().count(), 1);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ checks, routes: routes.length, widths: [375, 768, 1280, 1600], javascript: "interactive + disabled", browser_errors: errors.length }));
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
