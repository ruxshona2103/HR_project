import { http, ApiError } from "../api.js";
import { EP } from "../config.js";
import { esc, toast, matchGauge, emptyState, errorState, loadingBlock, openModal } from "../components.js";
import { renderFields, collectFormData } from "../formkit.js";
import { store } from "../store.js";
import { navigate } from "../router.js";

/* ============================================================
   OVERVIEW
   ============================================================ */
export async function renderCandidateHome() {
  let me = null,
    err = null;
  try {
    me = await http.get(EP.me);
  } catch (e) {
    err = e.message;
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">Boshqaruv paneli</div>
        <h2>Xush kelibsiz, ${esc(me?.first_name || "nomzod")}!</h2>
        <p>Rezyumeni to'ldiring, vakansiyalarni ko'rib chiqing va AI yordamida o'zingizni sinab ko'ring.</p>
      </div>
      ${err ? errorState(err) : ""}
      <div class="grid grid-3">
        <div class="card card-hover">
          <span class="badge badge-primary">1-qadam</span>
          <h3 style="margin-top:12px">Rezyumeni to'ldiring</h3>
          <p>Ko'nikma, tajriba, ta'lim va boshqa bo'limlarni to'ldiring.</p>
          <button class="btn btn-primary btn-block" data-nav="/candidate/resume">Rezyumega o'tish</button>
        </div>
        <div class="card card-hover">
          <span class="badge badge-gold">2-qadam</span>
          <h3 style="margin-top:12px">Vakansiyalarni ko'ring</h3>
          <p>Ochiq lavozimlarni ko'rib, sizga mos bo'lganlarini toping.</p>
          <button class="btn btn-ghost btn-block" data-nav="/vacancies">Vakansiyalar</button>
        </div>
        <div class="card card-hover">
          <span class="badge">3-qadam</span>
          <h3 style="margin-top:12px">AI bilan tekshiring</h3>
          <p>Rezyumeni vakansiyaga solishtiring va AI intervyusidan o'ting.</p>
          <button class="btn btn-ghost btn-block" data-nav="/candidate/ai-check">AI tekshiruv</button>
        </div>
      </div>
      <div class="card card-pad-lg" style="margin-top:24px">
        <h3>Profil ma'lumotlari</h3>
        <div class="kv"><span>Ism familiya</span><b>${esc([me?.first_name, me?.last_name].filter(Boolean).join(" ") || "-")}</b></div>
        <div class="kv"><span>Email</span><b>${esc(me?.email || "-")}</b></div>
        <div class="kv"><span>Telefon</span><b>${esc(me?.phone_number || "-")}</b></div>
        <div class="kv"><span>Foydalanuvchi turi</span><b>${me?.user_type === "candidate" ? "Nomzod" : esc(me?.user_type || "-")}</b></div>
        <div style="margin-top:14px"><button class="btn btn-ghost btn-sm" data-nav="/settings">Profilni tahrirlash →</button></div>
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
   RESUME BUILDER
   ============================================================ */
const SECTION_CONFIG = {
  konikmalar: {
    label: "Ko'nikmalar",
    fields: [
      { name: "nom", label: "Ko'nikma nomi", required: true, placeholder: "Python" },
      { name: "daraja", label: "Daraja", placeholder: "yuqori / o'rta / boshlang'ich" },
      { name: "kategoriya", label: "Kategoriya", placeholder: "Dasturlash tillari" },
    ],
    title: (i) => i.nom,
    sub: (i) => [i.kategoriya, i.daraja].filter(Boolean).join(" · "),
  },
  tillar: {
    label: "Tillar",
    fields: [
      { name: "til_nomi", label: "Til nomi", required: true, placeholder: "Ingliz tili" },
      { name: "daraja", label: "Daraja", placeholder: "B2" },
    ],
    title: (i) => i.til_nomi,
    sub: (i) => i.daraja,
  },
  "ish-tajribasi": {
    label: "Ish tajribasi",
    fields: [
      { name: "kompaniya_nomi", label: "Kompaniya nomi", required: true },
      { name: "lavozim", label: "Lavozim", required: true },
      { name: "ish_turi", label: "Ish turi", placeholder: "to'liq / qisman" },
      { name: "boshlanish_sanasi", label: "Boshlanish sanasi", type: "date", required: true },
      { name: "tugash_sanasi", label: "Tugash sanasi", type: "date" },
      { name: "hozir_ishlayapman", label: "Hozir shu yerda ishlayapman", type: "checkbox" },
      { name: "shahar", label: "Shahar" },
      { name: "tavsif", label: "Vazifalar va yutuqlar tavsifi", type: "textarea" },
    ],
    title: (i) => `${i.lavozim} — ${i.kompaniya_nomi}`,
    sub: (i) => `${i.boshlanish_sanasi || ""} – ${i.hozir_ishlayapman ? "hozirgacha" : i.tugash_sanasi || ""}`,
  },
  talim: {
    label: "Ta'lim",
    fields: [
      { name: "muassasa_nomi", label: "Ta'lim muassasasi", required: true },
      { name: "daraja", label: "Daraja", placeholder: "bakalavr / magistr" },
      { name: "mutaxassislik", label: "Mutaxassislik", required: true },
      { name: "boshlanish_yili", label: "Boshlanish yili", type: "number", required: true },
      { name: "tugash_yili", label: "Tugash yili", type: "number" },
      { name: "hozir_oqiyapman", label: "Hozir o'qiyapman", type: "checkbox" },
      { name: "gpa", label: "GPA", type: "number", step: "0.01" },
    ],
    title: (i) => i.muassasa_nomi,
    sub: (i) => `${i.mutaxassislik} · ${i.boshlanish_yili || ""}–${i.hozir_oqiyapman ? "hozirgacha" : i.tugash_yili || ""}`,
  },
  sertifikatlar: {
    label: "Sertifikatlar",
    fields: [
      { name: "nomi", label: "Sertifikat nomi", required: true },
      { name: "tashkilot", label: "Bergan tashkilot", required: true },
      { name: "berilgan_sana", label: "Berilgan sana", type: "date", required: true },
      { name: "amal_qilish_muddati", label: "Amal qilish muddati", type: "date" },
      { name: "muddatsiz", label: "Muddatsiz", type: "checkbox" },
      { name: "sertifikat_id", label: "Sertifikat ID" },
      { name: "havola", label: "Tasdiqlash havolasi", type: "url" },
    ],
    title: (i) => i.nomi,
    sub: (i) => i.tashkilot,
  },
  maqolalar: {
    label: "Maqolalar",
    fields: [
      { name: "sarlavha", label: "Sarlavha", required: true },
      { name: "nashriyot", label: "Nashriyot / platforma" },
      { name: "nashr_sanasi", label: "Nashr sanasi", type: "date", required: true },
      { name: "havola", label: "Havola", type: "url" },
      { name: "tavsif", label: "Qisqacha tavsif", type: "textarea" },
    ],
    title: (i) => i.sarlavha,
    sub: (i) => i.nashriyot,
  },
  qiziqishlar: {
    label: "Qiziqishlar",
    fields: [{ name: "nom", label: "Qiziqish / hobbi", required: true }],
    title: (i) => i.nom,
    sub: () => "",
  },
  yutuqlar: {
    label: "Yutuqlar",
    fields: [
      { name: "nomi", label: "Yutuq nomi", required: true },
      { name: "tashkilot", label: "Bergan tashkilot" },
      { name: "sana", label: "Sana", type: "date" },
      { name: "tavsif", label: "Tavsif", type: "textarea" },
    ],
    title: (i) => i.nomi,
    sub: (i) => i.tashkilot,
  },
};

const RESUME_FIELDS = [
  { name: "mutaxasislik", label: "Mutaxassislik sohasi", placeholder: "Backend dasturlash" },
  { name: "lavozim", label: "Maqsadli lavozim", required: true, placeholder: "Junior Python Developer" },
  { name: "men_haqimda", label: "Men haqimda", type: "textarea" },
];
const ALOQA_FIELDS = [
  { name: "telefon", label: "Telefon raqam", required: true, placeholder: "+998901234567" },
  { name: "email", label: "Email", type: "email", required: true },
  { name: "shahar", label: "Shahar / viloyat" },
  { name: "telegram", label: "Telegram", placeholder: "@username" },
  { name: "linkedin", label: "LinkedIn", type: "url" },
  { name: "github", label: "GitHub", type: "url" },
  { name: "portfolio_url", label: "Portfolio sayti", type: "url" },
];

export async function renderCandidateResume() {
  let resume = null;
  let notCreated = false;
  try {
    resume = await http.get(EP.resume);
  } catch (e) {
    if (e.status === 404) notCreated = true;
    else return { html: `<div class="container section-tight">${errorState(e.message)}</div>` };
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">Rezyume</div>
        <h2>Rezyumeni tuzing</h2>
        <p>Barcha bo'limlar bitta joyda — to'ldirgan sari rezyumeningiz mukammallashadi.</p>
      </div>
      <div id="resume-root">${loadingBlock()}</div>
    </div>`;

  return {
    html,
    mount(root) {
      const box = root.querySelector("#resume-root");
      if (notCreated) {
        box.innerHTML = `
          <div class="card card-pad-lg">
            <h3>Hali rezyume yaratilmagan</h3>
            <p class="muted">Boshlash uchun asosiy ma'lumotlarni kiriting.</p>
            <form id="create-resume-form">
              ${renderFields(RESUME_FIELDS)}
              <button class="btn btn-primary" type="submit">Rezyume yaratish</button>
            </form>
          </div>`;
        box.querySelector("#create-resume-form").addEventListener("submit", async (e) => {
          e.preventDefault();
          const data = collectFormData(e.target, RESUME_FIELDS);
          try {
            await http.post(EP.resume, data);
            toast("Rezyume yaratildi!");
            const result = await renderCandidateResume();
            document.getElementById("app").innerHTML = result.html;
            result.mount(document.getElementById("app"));
          } catch (err) {
            toast(err.message, "error");
          }
        });
        return;
      }
      mountResumeDashboard(box, resume);
    },
  };
}

function mountResumeDashboard(box, resume) {
  const tabKeys = ["asosiy", ...Object.keys(SECTION_CONFIG)];
  const tabLabels = { asosiy: "Asosiy & aloqa", ...Object.fromEntries(Object.entries(SECTION_CONFIG).map(([k, v]) => [k, v.label])) };

  box.innerHTML = `
    <div class="tabs" id="resume-tabs">
      ${tabKeys.map((k, i) => `<button class="tab-btn ${i === 0 ? "active" : ""}" data-tab="${k}">${esc(tabLabels[k])}</button>`).join("")}
    </div>
    <div id="resume-tab-panel"></div>`;

  const panel = box.querySelector("#resume-tab-panel");

  function showTab(key) {
    box.querySelectorAll("#resume-tabs .tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === key));
    if (key === "asosiy") renderMainForm(panel, resume);
    else renderSectionManager(panel, key);
  }

  box.querySelectorAll("#resume-tabs .tab-btn").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  showTab("asosiy");
}

function renderMainForm(panel, resume) {
  panel.innerHTML = `
    <div class="grid grid-2">
      <div class="card">
        <h3>Asosiy ma'lumotlar</h3>
        <form id="main-form">
          ${renderFields(RESUME_FIELDS, resume)}
          <button class="btn btn-primary" type="submit">Saqlash</button>
        </form>
      </div>
      <div class="card">
        <h3>Aloqa ma'lumotlari</h3>
        <form id="aloqa-form">
          ${renderFields(ALOQA_FIELDS, resume.aloqa || {})}
          <button class="btn btn-primary" type="submit">Saqlash</button>
        </form>
      </div>
    </div>`;

  panel.querySelector("#main-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = collectFormData(e.target, RESUME_FIELDS);
    try {
      await http.put(EP.resume, data);
      toast("Asosiy ma'lumotlar saqlandi.");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  panel.querySelector("#aloqa-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = collectFormData(e.target, ALOQA_FIELDS);
    try {
      await http.put(EP.resume, { aloqa: data });
      toast("Aloqa ma'lumotlari saqlandi.");
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

async function renderSectionManager(panel, sectionKey) {
  const cfg = SECTION_CONFIG[sectionKey];
  panel.innerHTML = loadingBlock();
  let items = [];
  try {
    items = await http.get(EP.resumeSection(sectionKey));
  } catch (e) {
    panel.innerHTML = errorState(e.message);
    return;
  }

  function draw() {
    panel.innerHTML = `
      <div class="row-between" style="margin-bottom:16px">
        <h3 class="mb-0">${esc(cfg.label)}</h3>
        <button class="btn btn-primary btn-sm" id="add-item">+ Qo'shish</button>
      </div>
      <div class="list" id="section-list">
        ${
          items.length
            ? items
                .map(
                  (it) => `
              <div class="list-row">
                <div class="list-row-main">
                  <b>${esc(cfg.title(it))}</b>
                  <span>${esc(cfg.sub(it) || "")}</span>
                </div>
                <div class="list-row-actions">
                  <button class="btn btn-ghost btn-sm" data-edit="${it.id}">Tahrirlash</button>
                  <button class="btn btn-danger btn-sm" data-del="${it.id}">O'chirish</button>
                </div>
              </div>`
                )
                .join("")
            : emptyState("Bo'sh", "Hali hech narsa qo'shilmagan.")
        }
      </div>`;

    panel.querySelector("#add-item").addEventListener("click", () => openSectionForm(sectionKey, cfg, null, refresh));
    panel.querySelectorAll("[data-edit]").forEach((b) =>
      b.addEventListener("click", () => openSectionForm(sectionKey, cfg, items.find((i) => String(i.id) === b.dataset.edit), refresh))
    );
    panel.querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", async () => {
        if (!confirm("Ushbu yozuvni o'chirishni tasdiqlaysizmi?")) return;
        try {
          await http.del(EP.resumeSectionDetail(sectionKey, b.dataset.del));
          toast("O'chirildi.");
          refresh();
        } catch (err) {
          toast(err.message, "error");
        }
      })
    );
  }

  async function refresh() {
    try {
      items = await http.get(EP.resumeSection(sectionKey));
    } catch (e) {
      toast(e.message, "error");
    }
    draw();
  }

  draw();
}

function openSectionForm(sectionKey, cfg, existing, onDone) {
  const overlay = openModal(
    `
    <div class="modal-head">
      <h3 class="mb-0">${existing ? "Tahrirlash" : "Qo'shish"} — ${esc(cfg.label)}</h3>
      <button class="modal-close" data-close-modal>&times;</button>
    </div>
    <form id="section-form">
      ${renderFields(cfg.fields, existing || {})}
      <button class="btn btn-primary btn-block" type="submit">Saqlash</button>
    </form>
  `,
    {
      onMount(el) {
        el.querySelector("#section-form").addEventListener("submit", async (e) => {
          e.preventDefault();
          const data = collectFormData(e.target, cfg.fields);
          try {
            if (existing) await http.put(EP.resumeSectionDetail(sectionKey, existing.id), data);
            else await http.post(EP.resumeSection(sectionKey), data);
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

/* ============================================================
   AI RESUME CHECK
   ============================================================ */
export async function renderCandidateAiCheck(params, query) {
  let vacancies = [];
  try {
    const res = await http.get(EP.vacancies);
    vacancies = Array.isArray(res) ? res : res.results || [];
  } catch {
    /* ixtiyoriy — bo'sh ro'yxat bilan davom etamiz */
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">AI tekshiruv</div>
        <h2>Rezyumeni vakansiyaga solishtiring</h2>
        <p>Rezyume matnini kiriting va vakansiyani tanlang — AI moslik darajasi va tavsiyalarni chiqaradi.</p>
      </div>
      <div class="grid grid-2">
        <div class="card">
          <form id="ai-check-form" class="stack">
            <div class="field">
              <label>Vakansiya</label>
              <select name="vacancy_id" required>
                <option value="">— tanlang —</option>
                ${vacancies.map((v) => `<option value="${v.id}" ${String(v.id) === query.vacancy_id ? "selected" : ""}>${esc(v.title || "Vakansiya #" + v.id)}</option>`).join("")}
              </select>
            </div>
            <div class="field">
              <label>Rezyume matni</label>
              <textarea name="resume_text" required style="min-height:220px" placeholder="Rezyumeningiz matnini shu yerga joylashtiring..."></textarea>
              <div class="hint">Rezyume bo'limingizdan matnni nusxalab qo'yishingiz mumkin.</div>
            </div>
            <button class="btn btn-primary btn-block" type="submit">Tahlil qilish</button>
          </form>
        </div>
        <div class="card" id="ai-result">
          <div class="state-box"><b>Natija shu yerda chiqadi</b>Formani to'ldirib, "Tahlil qilish" tugmasini bosing.</div>
        </div>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      const form = root.querySelector("#ai-check-form");
      const resultBox = root.querySelector("#ai-result");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const btn = form.querySelector("button");
        btn.disabled = true;
        resultBox.innerHTML = loadingBlock("AI tahlil qilmoqda...");
        try {
          const res = await http.post(EP.aiResumeCheck, {
            vacancy_id: fd.get("vacancy_id"),
            resume_text: fd.get("resume_text"),
          });
          const score = res.match_score ?? res.score ?? 0;
          const tips = res.suggestions || res.tips || res.feedback;
          resultBox.innerHTML = `
            ${matchGauge(score, "Moslik darajasi")}
            <div class="divider"></div>
            <h3>Tavsiyalar</h3>
            <div style="white-space:pre-line;font-size:14px;color:var(--text-dim)">${esc(
              Array.isArray(tips) ? tips.join("\n") : tips || "AI tomonidan qo'shimcha izoh berilmadi."
            )}</div>
          `;
        } catch (err) {
          resultBox.innerHTML = errorState(err.message);
        } finally {
          btn.disabled = false;
        }
      });
    },
  };
}

/* ============================================================
   AI INTERVIEW (WebSocket chat)
   ============================================================ */
export async function renderCandidateInterview(params) {
  const vacancyId = params.id;
  let info = null,
    err = null;
  try {
    info = await http.get(EP.aiInterviewStart(vacancyId));
  } catch (e) {
    err = e.message;
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head">
        <div class="eyebrow">AI intervyu</div>
        <h2>${esc(info?.vacancy_title || "Intervyu")}</h2>
        <p>Sun'iy intellekt bilan real vaqtda suhbat orqali intervyu simulyatsiyasi.</p>
      </div>
      ${err ? errorState(err) : `
      <div class="card card-pad-lg" style="max-width:680px;margin:0 auto">
        <div class="row-between" style="margin-bottom:10px">
          <span class="row"><span class="ws-dot off" id="ws-dot"></span> <span id="ws-status" class="muted" style="font-size:13px">Ulanmagan</span></span>
          <button class="btn btn-ghost btn-sm" id="ws-connect">Suhbatni boshlash</button>
        </div>
        <div class="chat-window" id="chat-window"></div>
        <form class="chat-input-row" id="chat-form">
          <input name="message" placeholder="Javobingizni yozing..." disabled />
          <button class="btn btn-primary" type="submit" disabled>Yuborish</button>
        </form>
      </div>`}
    </div>`;

  return {
    html,
    mount(root) {
      if (err) return;
      const dot = root.querySelector("#ws-dot");
      const status = root.querySelector("#ws-status");
      const chatWindow = root.querySelector("#chat-window");
      const form = root.querySelector("#chat-form");
      const input = form.querySelector("input");
      const submitBtn = form.querySelector("button");
      const connectBtn = root.querySelector("#ws-connect");
      let ws = null;

      function addBubble(text, cls) {
        const el = document.createElement("div");
        el.className = `chat-bubble ${cls}`;
        el.textContent = text;
        chatWindow.appendChild(el);
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }

      function connect() {
        import("../config.js").then(({ getWsBase }) => {
          const url = `${getWsBase()}/ws/interview/${vacancyId}/`;
          ws = new WebSocket(url);
          status.textContent = "Ulanmoqda...";
          ws.addEventListener("open", () => {
            dot.classList.add("on");
            dot.classList.remove("off");
            status.textContent = "Ulandi";
            input.disabled = false;
            submitBtn.disabled = false;
            connectBtn.disabled = true;
          });
          ws.addEventListener("message", (ev) => {
            try {
              const data = JSON.parse(ev.data);
              addBubble(data.message, data.type === "system_message" ? "system" : "ai");
            } catch {
              addBubble(ev.data, "ai");
            }
          });
          ws.addEventListener("close", () => {
            dot.classList.remove("on");
            dot.classList.add("off");
            status.textContent = "Ulanish uzildi";
            input.disabled = true;
            submitBtn.disabled = true;
            connectBtn.disabled = false;
          });
          ws.addEventListener("error", () => {
            toast("WebSocket ulanishida xatolik. Backendda Channels/ASGI ishga tushirilganini tekshiring.", "error");
          });
        });
      }

      connectBtn.addEventListener("click", connect);

      form.addEventListener("submit", (e) => {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg || !ws || ws.readyState !== 1) return;
        addBubble(msg, "me");
        ws.send(JSON.stringify({ message: msg }));
        input.value = "";
      });
    },
  };
}
