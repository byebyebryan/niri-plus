import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import {chromium} from "playwright";

const output=path.resolve(process.argv[2]);
const identity=JSON.parse(await fs.readFile(path.join(output,"data/identity.json"),"utf8"));
const candidates=identity.candidates.map(candidate=>candidate.id);
const mime={".html":"text/html",".css":"text/css",".js":"text/javascript",".json":"application/json",".png":"image/png",".svg":"image/svg+xml",".woff2":"font/woff2",".txt":"text/plain"};
const server=http.createServer(async(request,response)=>{
  try{
    let route=decodeURIComponent(new URL(request.url,"http://localhost").pathname);
    if(route.endsWith("/"))route+="index.html";
    const file=path.resolve(output,"."+route);
    if(!file.startsWith(output+path.sep))throw new Error("outside export");
    const data=await fs.readFile(file);response.writeHead(200,{"Content-Type":mime[path.extname(file)]||"application/octet-stream"});response.end(data);
  }catch{response.writeHead(404).end()}
});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
const origin=`http://127.0.0.1:${server.address().port}/`;
const browser=await chromium.launch({headless:true});
const errors=[];let checks=0;
const shot=async(page,name,locator)=>{
  if(!process.env.NIRI_DESIGN_SCREENSHOTS)return;
  await fs.mkdir(process.env.NIRI_DESIGN_SCREENSHOTS,{recursive:true});
  await(locator||page).screenshot({path:path.join(process.env.NIRI_DESIGN_SCREENSHOTS,name+".png"),...(locator?{}:{fullPage:true})});
};
try{
  const page=await browser.newPage({viewport:{width:1440,height:1050},reducedMotion:"reduce"});
  page.on("pageerror",error=>errors.push(error.message));
  page.on("response",response=>{if(response.status()>=400)errors.push(`${response.status()} ${response.url()}`)});
  await page.goto(origin);await page.evaluate(()=>document.fonts.ready);
  assert.equal(await page.locator(".candidate-card").count(),candidates.length);assert.equal(await page.locator(".capability").count(),22);checks+=2;
  for(const candidate of candidates){
    const button=page.locator(`[data-candidate-button="${candidate}"]`);await button.focus();await page.keyboard.press("Enter");
    assert.equal(await page.locator(".prototype-canvas").getAttribute("data-candidate"),candidate);
    assert.equal(await button.getAttribute("aria-pressed"),"true");
    assert.equal(await page.locator(".token").count(),19);checks+=3;
    for(const scene of ["daily","launch","secure","edges"]){
      await page.locator(`[data-scene="${scene}"]`).click();
      assert.equal(await page.locator("[data-surface]:visible").count(),1);
      assert.equal(await page.locator("[data-surface]:visible").getAttribute("data-surface"),scene);checks+=2;
      if(scene==="secure"){
        assert.equal(await page.locator("#greeter-password").getAttribute("readonly"),"");
        await page.getByRole("button",{name:"Log in",exact:true}).click();
        assert.equal(await page.locator("[data-secure-error]").isVisible(),true);checks+=2;
      }
      await shot(page,candidate+"-"+scene,page.locator(".specimen-viewport"));
    }
  }
  await page.locator('[data-scene="launch"]').click();
  for(const hardware of ["laptop","desktop","minimal"]){
    await page.locator("#hardware").selectOption(hardware);
    assert.equal(await page.locator(".battery-card").isVisible(),hardware==="laptop");
    assert.equal(await page.locator(".gpu-cells").isVisible(),hardware==="desktop");
    assert.equal(await page.locator(".bluetooth-card").isVisible(),hardware!=="minimal");checks+=3;
  }
  await page.locator("#sample-filter").fill("buildbox");assert.equal(await page.locator(".picker-row:visible").count(),1);
  await page.locator('[data-picker-action="new"]').click();assert.equal(await page.locator('[data-picker-action="new"]').getAttribute("aria-pressed"),"true");checks+=2;
  await page.locator('[data-picker-mode="apps"]').click();
  assert.equal(await page.locator(".picker-row:visible").count(),4);
  assert.equal(await page.locator(".picker-actions").isVisible(),false);
  await page.locator("#sample-filter").fill("bluetooth");assert.equal(await page.locator(".picker-row:visible").count(),1);
  await page.locator('[data-picker-mode="agent"]').click();assert.equal(await page.locator(".picker-actions").isVisible(),true);checks+=4;
  await page.locator("[data-feedback]").click();assert.equal(await page.locator("[data-feedback-card]").isVisible(),true);
  await page.locator("[data-feedback-card]").waitFor({state:"hidden",timeout:3000});checks+=2;
  await page.getByLabel("Find a task, component, or gap").fill("bluetooth");assert.ok(await page.locator(".capability:visible").count()>0);
  await page.getByLabel("Find a task, component, or gap").fill("a-no-such-task");assert.equal(await page.locator(".capability:visible").count(),0);
  await page.getByLabel("Find a task, component, or gap").fill("");assert.equal(await page.locator(".capability:visible").count(),22);checks+=3;
  await page.locator('[data-native-font="noto"]').click();assert.match(await page.locator('[data-native="qt"]').getAttribute("src"),/qt-noto.png/);checks++;
  await page.locator('[data-candidate-button="slate-blue"]').click();await page.locator('[data-scene="daily"]').click();
  for(const width of [375,768,1440]){
    await page.setViewportSize({width,height:1000});await page.waitForTimeout(80);
    for(const route of ["","brief.html","identity.html","implementation.html","verification.html","story.html","design.html","terminal.html"]){
      await page.goto(origin+route);await page.evaluate(()=>document.fonts.ready);
      assert.equal(await page.locator("h1").count(),1);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`overflow ${route} at ${width}`);checks+=2;
    }
  }
  await page.goto(origin);await page.keyboard.press("Tab");assert.equal(await page.locator(":focus").innerText(),"Skip to review");await page.keyboard.press("Enter");assert.equal(await page.locator(":focus").getAttribute("id"),"main");checks+=2;
  assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),"auto");checks++;
  await shot(page,"review-full-1440");
  const scaled=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1.5,reducedMotion:"reduce"});
  const scaledPage=await scaled.newPage();await scaledPage.goto(origin);await scaledPage.evaluate(()=>document.fonts.ready);assert.ok(await scaledPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await shot(scaledPage,"review-dpr-1_5",scaledPage.locator(".specimen-viewport"));checks++;
  const noJS=await browser.newContext({viewport:{width:375,height:900},javaScriptEnabled:false});const staticPage=await noJS.newPage();
  await staticPage.goto(origin);assert.equal(await staticPage.locator(".candidate-card").count(),candidates.length);assert.equal(await staticPage.locator(".capability").count(),22);assert.equal(await staticPage.locator("[data-controls]:visible").count(),0);assert.ok(await staticPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));checks+=4;
  await staticPage.locator(".capability").first().locator("summary").click();assert.equal(await staticPage.locator(".capability[open]").count(),1);checks++;
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({checks,candidates:candidates.length,scenes:4,capabilities:22,native_samples:4,widths:[375,768,1440],fractional_dpr:1.5,javascript:"enabled + disabled",errors:errors.length}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
