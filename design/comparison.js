"use strict";
let currentScene = "launcher";
let currentType = "colors";
const sceneNames = {launcher: "Launcher & feedback", terminal: "Kitty + Zsh", files: "Files & forms", secure: "Login & lock"};
function context() {
  document.querySelector("[data-context]").textContent = `${sceneNames[currentScene]} · ${currentType === "colors" ? "Inter Variable across all three to isolate color differences." : "Original proposals: Graphite/Slate Blue use Inter; Neutral Slate uses Noto Sans."} All terminals use Meslo.`;
}
document.querySelector("[data-controls]").hidden = false;
document.querySelectorAll("[data-scene]").forEach(button => button.addEventListener("click", () => {
  currentScene = button.dataset.scene;
  document.querySelectorAll("[data-scene]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
  document.querySelectorAll("[data-surface]").forEach(scene => { scene.hidden = scene.dataset.surface !== currentScene; });
  context();
}));
document.querySelectorAll("[data-type]").forEach(button => button.addEventListener("click", () => {
  currentType = button.dataset.type;
  document.querySelectorAll("[data-type]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
  document.querySelectorAll(".mock-canvas").forEach(canvas => canvas.style.setProperty("--ui", `${currentType === "original" ? canvas.dataset.originalFont : "CompareInter"},CompareHan,sans-serif`));
  context();
}));
document.querySelector("[data-filter]").hidden = false;
function filter() {
  document.querySelectorAll('[data-shared="true"]').forEach(row => { row.hidden = document.getElementById("different-only").checked; });
}
document.getElementById("different-only").addEventListener("change", filter);
filter();
