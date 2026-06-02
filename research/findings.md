# Research Findings

Weekly intelligence log for WiFi CSI Intrusion Detection Platform.

---

## 2026-06-01 — Initial

### 1. Hardware Sourcing
- No research run yet. Baseline pending.

### 2. OpenWrt CSI Tools
- RuView repo uses ESP32 CSI. Our platform will use OpenWrt router CSI instead.
- ath9k-csi: mature, MT7621 well supported.
- ekstra-csi: newer, MediaTek chipset focus.

### 3. Origin AI / ADT Patents
- Origin AI acquired by ADT Feb 2026 for $170M.
- ACF-based (auto-correlation function). We use phase-based — different domain.
- 225+ patents in portfolio. Need SA provisional patent for our architecture.

### 4. SA Competitors
- Olarm: R1,195 + R73/mo. Add-on to existing alarm.
- Venus: Free app, WhatsApp alerts, PIR sensors, 4G SoftSIM.
- IDS Onyyx: ~R1,600 DIY kit.
- Tuya CST-G20: R1,610, basic PIR + door sensors.
- No WiFi CSI competitors in SA market.

### 5. WhatsApp Business API
- R0.14/msg for utility templates (SA pricing).
- Free within 24h service window.
- Cloud API available in SA.

### 6. POPIA Guidance
- Section 14: retain records no longer than necessary.
- 90 days standard for security events (common insurance claims window).
- 365 days as premium tier.
- POPIA-compliant if documented in privacy policy.

### 7. CSI Research Papers
- RuView's phase coherence peak tracking approach established.
- Multi-zone path analysis for person vs. pet discrimination.
- Dual-band fusion (2.4 + 5 GHz) for packet loss resilience.

---

*Next research run: 2026-06-08*

---

## 2026-06-01 — Weekly Research

### 1. Hardware Sourcing
- HLK-7621A module (MT7621A, dual-core MIPS 880MHz) available on Alibaba as HiLink embedded module — ~$12-18/unit at small qty, integrates NAT/QoS/VPN accelerators, 5-port GbE switch
- ZBT Z8102AX-M2-T (MT7981B + MT7976CN) — WiFi 6 AX3000, 5G/4G LTE, metal case, OpenWrt compatible. Available from 524wifi.net and Chinese distributors
- Generic MT7621-based router boards on Made-in-China.com at ~$15-25 for 10 MOQ (no 100/500 MOQ pricing found — requires direct supplier inquiry)
- No Alibaba listings explicitly quote MOQ pricing at 100/500 for complete router SKUs; most require RFQ for bulk
- MT7981 (Filogic 820) is gaining traction as the newer WiFi 6 alternative to MT7621 — expect to become primary chipset for new OpenWrt sensing routers
- Shipping to SA: DHL Express ~$20-30 for single unit (3-7 day), sea freight ~$3-5/kg for bulk (4-6 weeks). Courier UK-SA from £11-21 for small parcels
- Import duties + VAT (15%) apply on declared value to SA. No significant changes in trade terms
- HLK-7621A module is attractive for custom PCB integration if we build our own hardware in future

### 2. OpenWrt CSI Tools
- **ath9k-csi**: Stable, no major recent commits. Original WANDS repo remains the reference. OpenWrt 25.12.0 (March 2026) includes updated ath9k device compatibles in iwinfo — CSI support unaffected
- **nexmon_csi**: Still maintained. New issue (Apr 2026) BCM4366c0 on RT-AC86U returns errno 95 (unsupported). Data loss issue reported Oct 2025. Hardware update request open since May 2025. Raspberry Pi 4 CSI groundwork updated (May 2026) with kernel 6.12, modified brcmfmac driver
- **ekstra-csi**: Active on OpenWrt forums (March 2026 post). User "glimmer" building WiFi sensing platform on top. Full-metadata CSI extraction for mt76 hardware (MT7621/MT7981). This is our recommended path for MediaTek-based routers
- **OpenWrt 25.12.0** (March 2026): Supports 2200+ devices. Linux kernel 6.12.71. New targets incl. Siflower SoCs, ipq50xx/60xx. Known issues: Pixel 10 + WPA3 Wi-Fi 6 problems, 802.11r FT issues with WPA3
- **MT7902** (WiFi 6E) driver: Community patches now available for Linux (Feb 2026). Firmware in linux-firmware. Relevant if we consider WiFi 6E sensing in future
- **ESP32 CSI ecosystem**: Rapidly growing. ESPectre (Home Assistant CSI motion detection), esp-csi from Espressif (official), ESP32-S3/C6 supported. Community projects for presence detection, localization, HAR
- **RuView**: Now well-documented. Uses ESP32-S3 mesh (3-6 nodes, ~$54). Docker-based deployment. Full pose estimation, breathing, heart rate through walls (up to 5m)

