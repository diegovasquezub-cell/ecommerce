"""Registra el webhook de Telegram. Uso (desde la raíz): python scripts/set_webhook.py"""
import os
import sys
from pathlib import Path

import httpx
import truststore
from dotenv import load_dotenv

truststore.inject_into_ssl()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    sys.exit("Falta TELEGRAM_TOKEN en .env")
API = f"https://api.telegram.org/bot{TOKEN}"
PUBLIC_URL = (os.getenv("PUBLIC_URL") or "").rstrip("/")
SECRETO = os.getenv("TELEGRAM_SECRET")
if not PUBLIC_URL.startswith("https://") or not SECRETO:
    sys.exit("PUBLIC_URL (https) y TELEGRAM_SECRET deben estar en .env")

r = httpx.post(f"{API}/setWebhook", data={"url": f"{PUBLIC_URL}/telegram", "secret_token": SECRETO}, timeout=15)
print(r.status_code, r.text)