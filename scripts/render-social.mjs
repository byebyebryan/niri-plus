import { readFileSync } from "node:fs";
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = JSON.parse(readFileSync(path.join(root, "design/identity.json"), "utf8"));
const identity = source.candidates.find((candidate) => candidate.id === source.selected_candidate);
if (!identity) throw new Error("Selected identity is missing from design/identity.json");

const font = (filename) => `data:font/woff2;base64,${readFileSync(path.join(root, "design/assets/fonts", filename)).toString("base64")}`;
const colors = identity.colors;
const uiFamily = JSON.stringify(identity.ui_font);
const monoFamily = JSON.stringify(identity.mono_font);
const uiRegular = font("noto.woff2");
const uiMedium = font("noto-medium.woff2");
const uiSemibold = font("noto-semibold.woff2");
const monoRegular = font("meslo.woff2");

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><html><head><style>
  @font-face{font-family:${uiFamily};src:url(${JSON.stringify(uiRegular)}) format('woff2');font-weight:400}
  @font-face{font-family:${uiFamily};src:url(${JSON.stringify(uiMedium)}) format('woff2');font-weight:500}
  @font-face{font-family:${uiFamily};src:url(${JSON.stringify(uiSemibold)}) format('woff2');font-weight:600}
  @font-face{font-family:${monoFamily};src:url(${JSON.stringify(monoRegular)}) format('woff2');font-weight:400}
  *{box-sizing:border-box}body{margin:0;background:${colors.canvas};color:${colors.text};font-family:${uiFamily},'Source Han Sans CN',sans-serif;padding:48px 64px;width:1200px;height:630px}
  header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid ${colors.border};padding-bottom:22px}.brand{font-size:32px;font-weight:600;letter-spacing:-2px}.brand b{color:${colors.accent};font-weight:500;margin-left:3px}header p{font:500 11px ${monoFamily},monospace;letter-spacing:1.5px;color:${colors.muted};margin:0}
  main{display:grid;grid-template-columns:0.88fr 1.12fr;gap:48px;align-items:center;padding-top:36px}h1{font-size:68px;line-height:1.04;letter-spacing:-3px;font-weight:500;margin:0}h1 span{color:${colors.focus}}p{font-size:16px;line-height:1.65;color:${colors.secondary};max-width:390px;margin-top:22px}
  .desktop{background:${colors.surface};border:1px solid ${colors.border};display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;height:292px}.window{min-width:0;padding:14px;border:1px solid ${colors.border}}.browser-window{background:${colors.raised};color:${colors.text}}.browser-top{display:flex;justify-content:space-between;color:${colors.secondary};font:10px ${monoFamily},monospace}.browser-window h2{font-size:25px;line-height:1.18;letter-spacing:-0.6px;font-weight:500;margin:42px 0 0}.land{height:48px;background:${colors.input};border-left:4px solid ${colors.accent};margin-top:20px}.browser-window p{font-size:12px;line-height:1.5;margin:15px 0 0;color:${colors.muted}}
  .terminal-window{background:${colors.input};border:4px solid ${colors.focus};color:${colors.text};padding:12px;font:11px/1.85 ${monoFamily},monospace}.terminal-path{color:${colors.secondary};margin-bottom:14px}.terminal-path span{color:${colors.accent};margin-left:8px}.prompt{color:${colors.focus}}.success{color:${colors.success}}.selection{display:inline-block;background:${colors.selection};color:${colors.selection_text};padding:0 4px;margin-top:12px}.url{font:10px ${monoFamily},monospace;color:${colors.muted};margin-top:16px}
  </style></head><body><header><span class="brand">niri<b>+</b></span><p>NEUTRAL SLATE · DAILY LINUX DESKTOP</p></header><main><div><h1>Two halves.<br>One daily<br><span>desktop.</span></h1><p>Chrome, terminals, coding agents, and the useful little things between them.</p></div><div><div class="desktop"><div class="window browser-window"><div class="browser-top"><span>CHROME</span><span>WEB</span></div><h2>Read something.<br>Make something.</h2><div class="land"></div><p>Focus stays clear; the work stays yours.</p></div><div class="window terminal-window"><div class="terminal-path">~/projects <span>main</span></div><div><span class="prompt">❯</span> niri validate</div><div><span class="success">✓</span> Configuration is valid.</div><br><div>Inspect. Explain. Review.</div><div class="selection">Selected text stays readable</div><div><span class="prompt">❯</span> ▌</div></div></div><div class="url">dev.byebyebryan.com/niri-plus</div></div></main></body></html>`);
  await page.evaluate(async () => document.fonts.ready);
  const fontStatus = await page.evaluate(() => ({
    ui: document.fonts.check('500 18px "Noto Sans"'),
    mono: document.fonts.check('400 12px "MesloLGS Nerd Font"'),
  }));
  if (!fontStatus.ui || !fontStatus.mono) throw new Error(`Selected fonts failed to load: ${JSON.stringify(fontStatus)}`);
  await page.screenshot({ path: path.join(root, "assets/social.png") });
} finally {
  await browser.close();
}
