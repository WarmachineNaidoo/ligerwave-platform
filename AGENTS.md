# WiFi CSI Intrusion Detection Platform — South Africa

## Goal
Build a WiFi-CSI intrusion detection platform for the SA market. Router-based sensing (OpenWrt + CSI extraction), no per-room hardware. R500 device cost, R30/mo subscription. Privacy-first: device sees only radio-layer CSI (complex numbers), cannot decode user traffic.

## Business Model
- **Consumer self-service**: Buy box at retail → scan QR → social auth → add payment → router auto-pairs → dashboard + WhatsApp alerts live immediately
- **AR (Armed Response) companies**: Consumer generates API key from dashboard → shares with AR company → AR gets read-only CSI view for dispatch verification
- **Wholesale**: AR company resells at R15/mo wholesale; they set their own retail price. Consumer gets their own API key via the AR company
- **API keys**: Free, with expiry, per-property scoped. Permission levels: `read_only` | `dispatch` | `admin`. Consumer controls who has access

## Pricing
| Tier | Consumer pays | AR company pays | We receive |
|------|:------------:|:---------------:|:----------:|
| Direct consumer (self-monitor) | R30/mo | R0 | R30/mo |
| Direct + AR has API key | R30/mo | R0 | R30/mo |
| AR company resells | R0 | R15/mo | R15/mo |

## Key Technical Decisions
- **Phase-based signal processing** (not ACF) → avoids Origin AI's 225+ patent portfolio
- **Continuous CSI streaming** to Cloudflare R2 → ~R2/mo per home at 100-worker warehouse rates
- **Events stored in PostgreSQL** (metadata only, ~200 bytes); **raw CSI in object storage** (Cloudflare R2, $0.015/GB)
- **Data retention**: 90 days standard, 365 days premium. POPIA-compliant (records retained no longer than necessary for purpose)
- **WhatsApp alerts** (R0.14/msg) triggered only when system is ARMED. Free within 24h service window
- **No camera**, no PIR sensors. One box covers entire property through walls

## Arming Model
- Consumer sets per-day schedules (e.g., Mon-Fri 18:00-06:00, weekends all day)
- WhatsApp alerts fire ONLY when armed + high-confidence event
- Unarmed hours: continuous CSI stored for forensics, no alerts
- Manual override for temporary arm/disarm

## Competitive Landscape
- **Origin AI** (acquired by ADT $170M, Feb 2026): ACF-based, US market, premium installs. Not active in SA at R30 price point
- **PIR/door sensor kits** (Tuya R1,610, IDS Onyyx R1,600): Per-room install, ugly sensors, no through-wall. Our one-box is simpler
- **Camera + CV**: Privacy invasive, higher cost. We are privacy-first — different philosophy
- **Olarm** (R1,195 + R73/mo): Add-on to existing alarm. Complementary, not competitive
- **No one** serves SA at R500 + R30/mo with WiFi CSI

## Why We Win
- **One box, no install**: Plug into existing WiFi, whole property covered
- **Through-wall detection**: PIR can't do this
- **R30/mo vs R300-600/mo for AR**: 10x cheaper
- **Privacy-first**: No camera, no traffic inspection
- **AR companies get verification**: CSI trace evidence before dispatching (saves R200-500/false dispatch)

## Key Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **False alarm rate** | 7-day dark mode (learn baseline before alerts). Confidence tiers (60-80% log only, 80-92% dashboard, 92%+ alert). Multi-zone path analysis (person walks through zones, pet/fan stays in one). User feedback loop per home |
| **Loadshedding** | UPS bundle (R500 upsell, 4-6hr runtime). Graceful shutdown + restore alerts. USB 4G dongle option (R300) |
| **Support cost at R30** | Self-service only at R30 tier. Pro tier at R150 includes phone support. Remote diagnostics for 80% issue resolution |
| **Patent risk (Origin/ADT)** | Phase-based ≠ ACF. File SA provisional patent. Local market first. Open-source CSI capture pipeline (GPL), proprietary IP is server-side |
| **Consumer trust** | Target small business first (office managers understand WiFi presence). Monthly forensic reports prove value |
| **CSI packet loss** | Dual-band fusion (2.4 + 5 GHz). Both uplink and downlink CSI. Dedicated sensing channel |

## Cost Model (per home/month)
| Item | Cost |
|------|:----:|
| Continuous CSI storage (R2) | ~R2.00 |
| PostgreSQL + API compute | ~R0.50 |
| WhatsApp alerts (1-4/mo) | ~R0.14-0.56 |
| Payment processing (3%) | ~R0.90 |
| **Total** | **~R3.54-3.96** |
| **Subscription** | **R30.00** |
| **Gross margin** | **~87%** |

