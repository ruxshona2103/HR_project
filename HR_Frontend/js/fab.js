import { navigate } from "./router.js";

export function initFab() {
  if (document.getElementById("fab-wrap")) return;
  const wrap = document.createElement("div");
  wrap.className = "fab-wrap";
  wrap.id = "fab-wrap";
  wrap.innerHTML = `
    <div class="fab-hint" id="fab-hint">AI yordamchingiz shu yerda 👋</div>
    <div class="fab-panel" id="fab-panel">
      <div class="fab-panel-head"><b>AI yordamchi</b><button class="modal-close" id="fab-close">&times;</button></div>
      <div class="fab-action" data-nav="/vacancies">🔎 Vakansiyalarni qidirish</div>
      <div class="fab-action" data-nav="/candidate/ai-check">🤖 Rezyumeni AI bilan tekshirish</div>
      <div class="fab-action" data-nav="/candidate/resume">📝 Rezyume tuzish</div>
      <div class="fab-action" data-nav="/vacancies">🎙 AI intervyu (vakansiya tanlang)</div>
    </div>
    <button class="fab-btn" id="fab-btn" title="AI yordamchi">✦</button>
  `;
  document.body.appendChild(wrap);
  const panel = wrap.querySelector("#fab-panel");
  const hint = wrap.querySelector("#fab-hint");

  wrap.querySelector("#fab-btn").addEventListener("click", () => {
    panel.classList.toggle("open");
    hint.style.display = panel.classList.contains("open") ? "none" : "";
  });
  wrap.querySelector("#fab-close").addEventListener("click", () => {
    panel.classList.remove("open");
    hint.style.display = "";
  });
  wrap.querySelectorAll("[data-nav]").forEach((el) =>
    el.addEventListener("click", () => {
      panel.classList.remove("open");
      navigate(el.getAttribute("data-nav"));
    })
  );

  // Bir necha soniyadan keyin taklif matnini yashiramiz — chalg'itmasin
  setTimeout(() => {
    if (!panel.classList.contains("open")) hint.style.display = "none";
  }, 6000);
}
