# Cloudflare Pages — Section Planner

**Live website:** https://section-planner.pages.dev/

This folder contains the **static, browser-only edition** of Section Planner for United International University.

- No Render/Koyeb server, Python environment, paid API, or Cloudflare Worker is required.
- The Fall 2026 offering dataset is in `offerings.json`.
- Exhaustive scheduling runs in `scheduler-worker.js` in the visitor's browser.
- Faculty preferences, days filters, comparison and CSV/PDF/PNG/XLSX exports are included.
- Weekly routines use a day-by-time timetable: class blocks line up against time columns. View/compare/PNG/PDF share this layout; XLSX/CSV use a compatible day-by-time grid.
- Days without classes use compact rows. Routine exports also include structured **JSON** and recurring **ICS** calendar files. JSON is not directly importable by Google Calendar; select ICS and enter the real first and last class dates to import weekly events in the Asia/Dhaka timezone.
- Export libraries load from jsDelivr CDN, so downloading PDF, PNG and Excel requires access to those external scripts. CSV does not.
- This folder is isolated from the existing FastAPI website, which is left intact.

## Deploy via GitHub

1. Open https://dash.cloudflare.com/ and select **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Authorize the GitHub repository **hasiiib/section-planner** (it can be private).
3. Choose production branch **main**.
4. Select **no framework** and leave **Build command** empty.
5. Set **Build output directory** to `cloudflare` and leave root directory at the repo root.
6. Click **Save and Deploy**. The project is live at **https://section-planner.pages.dev/**. Visit it to test.

Cloudflare can redeploy automatically after pushes to `main`. No credit card or Python hosting server is involved in this static edition.

## Verify before sharing

1. Open the new `pages.dev` URL and click START; verify the preloaded courses appear.
2. Generate a small routine and verify there are no overlapping times, including multi-meeting sections.
3. Try Preferred Faculty Only, 1–5-day filters and morning/noon sorting.
4. Compare routines and try each export format.
5. Test on your phone and with a few selected courses before sharing widely.

**Notes:** Very large combinations use the visitor's CPU and memory and can take time. Cancel stops the browser worker; no generation results are silently described as complete. There is currently no user account or persistent saved-routine storage. If the CDN is blocked, PDF/PNG/XLSX export buttons report that their library could not load. This independent project is not an official UIU registration system.
