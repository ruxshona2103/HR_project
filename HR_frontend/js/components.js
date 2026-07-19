export function toast(message, type = "success", timeout = 3800) {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), timeout);
}

export function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function openModal(innerHtml, { onMount } = {}) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `<div class="modal-box">${innerHtml}</div>`;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });
  document.body.appendChild(overlay);
  const box = overlay.querySelector(".modal-box");
  box.querySelectorAll("[data-close-modal]").forEach((b) =>
    b.addEventListener("click", () => overlay.remove())
  );
  if (onMount) onMount(overlay);
  return overlay;
}

export function closeModal(overlay) {
  overlay?.remove();
}

export function loadingBlock(label = "Yuklanmoqda...") {
  return `<div class="loading-line"><span class="spinner"></span> ${esc(label)}</div>`;
}

export function emptyState(title, desc) {
  return `<div class="state-box"><b>${esc(title)}</b>${esc(desc)}</div>`;
}

export function errorState(message, retryId) {
  return `<div class="state-box"><b>Nimadir xato ketdi</b>${esc(message)}
    ${retryId ? `<div style="margin-top:14px"><button class="btn btn-ghost btn-sm" id="${retryId}">Qayta urinish</button></div>` : ""}
  </div>`;
}

/**
 * Ishga.AI signature element: AI moslik/score gauge — yarim doira arc, foiz bilan to'ldiriladi.
 * score: 0-100
 */
export function matchGauge(score, label = "AI moslik darajasi", size = 168) {
  const s = Math.max(0, Math.min(100, Math.round(score ?? 0)));
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const startAngle = 180; // yarim doira: chapdan o'ngga
  const endAngle = 180 + (180 * s) / 100;
  const toXY = (deg) => {
    const rad = (deg * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const [x1, y1] = toXY(180);
  const [x2, y2] = toXY(360);
  const [mx, my] = toXY(endAngle);
  const largeArc = s > 50 ? 1 : 0;
  const color = s >= 70 ? "var(--primary)" : s >= 40 ? "var(--gold)" : "var(--danger)";

  return `
  <div class="gauge-wrap">
    <svg width="${size}" height="${size / 2 + 26}" viewBox="0 0 ${size} ${size / 2 + 26}">
      <path d="M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}" fill="none" stroke="var(--border)" stroke-width="14" stroke-linecap="round"/>
      <path d="M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${mx} ${my}" fill="none" stroke="${color}" stroke-width="14" stroke-linecap="round"/>
      <text x="${cx}" y="${cy - 2}" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="30" font-weight="600" fill="var(--text)">${s}%</text>
    </svg>
    <div class="gauge-label">${esc(label)}</div>
  </div>`;
}

export function chip(text, tone = "") {
  return `<span class="badge ${tone}">${esc(text)}</span>`;
}

export function fmtDate(d) {
  if (!d) return "-";
  try {
    return new Date(d).toLocaleDateString("uz-UZ", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return d;
  }
}

export function fmtMoney(v, currency) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return `${n.toLocaleString("uz-UZ")} ${currency || ""}`.trim();
}
