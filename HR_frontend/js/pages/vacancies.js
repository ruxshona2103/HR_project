import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, chip, fmtMoney, fmtDate, emptyState, errorState, openModal } from "../components.js";
import { navigate } from "../router.js";
import { store } from "../store.js";

const EMPLOYMENT_LABELS = {
  FULL_TIME: "To'liq bandlik", PART_TIME: "Qisman bandlik", CONTRACT: "Shartnoma",
  INTERNSHIP: "Amaliyot", FREELANCE: "Frilans",
};
const WORK_FORMAT_LABELS = { OFFICE: "Ofis", REMOTE: "Masofadan", HYBRID: "Gibrid", FIELD: "Joylarda" };
const EXPERIENCE_LABELS = {
  NO_EXPERIENCE: "Tajribasiz", UP_TO_1: "1 yilgacha", ONE_TO_THREE: "1-3 yil",
  THREE_TO_FIVE: "3-5 yil", FIVE_PLUS: "5+ yil",
};

export async function renderVacancies() {
  let list = [];
  let loadError = null;
  try {
    const res = await http.get(EP.vacancies, { auth: true });
    list = Array.isArray(res) ? res : res.results || [];
  } catch (e) {
    loadError = e.message;
  }
  list = list.filter((v) => !v.status || v.status === "OPEN");

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">Ochiq lavozimlar</div>
        <h2>Vakansiyalar</h2>
        <p>Hozircha ${list.length} ta ochiq vakansiya mavjud. Sarlavha yoki hudud bo'yicha qidiring.</p>
      </div>
      <div class="row wrap" style="margin-bottom:22px">
        <input id="vac-search" placeholder="Lavozim, sohaviy yo'nalish yoki shahar bo'yicha qidirish..." style="max-width:420px" />
      </div>
      ${loadError ? errorState(loadError) : ""}
      <div class="grid grid-3" id="vac-grid">
        ${list.length ? list.map(vacancyCardHtml).join("") : ""}
      </div>
      ${!loadError && !list.length ? emptyState("Hozircha vakansiya yo'q", "Kompaniyalar tez orada yangi lavozimlar joylashadi.") : ""}
    </div>`;

  return {
    html,
    mount(root) {
      const search = root.querySelector("#vac-search");
      const grid = root.querySelector("#vac-grid");
      search?.addEventListener("input", () => {
        const q = search.value.trim().toLowerCase();
        const filtered = list.filter((v) =>
          [v.title, v.region, v.district, v.industry, v.specialization]
            .filter(Boolean)
            .some((f) => String(f).toLowerCase().includes(q))
        );
        grid.innerHTML = filtered.length
          ? filtered.map(vacancyCardHtml).join("")
          : emptyState("Hech narsa topilmadi", "Boshqa kalit so'z bilan qidirib ko'ring.");
        bindCards(grid, filtered);
      });
      bindCards(grid, list);
    },
  };
}

function bindCards(grid, list) {
  grid.querySelectorAll("[data-detail]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = list.find((x) => String(x.id) === btn.dataset.detail);
      if (v) showVacancyDetail(v);
    });
  });
}

function vacancyCardHtml(v) {
  const salary =
    v.salary_from || v.salary_to
      ? `${fmtMoney(v.salary_from, v.currency) || ""}${v.salary_from && v.salary_to ? " – " : ""}${
          v.salary_to ? fmtMoney(v.salary_to, v.currency) : ""
        }`
      : null;
  return `
    <div class="card card-hover vacancy-card">
      <div class="vacancy-top">
        <h3 class="vacancy-title">${esc(v.title || "Nomsiz vakansiya")}</h3>
        ${salary ? chip(salary, "badge-gold") : ""}
      </div>
      <div class="vacancy-meta">
        ${v.region ? `<span>📍 ${esc(v.region)}${v.district ? ", " + esc(v.district) : ""}</span>` : ""}
        ${v.employment_type ? `<span>🕒 ${esc(EMPLOYMENT_LABELS[v.employment_type] || v.employment_type)}</span>` : ""}
        ${v.experience_level ? `<span>📈 ${esc(EXPERIENCE_LABELS[v.experience_level] || v.experience_level)}</span>` : ""}
      </div>
      <p class="vacancy-desc">${esc((v.description || "Tavsif kiritilmagan.").slice(0, 160))}${(v.description || "").length > 160 ? "…" : ""}</p>
      <div class="vacancy-actions">
        <button class="btn btn-primary btn-sm" data-detail="${v.id}">Batafsil</button>
      </div>
    </div>`;
}

function showVacancyDetail(v) {
  const formats = Array.isArray(v.work_formats) ? v.work_formats.map((f) => WORK_FORMAT_LABELS[f] || f).join(", ") : "";
  const overlay = openModal(`
    <div class="modal-head">
      <h3 class="mb-0">${esc(v.title || "Vakansiya")}</h3>
      <button class="modal-close" data-close-modal>&times;</button>
    </div>
    <div class="stack">
      <div class="row wrap">
        ${v.region ? chip("📍 " + v.region + (v.district ? ", " + v.district : "")) : ""}
        ${v.employment_type ? chip(EMPLOYMENT_LABELS[v.employment_type] || v.employment_type) : ""}
        ${v.experience_level ? chip(EXPERIENCE_LABELS[v.experience_level] || v.experience_level) : ""}
        ${formats ? chip(formats) : ""}
      </div>
      <p>${esc(v.description || "Tavsif kiritilmagan.")}</p>
      ${v.required_skills ? `<div><b>Kerakli ko'nikmalar:</b><p>${esc(v.required_skills)}</p></div>` : ""}
      <div class="divider"></div>
      <div class="row wrap" style="gap:10px">
        <button class="btn btn-primary" id="go-ai-check">🤖 AI rezyume tekshiruvi</button>
        <button class="btn btn-gold" id="go-ai-interview">🎙 AI intervyuni boshlash</button>
      </div>
    </div>
  `, {
    onMount(el) {
      el.querySelector("#go-ai-check").addEventListener("click", () => {
        if (!store.isAuthed()) return navigate("/login");
        overlay.remove();
        navigate(`/candidate/ai-check?vacancy_id=${v.id}`);
      });
      el.querySelector("#go-ai-interview").addEventListener("click", () => {
        if (!store.isAuthed()) return navigate("/login");
        overlay.remove();
        navigate(`/candidate/interview/${v.id}`);
      });
    },
  });
}
