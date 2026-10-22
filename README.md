# Class Routine | UIU Smart Course Routine Generator

Native **PySide6** Linux Mint desktop application with local storage. The original UIU Fall 2026 offering PDF is bundled.

## Launch (Linux Mint)

Extract the ZIP, open a terminal in the extracted `UIU_Smart_Course_Routine_Generator` folder, and run:

```bash
./run.sh
```

The launcher creates `.venv`, installs Python dependencies **only inside that folder**, then starts the app. Internet is needed for first setup. No password, `sudo`, global pip, or browser server is involved. Alternative launch after setup:

```bash
.venv/bin/python main.py
```

If the launcher is not executable, use `bash run.sh`.

## Usage

1. **START** on the minimal welcome screen.
2. **Open File** accepts PDF, DOC/DOCX, XLS/XLSX or CSV course-offering files. A valid file must contain actual course-section records and weekday/time data. Invalid and unsupported files trigger a popup and do not advance. PDFs use UIU's position-aware extraction; structured files need column headers `Program, Course Code, Title, Section, Day1, Time1`, with optional Day2/Time2, rooms, faculty and credit. An old `.doc` needs locally installed LibreOffice for conversion; `.docx` imports directly. Click the warning icon to review parser warnings. Import automatically advances to course selection when valid.
3. **Select Courses**: filter `All` or any program actually found in the imported dataset. Search code/title; add distinct courses from multiple programs. Selected entries retain program, title and sections. Click **Generate Routines**. While processing, progress and Cancel appear; quick completions advance directly.
4. **Class Routines**: every valid assignment is available with one section per selected course. Routine cards load progressively on one scrollable page and are placed side by side when wide windows allow. Day column cells are vertically merged and centered. Hold **Ctrl + mouse wheel** to scale routine tables. Export any card via **Save / Export** (PDF, PNG, XLSX, CSV). Select multiple routine numbers with **Compare** to see them together.

Exports use the title **Class Routine** and matching Day / Class Period / Course Code / Course Title / Section / Faculty / Room columns. Excel and PDF provide merged days; CSV represents merges with a blank day on continuation rows. The PNG renderer visually centers day labels across their rows.

## Data and limitations

- Dataset and saved-routine records stay locally in `~/.local/share/uiu-smart-routines/routine.sqlite3`, or under `XDG_DATA_HOME` if configured.
- Importing a new dataset may replace an existing dataset **with the same name**. Existing saved routine records are retained.
- Missing faculty initials do not block import. `TBA` faculty values remain `TBA`. A class with only one full day/time pair is legitimate. A partially missing or malformed time slot is noted and never fabricated.
- When no trimester heading exists (non-PDF sources), the file name is used as the dataset name rather than inventing a trimester.
- The bundled 54-page PDF is a fixed-layout PDF; some original titles/faculty fields may physically overlap column edges. Import warnings can identify uncertain source fields. This importer follows the supplied document and does not infer missing values.
- Exhaustive enumeration can generate a **very large** number of assignments; the data is retained in memory until the session ends. Cancelling keeps partial results separate from completed runs and never labels them complete.
- Routine cards render incrementally to avoid showing thousands of table widgets at once. All routine choices remain accessible via **Show More Routines** or scrolling.
- Native PySide6 uses your Linux Mint system's graphical libraries. If you have a Qt/XCB system library error, install the missing package using Software Manager rather than running privileged scripts.

## Tests

```bash
.venv/bin/python -m pytest -q
```

The tests cover time overlap, exact-one-section scheduling, source PDF extraction, multiple meeting periods, generation completion, cancellation, dataset persistence, file type validation, CSV/Excel/Word imports and all four exports.

## Source files

`main.py` guards virtual-environment startup; `run.sh` bootstraps dependencies; `uiu/importers.py` reads the six formats; `uiu/parser.py` extracts PDF; `uiu/model.py` stores data objects; `uiu/scheduler.py` enumerates; `uiu/storage.py` persists datasets/routines; `uiu/gui.py` implements the desktop screens; `uiu/exports.py` renders exports; and `tests/` holds checks.
