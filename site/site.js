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

document.querySelectorAll("[data-surface-gallery]").forEach((gallery) => {
  const controls = gallery.querySelector("[data-surface-switcher]");
  const buttons = [...controls.querySelectorAll("[data-surface-button]")];
  const panels = [...gallery.querySelectorAll("[data-surface-panel]")];
  const activate = (name) => {
    buttons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.surfaceButton === name)));
    panels.forEach((panel) => { panel.hidden = panel.dataset.surfacePanel !== name; });
  };
  controls.hidden = false;
  activate(buttons[0].dataset.surfaceButton);
  buttons.forEach((button, index) => {
    button.addEventListener("click", () => activate(button.dataset.surfaceButton));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next].focus();
      buttons[next].click();
    });
  });
});

document.querySelectorAll("[data-surface-panel=launch]").forEach((panel) => {
  const filter = panel.querySelector("[data-launch-filter]");
  const rows = [...panel.querySelectorAll("[data-launch-row]")];
  const status = panel.querySelector("[data-launch-message]");
  const setSelected = (row) => {
    rows.forEach((item) => {
      const selected = item === row;
      item.classList.toggle("is-selected", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
    status.textContent = `Sample selection: ${row.querySelector("strong").textContent}. No session is opened.`;
  };
  filter.addEventListener("input", () => {
    const query = filter.value.trim().toLocaleLowerCase();
    let matches = 0;
    rows.forEach((row) => {
      row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
      if (!row.hidden) matches += 1;
    });
    status.textContent = matches ? `${matches} sample ${matches === 1 ? "row" : "rows"} match. No sessions are discovered.` : "No sample rows match. Try another name.";
  });
  rows.forEach((row) => row.addEventListener("click", () => setSelected(row)));
  panel.querySelectorAll("[data-launch-action]").forEach((button) => button.addEventListener("click", () => {
    panel.querySelectorAll("[data-launch-action]").forEach((other) => other.setAttribute("aria-pressed", String(other === button)));
    const row = rows.find((item) => item.classList.contains("is-selected"));
    status.textContent = `Sample action: ${button.textContent} · ${row?.querySelector("strong").textContent || "no selected row"}. Nothing is opened.`;
  }));
  panel.querySelector(".launch-rows")?.addEventListener("keydown", (event) => {
    if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
    const visible = rows.filter((row) => !row.hidden);
    const current = visible.indexOf(event.target.closest("[data-launch-row]"));
    if (current < 0 || visible.length < 2) return;
    event.preventDefault();
    const next = (current + (event.key === "ArrowDown" ? 1 : -1) + visible.length) % visible.length;
    visible[next].focus();
    setSelected(visible[next]);
  });
});

document.querySelectorAll("[data-login-error-toggle]").forEach((button) => button.addEventListener("click", () => {
  const error = button.closest(".secure-specimen").querySelector("[data-login-error]");
  error.hidden = !error.hidden;
  button.setAttribute("aria-expanded", String(!error.hidden));
  button.textContent = error.hidden ? "Show sample error" : "Hide sample error";
}));
