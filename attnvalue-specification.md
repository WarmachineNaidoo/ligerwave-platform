# AttnValue - Complete Project Specification

## 1. PROJECT OVERVIEW

AttnValue is a **video attention marketplace** where advertisers (buyers) pay verified human viewers (sellers) to watch their video ads. The platform features a Universal Basic Income (UBI) system funded from transaction fees, and includes 3 separate portals (seller, buyer, admin) with enterprise-grade security.

### Vision
Create a transparent, secure marketplace where advertisers reach real human attention and viewers are fairly compensated - revolutionizing digital advertising through verified human engagement.

---

## 2. BUSINESS MODEL

### 2.1 Fee Structure

| Fee Component | Calculation | Pre-Paid | Refundable | Notes |
|---|---|---|---|---|
| **Base Fee** | 5% of campaign value + $0.50 | Yes | No | Admin-adjustable via panel |
| **Video Upload Fee** | $0.025 per video | Yes | No | Covers security scanning costs |
| **View Fee (Standard 720p)** | $0.0025 per view per seller | Yes | No | 1.8x AWS bandwidth cost |
| **View Fee (Premium 1080p)** | $0.005 per view per seller | Yes | No | 1.7x AWS bandwidth cost |
| **Download Fee (Standard 720p)** | $0.0125 per targeted seller | Yes | No | 5× view fee |
| **Download Fee (Premium 1080p)** | $0.025 per targeted seller | Yes | No | 5× view fee |
| **Email Fee** | $1.00 per 100 targeted sellers | Yes | No | Covers AWS SES + margin |

### 2.2 Campaign Value

| Component | Pre-Paid | Refundable | Notes |
|---|---|---|---|
| Campaign value (seller payout pool) | Yes | Yes (unused portion) | Only paid to sellers who actually watch |
| Platform fees | Yes | No | All platform fees non-refundable |

### 2.3 Payout Model

| Parameter | Detail |
|---|---|
| **Payment Capture** | Immediate capture (charge card now) |
| **Payout to Sellers** | 30 days after contract ends (admin-adjustable via panel) |
| **Payout Delays** | Tiered by seller trust level |
| **Reserves** | Rolling reserve per seller tier |
| **Minimum Payout** | $20 threshold |
| **Payout Method** | Manual (seller requests), fees deducted from seller payout |
| **Payout Rails** | Stripe Connect Express (primary), Wise API (fallback for non-Stripe countries), USDC stablecoin (secondary fallback, pilot program) |
| **Platform Take Rate** | 5% + $0.50 base, plus usage-based fees |

**Why 30-day payout?** The 30-day delay is a structural chargeback mitigation measure. Buyers can file chargebacks up to 120-180 days after transaction. A 30-day hold on seller payouts ensures the platform has time to detect and respond to buyer-side payment reversals before funds leave the platform. This protects the platform from negative balances and protects legitimate sellers from clawbacks. All payout parameters are adjustable via the Admin Portal's fee configuration panel.

### 2.4 Seller Payout Tiers

| Tier | Requirements | Payout Delay | Rolling Reserve | Reserve Release |
|---|---|---|---|---|
| **New** | 0-3 months | 30 days | 15% | 90 days |
| **Established** | 3+ months, good history | 14 days | 10% | 60 days |
| **Top** | Trusted, low chargeback rate | 7 days | 5% | 30 days |

### 2.5 Buyer Limits

| Status | Max Contract Value | Searches/Month |
|---|---|---|
| Pre-KYC | $500 | 10 |
| Post-KYC | Unlimited | Unlimited |

### 2.6 Buyer Campaign Report

Sent via email when contract ends:

| Report Section | Data |
|---|---|
| Campaign Summary | Name, duration, quality tier, download flag |
| Total Spent | Campaign value + platform fees (itemized) |
| Platform Fees | 5% + $0.50, upload, views, downloads, email fees |
| Total Watchers | Unique sellers who completed >=1 view |
| Total Views Completed | Total views across all sellers |
| Seller Payout | Total amount paid to sellers |
| Unspent Refund | Amount returned from sellers who didn't watch |
| Download Activity | If enabled, how many used it |

---

## 3. FEES - COMPLETE EXPLANATION

### 3.1 Buyer Payment Breakdown (Example: $10,000 Campaign)

| Fee | Calculation | Amount | Non-refundable |
|---|---|---|---|
| Campaign Value | Seller payout pool | $10,000.00 | Refundable if unspent |
| Base Fee | 5% × $10,000 + $0.50 | $500.50 | Yes |
| Video Upload | 10 videos × $0.025 | $0.25 | Yes |
| View Fee | 5 views × 1,000 sellers × $0.0025 | $12.50 | Yes |
| Download Fee | 1,000 sellers × $0.0125 (if enabled) | $12.50 | Yes |
| Email Fee | (1,000 / 100) × $1.00 | $10.00 | Yes |
| **Total Customer Charge** | | **$10,535.75** | |

### 3.2 Seller Earnings (Same Campaign)