### 3. Origin AI / ADT
- ADT acquisition closed Feb 24, 2026 — $170M cash. 200+ early-priority global patents transferred
- Commercialization expected 2027, not immediate. Verisure signed 5-year renewable agreement ($30M development + per-home activation fee) for Europe/Latin America exclusivity
- **Compatible With Origin** program (CES 2026): Chipset partners preload Origin's Live Motion Engine. Qualcomm, Synaptics already evaluating. Commercial deployments late 2026
- **Synaptics partnership** (Jan 2026): Embedded Origin sensing in smart plugs, IoT hubs, security products — lowers integration friction for OEMs
- Origin TruShield Security uses existing IoT devices (smart speakers, plugs) as sensors — hardware-free approach
- IEEE 802.11bf support in Origin roadmap. SoC-level integration being standardized
- **No new overlapping patent filings found specifically on phase-based sensing** — our phase-based approach remains differentiated from Origin's ACF
- ADT product pipeline focused on US market premium tier — not targeting SA at R30 price point. Low risk of direct competition near-term
- Risk: Origin's "Compatible With" program could accelerate WiFi sensing adoption broadly, raising consumer awareness (good for market) but also setting expectations (need to match quality)

### 4. SA Competitors
- **Olarm**: Major move — launched **Olarm ONE** (June 1, 2026), a fully wireless smart alarm system with OPTEX detectors. Competes directly in DIY wireless alarm space. Supports up to 48 wireless devices, 150 zones, 999 users. 2000m wireless range. Dual SIM + Ethernet + WiFi backup. 24-month warranty. Price TBD at launch. 400K+ users, 900+ integrated armed response companies. This is the most significant SA competitive development — they are extending from add-on communicator to full system
- **Olarm MAX** still at R1,195 + R73/mo subscription. Olarm ONE positions them as a complete solution provider, not just accessory
- **IDS Onyyx**: Pricing stable at R2,899-R6,699 depending on kit. Available at CCTV Direct, Viscon. No significant product updates found
- **Tuya**: Smart GSM alarm kit at R1,590 (HenracTech). Basic WiFi alarm kit at R1,295. Low-end segment
- **Venus Security Solutions**: No new product announcements found. Appears stable/quiet
- **Hikvision**: Wireless alarm kits entering SA market at R1,799-R3,599 — new competitor in entry-level segment
- **No WiFi CSI competitors in SA market** — still an open gap. Olarm ONE is closest (wireless ecosystem) but uses traditional PIR sensors, not CSI
- Armed response monthly monitoring fees in SA: R200-500/mo — our R30/mo remains 7-17x cheaper

### 5. WhatsApp Business API
- **Major pricing model change**: Shifted from per-conversation to per-message billing (effective July 2025, fully rolled out by Apr 2026)
- **4 message categories**: Marketing (highest cost), Utility (~80-90% less than marketing), Authentication (low), Service (free within 24h customer service window)
- **SA pricing still ~R0.14/msg** for utility templates — no significant change detected
- **Free windows**: 24-hour customer service window (all replies free), 72-hour Free Entry Point window from Click-to-WhatsApp ads
- **Utility templates in CSW are free** — this is beneficial for us: if a user messages us first (e.g., disarm event), any utility response is free
- **Volume tiers** available for utility and authentication messages — relevant at scale
- **Template category determines cost** — must submit templates for approval with correct category. Misclassification (utility → marketing) increases cost
- No changes to region availability — SA still supported via Cloud API
- Template policy unchanged for utility notifications — security alerts qualify as utility

