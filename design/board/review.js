"use strict";
const data=JSON.parse(document.getElementById("review-data").textContent);
const canvas=document.querySelector(".prototype-canvas");
const frame=document.querySelector(".scaled-frame");
const viewport=document.querySelector(".specimen-viewport");
const controls=document.querySelector("[data-controls]");
let sizing="fit";
let feedbackTimer;
const fontNames={"inter.woff2":"ReviewInter","noto.woff2":"ReviewNoto","meslo.woff2":"ReviewMeslo","jetbrains.woff2":"ReviewJetBrains"};
const announce=(message)=>{document.querySelector("[data-sample-feedback]").textContent=message};
function fit(){
  const padding=parseFloat(getComputedStyle(viewport).paddingLeft)*2;
  const scale=sizing==="native"?1:Math.min(1,Math.max(.15,(viewport.clientWidth-padding-2)/1280));
  frame.style.width=`${1280*scale}px`;
  frame.style.height=`${760*scale}px`;
  canvas.style.transform=`scale(${scale})`;
}
function nativeFont(font){
  document.querySelectorAll("[data-native-font]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.nativeFont===font)));
  document.querySelectorAll("[data-native]").forEach(image=>{
    image.src=`assets/native/${image.dataset.native}-${font}.png`;
    image.alt=`Actual ${image.dataset.native.toUpperCase()} reference widgets in the original dark theme with ${font==="inter"?"Inter Variable":"Noto Sans"} 11 point and mixed Latin and Chinese sample text`;
  });
}
function candidate(id){
  const candidate=data.identity.candidates.find(candidate=>candidate.id===id);
  canvas.dataset.candidate=id;
  for(const [key,value] of Object.entries(candidate.colors))canvas.style.setProperty(`--${key.replaceAll("_","-")}`,value);
  canvas.style.setProperty("--ui",`${fontNames[candidate.ui_asset]},ReviewHan,sans-serif`);
  canvas.style.setProperty("--mono",`${fontNames[candidate.mono_asset]},ReviewHan,monospace`);
  document.querySelectorAll("[data-candidate-button]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.candidateButton===id)));
  document.querySelector("[data-candidate-name]").textContent=candidate.name+(id===data.identity.selected_candidate?" · selected identity":" · design history");
  document.querySelector("[data-candidate-summary]").textContent=candidate.summary;
  document.querySelector("[data-font-readout]").textContent=`${candidate.ui_font} 11pt / ${candidate.mono_font} 11pt`;
  document.querySelector("[data-tradeoff]").textContent=candidate.tradeoff;
  const grid=document.querySelector("[data-token-grid]");grid.replaceChildren();
  for(const [role,value] of Object.entries(candidate.colors)){
    const token=document.createElement("div");token.className="token";
    const swatch=document.createElement("div");swatch.className="token-swatch";swatch.style.background=value;swatch.setAttribute("aria-hidden","true");
    const name=document.createElement("strong");name.textContent=role;
    const hex=document.createElement("code");hex.textContent=value;
    token.append(swatch,name,hex);grid.append(token);
  }
  nativeFont(candidate.ui_asset==="noto.woff2"?"noto":"inter");
  announce(`Inspecting ${candidate.name}. This changes the specimen only; no preference is saved or applied.`);
}
function scene(name){
  document.getElementById("hardware").disabled=name!=="launch";
  document.querySelectorAll("[data-surface]").forEach(surface=>surface.hidden=surface.dataset.surface!==name);
  document.querySelectorAll("[data-scene]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.scene===name)));
  clearTimeout(feedbackTimer);document.querySelector("[data-feedback-card]").hidden=true;
  announce(`Showing ${name==="daily"?"daily work":name==="launch"?"launchers and information":name==="secure"?"login and locking":"edge states"}. All content is a design mockup.`);
}
function hardware(value){
  canvas.querySelectorAll(".gpu-cells").forEach(element=>element.hidden=value!=="desktop");
  canvas.querySelectorAll(".battery-card").forEach(element=>element.hidden=value!=="laptop");
  canvas.querySelectorAll(".bluetooth-card").forEach(element=>element.hidden=value==="minimal");
  const kind=canvas.querySelector(".network-kind");
  const label=canvas.querySelector(".network-label");
  kind.textContent=value==="laptop"?"WIFI":value==="desktop"?"ETH":"NET";
  label.textContent=value==="laptop"?"Workshop Wi-Fi":value==="desktop"?"198.51.100.24":"Disconnected";
  label.title=label.textContent;
  canvas.querySelector(".network-signal").hidden=value!=="laptop";
}
controls.hidden=false;
document.querySelectorAll("[data-candidate-button]").forEach(button=>button.addEventListener("click",()=>candidate(button.dataset.candidateButton)));
document.querySelectorAll("[data-scene]").forEach(button=>button.addEventListener("click",()=>scene(button.dataset.scene)));
document.querySelectorAll("[data-size]").forEach(button=>button.addEventListener("click",()=>{
  sizing=button.dataset.size;
  document.querySelectorAll("[data-size]").forEach(other=>other.setAttribute("aria-pressed",String(other===button)));
  fit();
  announce(sizing==="native"?"100% logical preview. Scroll the specimen to inspect its full canvas.":"Fit preview. Use 100% logical to assess text size.");
}));
document.getElementById("hardware").addEventListener("change",event=>{hardware(event.target.value);announce("Panel hardware fixture changed. No hardware is queried.")});
document.querySelector("[data-feedback]").addEventListener("click",()=>{
  clearTimeout(feedbackTimer);document.querySelector("[data-feedback-card]").hidden=false;
  announce("Sample volume feedback is shown for 1.5 seconds. No volume is changed.");
  feedbackTimer=setTimeout(()=>{document.querySelector("[data-feedback-card]").hidden=true},data.identity.shared.feedback_duration_ms);
});
document.querySelectorAll("[data-sample]").forEach(button=>button.addEventListener("click",()=>{
  announce(button.dataset.sample);
  if(button.closest(".scene-secure")&&button.textContent==="Log in")document.querySelector("[data-secure-error]").hidden=false;
}));
document.querySelectorAll("[data-picker-action]").forEach(button=>button.addEventListener("click",()=>{
  document.querySelectorAll("[data-picker-action]").forEach(other=>{other.classList.toggle("active",other===button);other.setAttribute("aria-pressed",String(other===button))});
  announce(`Sample named action: ${button.textContent}. The native picker owns its real action-cycle keys.`);
}));
document.getElementById("sample-filter").addEventListener("input",event=>{
  const query=event.target.value.trim().toLowerCase();let matches=0;
  document.querySelectorAll(".picker-rows:not([hidden]) .picker-row").forEach(row=>{row.hidden=!row.textContent.toLowerCase().includes(query);if(!row.hidden)matches++});
  announce(`${matches} sample picker rows match. No sessions are discovered.`);
});
document.querySelectorAll("[data-picker-mode]").forEach(button=>button.addEventListener("click",()=>{
  const apps=button.dataset.pickerMode==="apps";
  document.querySelectorAll("[data-picker-mode]").forEach(other=>other.setAttribute("aria-pressed",String(other===button)));
  document.querySelectorAll("[data-picker-kind]").forEach(rows=>{rows.hidden=rows.dataset.pickerKind!==button.dataset.pickerMode;rows.querySelectorAll(".picker-row").forEach(row=>row.hidden=false)});
  document.querySelector(".picker-actions").hidden=apps;
  document.querySelector("[data-picker-title]").textContent=apps?"Applications":"Agent Plus";
  document.querySelector("[data-picker-context]").textContent=apps?"Proposed utility entries":"local / remote";
  document.getElementById("sample-filter").value="";
  document.getElementById("sample-filter").placeholder=apps?"Find an application or utility":"Filter windows";
  document.querySelector(".picker-footer").textContent=apps?"Mod+D · type task/name · Enter opens · Escape / Ctrl+G cancel":"↑ ↓ rows · Alt+R refresh · Escape / Ctrl+G cancel";
  announce(apps?"The four utility entries are proposed additions to the existing Rofi application launcher.":"Agent Plus specimen, using fictional native windows.");
}));
document.querySelector("[data-native-controls]").hidden=false;
document.querySelectorAll("[data-native-font]").forEach(button=>button.addEventListener("click",()=>nativeFont(button.dataset.nativeFont)));
document.querySelector("[data-capability-filter]").hidden=false;
document.getElementById("capability-search").addEventListener("input",event=>{
  const query=event.target.value.trim().toLowerCase();let count=0;
  document.querySelectorAll(".capability").forEach(card=>{card.hidden=!card.textContent.toLowerCase().includes(query);if(!card.hidden)count++});
  document.querySelector("[data-capability-count]").textContent=count?`${count} of 22 capabilities`:"No matching capabilities. Try a task or component name.";
});
new ResizeObserver(fit).observe(viewport);
hardware("laptop");candidate(data.identity.selected_candidate);fit();