| Scenario | Calculation | Seller Earns |
|---|---|---|
| All 1,000 sellers watch 5× | 1,000 × 5 × $1.00 | $5,000 split |
| Only 800 sellers watch 5× | 800 × 5 × $1.00 | $4,000 paid out |
| Unspent returned to buyer | | $1,000 refunded |

### 3.3 Total Cost Examples (Fee Ambiguity Clarified)

**Example A: $500 Campaign (Local coffee shop, 30-second ad)**

| Component | Calculation | Amount |
|---|---|---|
| Campaign Value | Seller payout pool | $500.00 |
| Base Fee | 5% × $500 + $0.50 | $25.50 |
| Video Upload | 1 video × $0.025 | $0.03 |
| View Fee (Standard 720p) | 1 view × 200 sellers × $0.0025 | $0.50 |
| Email Fee | (200 / 100) × $1.00 | $2.00 |
| Stripe Processing | 2.9% × $528.03 + $0.30 | $15.61 |
| **Total Buyer Charge** | | **$543.64** |
| Seller Payout (if all watch) | $500 split among watchers | ~$2.50/seller |
| Platform Revenue | Fees - Stripe - AWS costs | ~$12.42 |

**Example B: $10,000 Campaign (DTC brand, 30-second ad, 1,000 viewers)**

| Component | Calculation | Amount |
|---|---|---|
| Campaign Value | Seller payout pool | $10,000.00 |
| Base Fee | 5% × $10,000 + $0.50 | $500.50 |
| Video Upload | 5 videos × $0.025 | $0.13 |
| View Fee (Standard) | 5 views × 1,000 sellers × $0.0025 | $12.50 |
| Download Fee | 1,000 sellers × $0.0125 (if enabled) | $12.50 |
| Email Fee | (1,000 / 100) × $1.00 | $10.00 |
| Stripe Processing | 2.9% × $10,535.63 + $0.30 | $305.83 |
| **Total Buyer Charge** | | **$10,841.46** |
| Seller Payout (if all watch) | $10,000 split among watchers | ~$2.00/seller/view |
| Platform Revenue | Fees - Stripe - AWS | ~$473-490 |

**Example C: $100,000 Campaign (Enterprise, 5-min documentary, Premium 1080p)**

| Component | Calculation | Amount |
|---|---|---|
| Campaign Value | Seller payout pool | $100,000.00 |
| Base Fee | 5% × $100,000 + $0.50 | $5,000.50 |
| Video Upload | 3 videos × $0.025 | $0.08 |
| View Fee (Premium 1080p) | 1 view × 10,000 sellers × $0.005 | $50.00 |
| Download Fee (Premium) | 10,000 sellers × $0.025 | $250.00 |
| Email Fee | (10,000 / 100) × $1.00 | $100.00 |
| Stripe Processing | 2.9% × $105,400.58 + $0.30 | $3,057.12 |
| **Total Buyer Charge** | | **$108,457.70** |
| Seller Payout (if all watch) | $100,000 split among watchers | ~$10.00/seller |
| Platform Revenue | Fees - Stripe - AWS | ~$4,840-5,050 |

**What this shows:** The buyer's effective total cost is ~8.4% above campaign value (platform fees + Stripe). The seller receives the full campaign value (minus reserve and Stripe payout fee). Platform fees scale with campaign complexity, not just size.

### 3.4 Platform Revenue

| Stream | Per $10K Campaign |
|---|---|
| Base Fee (5% + $0.50) | $500.50 |
| Upload Fees | $0.25 |
| View Fees | $12.50 |
| Download Fees (if enabled) | $12.50 |
| Email Fees | $10.00 |
| **Total Platform Revenue** | **$523.75 - $536.25** |

---

## 4. SECURITY & SCANNING

### 4.1 Malware Detection Pipeline

All uploaded content (videos + images/logos) goes through:

1. ClamAV Pre-Scan
   - Detects known malware signatures
   - Blocks known threat patterns
2. Transcoding/Re-encoding
   - Rebuilds container from scratch (strips container exploits)
   - Strips metadata, subtitles, non-video tracks
   - Neutralizes 90%+ of embedding attacks
3. GuardDuty Post-Scan
   - AWS managed malware protection
   - ML-based detection
   - 99%+ commercial-grade detection rate

### 4.2 Threat Coverage

| Threat Type | Mitigation | Effectiveness |
|---|---|---|
| Container header exploits | Transcoding rebuilds container | Near 100% |
| Disguised executables | ffmpeg decode fails + scan | Near 100% |
| Embedded scripts | Metadata/subtitles stripped | Near 100% |
| Known malware signatures | ClamAV + GuardDuty | ~99%+ |
| Steganographic payloads | Transcoding disrupts LSB/MV | ~90-95% |
| Subtitle parser exploits | Explicitly excluded in transcode | Near 100% |

### 4.3 Security Scanning Costs

| Scanner | Cost (1,000 videos) | Maintenance |
|---|---|---|
| ClamAV (self-managed) | ~$2.05/mo | Moderate (definition updates) |
| Transcoding (ffmpeg) | ~$15/mo (Lambda compute) | Low |
| GuardDuty | ~$45.22/mo | Zero (fully managed) |
| **Total** | **~$62.27/mo** | |