### 6. POPIA & Security
- **New POPIA health data regulations** published March 6, 2026 (Gov Gazette 54268) — effective immediately, no grace period
- Applies to insurance, medical schemes, employers, pension funds — **does not directly regulate security/IoT systems**
- **Information Regulator signaling tougher enforcement** (May 2026): 2025/26 Annual Performance Plan shows shift to proactive investigations, not just reactive complaint handling
- Only 33% of public bodies (278 of 853) submitted PAIA reports — private sector compliance even lower. Regulator planning legislative amendments to strengthen enforcement powers
- **Section 14 retention remains unchanged**: Records not longer than necessary for purpose. Security event data: 90 days standard, 365 days premium documented in privacy policy remains compliant
- Industry guidance emerging on cross-border transfer rules — relevant if we use non-SA cloud infrastructure (Cloudflare R2)
- Regulator pursuing high-profile enforcement actions — fines, imprisonment, compensation possible for non-compliance
- No specific IoT surveillance guidance published, but general POPIA applies to any personal information processing
- Recommendation: Document data retention policy, conduct POPIA impact assessment for CSI data classification (CSI complex numbers are not personal information under POPIA as they describe radio channel, not individuals)

### 7. CSI Research Papers
- **Wi-CCFAR (2025)**: Controllable False Alarm Rate human presence detector using normalizing flow networks. Directly applicable — uses CSI amplitude + phase for false alarm control. Published ResearchGate
- **Multi-Station WiFi CSI Sensing Framework** (arXiv 2603.11858, Mar 2026): Addresses station-wise feature missingness and limited labeled data. Multi-AP approach relevant for whole-home coverage
- **CSI-Bench**: Large-scale dataset — 460+ hours, 35 users, 26 environments, 16 device types. Multitask: fall detection, breathing, localization, HAR, user ID. Excellent resource for training and benchmarking
- **WiFi-3D-Fusion** (2025, GitHub): Open-source real-time 3D human pose from CSI. Local inference, web UI, 10 FPS. Uses DensePose-RCNN adapted for CSI
- **RuView** coverage (CNX Software, Mar 2026): Getting mainstream press attention. Raises privacy/surveillance concerns. Hardware cost ~$54 for ESP32-S3 mesh
- **DualMCN-CSI-Fall-Detection** (May 2026): Cross-environment fall detection using Mamba-Conv network. New architecture combining state space models with CNNs for CSI
- **Pre-processing of CSI signal for motion detection** (J-STAGE 2025): DC component removal + lowpass filtering improves true negative detection by 17.4%. Simple pre-processing gains
- **IEEE 802.11bf standard**: Approved 2024, now crossing into commercial deployment. Qualcomm building sensing into WiFi 7 chipsets. Privacy researchers raising concerns about beamforming-based identification (99.5% accuracy). Standard defines sensing measurement setup, reporting, initiator/responder coordination
- **Cognitive Systems WiFi Motion**: ODM integration process detailed — hardware assessment, base image integration, testing cycle. Relevant if we partner with ODM for router manufacturing
- **New CSI repos on GitHub**: esp32s3-wifi-csi-sensing (May 2026), Omni smart home presence detection, Secure WiFi CSI healthcare sensing, Spectrum Mapper with PCA/STFT

### Follow-up: ekstra-csi (key for our hardware path)
- **ekstra-csi** by Demetri Rodriguez (`imxdemetri/ekstra-csi`, Apache 2.0, Mar 2026) — full-metadata CSI extraction for MediaTek mt76 on OpenWrt
- Tested on **OpenWrt One (MT7981B)** — our target chipset. Extracts all metadata (source MAC, RSSI, SNR, sequence numbers) unlike MtkCSIdump
- BW80 gives **1,536 complex features/measurement** (256 subcarriers × 6 chains) — 17x more data than Intel 5300
- 7-20 Hz capture rate. Our recommended CSI extraction path for production

### Follow-up: rvCSI (Rust edge sensing runtime)
- **rvCSI** by ruvnet (May 2026) — Rust runtime that normalizes CSI from any source into typed events
- Ingest from Nexmon, ESP32, Intel, Atheros, file replay. DSP pipeline: Hampel filter, phase unwrap, smoothing, sliding variance, motion energy, presence detection
- Emits typed confidence-scored events. Bridges to RuVector for similarity search
- Already extracted from RuView. Could significantly accelerate our on-router processing

---

*Next research run: 2026-06-08*

---

## 2026-06-01 — Weekly Research (AttnValue-v2 Topics)

