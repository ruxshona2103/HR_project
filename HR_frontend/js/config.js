// Backend Django loyihasining manzili.
// Standart: mahalliy ishlab chiqish serveri. Sozlamalar sahifasidan (#/settings/api)
// istalgan vaqtda o'zgartirish mumkin — qiymat localStorage'da saqlanadi.
const DEFAULT_API_BASE = "http://127.0.0.1:8000/api";

export function getApiBase() {
  return localStorage.getItem("ishga_api_base") || DEFAULT_API_BASE;
}

export function setApiBase(url) {
  localStorage.setItem("ishga_api_base", url.replace(/\/+$/, ""));
}

export function getWsBase() {
  const api = getApiBase();
  try {
    const u = new URL(api);
    const wsProto = u.protocol === "https:" ? "wss:" : "ws:";
    return `${wsProto}//${u.host}`;
  } catch {
    return "ws://127.0.0.1:8000";
  }
}

// Barcha API endpointlari — backenddagi urls.py fayllari bilan bir xil.
export const EP = {
  // Auth — email
  emailLogin: "/users/auth/email/login/",
  emailRegisterCandidate: "/users/auth/email/register/candidate/",
  emailRegisterOrg: "/users/auth/email/register/organization/",
  emailVerify: "/users/auth/email/verify/",
  emailResend: "/users/auth/email/resend-code/",
  // Auth — phone
  phoneRegisterCandidate: "/users/auth/phone/register/candidate/",
  phoneRegisterOrg: "/users/auth/phone/register/organization/",
  phoneLogin: "/users/auth/phone/login/",
  phoneVerifyOtp: "/users/auth/phone/verify-otp/",
  // Token / session
  tokenRefresh: "/users/auth/token/refresh/",
  logout: "/users/auth/logout/",
  // Profile
  me: "/users/me/",
  changePassword: "/users/change-password/",
  deleteAccount: "/users/delete-account/",
  botLink: "/users/auth/bot-link/",
  telegramConnect: "/users/telegram/connect/",
  telegramDisconnect: "/users/telegram/disconnect/",
  telegramStatus: "/users/telegram/status/",
  // Landing (public)
  landingData: "/landing_page/landing-data/",
  products: "/landing_page/products/",
  pricing: "/landing_page/pricing/",
  contacts: "/landing_page/contacts/",
  // Vacancies (candidate view)
  vacancies: "/vacancies/vacancies/",
  // Company profile / vacancies management / AI questions (employer)
  companyProfile: "/profile/company-profile/",
  companyProfileMe: "/profile/company-profile/me/",
  companyVacancies: "/profile/company-vacancies/",
  aiQuestions: "/profile/ai-questions/",
  // Resume builder
  resume: "/resume/",
  resumeSection: (section) => `/resume/sections/${section}/`,
  resumeSectionDetail: (section, pk) => `/resume/sections/${section}/${pk}/`,
  // AI engine
  aiResumeCheck: "/ai_interview/resume-check/",
  aiInterviewStart: (vacancyId) => `/ai_interview/start-interview/${vacancyId}/`,
};
