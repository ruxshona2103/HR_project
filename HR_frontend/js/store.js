const K_ACCESS = "ishga_access";
const K_REFRESH = "ishga_refresh";
const K_USER = "ishga_user";

export const store = {
  getAccess: () => localStorage.getItem(K_ACCESS),
  getRefresh: () => localStorage.getItem(K_REFRESH),
  getUser: () => {
    const raw = localStorage.getItem(K_USER);
    return raw ? JSON.parse(raw) : null;
  },
  setSession({ access, refresh, user }) {
    if (access) localStorage.setItem(K_ACCESS, access);
    if (refresh) localStorage.setItem(K_REFRESH, refresh);
    if (user) localStorage.setItem(K_USER, JSON.stringify(user));
  },
  setUser(user) {
    localStorage.setItem(K_USER, JSON.stringify(user));
  },
  setAccess(access) {
    localStorage.setItem(K_ACCESS, access);
  },
  clear() {
    localStorage.removeItem(K_ACCESS);
    localStorage.removeItem(K_REFRESH);
    localStorage.removeItem(K_USER);
  },
  isAuthed() {
    return !!store.getAccess();
  },
  // Backend `user_type`: 'candidate' | 'organization'
  role() {
    const u = store.getUser();
    return u ? u.user_type : null;
  },
};
