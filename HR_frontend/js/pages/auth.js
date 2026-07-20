import { http, ApiError } from "../api.js";
import { EP } from "../config.js";
import { store } from "../store.js";
import { toast, esc } from "../components.js";
import { navigate } from "../router.js";

function authShell(activeTab, body) {
  return `
    <div class="container">
      <div class="auth-shell">
        <div class="auth-tabbar">
          <button data-nav="/login" class="${activeTab === "login" ? "active" : ""}">Kirish</button>
          <button data-nav="/register/candidate" class="${activeTab === "candidate" ? "active" : ""}">Nomzod</button>
          <button data-nav="/register/organization" class="${activeTab === "organization" ? "active" : ""}">Kompaniya</button>
        </div>
        <div class="card card-pad-lg">${body}</div>
        <div class="auth-switch">
          Telefon orqali kirmoqchimisiz? <a data-nav="/phone-auth">Bu yerdan o'ting</a>
        </div>
      </div>
    </div>`;
}

function bindNav(root) {
  root.querySelectorAll("[data-nav]").forEach((el) =>
    el.addEventListener("click", () => navigate(el.getAttribute("data-nav")))
  );
}

function afterLogin(payload) {
  store.setSession({ access: payload.access, refresh: payload.refresh, user: payload.user });
  toast(`Xush kelibsiz, ${payload.user?.first_name || ""}!`);
  navigate(payload.user?.user_type === "organization" ? "/employer" : "/candidate");
}

/* ----------------------------- LOGIN ----------------------------- */
export function renderLogin() {
  const html = authShell(
    "login",
    `
    <h2>Tizimga kirish</h2>
    <p class="muted">Email va parolingiz orqali kiring.</p>
    <form id="login-form" class="stack">
      <div class="field"><label>Email</label><input type="email" name="email" required placeholder="siz@mail.com" /></div>
      <div class="field"><label>Parol</label><input type="password" name="password" required placeholder="••••••••" /></div>
      <div id="login-error" class="form-error" style="display:none"></div>
      <button class="btn btn-primary btn-block" type="submit">Kirish</button>
    </form>
  `
  );
  return {
    html,
    mount(root) {
      bindNav(root);
      const form = root.querySelector("#login-form");
      const errBox = root.querySelector("#login-error");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        const fd = new FormData(form);
        const btn = form.querySelector("button");
        btn.disabled = true;
        try {
          const payload = await http.post(EP.emailLogin, {
            email: fd.get("email"),
            password: fd.get("password"),
          }, { auth: false });
          afterLogin(payload);
        } catch (err) {
          errBox.textContent = err.message;
          errBox.style.display = "block";
        } finally {
          btn.disabled = false;
        }
      });
    },
  };
}

/* ----------------------------- REGISTER ----------------------------- */
export function renderRegister(kind) {
  const isOrg = kind === "organization";
  const html = authShell(
    isOrg ? "organization" : "candidate",
    `
    <h2>${isOrg ? "Kompaniya sifatida ro'yxatdan o'tish" : "Nomzod sifatida ro'yxatdan o'tish"}</h2>
    <p class="muted">Email orqali ro'yxatdan o'ting — keyingi qadamda tasdiqlash kodi yuboriladi.</p>
    <form id="register-form" class="stack">
      <div class="form-grid">
        <div class="field"><label>Ism</label><input name="first_name" required /></div>
        <div class="field"><label>Familiya</label><input name="last_name" required /></div>
      </div>
      <div class="field"><label>Sharif (ixtiyoriy)</label><input name="middle_name" /></div>
      ${isOrg ? `
      <div class="form-grid">
        <div class="field"><label>Tashkilot nomi</label><input name="organization_name" required /></div>
        <div class="field"><label>Lavozimingiz</label><input name="position" placeholder="HR menejer" /></div>
      </div>` : ""}
      <div class="field"><label>Email</label><input type="email" name="email" required /></div>
      <div class="form-grid">
        <div class="field"><label>Parol</label><input type="password" name="password" required minlength="8" /></div>
        <div class="field"><label>Parolni tasdiqlang</label><input type="password" name="password_confirm" required minlength="8" /></div>
      </div>
      <div id="register-error" class="form-error" style="display:none"></div>
      <button class="btn btn-primary btn-block" type="submit">Tasdiqlash kodini olish</button>
    </form>
  `
  );
  return {
    html,
    mount(root) {
      bindNav(root);
      const form = root.querySelector("#register-form");
      const errBox = root.querySelector("#register-error");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        const fd = new FormData(form);
        const body = Object.fromEntries(fd.entries());
        const btn = form.querySelector("button");
        btn.disabled = true;
        try {
          const ep = isOrg ? EP.emailRegisterOrg : EP.emailRegisterCandidate;
          const res = await http.post(ep, body, { auth: false });
          toast(res.message || "Tasdiqlash kodi yuborildi.");
          navigate(`/verify?email=${encodeURIComponent(res.email || body.email)}`);
        } catch (err) {
          errBox.textContent = err.message;
          errBox.style.display = "block";
        } finally {
          btn.disabled = false;
        }
      });
    },
  };
}

