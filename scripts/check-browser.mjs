import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { chromium } from "playwright";

const output = path.resolve(process.argv[2] || "dist");
const prefix = "/niri-plus/";
const routes = ["", "story/", "tour/", "tour/earlier/", "design/", "design/contrast/", "architecture/", "components/", "setup/", "setup/agent/", "recipes/notifications/", "recipes/clipboard/", "recipes/session/", "recipes/terminal/", "recipes/desktop-utilities/", "recipes/rofi-controls/", "recipes/appearance/", "recipes/displays/", "recipes/login/", "recipes/hardware-feedback/", "recipes/input/", "recipes/files/", "reference/"];
const mime = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".png": "image/png", ".mp4": "video/mp4", ".svg": "image/svg+xml", ".json": "application/json", ".woff2": "font/woff2" };

function parseByteRange(header, size) {
  const match = /^bytes=(\d*)-(\d*)$/.exec(header || "");
  if (!match) return null;
  const [, first, last] = match;
  if (!first && !last) return { unsatisfiable: true };
  if (!first) {
    const suffixLength = Number(last);
    if (!Number.isSafeInteger(suffixLength) || suffixLength <= 0 || size <= 0) return { unsatisfiable: true };
    return { start: Math.max(0, size - suffixLength), end: size - 1 };
  }
  const start = Number(first);
  const requestedEnd = last ? Number(last) : size - 1;
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(requestedEnd) || start >= size || requestedEnd < start) return { unsatisfiable: true };
  return { start, end: Math.min(requestedEnd, size - 1) };
}

