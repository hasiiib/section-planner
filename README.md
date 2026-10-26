# Section Planner

**A smarter way to plan classes at United International University (UIU).**

[**Try Section Planner →**](https://section-planner.pages.dev/)

Section Planner is a student-built course routine generator for UIU. Choose courses, explore available sections, and find conflict-free weekly timetables without comparing every combination manually.

> **Current catalog:** United International University — Fall 2026 BSCSE and BSDS course offerings. This is an independent student project, **not** an official UIU registration service. Double-check final section availability, faculty, rooms, and timings with UIU before registering.

## Features

- **Preloaded course catalog** — search by course code or title; select courses from available programs.
- **Conflict-free scheduling** — generate feasible section combinations using every meeting's actual weekday and start/end time. Back-to-back classes are allowed.
- **Faculty preferences** — select one or more preferred instructors per course. If not all preferences can be met, see routines with the maximum achievable matches and a dismissible popup explaining identifiable overlaps.
- **Class-day filters** — filter for **1–5 days** per week.
- **Morning / Noon sorting** — prioritize routines with more classes in the chosen period; classes are not required to *all* fall within it.
- **Weekly timetable** — days down the side, class periods across the top, and positioned class cards showing course code, section, title, room, faculty, and meeting time. Empty days stay compact.
- **Real UIU time markers** — **8:30 AM, 9:51 AM, 11:11 AM, 12:31 PM, 1:51 PM, 3:11 PM, 4:30 PM**. Classes with exceptional start times are still positioned at their actual times.
- **Routine comparison** — compare different timetables.
- **Six export formats** — **PDF, PNG, XLSX, CSV, JSON, and ICS**. ICS supports recurring events for calendar applications, including Google Calendar; enter actual trimester start/end dates when exporting.
- **Conditional sections** — *If Required* sections are considered only if no complete regular-only routine is available.

Generation does not impose an arbitrary top-five results limit. Very large combinations may take significant time and memory in the browser; cancelling generation does not mean enumeration completed.

## Getting started

1. Visit **https://section-planner.pages.dev/** and select **START**.
2. Search for and add your courses.
3. Optionally select preferred faculty.
4. Generate conflict-free routines.
5. Filter, compare, and export a routine.

## How it's hosted

**The current live edition runs on Cloudflare Pages.** It is a static site: the catalog is preloaded, and schedule generation runs locally in the visitor's browser using a Web Worker. No hosted Python backend, file upload, or account is needed for routine generation.

| Path | Purpose |
| --- | --- |
| `cloudflare/index.html`, `cloudflare/style.css`, `cloudflare/app.js` | Live website UI and client-side exports |
| `cloudflare/scheduler-worker.js` | Browser-based exhaustive routine generation |
| `cloudflare/offerings.json` | Published Fall 2026 UIU course offerings |
| `cloudflare/README.md` | Cloudflare Pages deployment guide |
| `webapp.py`, `web_static/`, `uiu/` | Retained earlier Python/FastAPI implementation and shared tooling |
| `offering_data.json` | Original bundled processed offerings |
| `WEB_DEPLOY.md`, `render.yaml` | Legacy server deployment reference |

### Deploy your own Cloudflare Pages copy

Connect this repository to **Cloudflare Pages** and set:

- Production branch: `main`
- Framework preset: None
- Build command: *(empty)*
- Build output directory: `cloudflare`

See the [Cloudflare deployment instructions](cloudflare/README.md). The legacy FastAPI version is kept in the repository for reference; it is **not** required to run the Cloudflare Pages site.

### Data and limitations

- The current catalog is specifically for **UIU Fall 2026 BSCSE and BSDS**. Support for other trimesters or programs requires verified offering data.
- Class details may change; the planner cannot reserve sections, check remaining seats, or guarantee registration.
- Routine choices are held in the current browser session; no cloud-synced account or saved-routine database is provided.
- PDF, PNG, and XLSX browser exports load third-party libraries; they may require access to the library CDN.
- **JSON is a structured data export, not a Google Calendar import file.** For Google Calendar, export **ICS** and import it from Google Calendar settings.
- Exceptionally large schedules may exceed the browser's memory or processing capacity.

## Feedback

Found a bug or have a feature suggestion? Suggestions are welcome — the aim is to make UIU section selection a little easier.

**Made by Ayon**
