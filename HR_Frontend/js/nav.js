import { store } from "./store.js";
import { navigate } from "./router.js";
import { http } from "./api.js";
import { EP } from "./config.js";
import { toast } from "./components.js";

function link(path, label, currentPath) {
  const active = currentPath === path || (path !== "/" && currentPath.startsWith(path));
  return `<span class="nav-link ${active ? "active" : ""}" data-nav="${path}">${label}</span>`;
}

export function renderNav() {
  const bar = document.getElementById("topbar");
  const currentPath = "/" + (location.hash.slice(2) || "");
  const user = store.getUser();
  const role = store.role();

  let links = "";
  let right = "";

  if (!store.isAuthed()) {
    links = [
      link("/", "Bosh sahifa", currentPath),
      link("/vacancies", "Vakansiyalar", currentPath),
    ].join("");
    right = `
      <span class="nav-link" data-nav="/login">Kirish</span>
      <button class="btn btn-primary btn-sm" data-nav="/register/candidate">Ro'yxatdan o'tish</button>
    `;
  } else if (role === "organization") {
    links = [
      link("/employer", "Boshqaruv paneli", currentPath),
      link("/employer/vacancies", "Vakansiyalarim", currentPath),
      link("/employer/questions", "AI savollari", currentPath),
    ].join("");
    right = `
      <span class="nav-role-chip">Kompaniya</span>
      <span class="nav-link" data-nav="/settings">${escapeName(user)}</span>
      <button class="btn btn-ghost btn-sm" id="nav-logout">Chiqish</button>
    `;
  } else {
    links = [
      link("/candidate", "Boshqaruv paneli", currentPath),
      link("/candidate/resume", "Rezyume", currentPath),
      link("/vacancies", "Vakansiyalar", currentPath),
      link("/candidate/ai-check", "AI tekshiruv", currentPath),
    ].join("");
    right = `
      <span class="nav-role-chip">Nomzod</span>
      <span class="nav-link" data-nav="/settings">${escapeName(user)}</span>
      <button class="btn btn-ghost btn-sm" id="nav-logout">Chiqish</button>
    `;
  }

  bar.innerHTML = `
    <div class="nav-inner">
      <div class="brand" data-nav="/"><span class="brand-badge"></span>Ishga<span class="dot">.</span>AI</div>
      <nav class="nav-links">${links}</nav>
      <div class="nav-right">${right}</div>
    </div>
  `;

  bar.querySelectorAll("[data-nav]").forEach((el) =>
    el.addEventListener("click", () => navigate(el.getAttribute("data-nav")))
  );

  const logoutBtn = document.getElementById("nav-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      const refresh = store.getRefresh();
      try {
        if (refresh) await http.post(EP.logout, { refresh });
      } catch {
        /* baribir chiqamiz */
      }
      store.clear();
      toast("Tizimdan chiqdingiz.");
      navigate("/");
    });
  }
}

function escapeName(user) {
  if (!user) return "Profil";
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  return name || user.email || user.phone_number || "Profil";
}

document.addEventListener("route:rendered", renderNav);
