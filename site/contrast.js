const study = document.querySelector("[data-contrast-study]");
if (study) {
  study.querySelectorAll("[data-study-controls]").forEach(node => { node.hidden = false; });
  function views(attribute, cards, grid) {
    const buttons = [...study.querySelectorAll(`[${attribute}]`)];
    buttons.forEach(button => button.addEventListener("click", () => {
      const selected = button.getAttribute(attribute);
      buttons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
      let visible = 0;
      study.querySelectorAll(`[${cards}]`).forEach(card => {
        card.hidden = selected !== "all" && card.getAttribute(cards) !== selected && card.dataset.viewGroup !== selected;
        if (!card.hidden) visible++;
      });
      study.querySelector(`[${grid}]`).classList.toggle("is-single", visible === 1);
    }));
  }
  views("data-desktop-view", "data-desktop-card", "data-desktop-grid");
  views("data-terminal-view", "data-terminal-card", "data-terminal-grid");
  const states = {
    success: ["Connected", "Wi-Fi is ready"],
    warning: ["Weak signal", "Connection may be slow"],
    error: ["Disconnected", "No network connection"],
  };
  const stateButtons = [...study.querySelectorAll("[data-study-state]")];
  stateButtons.forEach(button => button.addEventListener("click", () => {
    const state = button.dataset.studyState;
    stateButtons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    study.querySelectorAll(".study-desktop").forEach(card => {
      card.dataset.state = state;
      card.querySelector("[data-status-title]").textContent = states[state][0];
      card.querySelector("[data-status-description]").textContent = states[state][1];
    });
  }));
  const sizeButtons = [...study.querySelectorAll("[data-terminal-size]")];
  sizeButtons.forEach(button => button.addEventListener("click", () => {
    sizeButtons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    study.querySelector("[data-terminal-grid]").style.setProperty("--sample-size", button.dataset.terminalSize === "larger" ? "12pt" : "11pt");
  }));
}
