/* =========================================================
   KisanMandi — shared app logic
   Minimal vanilla JS: page-to-page navigation, a couple of
   demo interactions (OTP, slot picking, queue refresh), and
   a tiny "database" in localStorage so the flow feels real.
   No frameworks, no build step.
   ========================================================= */

const KM = (() => {
  const STORAGE_KEY = "kisanmandi_state_v1";

  /** Demo/hardcoded account used to skip real OTP delivery. */
  const DEMO_ACCOUNT = {
    phone: "9876543210",
    otp: "1234",
    name: "रमेश जी",
    nameEn: "Ramesh Ji",
  };

  const defaultState = {
    loggedIn: false,
    user: null,
    booking: {
      center: "हापुड़ मंडी - केंद्र अ",
      centerEn: "Hapur Mandi - Center A",
      date: "15 Oct",
      dateLabel: "आज / Today",
      slotHi: "सुबह ८ - १० बजे",
      slotEn: "Morning (8:00 AM - 10:00 AM)",
      crop: "गेहूं / Wheat",
      bookedAt: "15 Oct, 08:30 AM",
    },
    queue: {
      myToken: 47,
      servingToken: 42,
      etaMinutes: 25,
    },
  };

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return structuredClone(defaultState);
      return { ...structuredClone(defaultState), ...JSON.parse(raw) };
    } catch (e) {
      return structuredClone(defaultState);
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* localStorage unavailable — demo still works in-memory for this page load */
    }
  }

  let state = loadState();

  function getState() {
    return state;
  }
  function setState(patch) {
    state = { ...state, ...patch };
    saveState(state);
  }

  /* ---------- Toast helper ---------- */
  function toast(message) {
    let el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("show"), 2200);
  }

  /* ---------- Bottom nav active state ---------- */
  function markActiveNav() {
    const page = document.body.dataset.page;
    document.querySelectorAll(".nav-item[data-nav]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.nav === page);
      btn.setAttribute(
        "aria-current",
        btn.dataset.nav === page ? "page" : "false"
      );
    });
  }

  /* ---------- Route guard: bounce to login if not authenticated ---------- */
  function requireAuth() {
    if (!getState().loggedIn && document.body.dataset.page !== "login") {
      window.location.href = "index.html";
    }
  }

  function init() {
    markActiveNav();
    document.querySelectorAll(".nav-item[data-nav]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.href;
        if (target) window.location.href = target;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", init);

  return {
    DEMO_ACCOUNT,
    getState,
    setState,
    toast,
    requireAuth,
  };
})();
