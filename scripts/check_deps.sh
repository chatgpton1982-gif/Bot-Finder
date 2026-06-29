#!/bin/bash
cd ~/tg_bot_finder
echo "=== Checking dependencies ==="
python3 -c "import aiogram; print('aiogram OK')" 2>&1
python3 -c "import telethon; print('telethon OK')" 2>&1
python3 -c "import litellm; print('litellm OK')" 2>&1
python3 -c "import aiosqlite; print('aiosqlite OK')" 2>&1
python3 -c "import dotenv; print('python-dotenv OK')" 2>&1
python3 -c "import pydantic; print('pydantic OK')" 2>&1
echo "=== Checking .env ==="
if [ -f .env ]; then
    echo ".env exists"
else
    echo ".env NOT found - copy .env.example to .env and fill values"
fi
echo "=== Checking middleware ==="
ls -la bot/middleware/ 2>&1
echo "=== Syntax check ==="
python3 -m py_compile bot/main.py 2>&1 && echo "main.py OK"
python3 -m py_compile bot/config.py 2>&1 && echo "config.py OK"
python3 -m py_compile bot/handlers/search.py 2>&1 && echo "search.py OK"
python3 -m py_compile bot/handlers/summary.py 2>&1 && echo "summary.py OK"
python3 -m py_compile bot/middleware/auth.py 2>&1 && echo "auth.py OK"
echo "=== Done ==="