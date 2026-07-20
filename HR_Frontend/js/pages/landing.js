import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, emptyState, chip } from "../components.js";
import { navigate } from "../router.js";
import { store } from "../store.js";
import { vacancyCardHtml } from "./vacancies.js";

export async function renderLanding() {
  let data = null;
  try {
    data = await http.get(EP.landingData, { auth: false });
  } catch {
    /* ixtiyoriy — landing sahifa ma'lumotlarsiz ham ishlaydi */
  }
  const contacts = data?.contacts;

  // Backendda VacancyViewSet faqat login qilgan foydalanuvchilarga ochiq (global
  // IsAuthenticated). Shu sababli mehmon uchun haqiqiy vakansiyalar o'rniga
  // "namuna" deb belgilangan namunaviy kartalar ko'rsatamiz — login qilingan
  // foydalanuvchiga esa haqiqiy so'nggi vakansiyalar chiqadi.
  let vacancies = [];
  let isSample = false;
  if (store.isAuthed()) {
    try {
      const res = await http.get(EP.vacancies);
      vacancies = (Array.isArray(res) ? res : res.results || []).filter((v) => !v.status || v.status === "OPEN").slice(0, 6);
    } catch {
      /* jim o'tamiz */
    }
  }
  if (!vacancies.length) {
    isSample = true;
    vacancies = SAMPLE_VACANCIES;
  }

  const html = `
    ${heroSection()}
    ${latestVacanciesSection(vacancies, isSample)}
    ${platformFeaturesSection()}
    ${aiCapabilitiesSection()}
    <section class="section-tight">
      <div class="container">
        ${ctaBanner()}
      </div>
    </section>
    ${footerSection(contacts)}
  `;

  return {
    html,
    mount(root) {
      root.querySelectorAll("[data-nav]").forEach((el) => el.addEventListener("click", () => navigate(el.getAttribute("data-nav"))));
      // vakansiya kartalaridagi "Ko'proq" — mehmon uchun kirishga yo'naltiradi
      root.querySelectorAll("[data-detail]").forEach((el) =>
        el.addEventListener("click", () => navigate(store.isAuthed() ? "/vacancies" : "/login"))
      );
    },
  };
}

/* ============================================================ */
function heroSection() {
  return `
    <section class="hero-v2">
      <div class="container hero-v2-inner">
        <div>
          <h1>Kelajak karyerangizni<br/>hozirdan boshlang</h1>
          <p class="hero-v2-lede">O'zbekistondagi AI asosidagi karyera platformasi. Vakansiya toping, rezyumeni sun'iy intellekt bilan tuzing va AI intervyu simulyatsiyasidan o'ting.</p>
          <div class="hero-v2-pills">
            <span class="hero-v2-pill">📄 Ochiq vakansiyalar</span>
            <span class="hero-v2-pill">🤖 AI moslik tahlili</span>
            <span class="hero-v2-pill">🎙 AI intervyu simulyatsiyasi</span>
          </div>
          <div class="hero-v2-actions">
            <button class="btn btn-gold" data-nav="/register/candidate">Hoziroq boshlash →</button>
            <button class="btn btn-ghost" style="border-color:rgba(255,255,255,.35);color:#fff" data-nav="/register/organization">Kompaniya sifatida qo'shilish</button>
          </div>
        </div>
        <div class="hero-v2-art">
          ${matchGaugeSvgLight()}
        </div>
      </div>
    </section>`;
}

function matchGaugeSvgLight() {
  return `
    <div style="text-align:center;color:#fff;padding:20px">
      <svg width="180" height="104" viewBox="0 0 180 104">
        <path d="M 26 90 A 64 64 0 0 1 154 90" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="14" stroke-linecap="round"/>
        <path d="M 26 90 A 64 64 0 0 1 132 34" fill="none" stroke="#e8b84b" stroke-width="14" stroke-linecap="round"/>
        <text x="90" y="80" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="26" font-weight="700" fill="#fff">87%</text>
      </svg>
      <div style="font-size:13px;opacity:.85;margin-top:6px">AI moslik darajasi — namuna natija</div>
    </div>`;
}

/* ============================================================ */
const SAMPLE_VACANCIES = [
  { id: "s1", title: "Backend dasturchi (Python/Django)", employment_type: "FULL_TIME", experience_level: "ONE_TO_THREE", work_formats: ["HYBRID"], salary_from: 8000000, salary_to: 15000000, currency: "UZS", region: "Toshkent shahri", district: "Chilonzor", description: "Django REST Framework asosida backend xizmatlarini yaratish va qo'llab-quvvatlash.", company_name: "Namuna kompaniya", vacant_slots: 2 },
  { id: "s2", title: "Frontend dasturchi (React)", employment_type: "FULL_TIME", experience_level: "UP_TO_1", work_formats: ["REMOTE"], salary_from: 6000000, salary_to: 10000000, currency: "UZS", region: "Jizzax", description: "Zamonaviy foydalanuvchi interfeyslarini React asosida ishlab chiqish.", company_name: "Namuna kompaniya", vacant_slots: 1 },
  { id: "s3", title: "HR menejeri", employment_type: "FULL_TIME", experience_level: "THREE_TO_FIVE", work_formats: ["OFFICE"], salary_from: 5000000, salary_to: 9000000, currency: "UZS", region: "Samarqand", description: "Xodimlarni yollash, moslashtirish va rivojlantirish jarayonlarini boshqarish.", company_name: "Namuna kompaniya", vacant_slots: 1 },
];

