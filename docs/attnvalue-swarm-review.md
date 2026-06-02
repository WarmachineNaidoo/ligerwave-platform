# AttnValue — Swarm Review Synthesis

**12 Hermes Workers | 8 Complete, 4 In Progress | May 14, 2026**

---

## A. What Works Well (Consensus Across All Workers)

**1. Core Differentiator is Genuine**
- Verified attention is a real gap. No major platform sells "proven human eyeballs."
- The guarantee model (pay only for verified attention, unspent refunded) is a strong buyer value prop.
- Gaze tracking + pause-on-look-away creates a fundamentally different ad product.

**2. UBI as Acquisition Narrative**
- 20% platform fees → regional pools is a genuine differentiator for seller recruitment.
- "Wealthy contribute more, equal split" messaging resonates with ethical positioning.
- Strong PR angle for launch.

**3. Technical Architecture is Sound**
- Modern stack choices consistently praised (React 19.2 + TanStack + Prisma + PostgreSQL).
- Three-portal isolation is enterprise-grade.
- GDPR compliance built-in from start (not retrofitted) mitigates regulatory risk.

**4. Dual Quality Tiers + End Cards**
- 720p Standard / 1080p Premium allows price discrimination without complexity.
- End card links for premium buyers is a simple, high-value upsell.

---

## B. Critical Risks (ELIMINATE BEFORE LAUNCH)

**#1. 30-Day Payout Contradicts UBI Messaging** (Called out by ALL workers)
- You're promoting UBI (immediate economic relief) while holding seller money for 30 days.
- New tier sells wait 30 days *and* lose 15% to reserve = 45 days total.
- **Fix**: Reduce New tier to 7 days / 10% reserve. Offer instant payout (2% fee) as opt-in. In developing markets, 30-day holds are prohibitive.

**#2. Biometric Friction Kills Seller Supply** (8 of 8 workers)
- Webcam + KYC + document upload before earning a penny → massive drop-off.
- Most gig workers expect phone verification only. Full KYC before first payout is unusual.
- **Fix**: Tiered verification — Standard (tab focus + click checks, no webcam), Premium (full biometric, higher payout). Or defer biometric to post-KYC step after first payout.

**#3. Chicken-and-Egg Remains Unsolved** (7 of 8 workers)
- Sellers need ads to watch. Buyers need sellers to reach. Both are empty at launch.
- UBI pool has zero funds until platform has transaction volume (catch-22).
- **Fix**: Bootstrap with a seller guarantee fund. Pre-commit $50-200K to guarantee minimum hourly rates for first 90 days regardless of buyer fill rate.

**#4. Fee Ambiguity / Total Take Rate Unclear** (5 of 8 workers)
- 5% + $0.50 base + usage fees + Stripe 2.9%+$0.30 + Chargeback 0.4% = total take rate ~8-10% for buyers.
- Sellers don't know their effective hourly rate from the spec.
- **Fix**: Publish a transparent "what buyers pay vs. what sellers earn" breakdown. Map the full economics.

**#5. Geographic Payout Limitations** (4 of 8 workers)
- Stripe Connect Express isn't available in all UBI-target countries (Southeast Asia, Africa, parts of LATAM).
- **Fix**: Add fallback payout rails (Wise API, local bank transfers, or crypto stablecoins).

**#6. Employment Classification Risk** (4 of 8 workers)
- Attention-scored, recurring paid work → regulators may reclassify sellers as employees.
- **Fix**: Independent contractor agreements + jurisdiction-specific legal review before launch. Model after gig platforms (Uber, Prolific) that have survived similar challenges.

**#7. False Positives Destroy Trust** (6 of 8 workers)
- Glasses, poor lighting, old webcams, disabilities → legitimate sellers flagged as inattentive.
- **Fix**: Published accuracy rates + seller appeal flow (anonymized heatmap + one-click dispute). Without this, seller trust is fragile.

---

## C. Improvement Suggestions (Incorporate into Build)

**1. TIERED VERIFICATION (Recommended by 6 workers)**
- Standard: Tab focus + periodic "are you watching?" clicks + phone gyroscope. No webcam.
- Premium: Full biometric (webcam + gaze + face presence). Higher payout per view.
- Ultra: Full gaze tracking + environment verification. Highest payout. Premium+ buyers only.
This gets sellers earning immediately without biometric friction.

**2. REDUCE SELLER PAYOUT DELAY**
- New tier: 7 days / 10% reserve (not 30/15)
- Established: 3 days / 5%
- Top: Next-day / 0%
- Add instant payout option: seller pays 2% fee to receive earnings in 24 hours.

**3. LAUNCH SINGLE-GEO, NOT 9 LANGUAGES**
- Consensus across all workers: 9 languages + 6 compliance frameworks before proving demand is over-engineering.
- Recommended launch geography: **US/UK buyers + Philippines/India sellers** (English-proficient, Stripe available, high gig economy participation).
- Expand to EU after proving unit economics.

**4. ADD BRAND SAFETY / AD MODERATION PIPELINE**
- No spec mentions what ads are allowed. Crypto scams, gambling, NSFW → destroy platform trust.
- **Fix**: Content rating tags, advertiser blocklists, publisher approval workflow before launch.

