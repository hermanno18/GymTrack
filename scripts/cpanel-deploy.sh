#!/bin/bash
# cPanel deploy script - runs as a single shell process so variables persist
# correctly throughout (unlike separate .cpanel.yml task lines, which each
# run in isolation and do NOT share exported variables between them).
set -e

# --- EDIT THESE VALUES ONCE, matching whatever Setup Python App actually shows ---
CPANEL_USERNAME="sccmvt58"
PYTHON_VERSION="3.10"            # CONFIRM via File Manager: check the folder name
                                   # under /home/sccmvt58/virtualenv/repositories/gymtrack/
                                   # -- it may be "3.10" or "3.10.21", use whatever's there.
# Application root in cPanel is "repositories/gymtrack" (NOT just "gymtrack") --
# both APP_ROOT and VENV below must mirror that exact relative path, or this
# script silently fails at the cd/source step and never installs deps or
# restarts Passenger.
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