## Storage at Scale
- 1,000 homes, 90-day rolling: ~46 GB PostgreSQL + ~1.26 TB R2 → ~R1,600/mo total infra
- 10,000 homes: ~460 GB PostgreSQL + ~12.6 TB R2 → ~R6,000/mo total infra
- PostgreSQL handles up to 32 TB with proper indexing. R2 has free egress

## Build Order (14 days estimated)

### Phase 1 — Platform Foundation
1. **Supabase project** — organizations, users, homes, events, csi_raw tables. RLS policies for multi-tenant
2. **FastAPI auth** — social auth (Google/Apple) + JWT + role middleware (consumer, AR, admin)
3. **Router pairing** — QR code → scan → auto-link to account
4. **Subscription + payment** — Yoco/Stripe integration. R30 direct / R15 wholesale
5. **Event ingestion** — POST /device/events (router pushes CSI). Continuous → R2. Events → PostgreSQL
6. **Event query API** — GET /homes/{id}/events (filtered, paginated). Raw CSI binary retrieval
7. **API key system** — Generate/revoke with expiry, per-home scope, permission levels

### Phase 2 — Consumer Features
8. **Dashboard** — Live status, event feed, CSI replay heatmap
9. **Arming schedule** — Per-day timers + manual override
10. **WhatsApp alerts** — High-confidence events during armed hours
11. **Monthly report** — Auto-generated PDF activity summary
12. **AI agent** — Natural language queries against event DB + CSI traces

### Phase 3 — Wellness Features (expansion)
13. **Breathing rate monitoring** — PCA/spectral peak detection on CSI during stationary periods (sleep, sitting)
14. **Sleep quality trends** — Overnight breathing pattern reports (non-medical)
15. **Fall detection** — CNN-LSTM on CSI during armed hours (separate from intrusion alerts)
16. **Weekly wellness summary** — Combined security + wellness report
17. **Optional: SAHPRA upgrade path** — If wellness features prove lucrative, pursue SAHPRA Class I/II medical device certification for clinical-grade monitoring

### Phase 4 — AR Company Features
18. **Dispatch dashboard** — View all properties with keys. Active alerts, CSI replay, ack/dismiss/dispatch
19. **White-label API** — REST feed for existing dispatch consoles
20. **Bulk key management** — AR company manages keys for their customers

### Phase 5 — Hardware Validation
21. **Buy 1 router** — Xiaomi Mi Router 4A (~R379, Incredible Connection)
22. **Flash OpenWrt + CSI patches** — Get CSI streaming to cloud
23. **1-week single-room test** — Measure false alarm rate
24. **Dark mode learning** — 7-day baseline per home

## Competitor Technologies
| Tech | Our advantage |
|------|---------------|
| **mmWave radar** (R800-1,500, 6-8m range, LoS) | Our CSI goes through walls, longer range, cheaper |
| **PIR + door sensors** (R1,600, per-room install) | One box, no sensors to place |
| **Camera + CV** (R1,500+, privacy invasive) | No camera, can't see faces |

## Architecture Summary
```
Router (on-site) → HTTPS CSI stream → Cloud API (FastAPI)
  ├── Raw CSI → Cloudflare R2 (object storage)
  └── Metadata → PostgreSQL (Supabase)
        ├── Armed? → Process confidence → WhatsApp alert + AR feed
        ├── Unarmed? → Store only (forensics, AI queries)
        └── Stationary? → Wellness pipeline
              ├── Breathing rate (PCA + spectral peak)
              ├── Sleep quality trends
              └── Fall detection (CNN-LSTM)
```

## API Access Model
- Consumer owns subscription → generates API keys for AR companies
- AR company plugs key into their dashboard → read-only view of that property
- One property can have multiple keys (consumer + multiple AR companies + family members)
- Keys have expiry dates set by the creator

