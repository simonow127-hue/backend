# Generates Easypanel env vars from a Google service-account JSON file.
# Usage: save JSON as backend/secrets/riads-sheets.json then run this script.

$ErrorActionPreference = "Stop"
$secretsFile = Join-Path $PSScriptRoot "..\secrets\riads-sheets.json"
$sheetId = "1Dypu_WkwyH2VXI94nOg4urxby20ktNMu2Od5wulRvRs"

if (-not (Test-Path $secretsFile)) {
    Write-Host ""
    Write-Host "1) Open: https://console.cloud.google.com/iam-admin/serviceaccounts"
    Write-Host "2) Create service account -> Keys -> Add key -> JSON"
    Write-Host "3) Save file as: $secretsFile"
    Write-Host "4) Share your Google Sheet with the service account email (Editor)"
    Write-Host "   Sheet: https://docs.google.com/spreadsheets/d/$sheetId/edit"
    Write-Host "5) Run this script again"
    Write-Host ""
    exit 1
}

$json = Get-Content $secretsFile -Raw | ConvertFrom-Json
$minified = (Get-Content $secretsFile -Raw) -replace "`r?`n", "" -replace "\s+", " "

Write-Host ""
Write-Host "=== Easypanel Environment (copy/paste) ===" -ForegroundColor Green
Write-Host "ENABLE_SHEETS_WEBHOOK=true"
Write-Host "GOOGLE_SHEET_ID=$sheetId"
Write-Host "GOOGLE_SERVICE_ACCOUNT_JSON=$minified"
Write-Host ""
Write-Host "Share sheet with (Editor):" -ForegroundColor Yellow
Write-Host $json.client_email
Write-Host ""
Write-Host "Then Redeploy backend and open: https://api.riads.shop/health"
Write-Host 'Expect: "sheets_ready": true'
Write-Host ""
