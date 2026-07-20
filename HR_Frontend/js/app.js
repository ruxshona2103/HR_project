import { route, startRouter, setNotFound } from "./router.js";
import { store } from "./store.js";
import { initFab } from "./fab.js";
import "./nav.js";

import { renderLanding } from "./pages/landing.js";
import { renderRolePicker, renderLogin, renderRegister, renderVerify, renderPhoneAuth } from "./pages/auth.js";
import { renderVacancies } from "./pages/vacancies.js";
import {
  renderCandidateHome,
  renderCandidateResume,
  renderCandidateAiCheck,
  renderCandidateInterview,
} from "./pages/candidate.js";
import {
  renderEmployerHome,
  renderEmployerProfile,
  renderEmployerVacancies,
  renderEmployerQuestions,
} from "./pages/employer.js";
import { renderSettings, renderApiSettings } from "./pages/settings.js";

const guestOnly = () => (store.isAuthed() ? (store.role() === "organization" ? "/employer" : "/candidate") : null);
const candidateOnly = () => {
  if (!store.isAuthed()) return "/login";
  if (store.role() === "organization") return "/employer";
  return null;
};
const employerOnly = () => {
  if (!store.isAuthed()) return "/login";
  if (store.role() !== "organization") return "/candidate";
  return null;
};

// Public
route("/", renderLanding);
route("/vacancies", renderVacancies, () => (store.isAuthed() ? null : "/login"));

// Auth
route("/login", renderRolePicker, guestOnly);
route("/login/candidate", () => renderLogin("candidate"), guestOnly);
route("/login/organization", () => renderLogin("organization"), guestOnly);
route("/register/:kind", (p) => renderRegister(p.kind), guestOnly);
route("/verify", renderVerify, guestOnly);
route("/phone-auth", renderPhoneAuth, guestOnly);

// Candidate
route("/candidate", renderCandidateHome, candidateOnly);
route("/candidate/resume", renderCandidateResume, candidateOnly);
route("/candidate/ai-check", renderCandidateAiCheck, candidateOnly);
route("/candidate/interview/:id", renderCandidateInterview, candidateOnly);

// Employer
route("/employer", renderEmployerHome, employerOnly);
route("/employer/profile", renderEmployerProfile, employerOnly);
route("/employer/vacancies", renderEmployerVacancies, employerOnly);
route("/employer/questions", renderEmployerQuestions, employerOnly);

// Settings
route("/settings", renderSettings, () => (store.isAuthed() ? null : "/login"));
route("/settings/api", renderApiSettings);

setNotFound(
  () => `<div class="container section text-center"><div class="state-box"><b>404</b>Bunday sahifa mavjud emas.</div></div>`
);

startRouter();
initFab();
