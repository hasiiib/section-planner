# Contributing to Section Planner

Thanks for helping improve Section Planner for United International University (UIU) students.

## Reporting a problem

When reporting an issue, include:
- The page or feature involved (course search, faculty preferences, routine generation, comparison, export).
- The selected course codes and sections, if relevant.
- What you expected and what happened instead.
- Browser/device information and steps to reproduce.

**Please do not post personal credentials, student IDs, or private information.**

## Suggesting a feature

Explain what you want to achieve, why it would help with UIU section selection, and how it should behave when a routine is impossible.

## Updating course offerings

The currently published catalog is for UIU Fall 2026. New course data must be verified against the applicable official offering document. Never guess missing course titles, sections, faculty, rooms, credits, or meeting times.

The live Cloudflare Pages edition uses `cloudflare/offerings.json`. Any related source dataset update should stay consistent with `offering_data.json` where appropriate. Preserve program, course code, section, all meeting days, and exact start/end minutes.

## Working on the website

The current public version is in `cloudflare/`, not the legacy FastAPI folders.

- `cloudflare/app.js` — UI, filtering, timetable, and exports
- `cloudflare/scheduler-worker.js` — conflict-free routine generation
- `cloudflare/style.css` — design and layout
- `cloudflare/index.html` — page structure

You can serve the `cloudflare/` directory with a local static file server for manual testing. Be sure to verify that back-to-back classes do not conflict, overlapping classes are rejected, every meeting is retained, faculty fallback reports its limits, and timetable exports represent the same routine.

## Pull requests

Keep each change focused, describe why it is useful, and mention what was tested. Do not claim a feature is tested unless you actually ran the checks.

This is an independent student project and is not affiliated with UIU's official registration system.
