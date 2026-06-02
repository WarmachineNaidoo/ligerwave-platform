-- WiFi CSI Platform — Initial Schema
-- Run this in Supabase SQL Editor

-- 1. Organizations (Alarm Companies / Guarding Companies)
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('alarm_company', 'guarding_company', 'consumer')),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  role TEXT NOT NULL DEFAULT 'consumer' CHECK (role IN ('admin', 'staff', 'dispatcher', 'consumer')),
  email TEXT UNIQUE,
  phone TEXT,
  name TEXT,
  avatar_url TEXT,
  whatsapp_id TEXT,
  auth_provider TEXT,  -- 'google', 'apple', 'email'
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Homes (properties)
CREATE TABLE homes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  name TEXT,
  address TEXT,
  lat FLOAT,
  lng FLOAT,
  tier TEXT NOT NULL DEFAULT 'basic' CHECK (tier IN ('basic', 'premium')),
  retention_days INT NOT NULL DEFAULT 90,
  status TEXT NOT NULL DEFAULT 'disarmed' CHECK (status IN ('armed', 'disarmed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Devices (routers, 1:1 with homes)
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  home_id UUID UNIQUE NOT NULL REFERENCES homes(id),
  gateway_id TEXT UNIQUE NOT NULL,
  firmware_ver TEXT,
  last_seen TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Arming schedules (per home)
CREATE TABLE arming_schedules (
  home_id UUID PRIMARY KEY REFERENCES homes(id),
  monday_start TIME, monday_end TIME,
  tuesday_start TIME, tuesday_end TIME,
  wednesday_start TIME, wednesday_end TIME,
  thursday_start TIME, thursday_end TIME,
  friday_start TIME, friday_end TIME,
  saturday_start TIME, saturday_end TIME,
  sunday_start TIME, sunday_end TIME,
  manual_override BOOLEAN NOT NULL DEFAULT false,
  manual_armed BOOLEAN NOT NULL DEFAULT false,
  override_until TIMESTAMPTZ
);

-- 6. Events (intrusion, motion, armed/disarmed)
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  home_id UUID NOT NULL REFERENCES homes(id),
  event_type TEXT NOT NULL CHECK (event_type IN ('intrusion', 'motion', 'armed', 'disarmed', 'tamper', 'power_loss', 'power_restore', 'breathing', 'fall')),
  confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
  zone TEXT,
  zone_path TEXT[],  -- ordered list of zones the person walked through
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  resolution TEXT CHECK (resolution IN ('false_alarm', 'confirmed', 'dispatched')),
  csi_size_bytes INT  -- size of raw CSI blob in storage
);
CREATE INDEX idx_events_home_id ON events(home_id);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_type ON events(event_type);

-- 7. Raw CSI storage reference
CREATE TABLE csi_raw (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID UNIQUE NOT NULL REFERENCES events(id),
  storage_path TEXT NOT NULL,  -- R2 object key
  format TEXT NOT NULL DEFAULT 'complex_float32',
  sample_rate INT,
  duration_ms INT,
  carrier_count INT,
  size_bytes INT NOT NULL
);

-- 8. API Keys
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  home_id UUID NOT NULL REFERENCES homes(id),
  label TEXT,
  key_hash TEXT UNIQUE NOT NULL,
  permissions TEXT NOT NULL DEFAULT 'read_only' CHECK (permissions IN ('read_only', 'dispatch', 'admin')),
  expires_at TIMESTAMPTZ,
  created_by UUID NOT NULL REFERENCES users(id),
  revoked BOOLEAN NOT NULL DEFAULT false,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_api_keys_home_id ON api_keys(home_id);

-- 9. Subscriptions
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  home_id UUID UNIQUE NOT NULL REFERENCES homes(id),
  provider TEXT NOT NULL DEFAULT 'stripe' CHECK (provider IN ('stripe', 'yoco')),
  provider_subscription_id TEXT,
  tier TEXT NOT NULL CHECK (tier IN ('basic', 'premium', 'wholesale')),
  amount_cents INT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'ZAR',
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'canceled', 'trialing')),
  current_period_start TIMESTAMPTZ NOT NULL DEFAULT now(),
  current_period_end TIMESTAMPTZ NOT NULL,
  canceled_at TIMESTAMPTZ
);

-- 10. Audit log (immutable, append-only)
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  details JSONB DEFAULT '{}',
  ip_address TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- 11. Webhooks (for AR company dispatch)
CREATE TABLE webhooks (
  home_id UUID PRIMARY KEY REFERENCES homes(id),
  url TEXT NOT NULL,
  event_types TEXT[] NOT NULL DEFAULT '{intrusion}',
  min_confidence FLOAT NOT NULL DEFAULT 0.92,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE homes ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE csi_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE arming_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
