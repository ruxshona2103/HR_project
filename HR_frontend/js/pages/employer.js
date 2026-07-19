import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, toast, chip, fmtMoney, emptyState, errorState, loadingBlock, openModal } from "../components.js";
import { renderFields, collectFormData } from "../formkit.js";
import { navigate } from "../router.js";

/* ============================================================
   OVERVIEW
   ============================================================ */
export async function renderEmployerHome() {
  let profile = null,
    err = null;
  try {
    profile = await http.get(EP.companyProfileMe);
  } catch (e) {
    err = e.message;
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">Kompaniya paneli</div>
        <h2>${esc(profile?.name || "Kompaniyangizga xush kelibsiz")}</h2>
        <p>Kompaniya profilini to'ldiring, vakansiyalar joylashtiring va AI intervyu savollarini sozlang.</p>
      </div>
      ${err ? errorState(err) : ""}
      <div class="grid grid-3">
        <div class="card"><span class="badge badge-primary">Jami</span><h3 style="margin-top:10px;font-size:32px">${profile?.vacancies_total ?? "-"}</h3><p>vakansiya</p></div>
        <div class="card"><span class="badge badge-gold">Ochiq</span><h3 style="margin-top:10px;font-size:32px">${profile?.vacancies_open ?? "-"}</h3><p>faol e'lon</p></div>
        <div class="card"><span class="badge">Yopiq</span><h3 style="margin-top:10px;font-size:32px">${profile?.vacancies_closed ?? "-"}</h3><p>yakunlangan</p></div>
      </div>
      <div class="grid grid-2" style="margin-top:24px">
        <div class="card card-hover">
          <h3>Kompaniya profili</h3>
          <p>Nom, sohaviy yo'nalish, manzil va veb-sayt ma'lumotlarini yangilang.</p>
          <button class="btn btn-primary btn-block" data-nav="/employer/profile">Profilni boshqarish</button>
        </div>
        <div class="card card-hover">
          <h3>Vakansiyalar</h3>
          <p>Yangi lavozim joylashtiring yoki mavjudlarini tahrirlang.</p>
          <button class="btn btn-primary btn-block" data-nav="/employer/vacancies">Vakansiyalarni boshqarish</button>
        </div>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      root.querySelectorAll("[data-nav]").forEach((el) => el.addEventListener("click", () => navigate(el.getAttribute("data-nav"))));
    },
  };
}

/* ============================================================
   COMPANY PROFILE
   ============================================================ */
const COMPANY_FIELDS = [
  { name: "name", label: "Kompaniya nomi", required: true },
  { name: "industry", label: "Sohaviy yo'nalish", placeholder: "IT, ishlab chiqarish, ..." },
  { name: "website", label: "Veb-sayt", type: "url" },
  { name: "location", label: "Manzil / hudud" },
  { name: "short_description", label: "Qisqacha tavsif", type: "textarea" },
];

export async function renderEmployerProfile() {
  let profile = {};
  try {
    profile = await http.get(EP.companyProfileMe);
  } catch (e) {
    return { html: `<div class="container section-tight">${errorState(e.message)}</div>` };
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head"><div class="eyebrow">Kompaniya</div><h2>Kompaniya profili</h2></div>
      <div class="card card-pad-lg" style="max-width:640px">
        <form id="company-form">
          ${renderFields(COMPANY_FIELDS, profile)}
          <button class="btn btn-primary" type="submit">Saqlash</button>
        </form>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      root.querySelector("#company-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = collectFormData(e.target, COMPANY_FIELDS);
        try {
          await http.patch(EP.companyProfileMe, data);
          toast("Kompaniya profili saqlandi.");
        } catch (err) {
          toast(err.message, "error");
        }
      });
    },
  };
}

/* ============================================================
   VACANCY MANAGEMENT
   ============================================================ */
