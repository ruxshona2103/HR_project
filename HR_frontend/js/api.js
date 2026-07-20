import { getApiBase, EP } from "./config.js";
import { store } from "./store.js";

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

// Backend serializerlari ko'pincha {"field": ["xato matni"]} yoki
// {"error": "..."} / {"detail": "..."} / {"xato": "..."} ko'rinishida xato qaytaradi.
// Shularning barchasini odam o'qiy oladigan bitta matnga aylantiramiz.
function flattenErrors(data) {
  if (!data) return "Noma'lum xatolik yuz berdi.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (data.error) return data.error;
  if (data.xato) return data.xato;
  if (data.message) return data.message;
  const parts = [];
  for (const [key, val] of Object.entries(data)) {
    const text = Array.isArray(val) ? val.join(" ") : String(val);
    parts.push(key === "error" || key === "non_field_errors" ? text : `${key}: ${text}`);
  }
  return parts.join(" | ") || "Noma'lum xatolik yuz berdi.";
}

let refreshPromise = null;

async function doRefresh() {
  const refresh = store.getRefresh();
  if (!refresh) throw new ApiError("Sessiya tugagan, qayta kiring.", 401, null);
  const res = await fetch(getApiBase() + EP.tokenRefresh, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    store.clear();
    throw new ApiError("Sessiya muddati tugadi, qaytadan kiring.", 401, null);
  }
  const data = await res.json();
  store.setAccess(data.access);
  return data.access;
}

/**
 * @param {string} path - EP dagi yo'l, masalan EP.me
 * @param {object} opts - { method, body, isForm, auth }
 */
export async function api(path, opts = {}) {
  const { method = "GET", body, isForm = false, auth = true, _retried = false } = opts;

  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";

  if (auth) {
    const token = store.getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(getApiBase() + path, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  });

  // Access token muddati tugagan bo'lsa — bir marta yangilab, so'rovni qaytaramiz.
  if (res.status === 401 && auth && !_retried && store.getRefresh()) {
    try {
      if (!refreshPromise) refreshPromise = doRefresh().finally(() => (refreshPromise = null));
      await refreshPromise;
      return api(path, { ...opts, _retried: true });
    } catch (e) {
      store.clear();
      location.hash = "#/login";
      throw e;
    }
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(flattenErrors(data), res.status, data);
  }
  return data;
}

export const http = {
  get: (path, opts) => api(path, { ...opts, method: "GET" }),
  post: (path, body, opts) => api(path, { ...opts, method: "POST", body }),
  put: (path, body, opts) => api(path, { ...opts, method: "PUT", body }),
  patch: (path, body, opts) => api(path, { ...opts, method: "PATCH", body }),
  del: (path, opts) => api(path, { ...opts, method: "DELETE" }),
};
