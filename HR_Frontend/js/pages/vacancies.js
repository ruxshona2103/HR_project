import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, chip, fmtMoney, fmtDate, emptyState, errorState, openModal } from "../components.js";
import { navigate } from "../router.js";
import { store } from "../store.js";

const EMPLOYMENT_LABELS = {
  FULL_TIME: "To'liq bandlik", PART_TIME: "Qisman bandlik", CONTRACT: "Shartnoma asosida",
  INTERNSHIP: "Amaliyot", FREELANCE: "Frilans",
};
const WORK_FORMAT_LABELS = { OFFICE: "Ofis", REMOTE: "Masofadan", HYBRID: "Gibrid", FIELD: "Har xil joyda" };
const EXPERIENCE_LABELS = {
  NO_EXPERIENCE: "Tajribasiz", UP_TO_1: "1 yilgacha", ONE_TO_THREE: "1-3 yil",
  THREE_TO_FIVE: "3-5 yil", FIVE_PLUS: "5+ yil",
};
const EDUCATION_LABELS = {
  NOT_REQUIRED: "Muhim emas", SECONDARY: "O'rta", SECONDARY_SPECIAL: "O'rta maxsus",
  BACHELOR: "Bakalavr", MASTER: "Magistr", PHD: "PhD",
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
      <div class="row-between wrap" style="margin-bottom:8px">
        <div class="section-head mb-0">
          <div class="eyebrow">Ochiq lavozimlar</div>
          <h2>Vakansiyalar</h2>
        </div>
        <div class="pill-tabs">
          <button class="pill-tab active">Mahalliy vakansiyalar</button>
          <button class="pill-tab" id="tab-foreign">Xorijiy vakansiyalar</button>
        </div>
      </div>
      <p style="margin-bottom:20px">Hozircha <b>${list.length}</b> ta ochiq vakansiya mavjud.</p>

      <div class="vac-layout">
        <aside class="filter-panel card">
          <h3 style="font-size:15px;margin-bottom:16px">Vakansiyalarni saralash</h3>

          <div class="field"><input id="f-search" placeholder="Lavozim, sohaviy yo'nalish, shahar..." /></div>

          <div class="filter-group">
            <label class="filter-label">Hudud</label>
            <select id="f-region"><option value="">Barcha viloyatlar</option></select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Ish joyi</label>
            ${Object.entries(WORK_FORMAT_LABELS)
              .map(
                ([val, lbl]) => `
              <div class="filter-check-row"><input type="checkbox" data-filter="work_format" value="${val}" id="wf-${val}"/><label for="wf-${val}">${esc(lbl)}</label></div>`
              )
              .join("")}
          </div>

          <div class="filter-group">
            <label class="filter-label">Tajriba</label>
            <select id="f-experience">
              <option value="">Barchasi</option>
              ${Object.entries(EXPERIENCE_LABELS).map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")}
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Ta'lim darajasi</label>
            <select id="f-education">
              <option value="">Barchasi</option>
              ${Object.entries(EDUCATION_LABELS).map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")}
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Bandlik turi</label>
            ${Object.entries(EMPLOYMENT_LABELS)
              .map(
                ([val, lbl]) => `
              <div class="filter-check-row"><input type="checkbox" data-filter="employment" value="${val}" id="et-${val}"/><label for="et-${val}">${esc(lbl)}</label></div>`
              )
              .join("")}
          </div>

          <button class="btn btn-ghost btn-sm btn-block" id="f-reset">Filtrni tozalash</button>
        </aside>

        <div>
          ${loadError ? errorState(loadError) : ""}
          <div class="grid grid-3" id="vac-grid">
            ${list.length ? list.map(vacancyCardHtml).join("") : ""}
          </div>
          ${!loadError && !list.length ? emptyState("Hozircha vakansiya yo'q", "Kompaniyalar tez orada yangi lavozimlar joylashadi.") : ""}
        </div>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      const grid = root.querySelector("#vac-grid");
      const search = root.querySelector("#f-search");
      const regionSelect = root.querySelector("#f-region");

      // Hudud select'ni mavjud vakansiyalar asosida to'ldiramiz
      const regions = [...new Set(list.map((v) => v.region).filter(Boolean))].sort();
      regionSelect.innerHTML += regions.map((r) => `<option value="${esc(r)}">${esc(r)}</option>`).join("");

      function applyFilters() {
        const q = search.value.trim().toLowerCase();
        const region = regionSelect.value;
        const exp = root.querySelector("#f-experience").value;
        const edu = root.querySelector("#f-education").value;
        const workFormats = [...root.querySelectorAll('[data-filter="work_format"]:checked')].map((c) => c.value);
        const employments = [...root.querySelectorAll('[data-filter="employment"]:checked')].map((c) => c.value);

        const filtered = list.filter((v) => {
          if (q && ![v.title, v.region, v.district, v.industry, v.specialization].filter(Boolean).some((f) => String(f).toLowerCase().includes(q))) return false;
          if (region && v.region !== region) return false;
          if (exp && v.experience_level !== exp) return false;
          if (edu && v.education_level !== edu) return false;
          if (workFormats.length && !(Array.isArray(v.work_formats) && workFormats.some((f) => v.work_formats.includes(f)))) return false;
          if (employments.length && !employments.includes(v.employment_type)) return false;
          return true;
        });

        grid.innerHTML = filtered.length ? filtered.map(vacancyCardHtml).join("") : emptyState("Hech narsa topilmadi", "Filtrlarni o'zgartirib ko'ring.");
        bindCards(grid, filtered);
      }

      root.querySelectorAll("#f-search, #f-region, #f-experience, #f-education").forEach((el) => el.addEventListener("input", applyFilters));
      root.querySelectorAll('[data-filter]').forEach((el) => el.addEventListener("change", applyFilters));
      root.querySelector("#f-reset").addEventListener("click", () => {
        search.value = "";
        root.querySelectorAll("select").forEach((s) => (s.value = ""));
        root.querySelectorAll('[data-filter]').forEach((c) => (c.checked = false));
        applyFilters();
      });
      root.querySelector("#tab-foreign")?.addEventListener("click", () => {
        const box = root.querySelector("#vac-grid");
        box.innerHTML = emptyState("Xorijiy vakansiyalar", "Hozircha bu bo'lim tayyorlanmoqda.");
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

export function vacancyCardHtml(v) {
  const salary =
    v.salary_from || v.salary_to
      ? `${fmtMoney(v.salary_from, v.currency) || ""}${v.salary_from && v.salary_to ? " – " : ""}${
          v.salary_to ? fmtMoney(v.salary_to, v.currency) : ""
        }`
      : "Kelishuv asosida";
  const formats = Array.isArray(v.work_formats) ? v.work_formats.map((f) => WORK_FORMAT_LABELS[f] || f) : [];
  const isNew = v.created_at ? (Date.now() - new Date(v.created_at).getTime()) / 86400000 < 14 : false;

  return `
    <div class="card card-hover vac-card-v2">
      <div class="vac-card-v2-top">
        ${isNew ? `<span class="vac-new-badge">Yangi</span>` : `<span></span>`}
        <span class="vac-save-btn" title="Saqlash">☆</span>
      </div>
      <h3>${esc(v.title || "Nomsiz vakansiya")}</h3>
      <div class="vac-tags-row">
        ${formats.map((f) => `<span class="vac-tag">${esc(f)}</span>`).join("")}
        ${v.employment_type ? `<span class="vac-tag">${esc(EMPLOYMENT_LABELS[v.employment_type] || v.employment_type)}</span>` : ""}
        ${v.experience_level ? `<span class="vac-tag">${esc(EXPERIENCE_LABELS[v.experience_level] || v.experience_level)}</span>` : ""}
      </div>
      <div class="vac-salary-v2">${esc(salary)}</div>
      <p class="vac-desc-v2">${esc((v.description || "Tavsif kiritilmagan.").slice(0, 130))}${(v.description || "").length > 130 ? "…" : ""}</p>
      <span class="vac-more-link" data-detail="${v.id}">Ko'proq</span>
      <div class="vac-company-v2">"${esc(v.company_name || v.industry || "Kompaniya")}"</div>
      ${v.region ? `<div class="vac-loc-v2">📍 ${esc(v.region)}${v.district ? ", " + esc(v.district) : ""}</div>` : ""}
      <div class="vac-stats-row">
        ${v.vacant_slots ? `<span>👥 ${esc(v.vacant_slots)} o'rin</span>` : ""}
        ${v.publish_start ? `<span>📅 ${fmtDate(v.publish_start)}${v.publish_end ? " – " + fmtDate(v.publish_end) : ""}</span>` : ""}
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
