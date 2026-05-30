-- Run manually if you prefer SQL over Alembic (PostgreSQL)
-- Revision: 0002 — admin analytics geo + IP cache

ALTER TABLE analytics_events
  ADD COLUMN IF NOT EXISTS client_ip TEXT,
  ADD COLUMN IF NOT EXISTS geo_valid BOOLEAN,
  ADD COLUMN IF NOT EXISTS geo_reason TEXT;

CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events (created_at);
CREATE INDEX IF NOT EXISTS ix_analytics_events_geo_valid ON analytics_events (geo_valid);
CREATE INDEX IF NOT EXISTS ix_analytics_events_event_name ON analytics_events (event_name);

CREATE TABLE IF NOT EXISTS ip_geo_cache (
  ip TEXT PRIMARY KEY,
  country_iso TEXT,
  is_valid_traffic BOOLEAN NOT NULL DEFAULT FALSE,
  reason_code TEXT NOT NULL DEFAULT 'unknown',
  checked_at TIMESTAMPTZ DEFAULT NOW()
);
