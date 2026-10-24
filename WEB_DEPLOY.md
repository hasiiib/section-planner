# Section Planner — Deployment and maintenance

**Production site:** https://section-planner.onrender.com/

The active deployment is a **Python FastAPI website** serving a browser UI. It is currently configured for United International University (UIU) and preloads the Fall 2026 BSCSE/BSDS offering catalog. **Visitors do not upload course PDFs.**

## Hosting on Render

1. Keep this GitHub repository private if you don't want the server-side Python code publicly browsable.
2. In [Render](https://dashboard.render.com/), connect the repository and choose **New → Blueprint**.
3. Use the root `render.yaml` configuration. It specifies:
   - Python web service named `section-planner`
   - `pip install -r web-requirements.txt`
   - `uvicorn webapp:app --host 0.0.0.0 --port $PORT`
   - health endpoint `/api/health`
4. Deploy the latest `main` commit. Open the service URL when its state is **Live**.
5. Confirm that START loads courses and that generation, filtering, comparison and exports work.

If a commit doesn't trigger auto-deployment, choose **Manual Deploy → Deploy latest commit** in the web service. Render free-plan limits, cold starts, build failures and server resource exhaustion can affect availability.

## What gets deployed

Render uses `webapp.py`, `web_static/`, `offering_data.json`, `uiu/`, and `web-requirements.txt`.

The repository retains an older optional PySide6 desktop edition (`main.py`, `run.sh`, `requirements.txt`). **It is not part of the Render launch path.** Do not delete shared `uiu/` modules, since the website depends on them.

## Managing course offerings

`offering_data.json` contains the preprocessed source course sections. When new UIU offerings arrive:

1. Obtain the official offering sheet.
2. Parse and review course codes, sections, faculty, credits, each meeting day and each time range; manually check ambiguous clipped fields against the original.
3. Keep the existing catalog as a backup before merging.
4. Merge unique offerings carefully using **trimester + program + course code + section**. Preserve valid existing entries unless replacing an updated entry for the same identifier.
5. Verify that the intended programs and courses show up, including faculty preference options, then commit the updated dataset and redeploy.

The website currently has **one active bundled dataset** rather than an admin login or multi-term database. The self-service admin offering manager has *not* been implemented. Avoid uploading user-submitted files to the public server without building proper access control and durable storage.

## Local smoke test

With Python 3:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r web-requirements.txt
.venv/bin/python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/api/health` (should return a JSON OK status), then open `http://127.0.0.1:8000/`.

### Suggested checks after each update

- START displays preloaded BSCSE/BSDS courses without requiring a file.
- Multiple selected courses retain their available sections and optional preferred faculty names.
- All displayed routines are conflict-free; back-to-back classes are allowed.
- Preferred-only falls back to maximum match when no exact match exists and its popup can be closed.
- Results offer 1–5 class-day filters and morning/noon sorting.
- PDF, PNG, XLSX and CSV outputs include course credits.
- Directly compare the offering details with official UIU records before section selection.

## Privacy and limitations

This is an independent student-made planner, not an official UIU registration service. A private GitHub repository protects server source from casual browsing, but shipped browser JavaScript and HTML are inherently accessible to visitors. It does not support student logins, saved cloud routines or seat-availability verification. No deployed code can guarantee perfect matching of faculty assignments that may change after publication.

**Maintainer:** Ayon.
