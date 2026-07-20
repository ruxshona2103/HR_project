import { http } from "../api.js";
import { EP } from "../config.js";
import { esc, toast, errorState } from "../components.js";
import { renderFields, collectFormData } from "../formkit.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { getApiBase, setApiBase } from "../config.js";

const PROFILE_FIELDS = [
  { name: "first_name", label: "Ism", required: true },
  { name: "last_name", label: "Familiya", required: true },
  { name: "middle_name", label: "Sharif" },
  { name: "phone_number", label: "Telefon raqam", placeholder: "+998901234567" },
];

export async function renderSettings() {
  let me = null;
  try {
    me = await http.get(EP.me);
  } catch (e) {
    return { html: `<div class="container section-tight">${errorState(e.message)}</div>` };
  }

  let telegram = null;
  try {
    telegram = await http.get(EP.telegramStatus);
  } catch {
    /* ixtiyoriy */
  }

  const html = `
    <div class="container section-tight">
      <div class="section-head"><div class="eyebrow">Sozlamalar</div><h2>Profil va hisob</h2></div>

      <div class="grid grid-2">
        <div class="card">
          <h3>Shaxsiy ma'lumotlar</h3>
          <form id="profile-form">
            ${renderFields(PROFILE_FIELDS, me)}
            <button class="btn btn-primary" type="submit">Saqlash</button>
          </form>
        </div>

        <div class="card">
          <h3>Parolni o'zgartirish</h3>
          <form id="password-form" class="stack">
            <div class="field"><label>Eski parol</label><input type="password" name="old_password" required /></div>
            <div class="field"><label>Yangi parol</label><input type="password" name="new_password" required minlength="8" /></div>
            <div class="field"><label>Yangi parolni tasdiqlang</label><input type="password" name="new_password_confirm" required minlength="8" /></div>
            <button class="btn btn-primary" type="submit">Parolni yangilash</button>
          </form>
        </div>
      </div>

      <div class="grid grid-2" style="margin-top:20px">
        <div class="card">
          <h3>Telegram bot</h3>
          <p class="muted">Bildirishnomalar va telefon orqali tasdiqlash uchun Telegram botni ulang.</p>
          <div class="kv"><span>Holati</span><b>${telegram?.is_linked ? "Ulangan ✅" : "Ulanmagan"}</b></div>
          <div class="row" style="margin-top:12px">
            <button class="btn btn-ghost btn-sm" id="bot-link-btn">Bot havolasini olish</button>
            ${telegram?.is_linked ? `<button class="btn btn-danger btn-sm" id="tg-disconnect">Uzish</button>` : ""}
          </div>
          ${telegram?.connect_instructions ? `<p class="muted" style="margin-top:10px;font-size:13px">${esc(telegram.connect_instructions)}</p>` : ""}
        </div>

        <div class="card">
          <h3 style="color:var(--danger)">Xavfli hudud</h3>
          <p class="muted">Hisobni butunlay o'chirish — bu amalni qaytarib bo'lmaydi.</p>
          <button class="btn btn-danger" id="delete-account">Hisobni o'chirish</button>
        </div>
      </div>
    </div>`;

  return {
    html,
    mount(root) {
      root.querySelector("#profile-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = collectFormData(e.target, PROFILE_FIELDS);
        try {
          const updated = await http.patch(EP.me, data);
          store.setUser(updated);
          toast("Profil yangilandi.");
        } catch (err) {
          toast(err.message, "error");
        }
      });

      root.querySelector("#password-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await http.post(EP.changePassword, Object.fromEntries(fd.entries()));
          toast("Parol yangilandi.");
          e.target.reset();
        } catch (err) {
          toast(err.message, "error");
        }
      });

      root.querySelector("#bot-link-btn").addEventListener("click", async () => {
        try {
          const res = await http.get(EP.botLink);
          window.open(res.bot_link, "_blank");
        } catch (err) {
          toast(err.message, "error");
        }
      });

      root.querySelector("#tg-disconnect")?.addEventListener("click", async () => {
        try {
          await http.post(EP.telegramDisconnect, {});
          toast("Telegram uzildi.");
          navigate("/settings");
          location.reload();
        } catch (err) {
          toast(err.message, "error");
        }
      });

      root.querySelector("#delete-account").addEventListener("click", async () => {
        if (!confirm("Hisobingizni butunlay o'chirmoqchimisiz? Bu amalni qaytarib bo'lmaydi!")) return;
        try {
          await http.del(EP.deleteAccount);
          store.clear();
          toast("Hisob o'chirildi.");
          navigate("/");
        } catch (err) {
          toast(err.message, "error");
        }
      });
    },
  };
}

export function renderApiSettings() {
  const html = `
    <div class="container section-tight">
      <div class="section-head"><div class="eyebrow">Sozlamalar</div><h2>API manzili</h2></div>
      <div class="card" style="max-width:520px">
        <p class="muted">Bu frontend Django backend bilan REST API orqali ishlaydi. Backend qayerda ishlab turganini shu yerda ko'rsating (masalan mahalliy serverda yoki Coolify orqali joylashtirilgan domenda).</p>
        <form id="api-form" class="stack">
          <div class="field">
            <label>Backend API manzili</label>
            <input name="api_base" value="${esc(getApiBase())}" placeholder="https://api.example.uz/api" />
            <div class="hint">Oxirida slash bo'lmasin. Masalan: http://127.0.0.1:8000/api</div>
          </div>
          <button class="btn btn-primary" type="submit">Saqlash</button>
        </form>
      </div>
    </div>`;
  return {
    html,
    mount(root) {
      root.querySelector("#api-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const val = new FormData(e.target).get("api_base");
        setApiBase(val);
        toast("API manzili saqlandi.");
      });
    },
  };
}
