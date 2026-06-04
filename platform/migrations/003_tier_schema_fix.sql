-- WiFi CSI Platform — Tier Schema Fix + Consent Table
-- Run this in the Supabase SQL Editor at:
-- https://supabase.com/dashboard/project/zchqctktwkimfecmjnon/sql/new
-- ================================================================

-- 1. Migrate existing data to new tier names
UPDATE homes SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'wholesale' WHERE tier = 'basic' AND provider = 'wholesale';

-- 2. Update tier CHECK constraints
ALTER TABLE homes DROP CONSTRAINT IF EXISTS homes_tier_check;
ALTER TABLE homes ADD CONSTRAINT homes_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium'));

ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_tier_check;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium', 'wholesale'));

-- 3. Allow NULL user_id in audit_logs for breach/system records
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;

-- 4. Add a consent log table for POPIA/GDPR audit trail
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
CREATE INDEX idx_consent_logs_user ON consent_logs(user_id);
ALTER TABLE consent_logs ENABLE ROW LEVEL SECURITY;