function latestVacanciesSection(vacancies, isSample) {
  return `
    <section class="section-tight">
      <div class="container">
        <div class="section-head">
          <div class="eyebrow">Vakansiyalar</div>
          <h2>Eng so'nggi vakansiyalar</h2>
          <p>Eng yaxshi kompaniyalardan eng so'nggi ish o'rinlari. ${isSample ? "Barchasini ko'rish uchun tizimga kiring." : "Hoziroq ariza yuboring!"}</p>
        </div>
        ${isSample ? `<div style="margin-bottom:16px">${chip("Namuna kartalar — kirgandan so'ng haqiqiy vakansiyalar chiqadi", "badge-gold")}</div>` : ""}
        <div class="grid grid-3">
          ${vacancies.map(vacancyCardHtml).join("")}
        </div>
        <div class="text-center" style="margin-top:26px">
          <button class="btn btn-primary" data-nav="${store.isAuthed() ? "/vacancies" : "/login"}">Barcha vakansiyalarni ko'rish →</button>
        </div>
      </div>
    </section>`;
}

/* ============================================================ */
function platformFeaturesSection() {
  const items = [
    ["📝", "Rezyume yaratish", "Bo'lim-bo'lim to'ldiriladigan professional rezyume tuzuvchi."],
    ["✅", "Vakansiyalarga ariza", "O'zingizga mos vakansiyalarni toping va AI orqali baholaning."],
    ["🏢", "Kompaniya uchun boshqaruv", "Vakansiya joylashtirish va nomzodlarni AI yordamida baholash."],
    ["📈", "Karyera o'sishi", "AI tavsiyalari orqali ko'nikmalaringizni rivojlantiring."],
  ];
  return `
    <section class="section-tight">
      <div class="container">
        <div class="section-head"><div class="eyebrow">Imkoniyatlar</div><h2>Platforma haqida</h2></div>
        <div class="grid grid-4">
          ${items
            .map(
              ([icon, title, desc]) => `
            <div class="card feature-row">
              <div class="feature-icon-box">${icon}</div>
              <div><h4>${esc(title)}</h4><p>${esc(desc)}</p></div>
            </div>`
            )
            .join("")}
        </div>
      </div>
    </section>`;
}

function aiCapabilitiesSection() {
  const items = [
    ["🤖", "AI rezyume tekshiruvi", "Rezyumeni vakansiya bilan solishtirib, moslik foizini hisoblaydi."],
    ["🎙", "AI bilan interaktiv suhbat", "Real intervyu simulyatsiyasi orqali suhbatga tayyorlaning."],
    ["🧭", "AI tavsiyalari", "Tavsiyalar asosida rezyumeni va ko'nikmalarni yaxshilang."],
  ];
  return `
    <section class="section-tight">
      <div class="container">
        <div class="section-head"><div class="eyebrow">Sun'iy intellekt</div><h2>AI imkoniyatlari</h2></div>
        <div class="grid grid-3">
          ${items
            .map(
              ([icon, title, desc]) => `
            <div class="card feature-row">
              <div class="feature-icon-box gold">${icon}</div>
              <div><h4>${esc(title)}</h4><p>${esc(desc)}</p></div>
            </div>`
            )
            .join("")}
        </div>
      </div>
    </section>`;
}

/* ============================================================ */
function ctaBanner() {
  return `
    <div class="cta-banner">
      <div>
        <h2>Karyerangizni bugundan boshlashga tayyormisiz?</h2>
        <p>O'zbekistonda ish, amaliyot va professional rivojlanish uchun AI asosidagi karyera platformasi.</p>
      </div>
      <button class="btn btn-gold" data-nav="/register/candidate">Boshlash →</button>
    </div>`;
}

/* ============================================================ */
function footerSection(contacts) {
  return `
    <footer class="footer-v2">
      <div class="container">
        <div class="footer-v2-grid">
          <div>
            <div class="footer-brand" style="margin-bottom:10px">Ishga<span class="dot">.</span>AI</div>
            <p style="max-width:32ch">O'zbekistonda ish, amaliyot va professional rivojlanish uchun AI asosidagi karyera platformasi.</p>
          </div>
          <div>
            <h5>Platforma</h5>
            <ul class="footer-v2-links">
              <li><a data-nav="/vacancies">Bo'sh ish o'rinlari</a></li>
              <li><a data-nav="/candidate/resume">Rezyume yaratish</a></li>
              <li><a data-nav="/register/organization">Kompaniyalar uchun</a></li>
            </ul>
          </div>
          <div>
            <h5>AI imkoniyatlari</h5>
            <ul class="footer-v2-links">
              <li><a data-nav="/candidate/ai-check">AI rezyume tekshiruvi</a></li>
              <li><a data-nav="/vacancies">AI intervyu simulyatsiyasi</a></li>
            </ul>
          </div>
          <div>
            <h5>Umumiy</h5>
            <ul class="footer-v2-links">
              <li><a data-nav="/settings/api">Sozlamalar</a></li>
              ${contacts?.email ? `<li><a href="mailto:${esc(contacts.email)}">${esc(contacts.email)}</a></li>` : ""}
              ${contacts?.phone_number ? `<li>${esc(contacts.phone_number)}</li>` : ""}
            </ul>
          </div>
        </div>
        <div class="footer-v2-bottom">
          <span>© ${new Date().getFullYear()} Ishga.AI. Barcha huquqlar himoyalangan.</span>
          <span>Otabek Nematov tomonidan ishlab chiqilgan</span>
        </div>
      </div>
    </footer>`;
}

/* ============================================================
   Floating AI assistant widget: mounted globally from app.js
   (see js/fab.js) — nothing to do here anymore.
   ============================================================ */
