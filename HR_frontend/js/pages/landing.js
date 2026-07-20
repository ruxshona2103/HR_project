import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, matchGauge, fmtMoney, emptyState } from "../components.js";
import { navigate } from "../router.js";

export async function renderLanding() {
  let data = null;
  let loadError = null;
  try {
    data = await http.get(EP.landingData, { auth: false });
  } catch (e) {
    loadError = e.message;
  }

  const team = data?.team;
  const products = data?.products || [];
  const pricing = data?.pricing || [];
  const contacts = data?.contacts;
  const steps = data?.how_it_works || [];

  const html = `
    <section class="hero">
      <div class="container hero-grid">
        <div>
          <div class="eyebrow">Sun'iy intellekt asosidagi HR platforma</div>
          <h1>Nomzod bilan vakansiyani<br/><em>AI aniqligida</em> bog'laymiz</h1>
          <p class="hero-lede">
            Rezyumeningizni tuzing, vakansiyalarga murojaat qiling — sun'iy intellekt rezyumeni tahlil qilib,
            moslik darajasini hisoblab beradi va real intervyu simulyatsiyasini o'tkazadi.
            Kompaniyalar esa nomzodlarni tezroq va aniqroq tanlaydi.
          </p>
          <div class="hero-actions">
            <button class="btn btn-primary" data-nav="/register/candidate">Nomzod sifatida boshlash</button>
            <button class="btn btn-ghost" data-nav="/register/organization">Kompaniya sifatida ro'yxatdan o'tish</button>
          </div>
          <div class="hero-stats">
            <div class="hero-stat"><b>${team?.experience_years ? team.experience_years + "+" : "—"}</b><span>yillik tajriba</span></div>
            <div class="hero-stat"><b>${products.length || "—"}</b><span>platforma imkoniyati</span></div>
            <div class="hero-stat"><b>2</b><span>bosqichli AI baholash</span></div>
          </div>
        </div>
        <div class="card card-pad-lg gauge-card card-hover">
          <div class="row-between" style="margin-bottom:10px">
            <span class="badge badge-primary">Namuna natija</span>
            <span class="muted" style="font-size:12px">jonli demo</span>
          </div>
          ${matchGauge(87, "Nomzod rezyumesi vakansiyaga mosligi")}
          <div class="gauge-legend"><span>0%</span><span>50%</span><span>100%</span></div>
          <hr class="divider" />
          <div class="steps-flow">
            <div class="step-row"><span class="step-num">1</span><p><b>Rezyume yuboriladi</b> — matn yoki fayl ko'rinishida.</p></div>
            <div class="step-row"><span class="step-num">2</span><p><b>AI tahlil qiladi</b> — ko'nikma va tajriba solishtiriladi.</p></div>
            <div class="step-row"><span class="step-num">3</span><p><b>Natija va tavsiyalar</b> — moslik foizi va yaxshilash bo'yicha maslahat.</p></div>
          </div>
        </div>
      </div>
    </section>

    <section class="section-tight">
      <div class="container">
        <div class="section-head center">
          <div class="eyebrow" style="justify-content:center">Ishlash tartibi</div>
          <h2>Ariza topshirishdan ishga joylashishgacha</h2>
        </div>
        <div class="grid grid-3">
          ${flowCard("01", "Nomzod", "Ro'yxatdan o'tasiz, rezyume tuzasiz va mos vakansiyalarni ko'rasiz.")}
          ${flowCard("02", "AI tahlil", "Rezyume vakansiya bilan solishtiriladi, moslik foizi va tavsiyalar chiqadi.")}
          ${flowCard("03", "AI intervyu", "Real suhbat simulyatsiyasidan o'tib, HR jamoasiga tayyor holda chiqasiz.")}
        </div>
      </div>
    </section>

    ${
      products.length
        ? `<section class="section-tight">
      <div class="container">
        <div class="section-head">
          <div class="eyebrow">Imkoniyatlar</div>
          <h2>Platforma nimalarni taklif qiladi</h2>
        </div>
        <div class="grid grid-3">
          ${products
            .map(
              (p) => `
            <div class="card card-hover">
              ${p.icon ? `<img class="product-icon" src="${esc(p.icon)}" alt="" />` : ""}
              <h3 style="margin-top:14px">${esc(p.name)}</h3>
              <p>${esc(p.description)}</p>
            </div>`
            )
            .join("")}
        </div>
      </div>
    </section>`
        : ""
    }

    ${
      pricing.length
        ? `<section class="section-tight">
      <div class="container">
        <div class="section-head center">
          <div class="eyebrow" style="justify-content:center">Tariflar</div>
          <h2>Kompaniyangizga mos rejani tanlang</h2>
        </div>
        <div class="grid grid-3">
          ${pricing
            .map(
              (p) => `
            <div class="card card-hover pricing-card">
              <span class="badge badge-gold">${esc(p.name)}</span>
              <div class="pricing-price">${fmtMoney(p.price, p.currency) || "Kelishuv asosida"}</div>
              <div class="pricing-feat">${esc(p.features)}</div>
              <button class="btn btn-ghost btn-block" data-nav="/register/organization" style="margin-top:10px">Tanlash</button>
            </div>`
            )
            .join("")}
        </div>
      </div>
    </section>`
        : ""
    }

    ${
      team
        ? `<section class="section-tight">
      <div class="container">
        <div class="card card-pad-lg" style="max-width:760px;margin:0 auto">
          <div class="eyebrow">Jamoa haqida</div>
          <h2>${esc(team.title)}</h2>
          <p>${esc(team.description)}</p>
        </div>
      </div>
    </section>`
        : ""
    }

    <section class="section-tight">
      <div class="container">
        <div class="card card-pad-lg" style="display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap">
          <div>
            <h3 style="margin-bottom:6px">Bog'lanish</h3>
            ${
              contacts
                ? `<div class="stack">
                    ${contacts.phone_number ? `<div class="contact-row">☎ ${esc(contacts.phone_number)}</div>` : ""}
                    ${contacts.email ? `<div class="contact-row">✉ ${esc(contacts.email)}</div>` : ""}
                    ${contacts.telegram_link ? `<div class="contact-row"><a href="${esc(contacts.telegram_link)}" target="_blank" rel="noopener">Telegram</a></div>` : ""}
                    ${contacts.instagram_link ? `<div class="contact-row"><a href="${esc(contacts.instagram_link)}" target="_blank" rel="noopener">Instagram</a></div>` : ""}
                  </div>`
                : `<p class="muted">Aloqa ma'lumotlari hali admin panelda to'ldirilmagan.</p>`
            }
          </div>
          <button class="btn btn-primary" data-nav="/register/candidate">Hoziroq boshlash</button>
        </div>
      </div>
    </section>

    ${loadError ? `<div class="container">${emptyState("Landing ma'lumotlari yuklanmadi", "Backend serverga ulanib bo'lmadi: " + loadError + ". API manzilini #/settings/api sahifasida tekshiring.")}</div>` : ""}
  `;

  return {
    html,
    mount(root) {
      root.querySelectorAll("[data-nav]").forEach((el) =>
        el.addEventListener("click", () => navigate(el.getAttribute("data-nav")))
      );
    },
  };
}

function flowCard(num, title, desc) {
  return `
    <div class="card">
      <div class="step-num" style="margin-bottom:14px">${num}</div>
      <h3>${esc(title)}</h3>
      <p>${esc(desc)}</p>
    </div>`;
}