### 4.4 Platform Security

| Feature | Implementation |
|---|---|
| **Two-Factor Authentication (2FA)** | Required for high-value actions |
| **Session Management** | Device history, view/suspend sessions |
| **Rate Limiting** | Redis-based, per-user/IP/key |
| **Anomaly Detection** | Flag unusual activity patterns |
| **Bot Detection** | CAPTCHA, behavioral analysis, IP reputation |
| **Audit Logging** | All sensitive operations logged |
| **RBAC** | Role-based access control for all portals |
| **Database Encryption** | Encrypted at rest + in transit |
| **API Auth** | API keys tied to KYC-verified accounts |

---

## 5. CHARGEBACK MITIGATION

### 5.1 Risk Analysis

| Party | Can File Chargeback? | Risk Level |
|---|---|---|
| **Buyer** (advertiser) | YES - card payment | HIGH - main risk |
| **Seller** (viewer) | NO - receives payouts via Stripe Connect | None |

### 5.2 Buyer-Side Chargeback Mitigation Stack

| Layer | Tool | Cost | Coverage |
|---|---|---|---|
| 1. Prevention | Stripe Radar ML + custom rules | $0.02-0.07/txn | Blocks 38% fraud before it happens |
| 2. Liability Shift | Adaptive 3D Secure 2.0 | Free with Radar | Fraud liability shifts to card issuer |
| 3. Insurance | Stripe Chargeback Protection | 0.4% of volume | Auto-reimburses fraud disputes (amount + fee) |
| 4. Recovery | Smart Disputes (auto-evidence) | 30% if won | AI fights remaining disputes automatically |
| 5. Structural | Delayed payouts + rolling reserves | Free (operational) | Most effective for service disputes |
| 6. Operational | Refund-first customer support | Free | Prevents chargebacks in first place |

### 5.3 Chargeback Response

| Scenario | Action |
|---|---|
| Buyer files chargeback | Flag to admin + ban buyer + ban all linked accounts |
| Fraud dispute | Chargeback Protection auto-reimburses |
| Service dispute | Smart Disputes auto-evidence submission |
| Max chargeback window | Up to 120-180 days (6 months) |

### 5.4 Evidence Collection for Disputes

| Evidence Type | What to Store | Use Case |
|---|---|---|
| Delivery logs | Exact timestamps, IP, device per view | Product not received |
| Face verification | Face embedding hash (one-way SHA-256), start/end timestamps, infraction log (type + timestamp) | Seller verified watching |
| T&C acceptance | Digital signature at purchase | Not as described |
| Video listing snapshot | Exact listing at time of purchase | Not as described |
| Customer communication | Emails, chat logs | All scenarios |
| Access activity log | Account access records | Unauthorized transaction |

---

## 6. ATTENTION VERIFICATION SYSTEM

### 6.1 Why Full Biometric Verification at MVP

AttnValue is an **attention marketplace**, not an impression marketplace. The core value proposition to buyers is: *"You only pay for proven human attention."* This guarantee is only meaningful if the verification can detect bots, automated scripts, pre-recorded video loops, multi-tab passive playback, and other fraud vectors. Tab-focus-only or click-based verification can be trivially bypassed with browser automation tools.

Full biometric verification (webcam + face presence + gaze estimation) provides:
- **Proof a human is present**, not just a browser tab in focus
- **Proof the human is watching**, not looking away or multitasking
- **Proof the human is unique**, not a deepfake or pre-recorded loop
- **Detection of attention breaks** via gaze tracking and head pose estimation

Ad pauses on infraction and provides real-time feedback. This is how AttnValue differentiates from every other ad platform — and it's why buyers will pay a premium.

### 6.2 Model: Binary Pass/Fail

**Pass:** Viewer completed the full ad video with zero infractions (or within the adjustable grace period).
**Fail:** Any infraction beyond the threshold → ad stops immediately → seller notified in real-time.

**Payout is binary:**
- **Pass** → full seller payout
- **Fail** → $0 payout, regardless of how much of the video was watched

### 6.3 Active Challenge-Response (Start & End)

| Phase | Action | Duration | Purpose |
|-------|--------|----------|---------|
| **Start Challenge** | "Blink twice to begin watching" - counts 2 blinks via EAR (Eye Aspect Ratio) | 3-5s overlay | Confirms real human present at session start |
| **End Challenge** | "Nod once to confirm you watched" - detects head nod | 3-5s overlay | Closes the session, verifies same person throughout |

**Implementation:**
- WebRTC `getUserMedia({ video: { facingMode: "user" } })`
- Local ONNX runtime with MediaPipe face mesh — all processing in-browser
- Raw video frames never leave the browser
- Start challenge stores `session_start_ts` + SHA-256 `face_embedding_hash` (one-way, non-reversible) for continuity check at end

**Start challenge failure modes:**
- No camera detected → block playback
- No face detected after 10s → block
- < 2 blinks in 15s → retry once, then block
- Multiple faces detected → block (must be alone)

### 6.4 Passive Continuous Verification (During Ad)

Runs every ~500ms in a Web Worker. All processing is **local** — no data leaves the browser during the ad.

