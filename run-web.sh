#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo 'Python 3 is required.' >&2; exit 1; fi
if [ ! -f .venv/bin/python ]; then python3 -m venv .venv || { echo 'Install python3-venv via the system package manager, then retry.' >&2; exit 1; }; fi
.venv/bin/python -m pip install -r web-requirements.txt || { echo 'Package installation failed; check internet access and pip errors.' >&2; exit 1; }
exec .venv/bin/python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