const CH = {
  employment: [
    ["FULL_TIME", "To'liq bandlik"], ["PART_TIME", "Qisman bandlik"], ["CONTRACT", "Shartnoma asosida"],
    ["INTERNSHIP", "Amaliyot"], ["FREELANCE", "Frilans"],
  ],
  experience: [
    ["NO_EXPERIENCE", "Tajribasiz"], ["UP_TO_1", "1 yilgacha"], ["ONE_TO_THREE", "1-3 yil"],
    ["THREE_TO_FIVE", "3-5 yil"], ["FIVE_PLUS", "5+ yil"],
  ],
  education: [
    ["NOT_REQUIRED", "Muhim emas"], ["SECONDARY", "O'rta"], ["SECONDARY_SPECIAL", "O'rta maxsus"],
    ["BACHELOR", "Bakalavr"], ["MASTER", "Magistr"], ["PHD", "PhD"],
  ],
  schedule: [
    ["5_2", "5/2"], ["6_1", "6/1"], ["4_4", "4/4"], ["4_2", "4/2"], ["3_2", "3/2"], ["2_2", "2/2"], ["2_1", "2/1"],
    ["WEEKENDS", "Dam olish kunlarida"], ["FLEXIBLE", "Erkin"], ["OTHER", "Boshqa"],
  ],
  hours: [["2","2"],["4","4"],["6","6"],["8","8"],["10","10"],["12","12"],["24","24"],["BY_AGREEMENT","Kelishuv bo'yicha"],["OTHER","Boshqa"]],
  currency: [["UZS","UZS"],["USD","USD"],["EUR","EUR"],["RUB","RUB"]],
  type: [["system","System"],["national","National"],["international","International"]],
  status: [["OPEN","Ochiq"],["CLOSED","Yopiq"]],
  workFormat: [["OFFICE","Ofis"],["REMOTE","Masofadan"],["HYBRID","Gibrid"],["FIELD","Joylarga chiqish"]],
};
const opts = (arr) => arr.map(([value, label]) => ({ value, label }));

const VACANCY_FIELDS = [
  { name: "title", label: "Lavozim nomi", required: true },
  { name: "status", label: "Holati", type: "select", options: opts(CH.status) },
  { name: "industry", label: "Kasb sohasi" },
  { name: "specialization", label: "Kasb yo'nalishi" },
  { name: "vacant_slots", label: "Vakant o'rinlar soni", type: "number" },
  { name: "employment_type", label: "Bandlik turi", type: "select", options: opts(CH.employment) },
  { name: "experience_level", label: "Tajriba darajasi", type: "select", options: opts(CH.experience) },
  { name: "education_level", label: "Ta'lim darajasi", type: "select", options: opts(CH.education) },
  { name: "region", label: "Viloyat" },
  { name: "district", label: "Tuman / shahar" },
  { name: "work_schedule", label: "Ish jadvali", type: "select", options: opts(CH.schedule) },
  { name: "daily_hours", label: "Kunlik soat", type: "select", options: opts(CH.hours) },
  { name: "salary_from", label: "Maosh (dan)", type: "number" },
  { name: "salary_to", label: "Maosh (gacha)", type: "number" },
  { name: "currency", label: "Valyuta", type: "select", options: opts(CH.currency) },
  { name: "min_experience", label: "Minimal tajriba (yil)", type: "number" },
  { name: "type", label: "Vakansiya turi", type: "select", options: opts(CH.type) },
  { name: "publish_start", label: "E'lon boshlanish sanasi", type: "date" },
  { name: "publish_end", label: "E'lon tugash sanasi", type: "date" },
  { name: "company_address", label: "Kompaniya manzili", type: "textarea" },
  { name: "map_lat", label: "Xarita — Kenglik (latitude)", type: "number", step: "0.000001" },
  { name: "map_lng", label: "Xarita — Uzunlik (longitude)", type: "number", step: "0.000001" },
  { name: "required_skills", label: "Kerakli ko'nikmalar (vergul bilan)", type: "textarea" },
  { name: "description", label: "Vakansiya tavsifi", type: "textarea", required: true },
  { name: "ai_improved_description", label: "AI tomonidan takomillashtirilgan tavsif (ixtiyoriy)", type: "textarea", hint: "Agar to'ldirilsa, AI tavsifi sifatida saqlanadi." },
];

const WORK_FORMAT_OPTIONS = opts(CH.workFormat);

