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
GOOGLE_SHEETS_WEBHOOK_URL=<your Apps Script URL>
ENABLE_SHEETS_WEBHOOK=true
```

Health check URL: `https://api.riads.shop/health`

Response must include `"sheets_webhook_configured": true`. If `false`, add `GOOGLE_SHEETS_WEBHOOK_URL` (Apps Script URL ending in `/exec`) and redeploy.

After a test order, check DB `orders.status`:
- `sent_to_sheet` — row reached Google Sheets
- `sheet_failed` — URL wrong, script not deployed, or script error (see backend logs)
- `new` — webhook never ran (old deploy) or URL empty

Google Sheet: redeploy Apps Script after updating `docs/google-apps-script-webhook.js` (writes to **first tab** by default).

### Option B — Direct API (no Apps Script, recommended)

1. Save Google service-account JSON as `backend/secrets/riads-sheets.json`
2. Run: `powershell -File backend/scripts/setup-google-sheets.ps1`
3. Copy the printed env vars into Easypanel → Redeploy
4. Share the sheet with the service account email (Editor)
5. Test: `POST https://api.riads.shop/health/sheets-test`

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
