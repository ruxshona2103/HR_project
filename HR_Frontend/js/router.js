const routes = [];
let notFoundHandler = () => `<div class="container section"><div class="state-box"><b>404</b>Sahifa topilmadi.</div></div>`;

export function route(pattern, handler, guard = null) {
  const paramNames = [];
  const regex = new RegExp(
    "^" +
      pattern.replace(/:[a-zA-Z]+/g, (m) => {
        paramNames.push(m.slice(1));
        return "([^/]+)";
      }) +
      "$"
  );
  routes.push({ regex, paramNames, handler, guard });
}

export function setNotFound(handler) {
  notFoundHandler = handler;
}

export function navigate(path) {
  location.hash = path.startsWith("#") ? path : `#${path}`;
}

async function render() {
  const app = document.getElementById("app");
  const raw = location.hash.slice(1) || "/";
  const [path] = raw.split("?");
  const query = Object.fromEntries(new URLSearchParams(raw.split("?")[1] || ""));

  for (const r of routes) {
    const m = path.match(r.regex);
    if (m) {
      const params = {};
      r.paramNames.forEach((name, i) => (params[name] = decodeURIComponent(m[i + 1])));
      if (r.guard) {
        const redirect = r.guard(params, query);
        if (redirect) {
          navigate(redirect);
          return;
        }
      }
      app.innerHTML = loadingHtml();
      try {
        const result = await r.handler(params, query);
        if (typeof result === "string") {
          app.innerHTML = result;
        } else if (result && typeof result === "object") {
          app.innerHTML = result.html;
          if (typeof result.mount === "function") result.mount(app);
        }
      } catch (e) {
        app.innerHTML = `<div class="container section"><div class="state-box"><b>Xatolik</b>${escapeHtml(
          e.message || String(e)
        )}</div></div>`;
      }
      window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
      document.dispatchEvent(new CustomEvent("route:rendered", { detail: { path } }));
      return;
    }
  }
  app.innerHTML = notFoundHandler();
}

function loadingHtml() {
  return `<div class="container section text-center"><span class="spinner"></span></div>`;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
export function startRouter() {
  render();
}
