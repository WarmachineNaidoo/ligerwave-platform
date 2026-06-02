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

## File Locations
- `C:\work\Software\New project 1\RuView\` — cloned RuView repo (reference for signal processing, WebSocket, existing API patterns)
- `C:\work\Software\New project 1\research\` — automated research agent
- `C:\work\Software\New project 1\platform\` — platform API code (FastAPI + Supabase schema)

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
