"use strict";

const scenes = {
  browser: {
    name: "Browser & files",
    description: "Chrome for interactive work. Dolphin and file dialogs for the natural next step.",
    key: "B",
  },
  terminal: {
    name: "Terminals & agents",
    description: "Build at the keyboard. Inspect configuration, ask an agent, and return to a dedicated TUI window.",
    key: "A",
  },
  panel: {
    name: "Information on demand",
    description: "Open the panel when you need it. Clipboard history is a separate picker on Mod+Y.",
    key: "N",
    title: "Notifications & system",
    rows: [["System", "CPU · RAM"], ["Network", "Workshop Wi-Fi"], ["Bluetooth", "Keyboard · Headphones"], ["Notifications", "Back to the right window"]],
    foot: "Illustration · sample values · reads while open",
  },
  remote: {
    name: "Work across hosts",
    description: "Find the machine and session where the work lives. SSH access and routes are configured explicitly.",
    key: "S",
    title: "SSH Plus / recent hosts",
    rows: [["workstation", "development"], ["buildbox", "builds"], ["lab", "experiments"]],
    foot: "↑ ↓ choose · Tab action · Enter open · Esc cancel",
  },
};

document.querySelectorAll("[data-workbench]").forEach((workbench) => {
  const controls = workbench.querySelector("[data-scene-controls]");
  const stage = workbench.querySelector(".desktop-stage");
  const overlay = workbench.querySelector("[data-scene-overlay]");
  controls.hidden = false;
  controls.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sceneButton;
      const scene = scenes[key];
      stage.dataset.scene = key;
      controls.querySelectorAll("button").forEach((other) => other.setAttribute("aria-pressed", String(other === button)));
      workbench.querySelector("[data-scene-name]").textContent = scene.name;
      workbench.querySelector("[data-scene-description]").textContent = scene.description;
      workbench.querySelector("[data-scene-key] kbd:last-child").textContent = scene.key;
      overlay.replaceChildren();
      overlay.hidden = !scene.rows;
      if (scene.rows) {
        const title = document.createElement("p");
        title.className = "overlay-title";
        title.textContent = scene.title;
        overlay.append(title);
        scene.rows.forEach(([label, value], index) => {
          const row = document.createElement("div");
          row.className = "overlay-row" + (key === "remote" && index === 0 ? " selected" : "");
          [label, value].forEach((text) => {
            const span = document.createElement("span");
            span.textContent = text;
            row.append(span);
          });
          overlay.append(row);
        });
        const foot = document.createElement("p");
        foot.className = "overlay-foot";
        foot.textContent = scene.foot;
        overlay.append(foot);
      }
    });
  });
});

const search = document.querySelector("[data-key-search]");
if (search) {
  const input = search.querySelector("input");
  const count = search.querySelector("[data-key-count]");
  const table = search.parentElement.querySelector(".key-search ~ .table-scroll");
  table.dataset.keyTable = "";
  const rows = [...table.querySelectorAll("tbody tr")];
  search.hidden = false;
  const filter = () => {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      row.hidden = !row.textContent.toLowerCase().includes(query);
      if (!row.hidden) visible += 1;
    });
    count.textContent = visible === 0 ? "No matching bindings. Try another task or key." : `${visible} of ${rows.length} bindings`;
  };
  input.addEventListener("input", filter);
  filter();
}
