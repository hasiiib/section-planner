# Section Planner: browser deployment

This repository contains **two editions**:

- `main.py` + `./run.sh`: original PySide6 Linux desktop application.
- `webapp.py` + `web_static/`: browser edition. The browser sends course-offering files and selected sections to a server. Python extraction, scheduling and exports run on the server, not in browser JavaScript.

The web edition keeps no uploaded files beyond temporary request processing. It does not currently provide accounts or persistent saved routines. Browser results exist only in the current page session. **Avoid uploading confidential course files to a public third-party server.**

## Recommended: deploy on Render from a PRIVATE GitHub repository

1. Create a **private** repository on https://github.com/new (choose **Private**). Do not upload your `.venv` directory or database files. Upload the **contents of this project folder**, including `render.yaml`, `webapp.py`, `web_static`, `uiu`, `web-requirements.txt`.
2. Open https://dashboard.render.com/ and connect GitHub.
3. Choose **New → Blueprint** and select the private repository. Render will read `render.yaml`. If the Blueprint option is unavailable, create **New → Web Service**, select the repo, set **Python** runtime, build command `pip install -r web-requirements.txt`, start command `uvicorn webapp:app --host 0.0.0.0 --port $PORT` and health check `/api/health`.
4. Deploy. After Render reports *Live*, open the generated `https://...onrender.com` URL.
5. Share that URL, **not** the GitHub repository URL. The repo can remain private while the deployed site is public.

Render free services may sleep after 15 minutes, take time to wake, and have usage limits. They are for experimentation, not production reliability. Source code on the server is not publicly downloaded by ordinary website visitors, but no public deployment can promise absolute protection of the frontend, API or security vulnerabilities. Use a paid service with monitoring and rate limiting for wider public use.

### Local website testing (Linux Mint)

```bash
cd UIU_Smart_Course_Routine_Generator
python3 -m venv .venv
.venv/bin/python -m pip install -r web-requirements.txt
.venv/bin/python -m uvicorn webapp:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in a browser. Stop with Ctrl+C. The `.doc` importer needs system LibreOffice; use `.docx` instead if it is unavailable. Other formats run with Python dependencies.

### Why not deploy the PySide6 window to Vercel?

Vercel serves websites and server-side functions, not interactive Qt desktop windows. A web version is necessary. This package includes the web edition. Vercel can run FastAPI, but per-request duration and resource limits are significant for exhaustive schedule enumeration. **Render is recommended first** because the service supports an always-running Python process while active. No arbitrary maximum of five routines is imposed; exceptionally large combinations can still exhaust a visitor's browser memory, data transfer or a hosting limit. Generation streams results as they are found, and Cancel aborts the browser request.

## Verify before sharing

- Import your Fall 2026 PDF and verify total records, program filter and warning details.
- Check a regular-only assignment and an impossible regular assignment to confirm If Required fallback.
- Generate and compare multiple routines, export PDF / PNG / XLSX / CSV.
- Verify on desktop and mobile browsers. The original PySide6 GUI is still available separately.

## Notes about source data

The original Fall 2026 PDF contains some course titles clipped at the source table's column boundary. The importer restores a longer title only when another record for the **same program and course** contains that text. Otherwise it retains a readable warning. It never guesses the missing remainder of a course title. Faculty initials are optional. Sections explicitly marked **If Required** are considered only when regular sections cannot produce any complete valid routine. TBA instructors remain TBA.
