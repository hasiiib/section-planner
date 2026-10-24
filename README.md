# Section Planner

**A smarter way to plan classes at United International University (UIU).**

Section Planner helps UIU students explore course offerings and build conflict-free class routines without manually comparing dozens of sections.

**Live website:** https://section-planner.onrender.com/

> **Current coverage:** UIU Fall 2026 course offerings from the provided BSCSE / BSDS dataset. The catalog is preloaded: visitors do **not** need to upload a PDF. This is an independent student project, not an official UIU service. Course sections, faculty assignments and times may change; confirm details through official UIU channels before registration.

## Features

- **Preloaded UIU courses** — search by course code or title, filter by program, and pick courses.
- **Conflict-free routine generation** — one section per selected course; overlapping class times are rejected.
- **Optional faculty preferences** — prioritize routines matching chosen instructors. When all preferences cannot be met, show the highest achievable matches and describe identifiable overlaps.
- **Preferred Faculty Only** — show routines with the maximum available faculty matches when an exact match is impossible.
- **Class-day filters** — show routines with 1–5 class days per week; select multiple day counts.
- **Morning / Noon sorting** — rank schedules toward the chosen time of day; it does **not** require every class to fall in that period.
- **Compare and export** — compare routine tables and export PDF, PNG, XLSX or CSV, including course credits.
- **Conditional sections** — “If Required” sections are used only when regular sections cannot form a complete valid routine; availability must be confirmed by UIU.

The scheduler enumerates valid section combinations rather than imposing an arbitrary five-routine limit. Very large searches can take time; progress/cancellation and browser/server resource limits still apply.

## How to use

1. Open **https://section-planner.onrender.com/** and press **START**.
2. Search for courses, optionally filter by program, and add your courses.
3. If you want, select preferred faculty for individual courses.
4. Select **Generate Routines**.
5. Filter the results by class days or faculty matches, sort by Morning / Noon, compare routines and export your favorite option.

Faculty and time preferences affect ranking and filtering; they **never** make an overlapping class combination valid. Some preferred faculty combinations may be impossible.

## Technology

- **Frontend:** HTML, CSS and JavaScript (`web_static/`)
- **Backend:** Python, FastAPI (`webapp.py`)
- **Scheduling:** Python (`uiu/scheduler.py`)
- **Data:** bundled, preprocessed UIU Fall 2026 offerings (`offering_data.json`)
- **Hosting:** Render (`render.yaml`)

The source repository can stay private while the Render-hosted website is public.

## Run the website locally

Requires Python 3:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r web-requirements.txt
.venv/bin/python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Stop the server with Ctrl+C. The web app does not require PySide6 or a Linux desktop environment.

## Deploy and update the catalog

Render reads `render.yaml` from the repository root. Connect the private GitHub repository via **New → Blueprint**, then deploy. See [WEB_DEPLOY.md](WEB_DEPLOY.md) for setup and troubleshooting.

To add offerings for another program or trimester, prepare and validate new source data first; merge on **program + course code + section within the appropriate trimester**. Do not blindly replace the current CSE/DS offerings or guess clipped titles. The present website serves one preloaded catalog; multi-trimester administration and self-service publishing are not implemented.

## Project files

| Path | Purpose |
| --- | --- |
| `webapp.py` | Website and API |
| `web_static/` | Website interface |
| `offering_data.json` | Bundled course-section dataset |
| `uiu/` | Course models, scheduler, parsing and exports |
| `render.yaml` | Render deployment configuration |
| `web-requirements.txt` | Website dependencies |
| `tests/` | Automated tests |
| `main.py`, `run.sh`, `run-web.sh`, `requirements.txt` | Legacy/optional local launch tools; not required for Render hosting |

## Limitations and feedback

This is currently designed for **United International University** and uses the uploaded Fall 2026 offering data. It does not enroll students or verify seat availability. Routine results remain in the current browser session; there is no student account or cloud-saved routine library. A free Render instance may take time to wake after inactivity.

Found a bug or have a feature suggestion? Feedback is welcome. The goal is to make section selection less stressful for UIU students.

---

**Made by Ayon**