/* ----------------------------- VERIFY EMAIL ----------------------------- */
export function renderVerify(params, query) {
  const email = query.email || "";
  const html = authShell(
    "login",
    `
    <h2>Emailni tasdiqlash</h2>
    <p class="muted">Emailingizga (${esc(email) || "ko'rsatilgan manzil"}) yuborilgan 6 xonali kodni kiriting.</p>
    <form id="verify-form" class="stack">
      <div class="field"><label>Email</label><input type="email" name="email" required value="${esc(email)}" /></div>
      <div class="field"><label>Tasdiqlash kodi</label><input name="code" required minlength="6" maxlength="6" placeholder="123456" /></div>
      <div id="verify-error" class="form-error" style="display:none"></div>
      <button class="btn btn-primary btn-block" type="submit">Tasdiqlash</button>
      <button class="btn btn-ghost btn-block" type="button" id="resend-btn">Kodni qayta yuborish</button>
    </form>
  `
  );
  return {
    html,
    mount(root) {
      bindNav(root);
      const form = root.querySelector("#verify-form");
      const errBox = root.querySelector("#verify-error");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        const fd = new FormData(form);
        const btn = form.querySelector("button[type=submit]");
        btn.disabled = true;
        try {
          const payload = await http.post(
            EP.emailVerify,
            { email: fd.get("email"), code: fd.get("code") },
            { auth: false }
          );
          store.setSession({
            access: payload.tokens.access,
            refresh: payload.tokens.refresh,
            user: payload.user,
          });
          toast("Muvaffaqiyatli ro'yxatdan o'tdingiz!");
          navigate(payload.user?.user_type === "organization" ? "/employer" : "/candidate");
        } catch (err) {
          errBox.textContent = err.message;
          errBox.style.display = "block";
        } finally {
          btn.disabled = false;
        }
      });
      root.querySelector("#resend-btn").addEventListener("click", async () => {
        const emailVal = form.email.value;
        if (!emailVal) return toast("Avval emailni kiriting.", "error");
        try {
          const res = await http.post(EP.emailResend, { email: emailVal }, { auth: false });
          toast(res.message || "Yangi kod yuborildi.");
        } catch (err) {
          toast(err.message, "error");
        }
      });
    },
  };
}

