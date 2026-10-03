#!/bin/bash
# Double-click this file on the Mac to start the app. (Runs from this folder, uses the project's .venv.)
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "First-time setup..."
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
fi
export STOCK_APP_SAVE=1   # local mode: remember the paper-trading account between runs
.venv/bin/streamlit run app.py
