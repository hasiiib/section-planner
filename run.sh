#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || fail 'Python 3 is missing. Install python3 using Linux Mint Software Manager.'
command -v bash >/dev/null 2>&1 || fail 'bash is missing.'
python3 -c 'import venv,ensurepip,ssl' 2>/dev/null || fail 'Python venv/ensurepip/SSL unavailable. Install python3-venv and python3-pip using Software Manager.'
if [[ ! -f .venv/pyvenv.cfg ]]; then
    echo 'Creating private Python environment…'
    python3 -m venv .venv || fail 'Could not create .venv. Check available disk space and python3-venv.'
fi
[[ -x .venv/bin/python ]] || fail 'Virtual environment is incomplete. Remove .venv and rerun.'
if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    .venv/bin/python -m ensurepip --upgrade || fail 'pip bootstrap failed inside .venv.'
fi
echo 'Installing/verifying project dependencies in .venv…'
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt || fail 'Dependency installation failed. Check internet connectivity and pip error above.'
echo 'Starting UIU Smart Course Routine Generator…'
exec .venv/bin/python main.py "$@"
