import { esc } from "./components.js";

// field: { name, label, type: 'text'|'textarea'|'date'|'number'|'checkbox'|'url'|'email', required, hint, step }
export function renderFields(fields, values = {}) {
  return fields
    .map((f) => {
      const v = values[f.name] ?? "";
      if (f.type === "checkbox") {
        return `
        <div class="checkbox-row" style="margin-bottom:14px">
          <input type="checkbox" id="f-${f.name}" name="${f.name}" ${v ? "checked" : ""}/>
          <label for="f-${f.name}">${esc(f.label)}</label>
        </div>`;
      }
      if (f.type === "textarea") {
        return `<div class="field"><label>${esc(f.label)}${f.required ? " *" : ""}</label>
          <textarea name="${f.name}" ${f.required ? "required" : ""} placeholder="${esc(f.placeholder || "")}">${esc(v)}</textarea>
          ${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ""}
        </div>`;
      }
      if (f.type === "select") {
        return `<div class="field"><label>${esc(f.label)}${f.required ? " *" : ""}</label>
          <select name="${f.name}" ${f.required ? "required" : ""}>
            <option value="">${esc(f.placeholder || "— tanlang —")}</option>
            ${f.options
              .map((o) => `<option value="${esc(o.value)}" ${String(v) === String(o.value) ? "selected" : ""}>${esc(o.label)}</option>`)
              .join("")}
          </select>
          ${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ""}
        </div>`;
      }
      const type = f.type === "url" || f.type === "email" ? f.type : f.type === "date" ? "date" : f.type === "number" ? "number" : "text";
      return `<div class="field"><label>${esc(f.label)}${f.required ? " *" : ""}</label>
        <input type="${type}" name="${f.name}" value="${esc(v)}" ${f.required ? "required" : ""} ${f.step ? `step="${f.step}"` : ""} placeholder="${esc(f.placeholder || "")}" />
        ${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ""}
      </div>`;
    })
    .join("");
}

export function collectFormData(form, fields) {
  const fd = new FormData(form);
  const out = {};
  for (const f of fields) {
    if (f.type === "checkbox") {
      out[f.name] = form.querySelector(`[name="${f.name}"]`).checked;
      continue;
    }
    const raw = fd.get(f.name);
    // Bo'sh qiymatni umuman yubormaymiz — backendda ba'zi maydonlar (masalan
    // Vacancy.status, Vacancy.daily_hours) `blank=True` emas, shuning uchun
    // bo'sh string yoki `null` yuborilsa 400 xatolik beradi. Kalitni tashlab
    // ketish backenddagi standart qiymat ishlatilishiga imkon beradi.
    if (raw === "" || raw === null) continue;
    out[f.name] = raw;
  }
  return out;
}
