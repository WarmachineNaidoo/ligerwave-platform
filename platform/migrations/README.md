# Database Migrations

Run these in order in the Supabase SQL Editor.

## Order

1. `001_initial_schema.sql` — ✅ Already applied (tables exist with data)
2. `002_rls_policies.sql` — ✅ Already applied (RLS policies active)
3. `003_tier_schema_fix.sql` — ❌ **Needs manual run** in Supabase SQL Editor

## How to run

1. Go to https://supabase.com/dashboard/project/zchqctktwkimfecmjnon/sql
2. Open `003_tier_schema_fix.sql`
3. Click "Run"
