#!/bin/bash
# cPanel deploy script - runs as a single shell process so variables persist
# correctly throughout (unlike separate .cpanel.yml task lines, which each
# run in isolation and do NOT share exported variables between them).
set -e

# --- EDIT THESE TWO VALUES ONCE, after the one-time cPanel setup in DEPLOY.md ---
CPANEL_USERNAME="sccmvt58"
PYTHON_VERSION="3.10"
# --- Nothing below this line needs editing ---

APP_ROOT="/home/$CPANEL_USERNAME/repositories/gymtrack"
VENV="/home/$CPANEL_USERNAME/virtualenv/repositories/gymtrack/$PYTHON_VERSION/bin/activate"

source "$VENV"
cd "$APP_ROOT"

pip install -r requirements.txt

# Passenger watches app_root/tmp/restart.txt - touching it bounces the app
# so the newly-pulled code + deps actually take effect.
mkdir -p tmp
touch tmp/restart.txt

echo "Deploy complete: dependencies installed, Passenger restart triggered."