#### Signal A — Face Presence & Continuity

| Check | Implementation | Weight |
|-------|---------------|--------|
| Face detected in frame | MediaPipe face mesh | 40% |
| Single face only | Face count == 1 | 10% |
| Face embedding consistency | Cosine similarity > 0.85 between successive frames | 20% |

#### Signal B — Gaze & Attention

| Check | Implementation | Weight |
|-------|---------------|--------|
| Eyes open (not blinked away) | EAR > threshold | 15% |
| Gaze direction toward screen | Head pose estimation (nose vector + eye landmarks) | 10% |
| Natural micro-saccades | Gaze jitter within 0.5-5° every 0.3-4s | 5% |

#### Signal C — Environment Integrity

| Check | Implementation | Weight |
|-------|---------------|--------|
| Browser tab focused | `document.visibilityState === 'visible'` | 20% |
| Window not minimized | No blur events | 5% |
| No DevTools open | `outerWidth - innerWidth` detection | 5% |
| Consistent frame cadence | Camera timestamps vs `performance.now()` — real webcam has micro-jitter | 10% |

#### Signal D — Interaction (if ad is clickable/scrollable)

| Check | Implementation | Weight |
|-------|---------------|--------|
| Mouse movement while face present | Cursor + gaze correlation | 10% |
| Click/tap within ad area | Event listener | 5% |
| Scroll behavior | Natural vs bot-like | 5% |

### 6.5 Infraction Rules

When any signal drops below threshold for longer than the **grace period**, an infraction is recorded.

| Infraction | 1st Occurrence | 2nd Occurrence |
|------------|---------------|----------------|
| Tab loses focus (alt-tab / window switch) | Ad stops → overlay with reason → ad restarts from **beginning** | Permanent FAIL — session over, no payout |
| Face leaves frame > grace period | Same — restart from beginning | Permanent fail |
| Multiple faces detected | Same — restart from beginning | Permanent fail |
| Eyes closed > grace period | Same — restart from beginning | Permanent fail |
| Camera disconnected | Same — restart from beginning | Permanent fail |
| DevTools opened | Same — restart from beginning | Permanent fail |

**Grace period default:** 3s (admin-adjustable via panel, 0-10s)
**Infraction counter:** Per-session (resets for each new watch attempt)
**Strike reset:** Strikes reset on successful session completion (admin-toggleable)
**Minimum time between strikes:** 0s — failing 2s into a restart counts as the 2nd occurrence immediately

### 6.6 Admin-Adjustable Parameters Panel

| Parameter | Default | Range |
|-----------|---------|-------|
| Grace period (seconds) | 3 | 0-10s |
| Tab switch max before fail | 2 | 0-10 |
| Face lost max before fail | 2 | 0-10 |
| Multiple faces max before fail | 2 | 0-10 |
| Eyes closed max before fail | 2 | 0-10 |
| Camera lost max before fail | 2 | 0-10 |
| DevTools max before fail | 2 | 0-10 |
| Reset strikes on successful completion | true | true/false |
| Minimum time between strikes to count separately | 0 | 0-60s |

Each infraction type has independent thresholds so admin can tune per risk level.

### 6.7 Viewer Overlay Messages

| Trigger | Overlay Text |
|---------|-------------|
| Tab switch | *"Ad paused — you switched tabs. Close to restart from the beginning."* |
| Face left frame | *"Ad paused — you moved away from the camera. Close to restart."* |
| Multiple faces | *"Ad paused — multiple faces detected. Please view alone. Close to restart."* |
| Eyes closed | *"Ad paused — eyes were closed too long. Close to restart."* |
| Camera lost | *"Ad paused — camera disconnected. Close to restart."* |
| DevTools opened | *"Ad paused — developer tools detected. Close to restart."* |
| Permanent fail | *"Session ended — too many interruptions."* (no restart offered) |

### 6.8 Real-Time Seller Feedback (WebSocket)

Seller receives notification instantly on every infraction, not after session ends.

**WebSocket event — infraction (1st occurrence):**
```json
{
  "type": "ad_infraction",
  "session_id": "sess_abc123",
  "buyer_id": "buy_xyz",
  "ad_id": "ad_456",
  "timestamp_seconds": 14.5,
  "total_duration_seconds": 30,
  "progress_pct": 48.3,
  "infraction_type": "tab_switch",
  "occurrence_number": 1,
  "action": "restart",
  "session_status": "restarted"
}
```

**WebSocket event — permanent fail (2nd occurrence):**
```json
{
  "type": "ad_failed",
  "session_id": "sess_abc123",
  "buyer_id": "buy_xyz",
  "ad_id": "ad_456",
  "fail_reason": "2nd tab switch",
  "total_time_watched_seconds": 22.0,
  "payout_due": 0.00
}
```

### 6.9 Buyer Dashboard Indicators

Buyers see:
- **Completion rate** — what % of sessions passed vs failed
- **Fail breakdown** by infraction type (e.g., "17% tab switches, 3% face lost")
- **Average time-watched-before-fail** for failed sessions
- **Viewer quality filters** — option to exclude viewers with low completion rates from future campaigns