## Latest Additions (2026-06-03)
- **11 premium CSI detection services**: `services/premium.py` — door/window, vehicle, fire/smoke, heart rate, gait ID, routine deviation, baby cry, room occupancy, smart triggers, water leak, structural movement. Each is a standalone detector class fed CSI data from the live ingestion pipeline.
- **Feature gating system**: `services/feature_flags.py` — rollout stages (`dev` → `alpha` → `beta` → `ga`), tester user lists, `is_available(feature, user_id)` check. Admin controls which users see which features via GoTrue admin API (no DDL).
- **Admin rollout dashboard**: `static/admin.html` — web UI to manage stage per feature, add/remove testers. Accessible at `/admin` after login.
- **Subscription tier model**: `services/features.py` — `Free`, `Security+` (R30), `Wellness+` (R30), `Intelligence+` (R30), `Premium Bundle` (R80). Tier maps to feature sets. Individual toggles override tier defaults.
- **Premium router**: `routers/premium.py` — 15 endpoints covering subscription management, feature toggles, and live status for each premium detector. Each endpoint gated by both rollout availability + subscription check.
- **Settings UI**: Premium toggle switches in settings page, tier upgrade buttons, gait naming section (learn named walking patterns), subscription display.
- **Dashboard premium section**: Dynamically renders available premium feature cards in the dashboard main view. Shows live status (heart rate BPM, gait match, occupancy count, structural days).
- **Gait identification with naming**: `GaitDetector` extracts step cadence + amplitude signature, builds a fingerprint per named person, matches live walking against known gaits. UI supports learning new gaits with a name.
- **Admin router**: `routers/admin.py` — `GET /admin/features`, `POST /admin/features/stage`, `POST /admin/features/tester`, `DELETE /admin/features/tester`. Admin role required.

## Full Product Lineup

| # | Product | Customer | Device | Antenna | Power | Price | Latency | Status |
|---|---------|----------|--------|---------|-------|-------|---------|--------|
| 1 | **Security+** | Consumer | Mi Router 4A | Omni 3dBi | 20dBm | R30/mo | ~2s | ✅ Live |
| 2 | **Wellness+** | Consumer | Same | — | — | R30/mo | ~2s | ✅ Live |
| 3 | **Intelligence+** | Consumer | Same | — | — | R30/mo | ~2s | ✅ Live |
| 4 | **Premium Bundle** | Consumer | Same | — | — | R80/mo | ~2s | ✅ Live |
| 5 | **AR Premium** | AR companies | Same | — | — | R100/mo | **~600ms WS** | 🆕 Design |
| 6 | **Wholesale** | AR resellers | Same | — | — | R15/mo | ~2s | ✅ Live |
| 7 | **Trace** | SAPS/Military | **EAP225-Outdoor** | Omni 5dBi | 27dBm | R2,500-5k/kit | **~600ms WS** | 🆕 Design done |
| 8 | **PrisonGuard** | Corrections | **CPE510** | **Directional 13dBi** | **30dBm** | R2,500/block/mo | **~600ms WS** | 🆕 Design done |
| 9 | **Drone** | Tactical ops | **EAP225-on-drone** | Omni 5dBi | 27dBm | ~R67k/kit | **~600ms WS** | 🆕 Design done |

## Product 7 — Ligerwave Trace (SAPS/Military)
### Overview
Through-wall HR monitoring for tactical pre-entry intel. Officer places router near wall, 30s calibration builds heatmap showing persons inside, taps target, hears HR tones via BT earpiece.