export async function renderEmployerVacancies() {
  let list = [];
  try {
    const res = await http.get(EP.companyVacancies);
    list = Array.isArray(res) ? res : res.results || [];
  } catch (e) {
    return { html: `<div class="container section-tight">${errorState(e.message)}</div>` };
  }

  const html = `
    <div class="container section-tight">
      <div class="row-between">
        <div class="section-head mb-0"><div class="eyebrow">Kompaniya</div><h2>Vakansiyalarim</h2></div>
        <button class="btn btn-primary" id="add-vacancy">+ Yangi vakansiya</button>
      </div>
      <div class="list" id="vac-list" style="margin-top:20px">
        ${list.length ? list.map(vacRow).join("") : emptyState("Hali vakansiya yo'q", "Birinchi lavozimingizni joylashtiring.")}
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      bindList(root, list);
      root.querySelector("#add-vacancy").addEventListener("click", () => openVacancyForm(null, () => reload(root)));
    },
  };

  function vacRow(v) {
    const salary = v.salary_from || v.salary_to ? `${fmtMoney(v.salary_from, v.currency) || ""} – ${fmtMoney(v.salary_to, v.currency) || ""}` : "kelishuv asosida";
    return `
    <div class="list-row">
      <div class="list-row-main">
        <b>${esc(v.title || "Nomsiz")} ${v.status === "CLOSED" ? chip("Yopiq", "badge-danger") : chip("Ochiq", "badge-primary")}</b>
        <span>${esc(v.region || "")} · ${esc(salary)}</span>
      </div>
      <div class="list-row-actions">
        <button class="btn btn-ghost btn-sm" data-edit="${v.id}">Tahrirlash</button>
        <button class="btn btn-danger btn-sm" data-del="${v.id}">O'chirish</button>
      </div>
    </div>`;
  }

  function bindList(root, items) {
    root.querySelectorAll("[data-edit]").forEach((b) =>
      b.addEventListener("click", () => openVacancyForm(items.find((i) => String(i.id) === b.dataset.edit), () => reload(root)))
    );
    root.querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", async () => {
        if (!confirm("Vakansiyani o'chirishni tasdiqlaysizmi?")) return;
        try {
          await http.del(`${EP.companyVacancies}${b.dataset.del}/`);
          toast("O'chirildi.");
          reload(root);
        } catch (err) {
          toast(err.message, "error");
        }
      })
    );
  }

  async function reload(root) {
    try {
      const res = await http.get(EP.companyVacancies);
      list = Array.isArray(res) ? res : res.results || [];
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    const box = root.querySelector("#vac-list");
    box.innerHTML = list.length ? list.map(vacRow).join("") : emptyState("Hali vakansiya yo'q", "Birinchi lavozimingizni joylashtiring.");
    bindList(root, list);
  }

  function openVacancyForm(existing, onDone) {
    const selectedFormats = new Set(existing?.work_formats || []);
    const overlay = openModal(
      `
      <div class="modal-head">
        <h3 class="mb-0">${existing ? "Vakansiyani tahrirlash" : "Yangi vakansiya"}</h3>
        <button class="modal-close" data-close-modal>&times;</button>
      </div>
      <form id="vacancy-form">
        <div class="field">
          <label>Ish turi (bir nechtasini tanlash mumkin)</label>
          <div class="chip-select" id="work-format-chips">
            ${WORK_FORMAT_OPTIONS.map(
              (o) => `<span class="chip-option ${selectedFormats.has(o.value) ? "selected" : ""}" data-value="${o.value}">${esc(o.label)}</span>`
            ).join("")}
          </div>
        </div>
        ${renderFields(VACANCY_FIELDS, existing || {})}
        <button class="btn btn-primary btn-block" type="submit">Saqlash</button>
      </form>
    `,
      {
        onMount(el) {
          const chipsBox = el.querySelector("#work-format-chips");
          chipsBox.querySelectorAll(".chip-option").forEach((chip) => {
            chip.addEventListener("click", () => {
              const v = chip.dataset.value;
              if (selectedFormats.has(v)) {
                selectedFormats.delete(v);
                chip.classList.remove("selected");
              } else {
                selectedFormats.add(v);
                chip.classList.add("selected");
              }
            });
          });
          el.querySelector("#vacancy-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const data = collectFormData(e.target, VACANCY_FIELDS);
            data.work_formats = Array.from(selectedFormats);
            try {
              if (existing) await http.patch(`${EP.companyVacancies}${existing.id}/`, data);
              else await http.post(EP.companyVacancies, data);
              toast("Vakansiya saqlandi.");
              overlay.remove();
              onDone();
            } catch (err) {
              toast(err.message, "error");
            }
          });
        },
      }
    );
  }
}

/* ============================================================
   AI INTERVIEW QUESTIONS
   ============================================================ */
const QUESTION_FIELDS = [
  { name: "text", label: "Savol matni", type: "textarea", required: true },
  {
    name: "question_type", label: "Turi", type: "select",
    options: [{ value: "technical", label: "Texnik" }, { value: "hr", label: "HR" }, { value: "behavioral", label: "Xulq-atvor" }],
  },
  {
    name: "difficulty", label: "Daraja", type: "select",
    options: [{ value: "junior", label: "Junior" }, { value: "middle", label: "Middle" }, { value: "senior", label: "Senior" }],
  },
  { name: "is_active", label: "Faol", type: "checkbox" },
];

export async function renderEmployerQuestions() {
  let items = [];
  try {
    items = await http.get(EP.aiQuestions);
  } catch (e) {
    return { html: `<div class="container section-tight">${errorState(e.message)}</div>` };
  }

  const html = `
    <div class="container section-tight">
      <div class="row-between">
        <div class="section-head mb-0"><div class="eyebrow">AI intervyu</div><h2>Savollar banki</h2></div>
        <button class="btn btn-primary" id="add-q">+ Savol qo'shish</button>
      </div>
      <p>Bu savollar nomzodlar bilan AI intervyu simulyatsiyasida ishlatiladi.</p>
      <div class="list" id="q-list" style="margin-top:16px">
        ${items.length ? items.map(qRow).join("") : emptyState("Savollar yo'q", "AI intervyu uchun birinchi savolni qo'shing.")}
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      bind(root, items);
      root.querySelector("#add-q").addEventListener("click", () => openForm(null, () => reload(root)));
    },
  };

  function qRow(q) {
    return `
    <div class="list-row">
      <div class="list-row-main">
        <b>${esc((q.text || "").slice(0, 90))}${(q.text || "").length > 90 ? "…" : ""}</b>
        <span>${esc(q.question_type)} · ${esc(q.difficulty)} ${q.is_active ? "" : "· nofaol"}</span>
      </div>
      <div class="list-row-actions">
        <button class="btn btn-ghost btn-sm" data-edit="${q.id}">Tahrirlash</button>
        <button class="btn btn-danger btn-sm" data-del="${q.id}">O'chirish</button>
      </div>
    </div>`;
  }

  function bind(root, list) {
    root.querySelectorAll("[data-edit]").forEach((b) =>
      b.addEventListener("click", () => openForm(list.find((i) => String(i.id) === b.dataset.edit), () => reload(root)))
    );
    root.querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", async () => {
        if (!confirm("Savolni o'chirishni tasdiqlaysizmi?")) return;
        try {
          await http.del(`${EP.aiQuestions}${b.dataset.del}/`);
          toast("O'chirildi.");
          reload(root);
        } catch (err) {
          toast(err.message, "error");
        }
      })
    );
  }

  async function reload(root) {
    try {
      items = await http.get(EP.aiQuestions);
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    const box = root.querySelector("#q-list");
    box.innerHTML = items.length ? items.map(qRow).join("") : emptyState("Savollar yo'q", "AI intervyu uchun birinchi savolni qo'shing.");
    bind(root, items);
  }

  function openForm(existing, onDone) {
    const overlay = openModal(
      `
      <div class="modal-head">
        <h3 class="mb-0">${existing ? "Savolni tahrirlash" : "Yangi savol"}</h3>
        <button class="modal-close" data-close-modal>&times;</button>
      </div>
      <form id="q-form">
        ${renderFields(QUESTION_FIELDS, existing || { is_active: true })}
        <button class="btn btn-primary btn-block" type="submit">Saqlash</button>
      </form>
    `,
      {
        onMount(el) {
          el.querySelector("#q-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const data = collectFormData(e.target, QUESTION_FIELDS);
            try {
              if (existing) await http.patch(`${EP.aiQuestions}${existing.id}/`, data);
              else await http.post(EP.aiQuestions, data);
              toast("Saqlandi.");
              overlay.remove();
              onDone();
            } catch (err) {
              toast(err.message, "error");
            }
          });
        },
      }
    );
  }
}