### 6.10 Seller Appeal Flow

If a seller believes a session was incorrectly failed, they can:

1. View an anonymized **session heatmap** showing: time segments, infraction type and timestamp, reason codes for each triggered signal
2. Submit a **one-click appeal** — no form, no support ticket
3. Appeal reviewed within **24 hours** — automated replay re-running verification pipeline on recorded session frames; if still ambiguous, human admin review
4. If upheld, session is marked as passed and payout is issued

**Target KPIs:**
- < 3% of all sessions appealed
- < 1% of appeals upheld
- False positive rate published on trust page

### 6.11 Privacy & GDPR Compliance

- All biometric processing is **local** — raw video frames *never* leave the browser
- Data transmitted to server:
  - `session_id`, `start_ts`, `end_ts`
  - `session_status` (pass/fail)
  - `face_embedding_hash` (SHA-256 — one-way, non-reversible)
  - `infraction log` (type + timestamp only, no video/images)
- No raw video, no images, no biometric templates stored server-side
- **DSR:** "Delete my data" = drop the hash and infraction timestamps
- **Consent:** Explicit opt-in at account creation (biometric verification consent, documented in ToS)
- **Retention:** Session scores retained 90 days (chargeback window), then aggregated/anonymized

### 6.12 Edge Cases

| Case | Handling |
|------|----------|
| Short videos (< 15s) | No passive verification needed — start + end challenge only. Pass = both completed |
| User watches via mobile | Use front camera + gyroscope — head movement must match gyro data |
| Multiple ads in one session | Start challenge once, passive continues, end challenge once. If gap > 5min between ads, re-challenge |
| User in dark room | IR face detection may fail — fallback to browser focus + interaction signals (lower confidence) |
| User wears glasses/hat/mask | MediaPipe handles most occlusions. Sunglasses → EAR fails, but head pose + tab focus still work |
| User watches on TV (no camera) | Not supported at MVP. Requires webcam |
| Pet/kid walks into frame | Multiple faces → infraction. 1st = restart, 2nd = fail |
| Network glitch (camera freezes) | Frame cadence anomaly → if > grace period, infraction. Auto-recovers when camera returns |
| Background lighting change | Temporary dip → recovers in 1-2s when tracking re-acquires |
| Extremely short restart (2s) | Still counts as 1st occurrence. 2nd infraction immediately after = permanent fail |

---

## 7. KYC SYSTEM

### 7.1 Requirements

| Party | KYC Required? | Components |
|---|---|---|
| **Buyers** | Yes (before first campaign) | Face matching + Phone + ID document |
| **Sellers** | Yes (before first payout) | Progressive: Phone + email verification first, full ID document KYC before payout |

### 7.2 Progressive KYC for Sellers

Progressive (tiered) KYC is legally sound under the **Risk-Based Approach (RBA)** recommended by the Financial Action Task Force (FATF) and adopted by virtually all national AML regulators. The principle is: customer due diligence (CDD) measures are proportionate to the assessed risk level, not one-size-fits-all.

**How it works for sellers:**

| Step | Method | When | Risk Basis |
|---|---|---|---|
| 1. Phone verification | SMS code to mobile | Before first viewing session | Low — no money moves until this completes |
| 2. Email verification | Link click | Before first viewing session | Low |
| 3. Identity verification (Full KYC) | Upload government ID + selfie + InsightFace face matching + duplicate detection | Before first payout (after $20+ accumulated earnings) | Standard — required before funds leave the platform |

This means sellers can start earning with just phone + email verification. Full document KYC is required before any payout — ensuring compliance with AML regulations while minimizing onboarding friction.

### 7.3 Legal Basis for Progressive KYC

