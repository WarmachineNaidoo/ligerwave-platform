-- WiFi CSI Platform — Tier Schema Fix
-- Aligns CHECK constraints with features.py tier values
-- Run this in Supabase SQL Editor after 001_initial_schema.sql and 002_rls_policies.sql

ALTER TABLE homes DROP CONSTRAINT IF EXISTS homes_tier_check;
ALTER TABLE homes ADD CONSTRAINT homes_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium'));

ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_tier_check;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium', 'wholesale'));
