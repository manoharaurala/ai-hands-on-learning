#!/usr/bin/env bash
# Setup — Future with Shivank AI Agents masterclass (macOS/Linux).  Run from this folder:   ./setup.sh
set -e

echo "==> Checking Python version (need 3.10+)"
python3 -c 'import sys; assert sys.version_info >= (3,10), "Need Python 3.10 or higher"'
python3 --version

echo "==> Creating virtual environment at /tmp/ruby-ai-agents-venv"
VENV_DIR="${VENV_DIR:-/tmp/ruby-ai-agents-venv}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "==> Upgrading pip"
python3 -m pip install --upgrade pip --quiet

echo "==> Installing packages (takes a couple of minutes)"
python3 -m pip install -r requirements.txt

echo "==> Setting region for this session"
export AWS_DEFAULT_REGION=us-east-1

echo ""
echo "=================================================================="
echo " Packages installed."
echo ""
echo " NEXT: make sure your AWS credentials are set, then run the check:"
echo ""
echo "   source $VENV_DIR/bin/activate"
echo "   export AWS_DEFAULT_REGION=us-east-1"
echo "   python3 00_check_setup.py"
echo "=================================================================="
