#!/bin/bash
# WeReadSync — One-click setup script

set -e

echo "============================================"
echo "  WRS001 — WeReadSync Setup"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required. Install from https://python.org"
    exit 1
fi
echo "[OK] Python $(python3 --version)"

# Install dependencies
echo "[*] Installing requests..."
pip3 install requests --quiet 2>/dev/null || pip install requests --quiet
echo "[OK] Dependencies installed"

# Setup config
if [ ! -f config/.env ]; then
    echo ""
    echo "============================================"
    echo "  API Key Setup"
    echo "============================================"
    echo ""
    echo "  Get your API Key from:"
    echo "  https://weread.qq.com/r/weread-skills"
    echo ""
    read -p "  Paste your API Key (wrk-...): " API_KEY
    if [ -n "$API_KEY" ] && [[ "$API_KEY" == wrk-* ]]; then
        echo "WEREAD_API_KEY=$API_KEY" > config/.env
        chmod 600 config/.env
        echo "  [OK] API Key saved to config/.env"
    else
        cp config/.env.example config/.env
        echo "  [!] Invalid key format. Edit config/.env manually."
    fi
fi

# First sync
echo ""
echo "[*] Running first sync..."
python3 src/weread_sync.py

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Output: $(pwd)/output/"
echo "  Next: open output/ in Obsidian or any Markdown editor"
echo ""
echo "  For hourly auto-sync, add to crontab:"
echo "  7 * * * * cd $(pwd) && python3 src/weread_sync.py --incremental >> sync.log 2>&1"