/* ----------------------------- PHONE AUTH ----------------------------- */
export function renderPhoneAuth() {
  const html = `
    <div class="container">
      <div class="auth-shell">
        <div class="card card-pad-lg">
          <h2>Telefon orqali kirish</h2>
          <p class="muted">Ro'yxatdan o'tish uchun Telegram bot orqali bir martalik kod (OTP) yuboriladi.</p>
          <div class="tabs" id="phone-tabs">
            <button class="tab-btn active" data-tab="reg-candidate">Nomzod — ro'yxatdan o'tish</button>
            <button class="tab-btn" data-tab="reg-org">Kompaniya — ro'yxatdan o'tish</button>
            <button class="tab-btn" data-tab="login">Kirish</button>
            <button class="tab-btn" data-tab="otp">OTP tasdiqlash</button>
          </div>
          <div id="phone-panel"></div>
        </div>
        <div class="auth-switch"><a data-nav="/login">← Email orqali kirish</a></div>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      bindNav(root);
      const panel = root.querySelector("#phone-panel");
      const tabs = root.querySelectorAll("#phone-tabs .tab-btn");
      const panels = {
        "reg-candidate": phonePanel("Nomzod ro'yxatdan o'tish", true, false),
        "reg-org": phonePanel("Kompaniya ro'yxatdan o'tish", true, true),
        login: phonePanel("Telefon bilan kirish", false, false),
        otp: otpPanel(),
      };

      function show(tab) {
        tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
        panel.innerHTML = panels[tab];
        bindPanel(tab);
      }

      function bindPanel(tab) {
        const form = panel.querySelector("form");
        const errBox = panel.querySelector(".form-error");
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          errBox.style.display = "none";
          const fd = new FormData(form);
          const btn = form.querySelector("button");
          btn.disabled = true;
          try {
            if (tab === "reg-candidate" || tab === "reg-org") {
              const body = Object.fromEntries(fd.entries());
              const ep = tab === "reg-org" ? EP.phoneRegisterOrg : EP.phoneRegisterCandidate;
              const res = await http.post(ep, body, { auth: false });
              toast(res.message || "OTP yuborildi.");
              show("otp");
            } else if (tab === "login") {
              const res = await http.post(EP.phoneLogin, { phone_number: fd.get("phone_number") }, { auth: false });
              toast(res.message || "OTP yuborildi.");
              show("otp");
            } else if (tab === "otp") {
              const payload = await http.post(
                EP.phoneVerifyOtp,
                { phone_number: fd.get("phone_number"), code: fd.get("code") },
                { auth: false }
              );
              const tokens = payload.tokens || payload;
              const user = payload.user || payload.user_data;
              store.setSession({ access: tokens.access, refresh: tokens.refresh, user });
              toast("Muvaffaqiyatli kirdingiz!");
              navigate(user?.user_type === "organization" ? "/employer" : "/candidate");
            }
          } catch (err) {
            errBox.textContent = err.message;
            errBox.style.display = "block";
          } finally {
            btn.disabled = false;
          }
        });
      }

      tabs.forEach((t) => t.addEventListener("click", () => show(t.dataset.tab)));
      show("reg-candidate");
    },
  };
}

function phonePanel(title, isRegister, isOrg) {
  return `
    <form class="stack">
      <p class="form-note">${esc(title)}</p>
      ${
        isRegister
          ? `<div class="form-grid">
              <div class="field"><label>Ism</label><input name="first_name" required /></div>
              <div class="field"><label>Familiya</label><input name="last_name" required /></div>
            </div>`
          : ""
      }
      ${isOrg ? `<div class="field"><label>Tashkilot nomi</label><input name="organization_name" required /></div>` : ""}
      <div class="field"><label>Telefon raqam</label><input name="phone_number" required placeholder="+998901234567" /></div>
      <div class="form-error" style="display:none"></div>
      <button class="btn btn-primary btn-block" type="submit">${isRegister ? "Ro'yxatdan o'tish" : "OTP olish"}</button>
    </form>`;
}

function otpPanel() {
  return `
    <form class="stack">
      <p class="form-note">Telegram botga kelgan 6 xonali kodni kiriting.</p>
      <div class="field"><label>Telefon raqam</label><input name="phone_number" required placeholder="+998901234567" /></div>
      <div class="field"><label>OTP kod</label><input name="code" required minlength="6" maxlength="6" /></div>
      <div class="form-error" style="display:none"></div>
      <button class="btn btn-primary btn-block" type="submit">Tasdiqlash</button>
    </form>`;
}