### 1. Biometric Verification
- **InsightFace v0.7** (released Apr 2026): New model packages released. Models available: buffalo_l, antelopev2, buffalo_s, buffalo_m. 99.8% LFW accuracy, <5ms inference. GitHub stars: 28.9k. Now offering commercial licensing for models (required for production use of pre-trained weights). PyPI package `insightface` (50M+ downloads).
- **InspireFace SDK**: Cross-platform C/C++ SDK with anti-spoofing and liveness detection. Supports Linux, Android, iOS, macOS, embedded devices.
- **InsightFace REST API**: New enterprise-grade API service for face swapping and high-precision recognition. HTTPS calls.
- **MediaPipe v0.10.35** (Apr 2026): Active development. FaceLandmarker C API with ImageProcessingOptions support. API3 migration nearly complete. Holistic Landmarker re-added to Python. Full-range face detection model support.
- **TensorFlow.js face-landmarks-detection**: v1.0.6 — last published ~2 years ago (stale). 29.9k weekly downloads. MediaPipeFaceMesh model with 478 keypoints. No version bumps detected.
- **ONNX Runtime**: Actively maintained on PyPI. No specific CPU face comparison benchmarks found in this research pass.
- Source: https://insightface.ai, https://github.com/deepinsight/insightface/releases, https://github.com/google-ai-edge/mediapipe/releases, https://www.npmjs.com/package/@tensorflow-models/face-landmarks-detection

### 2. Blockchain Wallet APIs
- **Etherscan**: Migrated to **API V2** — unified all 60+ EVM chains (ETH, BSC, Base, Arbitrum, HyperEVM, etc.) under single account/key. Multi-chain by changing `chainid` param. Documentation at docs.etherscan.io.
- **BscScan**: Same Etherscan API V2 infrastructure — covered by the same unified API.
- **Solscan**: Free tier (rate-limited). Pro **Lite plan** at $49/mo: 20M compute units/month, 1,000 req/min rate limit. Pro endpoints access (excludes multi-endpoints and some account metadata endpoints).
- **Blockchain.com**: Free tier — Explorer Blockchain Data API (JSON), Simple Query API (plain text), WebSockets, Market Data Exchange Rates, Charts/Statistics. Rate limits governed by API Terms of Service.
- **chainz.cryptoid.info**: Free blockchain explorer API for multiple coins (LTC, DOGE, etc.). No pricing page found — appears to remain free/no-auth.
- No deprecation warnings or major pricing changes detected on any platform.
- Source: https://docs.etherscan.io, https://docs.bscscan.com, https://docs.solscan.io/api-access/solscan-api-lite-plan.md, https://www.blockchain.com/explorer/api, https://chainz.cryptoid.info/api/

### 3. Google OAuth
- **Google Identity Services (GIS)**: Last updated 2026-02-10. No breaking changes detected. Active guide at developers.google.com/identity/gsi/web.
- **FedCM migration**: **Mandatory for new web apps** — Chrome phasing out third-party cookies. GIS now integrates FedCM API. Existing apps should migrate to FedCM.
- **Separation of auth & authorization**: GIS now enforces separation — auth API returns ID tokens only; authorization API returns access tokens only. Must call them at separate moments.
- **OAuth consent screen**: Verification required for sensitive/restricted scopes. Brand verification needed to show app name/logo (even for non-sensitive scopes). Annual re-verification for restricted scopes. Changes to approved app may trigger re-verification.
- **Authorized origins**: Standard OAuth 2.0 configuration. No policy changes detected.
- Source: https://developers.google.com/identity/gsi/web/guides/overview, https://support.google.com/cloud/answer/9110914

### 4. CloudFront SPA
- **Custom error responses** (recommended for SPAs): Configure CloudFront to return `/index.html` for 403/404 errors. This is simpler, no additional Lambda cost. Downside: all 404s return HTTP 200 (not ideal for SEO).
- **Lambda@Edge alternative**: More flexible — rewrite URLs at origin request event. Can return proper 404s for truly missing assets. Higher cost ($0.60/1M requests + Lambda compute). Good for complex routing logic.
- **Cache invalidation**: CloudFront supports `/*` wildcard invalidations. Cost: $0.005/object path. Free for up to 1,000 paths/month. Use versioned filenames (content hash in filename) to avoid invalidations entirely — just deploy new files, old ones naturally expire.
- **Best practice**: Hash-based filenames + no-cache `index.html` (cache with 0 TTL or use Cache-Control max-age=0) + custom error pages for SPA routing.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/custom-error-pages.html

### 5. Docker + pnpm
- **Official pnpm image**: `ghcr.io/pnpm/pnpm` — debian:stable-slim based, standalone binary, no Node.js bundled. Choose your own Node version. Tags: `<version>` (exact), `<major>`, `latest`.
- **Multi-stage builds** (pnpm recommended pattern):
  1. `base` stage with corepack enable
  2. `prod-deps` stage: `pnpm install --prod --frozen-lockfile` with BuildKit cache mount
  3. `build` stage: full `pnpm install` + `pnpm run build`
  4. Final: COPY from prod-deps + build stages