**5. ADD TARGETING CAPABILITIES BEFORE SELLING TO BUYERS**
- The spec lacks audience targeting (demographics, cohorts, interests).
- Verified attention without targeting = you're selling a verification layer, not a media buy.
- Start with basic targeting (age, gender, location, device type) and expand to interest-based.

**6. PUBLISH ATTENTION QUALITY SCORE**
- Beyond binary "verified/not verified," provide an AQ-score (1-100) based on completion rate, engagement, end-card interaction.
- Report this to buyers as tiered pricing levels.

**7. ADD SELLER ECONOMICS DASHBOARD**
- Show sellers: projected hourly rate, earnings so far, streak bonuses, attention score history.
- Transparency builds trust and reduces support tickets.

**8. BUILD SELLER APPEAL FLOW**
- When biometric pipeline flags a session as inattentive, show the seller an anonymized heatmap of their session.
- One-click appeal. Sellers tolerate strict rules if the process feels fair.

---

## D. Go-To-Market Strategy (Synthesized from All Workers)

### Phase 0: Before Launch (Now)

| Action | Who | Timeline |
|--------|-----|----------|
| Get OPENCODE_GO_API_KEY renewed (current returns 401) | You | Immediate |
| Decide: Standard tier with NO webcam | You + Swarm | Immediate |
| Reduce New seller payout to 7 days | Spec update | Immediate |
| Choose launch geography (recommend US buyers + PH/IN sellers) | You | Immediate |
| Pre-commit seller guarantee fund ($50-200K) | You | Before seller onboarding |

### Phase 1: Seller Land Rush (Weeks 1-6)

- Open seller registration in **1 country** (Philippines or India).
- Offer "Founding Viewer" status: guaranteed $3-5/hour for first 90 days, instant payout.
- Acquisition channels: Facebook groups, Reddit (r/beermoney, r/passiveincome), TikTok/YouTube Shorts.
- Incentivized referral: $5 sign-up bonus after first verified session.
- KYC: Phone verification first → document KYC only after $20+ earnings threshold.
- **Target**: 1,000 active sellers with >70% 7-day retention.

### Phase 2: Buyer Proof (Weeks 6-12)

- Target 10-20 DTC e-commerce brands / mobile app publishers.
- Offer: "First $500 of verified attention free." Remove buyer risk entirely.
- Pitch: "Your YouTube pre-roll is 60% bot traffic. Here's a receipt for every second of actual eyeballs."
- Pricing at this stage: 0% platform fee (eat costs to prove model).
- Collect case studies: cost-per-verified-minute vs. comparable CPM platforms.

### Phase 3: Platform Launch (Months 3-6)

- Launch self-serve buyer portal (Fast Contract mode only).
- Introduce platform fees at 5% + $0.50 (as spec'd).
- Open seller registration in 2nd geography (Nigeria or Brazil).
- Add buyer API for agencies.
- Target 500 buyers, $500K monthly GMV.

### Phase 4: Scale (Months 6-12)

- Launch Strategic mode for enterprise buyers.
- Launch Premium 1080p + End Card Links.
- Add 3 more languages (ES, DE, FR).
- Apply for B Corp certification (UBI narrative aligns perfectly).
- Publish "State of Human Attention" annual report as content marketing.

---

## E. Key Metrics to Track from Day One

| Side | Metric | Target |
|------|--------|--------|
| **Seller** | KYC completion rate | >40% |
| | Day-7 retention | >70% |
| | Day-30 retention | >50% |
| | Average sessions per seller per week | >5 |
| | Support tickets per 1K sellers | <50 |
| **Buyer** | Campaign repeat rate (within 30 days) | >60% |
| | Cost per verified minute vs. comparable CPM | <80% of benchmark |
| | Net revenue retention | >100% |
| **Platform** | False positive rate on attention verification | <3% |
| | Chargeback rate | <1% |
| | Gross margin per verified minute | Positive at 10K mins/week |
| | Seller referral rate | >0.5 per seller |

---

## F. Items Where Workers Disagreed

| Topic | Disagreement | My Recommendation |
|-------|-------------|-------------------|
| Seller-first vs. buyer-first bootstrap | 4 worker seller-first, 4 worker buyer-first | **Buyer-first with seller guarantee fund.** Pre-commit capital to guarantee seller payouts for first 90 days regardless of fill rate. |
| How strict should biometric verification be at launch? | 5 workers: tier down to tab-focus only. 3 workers: keep full biometric as differentiator. | **Tiered approach.** Standard (no webcam) gets sellers in door. Premium (full biometric) is the product you sell to buyers. |
| Single language or launch with 3-5? | 6 workers: single. 2 workers: 3 languages (EN/ES/FR). | **Single language (EN) for first 6 months.** The 9-language scope is the biggest time-to-market risk. |
| Platform fees at launch | 5 workers: 0% to seed. 3 workers: spec rate from day 1. | **0% for first 3 months.** Prove the model works, then introduce fees. Investor pitch is stronger with usage data. |

---

**Bottom Line from the Swarm:**

AttnValue has a genuinely defensible concept. The risks are **not technical** — they are **marketplace liquidity and seller onboarding friction.** The biggest immediate decisions: (1) fix the 30-day payout before it contradicts UBI messaging, (2) add a Standard tier without webcam to reduce seller drop-off, (3) pick one geography and prove the model before expanding to 9 languages.
