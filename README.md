# किसानमंडी / KisanMandi — Front-end Prototype

A mobile-first, bilingual (Hindi / English) front-end for a farmer procurement
("mandi") booking system: login, dashboard, slot booking, live queue status,
and booking tracking. Built as **plain HTML/CSS/JS** — no build step, no
dependencies, no external network calls (fonts/icons are system fonts and
inline SVG so it also works fully offline).

## File manifest

```
kisanmandi/
├── index.html          Page 1 — Login (mobile number + Send OTP, hardcoded demo account)
├── home.html            Page 2 — Home / Dashboard (nearest center + 4 action cards)
├── book-slot.html        Page 3 — Book Slot (stepper, center, date chips, time slots)
├── queue-status.html     Page 4 — Queue Live Status (token, ETA, progress bar)
├── tracking.html          Page 5 — Booking Tracking (step progress + details box)
├── css/
│   └── style.css         Shared, modular, mobile-first stylesheet (CSS variables/tokens)
├── js/
│   └── app.js             Shared logic: state (localStorage), auth guard, nav, toast
├── data/
│   ├── bookings.json      Example booking / tracking record
│   └── queue.json         Example queue + slot + date data
└── README.md              This file
```

Each screen from the reference design is its own routable HTML file (not one
long scrolling image), matching the required 1:1 page structure:

| # | Page | File |
|---|------|------|
| 1 | Login | `index.html` |
| 2 | Home / Dashboard | `home.html` |
| 3 | Book Slot | `book-slot.html` |
| 4 | Queue Status | `queue-status.html` |
| 5 | Booking Tracking / Status | `tracking.html` |

## How to preview locally

No build tools or installs are required.

**Option A — just open it**
Double-click `index.html` (or drag it into a browser window).

**Option B — local static server (recommended, avoids any `file://` quirks)**

```bash
cd kisanmandi
# Python 3
python3 -m http.server 8000
# then open http://localhost:8000 in your browser
```

or with Node:

```bash
npx serve .
```

## Demo / hardcoded account

To let you skip real OTP delivery while testing:

- **Mobile:** `98765 43210`
- **OTP:** `1234`
- Or just tap **"डेमो के रूप में लॉगिन करें / Continue with demo account"** on the login page.

Any other 10-digit number also works with OTP `1234` (this is a front-end
demo — there is no real backend or SMS sending).

## Navigation flow

```
Login (index.html)
   └── Send OTP → Verify → Home (home.html)
                              ├── Book Slot (book-slot.html)
                              │      └── Confirm Booking → Queue Status (queue-status.html)
                              ├── View Queue (queue-status.html)
                              ├── Track Status (tracking.html)
                              └── Call Help (tel: link)
```

A persistent **bottom navigation bar** (Home · Bookings · Queue · Status) is
present on every page after login, so any screen is reachable in one tap.
Inner pages also have a **back button** in the header.

## Interaction notes (what's "live" in this demo)

- Login: input validation, fake OTP send/verify, and the hardcoded demo
  account button. Successful login stores a small state object.
- Home: nearest-center card and 4 action cards are real links to the other
  pages; language chip is a toast-only demo toggle.
- Book Slot: step indicator (1 Center → 2 Time → 3 Done), date chips and
  time-slot buttons are selectable (full slots are disabled), "Confirm
  Booking" saves the selection and routes to Queue Status.
- Queue Status: shows your token vs. the currently-serving token, an ETA
  chip, and a progress bar; "Refresh Status" simulates the counter moving
  forward.
- Booking Tracking: 4-step vertical progress list (Slot Booked → In Queue →
  Under Process → Completed) plus a booking-details summary box.

State (logged-in user, current booking, queue numbers) is kept in
`localStorage` under the key `kisanmandi_state_v1` purely so the demo feels
continuous across pages/reloads — there is no real backend. `data/*.json`
shows the shape a real API response could take if you wire this up to one.

## Accessibility

- Semantic landmarks: `<header>`, `<main>`, `<nav>`, `<ol>` for the tracking
  steps.
- All icons are `aria-hidden`; interactive controls have accessible names
  (`aria-label`, visible text, or both).
- Visible focus ring on every interactive element (`:focus-visible`).
- Live regions: OTP/field errors use `role="alert"`; toasts and the
  queue banner use `role="status"`; the progress bar uses
  `role="progressbar"` with `aria-valuenow`.
- Color contrast follows the reference palette's dark-green-on-light-green
  and dark-text-on-white pairings, which meet WCAG AA for body text.
- `prefers-reduced-motion` is respected (transitions disabled).

## Customizing

- **Colors / spacing / radii**: all defined as CSS custom properties at the
  top of `css/style.css` (`:root { ... }`) — change once, applies everywhere.
- **Copy / bilingual labels**: edit directly in each page's HTML; Hindi and
  English labels are kept as separate `.hi` / `.en` elements so you can
  restyle or reorder them independently.
- **Real backend**: replace the `localStorage`-backed functions in
  `js/app.js` (`getState`, `setState`) with `fetch()` calls to your API,
  and swap `data/*.json` for live responses in the same shape.

## Browser support

Modern evergreen browsers (Chrome, Edge, Safari, Firefox), including mobile
Safari/Chrome. Uses only standard CSS (custom properties, grid, flexbox) and
vanilla JS (no transpilation needed).
