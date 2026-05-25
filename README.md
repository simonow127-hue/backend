# Riads Backend API

FastAPI service for [riads.shop](https://riads.shop) orders, analytics, and Google Sheets webhook.

## Easypanel (حل مشكل التشغيل)

If the container crashes with `please install fastapi[standard]`:

1. **Source:** GitHub `https://github.com/simonow127-hue/backend.git` branch `main`.
2. **Build:** Dockerfile (root of repo).
3. **Start command:** leave **empty** so Docker uses:
   ```txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
   ```
   If you must set a command manually, paste exactly the line above (not `fastapi run`).
4. **Port:** `8000`.
5. **Redeploy** with **Rebuild** after each push to `main`.

Required env (minimum):

```env
APP_ENV=production
DATABASE_URL=postgres://riads:riads@riads_database:5432/riads?sslmode=disable
RUN_MIGRATIONS_ON_START=true
FRONTEND_URL=https://riads.shop
CORS_ORIGINS=https://riads.shop,https://www.riads.shop
GOOGLE_SERVICE_ACCOUNT_JSON_B64=<from scripts/encode-service-account.py>
GOOGLE_SHEETS_SPREADSHEET_ID=1Dypu_WkwyH2VXI94nOg4urxby20ktNMu2Od5wulRvRs
ENABLE_SHEETS_WEBHOOK=true
```

Or use Apps Script: `GOOGLE_SHEETS_WEBHOOK_URL=...` (see `docs/google-sheets-setup.md`).

Health: `https://api.riads.shop/health` → `"sheets_mode": "direct"` or `"webhook"`, `"sheets_configured": true`.

After a test order, check DB `orders.status`:
- `sent_to_sheet` — row reached Google Sheets
- `sheet_failed` — URL wrong, script not deployed, or script error (see backend logs)
- `new` — webhook never ran (old deploy) or URL empty

Google Sheet: redeploy Apps Script after updating `docs/google-apps-script-webhook.js` (writes to **first tab** by default).

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