| Jurisdiction | Applicable Law / Standard | Why It Supports Progressive KYC |
|---|---|---|
| **International** | [FATF Recommendation 10](https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatfrecommendations.html) — Customer Due Diligence | Mandates a **risk-based approach**: CDD measures are proportionate to risk. Simplified due diligence is permitted when risks are lower. |
| **International** | [FATF Guidance on Risk-Based Approach](https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatfguidanceontherisk-basedapproachtocombatingmoneylaunderingandterroristfinancing-highlevelprinciplesandprocedures.html) | Explicitly states: "Simplified [CDD] measures may be appropriate in situations where low-risk is established." Regulated entities should assess risk and apply appropriate measures, not identical measures to all customers. |
| **European Union** | [EU AML Directive (AMLD5) — Directive (EU) 2018/843](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32018L0843) | Article 13(4) allows Member States to permit simplified CDD where lower risks are identified. Article 15 requires enhanced CDD for higher risks. |
| **United Kingdom** | [The Money Laundering, Terrorist Financing and Transfer of Funds (Information on the Payer) Regulations 2017](https://www.legislation.gov.uk/uksi/2017/692/contents) | Regulation 33 requires a risk-sensitive approach. Regulation 37 permits simplified due diligence where lower risk is established. |
| **United States** | [FinCEN Customer Due Diligence Rule (31 CFR 1010.230, 1020.220)](https://www.fincen.gov/resources/statutes-and-regulations/cdd-final-rule) | Requires risk-based procedures for CDD. Not all customers require the same level of verification — procedures must be commensurate with risk. |
| **Singapore** | [MAS Notice 626 (AML/CFT)](https://www.mas.gov.sg/regulation/notices/notice-626) | Paragraph 6.2 requires CDD measures that are risk-based. Simplified CDD permitted for lower-risk customers. |
| **UAE** | [ADGM AML Rulebook 2024](https://assets.adgm.com/download/assets/Anti-Money+Laundering+and+Sanctions+Rules+and+Guidance+AML+20250210.pdf) | Section 5.3 requires risk-based CDD. Simplified measures permitted where ML/TF risk is assessed as low. |
| **China** | [PIPL Article 6](http://www.npc.gov.cn/englishnpc/c23934/202112/1abd8837858940b38e88e6b62653334e.shtml) + [PBOC AML Regulations](http://www.pbc.gov.cn/english/130721/3133946/index.html) | Requires data minimization (collect minimum necessary). Progressive KYC aligns with PIPL's purpose limitation and necessity principles. |
| **Japan** | [APPI Article 17](https://www.ppc.go.jp/en/legal/) | Requires purpose-specific, minimum necessary collection. Progressive KYC collects only what's needed at each stage. |
| **South Korea** | [PIPA Article 16](https://pipc.go.kr/en/) | Requires collection within minimum scope reasonably related to purpose. |
| **Canada** | [PCMLTFA Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-184/) | Section 59(1)(b): "If the entity determines that there is a low risk of a money laundering or terrorist financing offence, it may conduct simplified measures." |
| **Australia** | [AML/CTF Act 2006](https://www.legislation.gov.au/C2006A00099/latest/text) | Section 35: risk-based CDD. AUSTRAC guidance explicitly permits simplified CDD for low-risk customers. |
| **Brazil** | [LGPD Article 6](https://www.gov.br/anpd/pt-br) + [COAF AML Rules](https://www.gov.br/coaf/pt-br) | Requires data minimization and proportionality. Progressive KYC is consistent with LGPD principles. |

### 7.4 KYC Flow

- Seller starts with phone verification (SMS code) + email — can begin viewing ads immediately
- Full KYC (ID upload + selfie + InsightFace matching + duplicate detection) must be completed before first payout
- Buyers complete full KYC before first campaign creation
- All users screened against sanctions lists at regular intervals

---

## 8. REFERRAL PROGRAM

| Parameter | Detail |
|---|---|
| **Type** | Dual-sided (buyer + seller) |
| **Reward** | Platform credits only (not cash) |
| **KYC Requirement** | Referred user must complete KYC before reward unlocks |
| **Credit Usage** | Seller credits for viewing, search credits for buyers |
| **Non-convertible** | Credits cannot be withdrawn as cash |

---

## 9. SOCIAL PROOF FEATURES

| Feature | Detail |
|---|---|
| **Verified Badges** | KYC-completed users get verified badge |
| **Seller Ratings** | Post-view rating system |
| **Live Activity Feed** | Real-time activity on platform |
| **Countdown Timers** | Contract expiry timers visible |
| **Leaderboards** | Top sellers by earnings |
| **Shareable Profiles** | Sellers can share profile links externally |

---

## 10. TRUST & SAFETY

| Feature | Implementation |
|---|---|
| **Report Button** | Flag content/users for review |
| **Trust-Based Moderation** | Trust-weighted reports (trusted users = higher weight) |
| **Automated Moderation** | Flag suspicious patterns |
| **Manual Review** | Admin panel for dispute resolution |
| **Dispute Resolution** | Automated (low-value) + Manual (high-value) |

---

## 11. SUPPORT SYSTEM

| Channel | Detail |
|---|---|
| **In-app chat** | Real-time support chat |
| **Knowledge base** | FAQ and help articles |
| **Priority support** | For enterprise buyers |

---

## 12. NOTIFICATIONS & EMAIL

### 12.1 Email Service

| Parameter | Detail |
|---|---|
| **Provider** | AWS SES |
| **Email Fee** | $1 per 100 targeted sellers |
| **From** | Buyer brand name + logo in seller emails |

### 12.2 Email Triggers

| Trigger | Recipient | Content |
|---|---|---|
| New ad available | Seller | Buyer logo + "New ad to watch" |
| Campaign complete | Buyer | Full report (spent, views, refund) |
| Payout available | Seller | Payout amount + request link |
| Chargeback filed | Admin | Alert + buyer details |
| KYC complete | User | Confirmation |
| UBI distributed | Seller | Amount received |

### 12.3 Seller Notification Preferences

| Option | Default |
|---|---|
| Per new ad (immediate) | Default |
| Daily digest | Optional |
| Weekly digest | Optional |
| None (manual check-in) | Optional |

---

## 13. BUYER API

### 13.1 API Capabilities

| Category | Endpoints |
|---|---|
| **Campaign Management** | Create, read, update, pause, delete campaigns |
| **Video Upload** | Upload ads with metadata (title, description, targeting) |
| **Targeting** | Set demographics, regions, seller criteria, view limits |
| **Reports** | Pull performance data (views, watchers, spend, completion rate) |
| **Webhooks** | Notify when campaign completes, report ready, chargeback |
| **Pricing** | Query available tiers & current fees |
| **Transaction History** | Download CSV exports |

### 13.2 API Implementation

| Feature | Detail |
|---|---|
| **Auth** | API keys tied to KYC-verified buyer accounts |
| **Rate Limits** | Per-key: requests/minute, campaign creates/hour |
| **Premium Tier** | API access requires buyer KYC + minimum campaign value |
| **Documentation** | OpenAPI/Swagger docs auto-generated |

---

## 14. GAMIFICATION

| Feature | Detail |
|---|---|
| **Levels** | Experience points for watching/completing ads |
| **Streaks** | Daily watch streak bonuses |
| **Badges** | Achievement badges (100 views, 1 year member, etc.) |
| **Challenges** | Time-limited challenges with bonus credits |

---

## 15. THREE PORTALS

### 15.1 Seller Portal

- Dashboard: Earnings, available ads, history
- Ad Watch: Video player + verification flow
- KYC: Upload documents, check status
- Payouts: Request payout, view history
- Profile: Shareable profile, settings
- Reports: Personal earnings reports

### 15.2 Buyer Portal

- Dashboard: Active campaigns, performance metrics
- Campaign Creation: Create ads, set targeting, upload videos
- Reports: Campaign analytics, download CSV
- API Keys: Generate/manage API keys, webhooks
- Profile: Company info, payment methods

### 15.3 Admin Portal

- User Management: View/ban users, manage KYC
- Campaign Moderation: Review campaigns, approve/reject
- Dispute Resolution: Review and resolve disputes
- Platform Analytics: GTV, MAU/DAU, payout volume, UBI distributed
- UBI Management: View pools, trigger distributions
- Fee Configuration: Adjust base percentage, view/download fees
- Content Management: Blog posts, SEO settings
- Audit Logs: All sensitive operations log

---

## 16. BLOG & SEO

| Feature | Detail |
|---|---|
| **Markdown Blog Engine** | Admin writes posts in Markdown |
| **SEO URLs** | `/blog/post-slug` with canonical tags |
| **Sitemap** | Auto-generated `sitemap.xml` |
| **RSS Feed** | Subscribe to new posts |
| **Categories & Tags** | Organize content for topic clusters |
| **Open Graph / Twitter Cards** | Social share previews |
| **Schema.org Structured Data** | Article, BlogPosting, FAQPage |
| **Draft/Publish Workflow** | Schedule posts, preview |
| **Blog Search** | Full-text search within blog |

---

## 17. TECH STACK

### 17.1 Frontend

| Technology | Purpose |
|---|---|
| **React 19.2** | UI framework |
| **TanStack Router/Start v1** | Routing + SSR |
| **Vite 7** | Build tool |
| **Zustand v5** | State management |
| **Tailwind CSS 4** | Styling |
| **Framer Motion / Motion** | Animations |
| **Recharts** | Charts and analytics |

### 17.2 Backend

| Technology | Purpose |
|---|---|
| **Node.js + Express** | API server |
| **Prisma** | ORM / data access |
| **PostgreSQL** | Primary database |
| **Redis + Bull** | Caching + job queues |

### 17.3 Infrastructure

| Technology | Purpose |
|---|---|
| **AWS ECS Fargate** | Compute (app servers) |
| **AWS RDS PostgreSQL** | Database |
| **AWS ElastiCache Redis** | Caching |
| **AWS S3** | Video/image storage |
| **AWS CloudFront** | CDN for assets + video |
| **AWS SES** | Email service |
| **AWS GuardDuty** | Malware scanning |
| **AWS Elemental MediaConvert** | Video transcoding |
| **Terraform** | Infrastructure as Code |

### 17.4 Development

| Tool | Purpose |
|---|---|
| **pnpm workspaces** | Monorepo management |
| **Docker Compose** | Local dev (PostgreSQL + Redis) |
| **Vitest** | Testing |
| **Stripe Connect Express** | Payment processing |

---

## 18. AWS INFRASTRUCTURE COSTS

### 18.1 MVP Scale (<1k MAU)

| Service | Monthly Cost |
|---|---|
| RDS PostgreSQL (t4g.small, 20GB) | ~$27 |
| ECS Fargate (0.5 vCPU × 2) | ~$34 |
| ElastiCache Redis (t4g.micro) | ~$11 |
| S3 + CloudFront (~10GB assets) | ~$5 |
| Application Load Balancer | ~$20 |
| GuardDuty | ~$5 |
| AWS SES | ~$2 |
| Route 53 + Secrets Manager | ~$2 |
| Data transfer (~50GB) | ~$5 |
| **Total** | **~$111/month** |

---

## 19. LOCAL DEVELOPMENT

### 19.1 Mock External Services

All external services mocked for local development:

| Service | Mock Approach |
|---|---|
| Stripe | Stripe test mode keys |
| InsightFace | Local Docker container |
| AWS SES | Local SMTP server (Mailpit) |
| AWS GuardDuty | Skip mock; ClamAV runs local |
| Blockchain explorers | Not used (internal DB) |

### 19.2 Docker Compose Services

| Service | Purpose |
|---|---|
| PostgreSQL | Database |
| Redis | Caching + Queue |
| ClamAV | Malware scanning |
| Mailpit | Local email testing |

### 19.3 Demo Accounts

| Account | Type | Pre-seeded Data |
|---|---|---|
| **demo-buyer** | Buyer/Advertiser | KYC complete, $5,000 balance |
| **demo-seller** | Seller/Viewer | KYC complete, 50 completed views |
| **demo-admin** | Admin | Full admin access |

---

## 20. ESTIMATED TIMELINE

### Full MVP + Maximum Polish: 16-24 weeks (4-6 months)

| Phase | Duration |
|---|---|
| Phase 1: Foundation (monorepo, Docker, Prisma, auth) | 1-2 weeks |
| Phase 2: Seller Portal (registration, KYC, dashboard, video player) | 2-3 weeks |
| Phase 3: Buyer Portal (campaign creation, analytics, API) | 2-3 weeks |
| Phase 4: Admin Portal (user mgmt, moderation, analytics, blogs) | 2 weeks |
| Phase 5: Payments & UBI (Stripe Connect, UBI, payouts) | 1-2 weeks |
| Phase 6: Social Proof & Trust (referrals, 2FA, anomaly detection) | 2 weeks |
| Phase 7: Polish & UX (mobile, emails, accessibility, notifications) | 3-4 weeks |
| Phase 8: Gamification (levels, streaks, leaderboards) | 2-3 weeks |
| Phase 9: Testing & Stabilization (integration tests, bug fixes) | 2 weeks |

---

## 21. GO-TO-MARKET

### Launch Strategy

| Parameter | Detail |
|---|---|
| **Launch Type** | Open signup (not invite-only) |
| **Languages** | English-only at launch. i18n framework will support future languages as platform expands. |
| **Launch Regions** | Country-specific UBI pools enabled from day 1 |

### Compliance

| Area | Detail |
|---|---|
| **Funds Custody** | No custody - Stripe Connect Express holds funds (licensed) |
| **MSB License** | Not needed (Stripe holds the money) |
| **KYC** | Both buyers and sellers (AML compliance) |
| **Tax Reporting** | Transaction export + 1099-K helpers |

### Disaster Recovery

| Metric | Target |
|---|---|
| RTO (Recovery Time Objective) | 4 hours |
| RPO (Recovery Point Objective) | 15 minutes |
| Backups | Automated daily + PITR |

### North Star Metric

**Gross Transaction Value (GTV)** - total value of all completed contracts

---

## 22. MVP SCOPE REDUCTIONS (Optional)

### Could defer for faster launch:

| Feature | Timeline Impact |
|---|---|
| Full observability (CloudWatch, X-Ray) | Defer - saves ~1 week |
| Advanced referral program | Defer - saves ~1 week |
| In-platform dispute system | Defer - saves ~1 week |
| Support tickets system | Defer - saves ~1 week |
| Ratings & reviews | Defer - saves ~1 week |
| Gamification | Defer - saves 2-3 weeks |
| Buyer API | Defer - saves ~1 week |
| Blog/SEO system | Defer - saves ~1 week |

### Fast-Track MVP: ~8-10 weeks (all above deferred)

---

## 23. POTENTIAL FRAUD VECTORS & MITIGATIONS

### Seller-Side Fraud

| Vector | Mitigation |
|---|---|---|
| Bot-based view farming | Start/end blink challenges, passive face tracking throughout, gaze verification, tab focus detection |
| Multi-account farming | Device fingerprinting, IP analysis, duplicate face detection (SHA-256 hash comparison), phone verification |
| Face spoofing | Start challenge liveness (blink detection), face embedding continuity check between start and end |
| Pre-recorded video loop attack | Real-time challenge-response (blink at start, nod at end), frame cadence timing analysis, face embedding consistency across session |
| Deepfake / real-time face swap | Face embedding similarity checks across session, micro-expression timing analysis, challenge-response |
| Referral self-referral | KYC verification before reward unlock |
| UBI duplicate accounts | KYC deduplication (face + phone + ID) |

### Buyer-Side Fraud

| Vector | Mitigation |
|---|---|
| Payment fraud / stolen cards | Stripe Radar, 3DS, KYC, pre-authorization |
| Chargeback fraud | Chargeback Protection, payout delays, reserves, account ban |
| Malicious video upload | ClamAV -> Transcode -> GuardDuty pipeline |
| Phishing via video | Scan metadata, moderation queue, report button |

### Content Attacks

| Vector | Mitigation |
|---|---|
| Steganographic malware | Transcoding disrupts LSB/MV embedding |
| Container exploits | Transcode rebuilds container, strips metadata |
| Disguised executables | File type validation + ffmpeg decode check |

### Platform Attacks

| Vector | Mitigation |
|---|---|
| Account takeover | 2FA, session management, rate limiting |
| API abuse | Rate limiting, API key rotation, anomaly detection |
| Data exfiltration | Audit logging, RBAC, encryption |

---

*Prepared for Hermes Swarm review - May 2026.*
