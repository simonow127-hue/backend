#!/usr/bin/env python3
"""Encode Google service account JSON for Easypanel (single-line env var)."""
import base64
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python scripts/encode-service-account.py path/to/service-account.json")
    sys.exit(1)

path = Path(sys.argv[1])
data = path.read_bytes()
b64 = base64.b64encode(data).decode("ascii")
print("\nAdd these in Easypanel → backend → Environment:\n")
print(f"GOOGLE_SHEETS_SPREADSHEET_ID=1noCh6q_Q-G-fnFWUoPdiHJ7aVL-9r2BMdHTI2xrVl1I")
print(f"GOOGLE_SERVICE_ACCOUNT_JSON_B64={b64}")
print("\nShare your Google Sheet with this email (Editor):")
info = __import__("json").loads(data)
print(info.get("client_email", "(missing client_email in JSON)"))
