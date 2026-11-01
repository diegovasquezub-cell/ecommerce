"""Muestra el estado del webhook de Telegram. Uso (desde la raíz): python scripts/webhook_info.py"""
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
r = httpx.get(f"{API}/getWebhookInfo", timeout=15)
print(r.status_code, r.text)
info = r.json().get("result", {})
if info.get("last_error_message"):
    print("ERROR PENDIENTE:", info["last_error_message"])
print("pendientes:", info.get("pending_update_count"))