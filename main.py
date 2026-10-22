#!/usr/bin/env python3
"""Main entry point. Outside .venv, bootstrap via run.sh unless explicitly disabled."""
import os
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VENV=ROOT/'.venv'

def main():
    if not (VENV/'pyvenv.cfg').exists() or Path(sys.prefix).resolve()!=VENV.resolve():
        if os.environ.get('UIU_BOOTSTRAP_ACTIVE')=='1':
            raise SystemExit('Virtual-environment bootstrap failed. Run ./run.sh for diagnostics.')
        env=os.environ.copy();env['UIU_BOOTSTRAP_ACTIVE']='1'
        raise SystemExit(subprocess.call(['bash',str(ROOT/'run.sh')],env=env,cwd=ROOT))
    try:
        from PySide6.QtWidgets import QApplication
        from uiu.gui import MainWindow,STYLE
    except ImportError as e:
        raise SystemExit(f'Missing Python dependency: {e}. Run ./run.sh to install requirements.')
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setStyleSheet(STYLE)
    window=MainWindow();window.show()
    return app.exec()

if __name__=='__main__':sys.exit(main())