const server = http.createServer(async (request, response) => {
  try {
    let url = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    if (!url.startsWith(prefix)) { response.writeHead(404).end(); return; }
    url = url.slice(prefix.length);
    if (!url || url.endsWith("/")) url += "index.html";
    const file = path.resolve(output, url);
    if (!file.startsWith(output + path.sep)) { response.writeHead(404).end(); return; }
    const bytes = await fs.readFile(file);
    const contentType = mime[path.extname(file)] || "text/plain";
    if (path.extname(file) === ".mp4") {
      const range = parseByteRange(request.headers.range, bytes.length);
      if (range?.unsatisfiable) {
        response.writeHead(416, { "Accept-Ranges": "bytes", "Content-Range": `bytes */${bytes.length}`, "Content-Type": contentType }).end();
        return;
      }
      if (range) {
        const body = bytes.subarray(range.start, range.end + 1);
        response.writeHead(206, {
          "Accept-Ranges": "bytes",
          "Content-Range": `bytes ${range.start}-${range.end}/${bytes.length}`,
          "Content-Length": body.length,
          "Content-Type": contentType,
        });
        response.end(request.method === "HEAD" ? undefined : body);
        return;
      }
      response.writeHead(200, { "Accept-Ranges": "bytes", "Content-Length": bytes.length, "Content-Type": contentType });
      response.end(request.method === "HEAD" ? undefined : bytes);
      return;
    }
    response.writeHead(200, { "Content-Type": contentType });
    response.end(request.method === "HEAD" ? undefined : bytes);
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
      await page.locator("img").evaluateAll((images) => images.filter((image) => !image.closest("video")).forEach((image) => { image.loading = "eager"; }));
      await page.waitForFunction(() => [...document.images].filter((image) => !image.closest("video")).every((image) => image.complete && image.naturalWidth > 0), null, { timeout: 10000 });
      const brokenImages = await page.locator("img").evaluateAll((images) => images.filter((image) => !image.closest("video") && (!image.complete || image.naturalWidth === 0)).map((image) => ({src: image.getAttribute("src"), complete: image.complete, width: image.naturalWidth})));
      assert.deepEqual(brokenImages, [], `broken image: ${route}`);
      checks += 6;
      if (process.env.NIRI_SCREENSHOTS && ["", "tour/", "tour/earlier/", "design/", "design/contrast/", "recipes/terminal/", "setup/", "setup/agent/", "recipes/login/", "recipes/session/", "recipes/input/", "recipes/desktop-utilities/"].includes(route) && [375, 1280].includes(width)) {
        await page.evaluate(() => document.fonts.ready);
        await fs.mkdir(process.env.NIRI_SCREENSHOTS, { recursive: true });
        await page.screenshot({ path: path.join(process.env.NIRI_SCREENSHOTS, `${route.replaceAll("/", "-") || "home"}-${width}.png`), fullPage: true });
      }
    }
  }
  await page.goto(origin);
  await page.locator('nav a', { hasText: "Setup" }).click();
  assert.equal(page.url(), origin + "setup/");
  assert.equal(await page.locator("main pre").count(), 0);
  const setupAction = page.locator('main a.button[href$="setup/agent/"], main a.button[href="agent/"]');
  const setupColors = await setupAction.evaluate((element) => {
    const style = getComputedStyle(element);
    return { foreground: style.color, background: style.backgroundColor };
  });
  assert.notEqual(setupColors.foreground, setupColors.background, "prose link styles must preserve button contrast");
  await setupAction.click();
  assert.match(page.url(), /setup\/agent\/$/);
  assert.equal(new URL(await page.locator('nav a[aria-current]').getAttribute("href"), page.url()).pathname, prefix + "setup/");
  const textLink = page.locator('main a[href$="agent.md"]').first();
  const textResponse = await page.request.get(new URL(await textLink.getAttribute("href"), page.url()).href);
  assert.equal(textResponse.status(), 200);
  assert.ok((await textResponse.text()).startsWith("# Agent setup guide"));
  assert.ok((await textResponse.text()).includes("## Completion report"));
  checks += 8;
  await page.goto(origin);
  const nativeDemoLink = page.locator('a[href$="tour/#native-reference-demo"]');
  assert.equal(await nativeDemoLink.count(), 1);
  await nativeDemoLink.click();
  assert.match(page.url(), /tour\/#native-reference-demo$/);
  assert.equal(await page.locator("[data-native-demo]").count(), 2);
  assert.equal(await page.locator("[data-native-demo]").first().getAttribute("data-native-demo"), "desktop-800");
  const earlierLink = page.locator('main a[href$="tour/earlier/"], main a[href="earlier/"]').first();
  assert.equal(await earlierLink.count(), 1);
  const provenanceResponse = await page.request.get(origin + "assets/provenance.json");
  assert.equal(provenanceResponse.status(), 200);
  const provenance = await provenanceResponse.json();
  const clipsById = Object.fromEntries(provenance.desktop_demos.clips.map((clip) => [clip.id, clip]));
  const inventoriedAssets = new Set(provenance.files.map((file) => file.path));
  checks += 3;
  const rangeResponse = await page.request.get(origin + "assets/demo-overview.mp4", { headers: { Range: "bytes=0-99" } });
  assert.equal(rangeResponse.status(), 206);
  assert.equal(rangeResponse.headers()["accept-ranges"], "bytes");
  assert.equal(rangeResponse.headers()["content-type"], "video/mp4");
  assert.match(rangeResponse.headers()["content-range"], /^bytes 0-99\/\d+$/);
  assert.equal((await rangeResponse.body()).length, 100);
  const invalidRange = await page.request.get(origin + "assets/demo-overview.mp4", { headers: { Range: "bytes=999999999999999-" } });
  assert.equal(invalidRange.status(), 416);
  checks += 5;
  for (const name of ["desktop-800", "controls-800", "desktop", "controls", "overview", "browser-files", "terminal", "information"]) {
    await page.goto(origin + (["desktop-800", "controls-800"].includes(name) ? "tour/" : "tour/earlier/"));
    const selector = `[data-native-demo="${name}"] video`;
    const video = page.locator(selector);
    assert.equal(await video.count(), 1);
    assert.equal(await video.evaluate((element) => element.controls), true);
    assert.equal(await video.evaluate((element) => element.autoplay), false);
    assert.equal(await video.evaluate((element) => element.preload), "none");
    assert.equal(await video.evaluate((element) => element.playsInline), true);
    const clip = clipsById[name];
    assert.ok(clip, `missing provenance record: ${name}`);
    assert.equal(clip.human_review, "pending", "automated playback does not substitute for human review");
    const mediaPaths = await video.evaluate((element) => ({
      poster: new URL(element.getAttribute("poster"), document.baseURI).pathname.replace(/^\/niri-plus\//, ""),
      source: new URL(element.querySelector("source")?.getAttribute("src"), document.baseURI).pathname.replace(/^\/niri-plus\//, ""),
      fallback: new URL(element.querySelector("a")?.getAttribute("href"), document.baseURI).pathname.replace(/^\/niri-plus\//, ""),
      download: new URL(element.closest("[data-native-demo]")?.querySelector(".native-demo-download")?.getAttribute("href"), document.baseURI).pathname.replace(/^\/niri-plus\//, ""),
    }));
    assert.equal(mediaPaths.poster, clip.poster);
    assert.equal(mediaPaths.source, clip.video);
    assert.equal(mediaPaths.fallback, clip.video);
    assert.equal(mediaPaths.download, clip.video);
    assert.ok(inventoriedAssets.has(mediaPaths.poster), `poster is outside explicit inventory: ${name}`);
    assert.ok(inventoriedAssets.has(mediaPaths.source), `video is outside explicit inventory: ${name}`);
    const [posterResponse, sourceResponse] = await Promise.all([
      page.request.head(origin + mediaPaths.poster),
      page.request.head(origin + mediaPaths.source),
    ]);
    assert.equal(posterResponse.status(), 200);
    assert.equal(posterResponse.headers()["content-type"], "image/png");
    assert.equal(sourceResponse.status(), 200);
    assert.equal(sourceResponse.headers()["content-type"], "video/mp4");
    assert.equal(await video.locator("source").getAttribute("type"), "video/mp4");
    assert.ok(await page.locator(`[data-native-demo="${name}"] .native-demo-steps li`).count() >= 3);
    await video.evaluate((element) => element.load());
    await page.waitForFunction((selector) => document.querySelector(selector)?.readyState >= 1, selector, { timeout: 15000 });
    const metadata = await video.evaluate((element) => ({ width: element.videoWidth, height: element.videoHeight, duration: element.duration, paused: element.paused }));
    assert.deepEqual([metadata.width, metadata.height], [clip.width, clip.height]);
    assert.ok(metadata.duration > 0 && Number.isFinite(metadata.duration));
    assert.ok(Math.abs(metadata.duration - clip.duration_seconds) < 0.1, `duration differs from measured provenance for ${name}`);
    assert.equal(metadata.paused, true, "native clips must wait for explicit playback");
    const poster = await page.evaluate((url) => new Promise((resolve) => {
      const image = new Image();
      image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
      image.onerror = () => resolve(null);
      image.src = url;
    }), await video.getAttribute("poster"));
    assert.deepEqual(poster, { width: clip.width, height: clip.height });
    await video.scrollIntoViewIfNeeded();
    await video.evaluate((element) => element.focus());
    assert.equal(await video.evaluate((element) => document.activeElement === element), true);
    await page.keyboard.press("Space");
    await page.waitForFunction((selector) => {
      const element = document.querySelector(selector);
      return element && !element.paused && element.currentTime > 0.1;
    }, selector, { timeout: 10000 });
    const beforeSeek = await video.evaluate((element) => element.currentTime);
    await video.evaluate((element) => { element.currentTime = Math.min(element.duration / 2, element.currentTime + 1); });
    await page.waitForFunction(({ selector, before }) => {
      const element = document.querySelector(selector);
      return element && !element.seeking && element.currentTime > before + 0.5;
    }, { selector, before: beforeSeek }, { timeout: 10000 });
    await page.keyboard.press("Space");
    await page.waitForFunction((selector) => document.querySelector(selector)?.paused, selector);
    checks += 13;
  }
  await page.setViewportSize({ width: 375, height: 900 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  for (const video of await page.locator(".native-demo-video").all()) {
    assert.ok((await video.boundingBox()).width <= 375);
    assert.equal(await video.evaluate((element) => element.paused), true);
  }
  assert.equal(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches), true);
  assert.equal(await page.locator(".native-demo-video").evaluateAll((nodes) => nodes.every((node) => getComputedStyle(node).animationDuration === "0s")), true);
  checks += 7;
  await page.setViewportSize({ width: 1280, height: 1000 });
  await page.goto(origin + "design/");
  const identity = await (await page.request.get(origin + "data/identity.json")).json();
  assert.equal(identity.selected_candidate, "neutral-slate");
  assert.equal(identity.direction.id, "neutral-slate");
  assert.equal(identity.direction.ui_font, "Noto Sans");
  assert.equal(identity.direction.mono_font, "MesloLGS Nerd Font");
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()), identity.direction.colors.canvas);
  assert.equal(await page.locator(".overview-stage").evaluate(node => getComputedStyle(node).backgroundColor), "rgb(0, 0, 0)");
  assert.equal(await page.locator("body").evaluate(node => getComputedStyle(node).backgroundColor), "rgb(17, 18, 19)");
  assert.equal(await page.locator(".overview-browser").evaluate(node => getComputedStyle(node).backgroundColor), "rgb(27, 29, 31)");
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
  assert.equal(await page.locator(".terminal-specimen").evaluate(node => getComputedStyle(node).backgroundColor), "rgb(0, 0, 0)");
  assert.equal(await page.locator("[aria-label='Selected terminal framing colors'] [role=listitem]").count(), 6);
  assert.equal(await page.locator(".ansi-reference-grid [role=listitem]").count(), 16);
  assert.ok(await page.evaluate(() => document.fonts.check('14px "Noto Sans"')));
  assert.ok(await page.evaluate(() => document.fonts.check('14px "MesloLGS Nerd Font"')));
  checks += 17;
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
  assert.equal(await page.locator("[data-terminal-card]:visible").count(), 4);
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()), identity.direction.colors.canvas);
  assert.deepEqual(await page.locator(".study-desktop").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).backgroundColor)), ["rgb(21, 23, 25)", "rgb(17, 18, 19)"]);
  const desktopText = await page.locator(".study-desktop").allInnerTexts();
  assert.equal(desktopText[0], desktopText[1]);
  const transcriptText = await page.locator(".study-transcript").allInnerTexts();
  assert.deepEqual(transcriptText, Array(4).fill(transcriptText[0]));
  const terminalBackgrounds = await page.locator(".study-terminal").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).backgroundColor));
  assert.deepEqual(terminalBackgrounds, Array(4).fill("rgb(0, 0, 0)"));
  assert.equal(await page.locator(".study-ansi [role=listitem]").count(), 64);
  assert.equal(await page.locator(".study-pairs [role=listitem]").count(), 28);
  assert.deepEqual(await page.locator('[data-terminal-card="black-balanced"] [data-pair-normal="1"], [data-terminal-card="black-balanced"] [data-pair-bright="9"]').evaluateAll(nodes => nodes.map(node => ({color: getComputedStyle(node).color, weight: getComputedStyle(node).fontWeight}))), [{color: "rgb(215, 124, 120)", weight: "400"}, {color: "rgb(242, 180, 173)", weight: "400"}]);
  assert.deepEqual(await page.locator(".t-rgb").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).color)), Array(4).fill("rgb(180, 168, 250)"));
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
  for (const view of ["black-balanced", "black-balanced-plus", "black-rich", "black-vivid", "middle", "all"]) {
    await page.locator(`[data-terminal-view="${view}"]`).click();
    assert.equal(await page.locator("[data-terminal-card]:visible").count(), view === "all" ? 4 : view === "middle" ? 2 : 1);
    if (view === "middle") assert.deepEqual(await page.locator("[data-terminal-card]:visible").evaluateAll(nodes => nodes.map(node => node.dataset.terminalCard)), ["black-balanced-plus", "black-rich"]);
    else if (view !== "all") assert.equal(await page.locator("[data-terminal-card]:visible").getAttribute("data-terminal-card"), view);
    checks += 2;
  }
  await page.locator('[data-terminal-size="larger"]').click();
  assert.deepEqual(await page.locator(".study-transcript").evaluateAll(nodes => nodes.map(node => getComputedStyle(node).fontSize)), Array(4).fill("16px"));
  assert.deepEqual(await page.locator("[data-pair-normal], [data-pair-bright]").evaluateAll(nodes => [...new Set(nodes.map(node => getComputedStyle(node).fontSize))]), ["16px"]);
  await page.locator('[data-terminal-size="standard"]').click();
  assert.ok(await page.locator(".study-transcript").first().evaluate(node => Math.abs(parseFloat(getComputedStyle(node).fontSize) - 14.6667) < .01));
  for (const details of await page.locator(".study-details").all()) {
    await details.locator("summary").click();
    assert.ok(await details.getAttribute("open") !== null);
    checks += 1;
  }
  checks += 14;
  // Native details keep page contents on the left, and give media more room when closed.
  for (const width of [375, 768, 1280, 1600]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(origin + "tour/");
    const contents = page.locator(".sidebar-contents");
    const summary = contents.locator("summary");
    assert.equal(await contents.evaluate((node) => node.open), width >= 1100);
    if (width >= 1100) {
      const expanded = (await page.locator(".prose").boundingBox()).width;
      await summary.focus();
      await page.keyboard.press("Enter");
      assert.equal(await contents.evaluate((node) => node.open), false);
      assert.ok((await page.locator(".prose").boundingBox()).width > expanded + 40);
      await page.keyboard.press("Enter");
      await page.keyboard.press("Escape");
      assert.equal(await contents.evaluate((node) => node.open), false);
      assert.equal(await summary.evaluate((node) => document.activeElement === node), true);
      const aside = await page.locator(".on-this-page").boundingBox();
      const main = await page.locator(".prose").boundingBox();
      assert.ok(aside.x + aside.width <= main.x);
    } else {
      await summary.click();
      assert.equal(await contents.evaluate((node) => node.open), true);
      await contents.locator('a[href="#explore-the-workflow"]').click();
      assert.equal(await contents.evaluate((node) => node.open), false);
    }
    const panelCapture = page.locator(".native-panel-shot");
    const panelImage = panelCapture.locator("img");
    await panelImage.scrollIntoViewIfNeeded();
    await panelImage.evaluate((node) => node.decode());
    assert.deepEqual(await panelImage.evaluate((node) => [node.naturalWidth, node.naturalHeight]), [1280, 800]);
    const imageBounds = await panelImage.boundingBox();
    const frameBounds = await panelCapture.locator(".native-panel-frame").boundingBox();
    assert.ok(Math.abs(imageBounds.width / imageBounds.height - 1280 / 800) < 0.01);
    assert.ok(Math.abs(imageBounds.x - frameBounds.x) < 2, "the full desktop must align with its frame");
    assert.ok(frameBounds.width >= (await page.locator(".prose").boundingBox()).width * 0.95);
    assert.ok((await panelCapture.locator("a").first().getAttribute("href")).endsWith("assets/workflow-panel.png"));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    checks += 12;
  }
  const workflow = provenance.desktop_walkthrough;
  assert.equal(workflow.type, "native captured frames");
  assert.equal(workflow.related_video, "assets/demo-desktop-800.mp4");
  for (const route of ["", "tour/"]) {
    for (const width of [375, 1280]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(origin + route);
      const workbench = page.locator("[data-workbench]");
      assert.equal(await workbench.locator(".desktop-stage, [data-scene-overlay]").count(), 0);
      for (const scene of workflow.scenes) {
        const button = workbench.locator(`[data-scene-button="${scene.id}"]`);
        await button.focus();
        await page.keyboard.press("Enter");
        assert.equal(await button.getAttribute("aria-pressed"), "true");
        assert.equal(await workbench.locator("[data-scene-panel]:visible").count(), 1);
        const panel = workbench.locator("[data-scene-panel]:visible");
        assert.equal(await panel.getAttribute("data-scene-panel"), scene.id);
        assert.equal(await workbench.locator('[data-scene-button][aria-pressed="true"]').count(), 1);
        const image = panel.locator("img");
        await panel.locator(".workflow-frame").scrollIntoViewIfNeeded();
        await image.evaluate((element) => element.decode());
        assert.deepEqual(await image.evaluate((element) => [element.naturalWidth, element.naturalHeight]), [1280, 800]);
        assert.ok((await image.getAttribute("src")).endsWith(scene.image));
        const fullScale = await image.evaluate((element) => element.getBoundingClientRect().width / element.closest(".workflow-frame").clientWidth);
        assert.ok(Math.abs(fullScale - 1) < 0.01, `scene should retain the full desktop: ${scene.id}`);
        const watch = new URL(await panel.locator('.scene-links a[href*=".mp4"]').getAttribute("href"), page.url());
        assert.ok(watch.pathname.endsWith(workflow.related_video));
        assert.equal(watch.hash, `#t=${scene.watch_from_seconds}`);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        if (process.env.NIRI_SCREENSHOTS) await workbench.screenshot({ path: path.join(process.env.NIRI_SCREENSHOTS, `workflow-${route ? "tour" : "home"}-${scene.id}-${width}.png`) });
        checks += 10;
      }
      assert.equal(await workbench.locator("[data-capture-toggle]").count(), 0);
      await workbench.locator('[data-scene-button="controls"]').focus();
      await page.keyboard.press("Home");
      checks += 1;
      assert.equal(await page.locator(":focus").getAttribute("data-scene-button"), "browser");
      await page.keyboard.press("ArrowRight");
      assert.equal(await page.locator(":focus").getAttribute("data-scene-button"), "terminal");
      await page.keyboard.press("End");
      assert.equal(await page.locator(":focus").getAttribute("data-scene-button"), "controls");
      await page.keyboard.press("ArrowRight");
      assert.equal(await page.locator(":focus").getAttribute("data-scene-button"), "browser");
      await page.keyboard.press("ArrowLeft");
      assert.equal(await page.locator(":focus").getAttribute("data-scene-button"), "controls");
      checks += 8;
    }
  }
  // Verify the browser honors a watch link's temporal fragment on the real MP4.
  const watchLink = page.locator('[data-scene-panel="controls"] .scene-links a[href*=".mp4"]').first();
  const watchTime = Number(new URL(await watchLink.getAttribute("href"), page.url()).hash.slice(3));
  await watchLink.click();
  await page.waitForFunction((time) => document.querySelector("video")?.currentTime >= time - 0.1, watchTime);
  assert.ok(await page.locator("video").evaluate((element, time) => element.currentTime < time + 5, watchTime));
  await page.locator("video").evaluate((element) => element.pause());
  checks += 2;
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
  for (const route of ["", "story/", "tour/", "tour/earlier/", "design/", "design/contrast/", "components/", "recipes/terminal/", "recipes/desktop-utilities/", "setup/", "setup/agent/", "reference/"]) {
    await staticPage.goto(origin + route);
    assert.ok((await staticPage.locator("main").innerText()).length > 400);
    const nativeContents = staticPage.locator(".sidebar-contents");
    if (await nativeContents.count()) {
      await nativeContents.locator("summary").click();
      assert.equal(await nativeContents.evaluate((node) => node.open), true);
      assert.ok(await nativeContents.locator("a").first().isVisible());
      checks += 2;
    }
    assert.equal(await staticPage.locator("[data-scene-controls]:visible").count(), 0);
    assert.equal(await staticPage.locator("[data-capture-controls]:visible").count(), 0);
    if (["", "tour/"].includes(route)) {
      assert.equal(await staticPage.locator("[data-scene-panel]:visible").count(), 4);
      assert.equal(await staticPage.locator("[data-scene-panel] .scene-links a:first-child").count(), 4);
      checks += 2;
    }
    assert.equal(await staticPage.locator("[data-surface-switcher]:visible").count(), 0);
    assert.ok(await staticPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    checks += 4;
  }
  await staticPage.goto(origin + "tour/");
  assert.equal(await staticPage.locator("[data-native-demo] video[controls]").count(), 2);
  assert.equal(await staticPage.locator("[data-native-demo] video[autoplay]").count(), 0);
  assert.ok((await staticPage.locator("[data-native-demo]").allInnerTexts()).join(" ").includes("Mod+Y"));
  assert.equal(await staticPage.locator("[data-native-demo] .native-demo-steps li").count(), 7);
  await staticPage.goto(origin + "tour/earlier/");
  assert.equal(await staticPage.locator("[data-native-demo] video[controls]").count(), 6);
  assert.equal(await staticPage.locator("[data-native-demo] video[autoplay]").count(), 0);
  assert.equal(await staticPage.locator("[data-native-demo] .native-demo-steps li").count(), 19);
  checks += 4;
  await staticPage.goto(origin + "design/");
  assert.equal(await staticPage.locator("[data-surface-panel]:visible").count(), 4);
  assert.equal(await staticPage.locator("[data-surface-button]:visible").count(), 0);
  assert.ok(await staticPage.locator("[data-surface-panel=terminal]").innerText());
  checks += 3;
  await staticPage.goto(origin + "design/contrast/");
  assert.equal(await staticPage.locator("[data-desktop-card]:visible").count(), 2);
  assert.equal(await staticPage.locator("[data-terminal-card]:visible").count(), 4);
  assert.equal(await staticPage.locator("[data-study-controls]:visible").count(), 0);
  assert.match(await staticPage.locator("main").innerText(), /proposal/i);
  checks += 4;
  await staticPage.goto(origin + "reference/");
  assert.equal(await staticPage.locator(".table-scroll tbody tr").first().count(), 1);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ checks, routes: routes.length, widths: [375, 768, 1280, 1600], javascript: "interactive + disabled", browser_errors: errors.length }));
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
