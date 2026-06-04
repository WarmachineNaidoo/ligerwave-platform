-- WiFi CSI Platform — Tier Schema Fix
-- Aligns CHECK constraints with features.py tier values
-- Run this in Supabase SQL Editor after 001_initial_schema.sql and 002_rls_policies.sql

-- First migrate existing data to new tier names
UPDATE homes SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'free' WHERE tier = 'basic';
UPDATE subscriptions SET tier = 'wholesale' WHERE tier = 'basic' AND provider = 'wholesale';

-- Then update the CHECK constraints
ALTER TABLE homes DROP CONSTRAINT IF EXISTS homes_tier_check;
ALTER TABLE homes ADD CONSTRAINT homes_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium'));

ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_tier_check;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_tier_check CHECK (tier IN ('free', 'security', 'wellness', 'intel', 'premium', 'wholesale'));

-- Update the audit_logs table to allow NULL user_id for breach records
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
