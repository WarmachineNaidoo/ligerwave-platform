-- WiFi CSI Platform — Row Level Security Policies
-- Run after 001_initial_schema.sql

-- === Helper functions ===

-- Get the user's organization_id
CREATE OR REPLACE FUNCTION public.user_org()
RETURNS UUID
LANGUAGE SQL STABLE
AS $$
  SELECT organization_id FROM public.users WHERE id = auth.uid()
$$;

-- Check if user belongs to the same org as a home
CREATE OR REPLACE FUNCTION public.user_owns_home(home_id UUID)
RETURNS BOOLEAN
LANGUAGE SQL STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.homes h
    WHERE h.id = home_id
    AND h.organization_id = public.user_org()
  )
$$;

-- === Organizations ===
CREATE POLICY "org_admin_read" ON public.organizations
  FOR SELECT USING (id = public.user_org());
CREATE POLICY "org_admin_update" ON public.organizations
  FOR UPDATE USING (id = public.user_org());

-- === Users ===
CREATE POLICY "user_read_own" ON public.users
  FOR SELECT USING (id = auth.uid() OR organization_id = public.user_org());
CREATE POLICY "user_update_own" ON public.users
  FOR UPDATE USING (id = auth.uid());

-- === Homes ===
CREATE POLICY "home_read_org" ON public.homes
  FOR SELECT USING (organization_id = public.user_org());
CREATE POLICY "home_insert_org" ON public.homes
  FOR INSERT WITH CHECK (organization_id = public.user_org());
CREATE POLICY "home_update_org" ON public.homes
  FOR UPDATE USING (organization_id = public.user_org());

-- === Devices ===
CREATE POLICY "device_read_org" ON public.devices
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.homes h WHERE h.id = home_id AND h.organization_id = public.user_org())
  );
CREATE POLICY "device_insert_org" ON public.devices
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM public.homes h WHERE h.id = home_id AND h.organization_id = public.user_org())
  );
CREATE POLICY "device_update_org" ON public.devices
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM public.homes h WHERE h.id = home_id AND h.organization_id = public.user_org())
  );

-- === Events ===
CREATE POLICY "event_read_org" ON public.events
  FOR SELECT USING (public.user_owns_home(home_id));
CREATE POLICY "event_insert_org" ON public.events
  FOR INSERT WITH CHECK (public.user_owns_home(home_id));

-- === CSI Raw ===
CREATE POLICY "csi_read_org" ON public.csi_raw
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.events e WHERE e.id = event_id AND public.user_owns_home(e.home_id))
  );
CREATE POLICY "csi_insert_org" ON public.csi_raw
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM public.events e WHERE e.id = event_id AND public.user_owns_home(e.home_id))
  );

-- === API Keys ===
CREATE POLICY "apikey_read_org" ON public.api_keys
  FOR SELECT USING (public.user_owns_home(home_id));
CREATE POLICY "apikey_insert_org" ON public.api_keys
  FOR INSERT WITH CHECK (public.user_owns_home(home_id));
CREATE POLICY "apikey_update_org" ON public.api_keys
  FOR UPDATE USING (public.user_owns_home(home_id));

-- === Subscriptions ===
CREATE POLICY "sub_read_org" ON public.subscriptions
  FOR SELECT USING (public.user_owns_home(home_id));
CREATE POLICY "sub_insert_org" ON public.subscriptions
  FOR INSERT WITH CHECK (public.user_owns_home(home_id));
CREATE POLICY "sub_update_org" ON public.subscriptions
  FOR UPDATE USING (public.user_owns_home(home_id));

-- === Arming Schedules ===
CREATE POLICY "arm_read_org" ON public.arming_schedules
  FOR SELECT USING (public.user_owns_home(home_id));
CREATE POLICY "arm_insert_org" ON public.arming_schedules
  FOR INSERT WITH CHECK (public.user_owns_home(home_id));
CREATE POLICY "arm_update_org" ON public.arming_schedules
  FOR UPDATE USING (public.user_owns_home(home_id));

-- === Audit Logs (admin/staff only) ===
CREATE POLICY "audit_read_admin" ON public.audit_logs
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role IN ('admin', 'staff'))
  );
CREATE POLICY "audit_insert_own" ON public.audit_logs
  FOR INSERT WITH CHECK (user_id = auth.uid());
