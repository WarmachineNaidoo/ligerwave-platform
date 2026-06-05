-- ══════════════════════════════════════════════════════════
-- MIGRATION 003 — Run in Supabase SQL Editor
-- ══════════════════════════════════════════════════════════
-- 1. Go to: https://supabase.com/dashboard/project/zchqctktwkimfecmjnon/sql/new
-- 2. Paste this entire file
-- 3. Click "Run" (or press Cmd+Enter)
-- 4. Done — takes 2 seconds
-- ══════════════════════════════════════════════════════════

-- Migrate existing data to new tier names
UPDATE homes SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'wholesale' WHERE tier = 'basic' AND provider = 'wholesale';

-- Update tier CHECK constraints
ALTER TABLE homes DROP CONSTRAINT IF EXISTS homes_tier_check;
ALTER TABLE homes ADD CONSTRAINT homes_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium'));

ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_tier_check;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium', 'wholesale'));

-- Allow NULL user_id in audit_logs for breach/system records
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;

-- Add consent_logs table for POPIA/GDPR audit trail
CREATE TABLE IF NOT EXISTS consent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  consent_type TEXT NOT NULL,
  consented BOOLEAN NOT NULL DEFAULT true,
  consent_version TEXT NOT NULL DEFAULT '1.0',
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_consent_logs_user ON consent_logs(user_id);
ALTER TABLE consent_logs ENABLE ROW LEVEL SECURITY;

-- Verify migration
SELECT 'Migration 003 complete' AS status,
       (SELECT COUNT(*) FROM homes WHERE tier = 'free') AS homes_on_free,
       (SELECT COUNT(*) FROM subscriptions WHERE tier = 'free') AS subs_on_free;
