import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><html><head><style>
  *{box-sizing:border-box}body{margin:0;background:#101315;color:#eeeae3;font-family:system-ui,sans-serif;padding:60px 72px;width:1200px;height:630px}
  header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #34393c;padding-bottom:28px}.brand{font-size:36px;font-weight:650;letter-spacing:-3px}.brand b{color:#a4c9ff;font-weight:400;margin-left:4px}header p{font:12px monospace;letter-spacing:2px;color:#a8acae}
  main{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center;padding-top:40px}h1{font-size:78px;line-height:1.02;letter-spacing:-5px;font-weight:550;margin:0}h1 span{color:#a4c9ff}p{font-size:17px;line-height:1.8;color:#a8acae;max-width:440px}.desktop{background:#07090a;border:1px solid #465462;border-radius:9px;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:18px;height:290px}.window{border:1px solid #8baaca;border-radius:4px;background:#ece8de;padding:15px;color:#313c3f}.window small{font:9px monospace}.window h2{font-family:Georgia,serif;font-weight:400;font-size:28px;margin-top:40px;line-height:1.05}.window:last-child{background:#1a2026;color:#b9d8aa;font:10px/2 monospace;padding-top:45px}.land{height:55px;background:#788f88;margin-top:20px}.url{font:11px monospace;color:#8f989d;margin-top:25px}
  </style></head><body><header><span class="brand">niri<b>+</b></span><p>BRYAN'S DAILY LINUX DESKTOP</p></header><main><div><h1>Two halves.<br>One daily<br><span>desktop.</span></h1><p>Chrome, terminals, coding agents,<br>and the useful little things between them.</p></div><div><div class="desktop"><div class="window"><small>CHROME</small><h2>Read something.<br>Make something.</h2><div class="land"></div></div><div class="window">~/projects<br><br>❯ niri validate<br>✓ Configuration is valid.<br><br>Inspect. Explain. Review.<br><br>❯ ▌</div></div><div class="url">dev.byebyebryan.com/niri-plus</div></div></main></body></html>`);
  await page.screenshot({ path: path.join(root, "assets/social.png") });
} finally {
  await browser.close();
}