### Key Specs
- Device: EAP225-Outdoor (400g, portable). Latency: ~600ms WebSocket push. 
- Phone app is thin client — zero signal processing code (IP protection)
- Audit log: Full session — officer ID, GPS, timestamps, BPM readings, immutable
- GPS: One-time at install (officer's phone) + IP geolocation fallback

### Tones: <70 BPM slow, 70-100 medium, >100 rapid flutter

### Design Decisions
- Cloud over local edge (IP theft risk if laptop stolen)
- 600ms not lower (HR changes in 3-5s cycles, diminishing returns)
- SAPS HR revocation webhook + admin fallback
- NOT admissible in court — operational intelligence tool only
- POPIA Section 6(1)(c) exempt (law enforcement)

## Product 8 — Ligerwave PrisonGuard (Corrections)
### Overview
Through-wall wellness + riot prediction. One CPE510 per cell block (20-30 cells). Control room dashboard with 600ms alerts.

### Key Specs
- Device: CPE510 (30dBm, 13dBi directional dish). Reason: focused beam penetrates more cells through concrete walls
- Pricing: R2,500/block/month. ~R21,000 hardware for 10-block prison

### Riot Prediction: Multi-signal weighted (HR deviation 0.4 + crowding 0.25 + gait 0.2 + movement 0.15). Configurable thresholds via admin panel (no coding).

### Tamper: Disconnect, jamming (RuView ais_prompt_shield), physical movement, theft. Remote deactivation via 3 layers: API key revocation + geographic fence + 24h offline self-disable.

### 10-clause ToS: Operational support only, no warranty, indemnification, liability cap, training required, export restriction (SA only), tamper prohibition, deactivation right, government use only.

## Product 5 — Ligerwave MineGuard (Mining / Industrial)
### Overview
Mine personnel safety without wearables. Uses mine's existing underground WiFi mesh. CSI APs detect every person through rock — presence, HR, breathing, gait, movement. No device for miner to wear.

### The Miner's Day — Journey Map
| Time | Activity | Current Problem | MineGuard Fix |
|------|----------|----------------|--------------|
| 05:30 | Arrive at mine, change into PPE | Manual sign-in queue | Auto-detected entering mine. Lamp room screen: "Good morning, Sipho — Shift B, Zone 4." |
| 06:00 | Cage descent | Supervisor counts heads manually | Live count: "12 of 12 present." |
| 06:15 | Travel to work area | No progress visibility | Real-time location. Travel time tracked per miner → identify fatigue/injury delays. |
| 06:30 | Pre-shift meeting | No proof it happened | 12 persons stationary 12 min in Zone 4 → logged as "safety meeting completed." |
| 06:45 | Inspect area (lone worker) | Nobody knows if too long in remote zone | Lone worker timer: >30 min reduced movement in isolated zone → alert. |
| 07:00-12:00 | Drilling, charging, support | Hard to track team spread across zone | Heatmap: "3 at face, 2 installing support, 1 at vent raise." HR + gait monitored through shift. |
| 09:00 | Tea break | No heat stress monitoring | HR recovery tracked. If someone's HR stays >90 during rest → "Not recovering — possible heat stress developing." |
| 12:30 | Blast clearance | Manual headcount takes 15-20 min | Instant: "Zone 4: 0 persons. All clear to blast." |
| 13:00 | Post-blast | Scramble to confirm everyone accounted | "All 12 persons detected, all HR normal. No injuries." |
| 13:30 | Surface | End-of-shift headcount | Automatic: "12 of 12 accounted for. Shift complete." |
| 14:00 | Home | Family worries | Family portal (30 min delay): "Sipho — Shift complete. Surfaced 13:45." |

### Normal Ops Features
- Auto shift reconciliation — system compares expected vs detected. Discrepancies alerted instantly.
- Hot zone monitoring — tagged high-risk areas. >30 min occupancy → alert.
- Productivity analytics — time per zone per role. Anomalies flagged to mine manager.
- Conveyor proximity alert — person within 5m of moving conveyor → operator alerted + auto-stop if ignored.
- Refuge bay occupancy — during emergency, track who has reached safe havens.
- Rest adequacy tracking — HR recovery during breaks. Slow recovery = heat stress flag.
- Gait fatigue index — walking speed + stride vs baseline. >20% deviation = fatigue marker.
- Rapid deployment mode — supervisor walks new tunnel once, system maps it. No IT needed.

### Extreme Events — Second-by-Second
| Event | Detection | 0-10s | 10s-5min | 5min+ |
|-------|-----------|-------|----------|-------|
| Rockfall | CSI noise spike + AP signal drop | "Seismic event Zone 4" | "3 persons in zone. 2 with HR. 1 no signal." | Rescue to coordinates of remaining 1. |
| Fire | CSI phase turbulence (hot air currents) | "Abnormal airflow Zone 7" | "Zone 7: 0 persons. Adjacent: 4 persons, HR elevated." | Evacuation path: "Zone 7 smoke-logged. Route through Zone 5." |
| Flood | CSI amplitude drop across APs | "Water detected Zone 9" | "2 persons Zone 9. 5 persons Zone 10." | "Estimated time to Zone 10: 12 min. Evacuate now." |
| Gas explosion | Broadband noise spike + signal loss | "Explosion Zone 6" | "4 persons pre-event. 2 post-event (HR). 2 no signal." | Rescue map: "Survivors at 30m/45m. Deceased at 15m/22m." |
| Power failure | APs going offline sequentially | "Power propagating from Zone 5" | "Last known: 8 persons in Zone 5-6 corridor." | Battery-backed APs in critical zones maintain tracking. |
| Toxic gas (H2S/CO) | Integration with gas sensors | "H2S alarm Zone 8. CSI: 5 persons there." | "Move to Zone 11 immediately." | Track evacuation: "3 of 5 moved. 2 still in Zone 8." |
| Trapped behind fall | AP on bystander side still works | "6 persons behind fall. All HR normal." | "All stable 5min post-event." | Borehole rescue: "Personnel 20m from AP. Drill within 3m." |
| Hostage/barricade | Unusual clustering + abnormal movement | "15 persons in Zone 3 (cap: 4)." | "Zone 3: 15 in one area. 1 isolated in Zone 5 with agitated gait." | Negotiation intel: "14 hostages, HR elevated. 1 agitator pacing." |

### System Integrations
- Seismic monitoring → CSI + seismic: "Seismic event + 3 persons in Zone 6 confirmed."
- Gas monitoring → Gas + CSI: "H2S alarm Zone 8. 2 persons there — evacuate."
- Ventilation → CSI + ventilation: "Smoke toward Zone 5. 12 persons there — redirect airflow."
- Blasting → CSI + blast: "Zone clearance — 0 persons. Permit to blast."
- Dispatch → CSI + fleet: "Person 5m behind reversing truck. Auto-brake."
- Mine plan → CSI + digital twin: "3 person-days tracked vs schedule in Zone 4."
- HR/shift → CSI + roster: "Expected 47. Detected 44. 3 unaccounted."
- Emergency response → CSI + protocol: "Zone 6 incident. 5 rescued. Auto-call to team."
- Refuge bays → CSI + refuge: "Bay 1: 23. Bay 2: 18. 5 en route, ETA 2 min."
- Lighting → CSI + lights: "Zone unoccupied 2h → dim. Person detected → restore."

### Advanced Features
| Feature | What It Does | Feasibility |
|---------|-------------|-------------|
| Fatigue Index | Gait degradation over shift vs baseline. Cross threshold → rotate. | ✅ GaitDetector exists |
| Heat Stress Prediction | HR trends + zone temp + crew rotation data | ✅ HR + movement tracked |
| Hydration Alert | HR recovery slope during rest breaks (soft alert only) | 🟡 Indirect marker |
| Confined Space Timer | Single person in small zone >60 min → alert | ✅ Zone mapping exists |
| Productivity vs Safety Dashboard | Man-hours vs incident flags per zone | ✅ Aggregate data |
| Automated DMR Reporting | Shift attendance, fatigue monitoring, incident log | ✅ All data captured |
| Family Portal | Read-only 30-min delay view: "Alive, mobile, shift ends 14:00." | ✅ Simple API |

### Stakeholder Dashboards

**Mine Manager:** Site summary — 234/236 personnel, zone-by-zone HR status, today's incidents, heat stress flags, fatigue interventions, productivity %, downloadable DMR reports.

**Safety Officer:** Active alerts (2), watch list (3 heat/fatigue/confined space), shift statistics (incidents 0, near-misses 2, fatigue interventions 3, heat stress 2), auto-generated DMR-ready PDFs.

**Shift Supervisor (phone):** Per-zone headcount, blast clearance status, lone worker timers. "31/31 ✅ All accounted." Quick alert + end shift buttons.

**Mine Rescue (emergency tablet):** Incident type + magnitude. Survivors: P1 (20m, HR 72), P2 (30m, HR 65), P3 (45m, NO HR). Blocked entry point + alternative route + team ETA.

### Summary — What Makes MineGuard Unique
1. Zero wearable — no badge, no battery, no charge. The miner just exists.
2. Through-rock detection — GPS/UWB/RFID all fail behind rock. CSI doesn't.
3. Alive vs dead confirmation — HR + breathing tells rescuers who to prioritize.
4. Gait-based identification — knows who is who, not just "someone is there."
5. 10+ extreme events mapped with second-by-second response.
6. Useful in normal ops too — productivity, fatigue, heat stress.
7. Uses existing mine WiFi — no new infrastructure.
8. No compliance failure point — works even when the system is forgotten or broken.
### Overview
Perimeter + internal road monitoring for gated estates. CPE510 along fence for approach detection. EAP225 on roads for vehicle vs person classification. Guard patrol verification via gait.

### Key Features: Perimeter mode (CPE510 directional), person vs vehicle (speed + amplitude + spectral signature, already built), gait-based patrol verification (GaitDetector), estate-scale heatmap, digging/tunnel detection.

### Hardware (500-home estate): 6x CPE510 (R7,200) + 10x EAP225 (R12,000) + installation (R15,000) = ~R34,600 total. Monthly cloud: R200.

## Product 9 — Ligerwave Drone (Tactical Ops)
### Overview
Drone-mounted CSI for building threat mapping. 30-40s hover above roof produces heatmap of persons inside. Hybrid CSI + visual tracking for urban pursuit.

### Key Specs
- Device: EAP225-Outdoor (400g — fits DJI Mavic 3). CPE510 (1.1kg) rejected — too heavy
- Range: 50m altitude, tile/concrete roof + 1-2 floors. Metal roof = accepted limitation
- 4G required for cloud uplink

### Build Phases: Phase 1 = heatmap + target lock (same code as Trace). Phase 2 = camera fusion. Phase 3 = autonomous visual follow + CSI backup when visual lost.

### Kit: DJI Mavic 3 (R25k) + EAP225 (R1,200) + 4G modem (R500) + battery/wiring (R300) = ~R27k total.

## Design Log — Key Decisions
| Decision | Rationale | Products |
|----------|-----------|----------|
| Cloud not edge | IP protection — thin client has no algorithms | Trace, Drone |
| EAP225 for portable, CPE510 for fixed | Weight (400g vs 1,100g) vs power (27dBm vs 30dBm) | All |
| 600ms not lower | HR cycles 3-5s, diminishing returns below 600ms | All |
| WS push not HTTP poll | Existing `/ws/{id}` reused | All |
| Metal roofs = limitation | Physics — Faraday cage at 2.4/5 GHz | Drone |
| Separate pipeline per product | Isolated infra, consumer unaffected | All |
| Revocation webhook + manual | SAPS HR integration + admin fallback | Trace |
| 10-clause ToS | Government contract protection | PrisonGuard |

## Hardware Comparison
- Mi Router 4A: 20dBm, 300g — Consumer
- EAP225-Outdoor: 27dBm, 400g — Trace, Drone
- CPE510: 30dBm, 13dBi directional, 1,100g — PrisonGuard
- Where to buy (Durban): Incredible Connection, Rectron (031 303 1122), Tarsus (031 267 1600), Takealot
- **POPIA compliance**:
  - **Data subject rights endpoints**: `routers/privacy.py` — `GET /privacy/my-data` (access), `DELETE /privacy/my-data` (deletion, keeps billing records), `POST /privacy/my-data/correction` (email/phone/name)
  - **POPIA notice banner**: Footer on dashboard with English/Afrikaans/Zulu i18n. Shows when logged in with link to `/privacy/my-data`
  - **Audit log retention**: `services/retention.py` — `purge_old_audit_logs()` anonymizes user_id + clears details after 3 years. Docker retention container now calls `purge_all()`
- **RF Tomography (passive radar live view)**:
  - `services/tomography.py` — 20×20 perturbation grid per home. Zone-to-cell mapping, exponential decay, cluster-based person detection
  - `routers/tomography.py` — `GET /tomography/{home_id}` returns grid heat + zone map + movement trails + detected persons
  - `dashboard.html` — Canvas render with live passive radar view. Red heat overlay, amber trails, zone borders with legend, person confidence dots. Refreshes every 2 seconds

## GitHub Account
- **Username**: WarmachineNaidoo
- **Platform repo**: `github.com/WarmachineNaidoo/ligerwave-platform.git` (branch: `master`)
- **RuView repo**: `github.com/ruvnet/RuView.git` (research reference, read-only)
- **Auth**: Push requires user to authenticate via `git push origin master`. Never push without confirming the remote is correct first.
- **Rule**: Always check the git remote URL before pushing. Never push to `ruvnet/*` repos — only push to `WarmachineNaidoo/*`.

## File Locations
- `C:\work\Software\New project 1\RuView\` — cloned RuView repo (reference for signal processing, WebSocket, existing API patterns)
- `C:\work\Software\New project 1\research\` — automated research agent
- `C:\work\Software\New project 1\platform\` — platform API code (FastAPI + Supabase schema)
- `C:\work\Software\New project 1\platform\SCALING.md` — detailed scaling plan through 100,000 homes with migration triggers

## Weekly Research Agent
Run every Monday to gather intelligence. Use `task` tool with `subagent_type: general` and the prompt from `research\research_config.md`. Findings append to `research\findings.md`.

### Topics covered
1. Hardware sourcing (Alibaba MT7621/MT7981 pricing)
2. OpenWrt CSI tools (ath9k, nexmon, ekstra updates)
3. Origin AI / ADT patent filings
4. SA competitor activity (Olarm, Venus, IDS, Tuya)
5. WhatsApp Business API pricing/policy changes
6. POPIA security data retention guidance
7. New CSI research papers (false alarm reduction, phase detection)

### How to run
```
task "Run weekly research. Use research_config.md for topics. Append to findings.md." subagent_type:general
```
