const API_BASE = '/api';

const App = {
  getLang() {
    return localStorage.getItem('km_lang') || 'en';
  },
  toggleLang() {
    const next = this.getLang() === 'hi' ? 'en' : 'hi';
    localStorage.setItem('km_lang', next);
    this.applyLang();
  },
  applyLang() {
    const lang = this.getLang();
    document.querySelectorAll('.hi').forEach(el => el.style.display = lang === 'hi' ? 'inline' : 'none');
    document.querySelectorAll('.en').forEach(el => el.style.display = lang === 'en' ? 'inline' : 'none');
    const btn = document.getElementById('langToggleBtn');
    if (btn) btn.innerText = lang === 'hi' ? 'English' : 'हिंदी';
  },
  getUser() {
    const u = localStorage.getItem('km_user');
    return u ? JSON.parse(u) : null;
  },
  setUser(user) {
    localStorage.setItem('km_user', JSON.stringify(user));
  },
  showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
  },
  initAuthGuard(isLoginPage = false) {
    const user = this.getUser();
    if (!user && !isLoginPage) {
      window.location.href = 'index.html';
    } else if (user && isLoginPage) {
      window.location.href = 'home.html';
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.applyLang();
});