- **pnpm deploy** for monorepos: `pnpm deploy --filter=app1 --prod /prod/app1` — copies only necessary files and packages. Solves the symlink issue in Docker by flattening the workspace.
- **Symlink issue**: pnpm uses symlinks for workspace packages. In Docker, `pnpm deploy` is the recommended solution (flattens to regular node_modules). Alternative: `node-linker=hoisted` in `.npmrc` (not recommended — defeats purpose of pnpm).
- **pnpm fetch** for CI/CD: only needs `pnpm-lock.yaml`. Layer cache survives unless deps change.
- **Corepack enable** is the standard approach for non-official base images.
- Source: https://pnpm.io/docker

### 6. SA Fintech & Crypto Regulations
- **FSCA Crypto Asset Licensing**: Crypto Asset Service Provider (CASP) licensing framework is in effect. All crypto asset service providers must be licensed by FSCA. Biometric verification for crypto wallets may fall under FSCA oversight if tied to financial services. Exact requirements from FSCA were not reachable (site returning 404s on specific pages — may need direct inquiry).
- **POPIA & Biometric Data**: Face embeddings are classified as biometric data → personal information under POPIA. Requires:
  - Consent from data subject
  - Retention limitation (Section 14 — not longer than necessary for purpose)
  - Security safeguards for storage
  - Cross-border transfer rules if using non-SA cloud infra (R2, AWS)
- **Stripe in SA**: **Not available** for SA merchants. Stripe does not officially operate in South Africa. Alternatives:
  - **Yoco**: SA-based. R49/mo card machine + 2.5% tx fees (in-person). 2.55% online. API/SDK access. R30 startup toolkit. Fast payouts daily.
  - **PayFast**: SA payment gateway.
  - **Peach Payments**: SA-based, supports recurring billing.
- Source: https://www.yoco.com/za/pricing/, FSCA website (partial), POPIA Section 14

### 7. React Native & Mobile
- **react-native-vision-camera v5.0.11** (May 2026): 9.4k stars, 207 releases. Features: 4k/8k capture, QR/Barcode scanner, Frame Processors (JS worklets for face detection, AI), HDR/Night modes, 30-240 FPS. V4 no longer maintained (archived). Active community.
- **expo-camera**: Available for Expo managed workflow. Less performant than vision-camera but simpler setup.
- **Background geolocation**: `@transistorsoft/react-native-background-geolocation` v5 — 2.9k stars, 176 tags. Battery-conscious with motion-detection (accelerometer/gyroscope). License required for RELEASE builds only (DEBUG free). Expo plugin available. V5 migration from V4 requires new license key.
- **Expo vs bare RN for MVP**: Expo (SDK 52+) now supports most native modules. Background geolocation has Expo plugin. VisionCamera has Expo support. Expo is viable for MVP if no deeply custom native modules needed.
- Source: https://github.com/mrousavy/react-native-vision-camera, https://github.com/transistorsoft/react-native-background-geolocation

### 8. Competitors (Attention Marketplaces)
- **Swagbucks**: Pays users for surveys, watching videos, shopping. Payout via PayPal/gift cards. Model: earn SB points → redeem for cash. Typical payout: ~$5-100 per redemption. No significant pricing model changes detected.
- **InboxDollars**: Similar model — paid emails, surveys, offers. Payout starting at $30+. Both Swagbucks and InboxDollars owned by Prodege.
- **UserTesting**: Enterprise plans (Advanced → Ultimate → Ultimate+) — pricing not public (requires inquiry). Testers paid per test (varies by type). AI-powered test creation and analysis. SOC2, ISO 27001, GDPR, HIPAA compliance. 3,000+ enterprise customers.
- **Brave Browser** (crypto-based attention): 100M MAU, 42M DAO (Oct 2025). BAT token — users earn for opt-in ads. Built-in crypto wallet. Brave Search, Leo AI. Firefox 149 (Apr 2026) shipped Brave's adblock-rs component for experimentation. Continues to be the dominant crypto attention marketplace.
- **No new major crypto-based attention marketplace entrants** detected. Brave remains the leader. No significant new UBI/crypto attention platforms found.
- Source: https://www.swagbucks.com, https://www.usertesting.com/pricing, https://en.wikipedia.org/wiki/Brave_(web_browser)

---

*Next research run: 2026-06-08*
