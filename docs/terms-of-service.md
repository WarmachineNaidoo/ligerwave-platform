# ADBOX — Terms & Conditions

**Version 1.0 | Effective Date: [Launch Date]**
**Governed by: Laws of England and Wales (with jurisdictional adaptations for international users)**

---

## 1. DEFINITIONS

| Term | Definition |
|------|-----------|
| **Platform** | AttnValue marketplace connecting Buyers (advertisers) with Sellers (viewers) |
| **Buyer** | User who creates campaigns, uploads video ads, and pays for verified attention |
| **Seller** | User who views ads and receives payment for verified attention |
| **Campaign** | A buyer's advertising contract specifying targeting, budget, duration, and quality tier |
| **Verification** | Multi-layer system (webcam, gaze tracking, face presence, gyroscope, tab focus) confirming human attention |
| **UBI Pool** | 20% of platform transaction fees distributed pro-rata to Sellers monthly |
| **End Card** | Optional 5-second clickable link displayed after a Premium campaign video |
| **GDPR** | EU General Data Protection Regulation (2016/679) |
| **Personal Data** | Any information relating to an identified or identifiable natural person |
| **Biometric Data** | Facial recognition data, gaze patterns, and similar unique identifiers collected during Verification |
| **Processing** | Any operation performed on Personal Data (collection, storage, analysis, deletion) |
| **Data Controller** | AttnValue Ltd — determines purposes and means of processing |
| **Data Processor** | Third parties processing data on behalf of AttnValue (AWS, Stripe, etc.) |
| **Supervisory Authority** | The data protection authority in your jurisdiction (e.g., ICO for UK, CNIL for France) |

---

## 2. ACCOUNT REGISTRATION & ELIGIBILITY

### 2.1 Age Requirement
- You must be **16 years or older** (or the age of majority in your country of residence, whichever is higher)
- If you are between 16 and the age of majority, a parent or guardian must accept these terms on your behalf
- **France**: Minimum 15 years for data processing consent (digital age of consent)
- **South Korea**: Minimum 14 years for PIPA compliance
- **China**: Personal Information Protection Law (PIPL) requires separate parental consent for minors under 14
- **Japan**: APPI requires parental consent for minors under 15
- **Germany**: Age of digital consent is 16 under TTDSG

### 2.2 Account Creation
- One account per natural person or registered legal entity
- You must provide accurate, complete, and current information
- Account sharing or multiple accounts for the same individual is prohibited
- KYC verification is mandatory for both Buyers and Sellers before any financial transaction

### 2.3 KYC Requirements
- **Identity Verification**: Valid government-issued ID (passport, national ID, driver's license)
- **Face Verification**: Live selfie matching against ID photo via InsightFace
- **Phone Verification**: SMS code to a valid mobile number
- **Address Verification** (for EU/UK Buyers over €250 monthly spend): Recent utility bill or bank statement
- **Duplicate Detection**: Cross-check of face, phone, and ID against existing accounts

### 2.4 Criminal Background & Sanctions
- We reserve the right to reject or terminate accounts of individuals or entities on:
  - EU Consolidated Sanctions List
  - UK Office of Financial Sanctions Implementation (OFSI) list
  - US OFAC SDN List
  - UN Security Council Sanctions List
  - Equivalent lists in China, Japan, South Korea, UAE, Saudi Arabia
- We may conduct periodic screening against these lists without prior notice

---

## 3. DATA PROTECTION & PRIVACY (GDPR COMPLIANCE)

### 3.1 Lawful Basis for Processing

| Processing Activity | Legal Basis (GDPR Article 6) | Special Category Basis (Article 9) |
|--------------------|------------------------------|-----------------------------------|
| Account registration & management | Contract (Art 6(1)(b)) | N/A |
| KYC verification | Legal obligation (Art 6(1)(c)) + Consent (Art 6(1)(a)) | Explicit consent (Art 9(2)(a)) for biometric matching |
| Attention verification (webcam, gaze) | Explicit Consent (Art 6(1)(a)) | Explicit consent (Art 9(2)(a)) for biometric/special category data |
| Campaign management & payments | Contract (Art 6(1)(b)) | N/A |
| UBI pool calculation & distribution | Contract (Art 6(1)(b)) | N/A |
| Marketing communications | Consent (Art 6(1)(a)) | N/A |
| Fraud detection & platform security | Legitimate interest (Art 6(1)(f)) | Necessary for substantial public interest (Art 9(2)(g)) |
| Compliance with legal requests | Legal obligation (Art 6(1)(c)) | N/A |
| Analytics & platform improvement | Consent (Art 6(1)(a)) | N/A |

### 3.2 Data Collected

| Category | Data Points | Retention Period |
|----------|-------------|-----------------|
| **Identity Data** | Full name, date of birth, government ID number, ID image | 5 years after account closure (legal obligation) |
| **Contact Data** | Email address, phone number, physical address | Duration of account + 3 years |
| **Biometric Data** | Facial images (selfies, webcam snapshots), gaze patterns, head pose data | 24 hours after verification session (except: retained for duration of dispute + 90 days if disputed) |
| **Financial Data** | Stripe Connect account ID, transaction history, payout records | 7 years (tax/compliance obligation) |
| **Technical Data** | IP address, device type, browser, operating system, screen resolution, gyroscope data | 90 days (session logs), 12 months (aggregated analytics) |
| **Usage Data** | Ad viewing history, campaign performance, verification scores, survey responses | Duration of account + 2 years |
| **Communication Data** | Support tickets, in-app chat, email correspondence | 3 years from last contact |

### 3.3 Your Rights Under GDPR

| Right | Description | Response Time |
|-------|-------------|---------------|
| **Right to be Informed** | About how your data is collected and used | Always available in this policy |
| **Right of Access** | Obtain confirmation of whether your data is processed and receive a copy | 30 days (extendable to 60 for complex requests) |
| **Right to Rectification** | Correct inaccurate or incomplete data | 30 days |
| **Right to Erasure** ("Right to be Forgotten") | Request deletion of your Personal Data where there is no compelling legal basis for continued processing | 30 days (exceptions: legal obligations, active disputes) |
| **Right to Restrict Processing** | Limit how your data is used while a complaint is investigated | 30 days |
| **Right to Data Portability** | Receive your data in a structured, machine-readable format (JSON) and transmit it to another controller | 30 days |
| **Right to Object** | Object to processing based on legitimate interests (including profiling and direct marketing) | 30 days |
| **Right to Withdraw Consent** | Withdraw consent at any time | Immediate for future processing |
| **Rights Related to Automated Decision-Making** | Not be subject to decisions based solely on automated processing that produce legal effects | Human review available |

**Important**: Withdrawal of biometric consent means you cannot use the attention verification system and therefore cannot participate as a Seller. Your account will be converted to Buyer-only.

### 3.4 Biometric Data — Explicit Consent

By clicking "I Consent" on the Biometric Consent dialog during Verification setup, you:

1. **Acknowledge** that the Platform collects and processes:
   - Real-time webcam video frames during viewing sessions
   - Facial geometry data for liveness detection
   - Gaze direction and dwell time for attention scoring
   - Head pose estimation for engagement verification

2. **Confirm** you understand that this constitutes "biometric data" under GDPR Article 9 and equivalent laws in:
   - **France**: Loi Informatique et Libertés
   - **Germany**: BDSG §22
   - **South Korea**: PIPA Article 23 (sensitive information)
   - **China**: PIPL Article 28 (sensitive personal information)
   - **Japan**: APPI (carefully protected personal information)
   - **Brazil**: LGPD Article 11 (sensitive personal data)

3. **Consent** freely and specifically to this processing for the sole purposes of:
   - Verifying that a human is watching the ad
   - Measuring attention quality
   - Detecting and preventing fraud (bots, deepfakes, multi-account farming)
   - Calculating Seller attention scores (which affect payout tiers)

4. **Understand** you may withdraw this consent at any time, with the consequence that you cannot serve as a Seller

5. **Acknowledge** that biometric data is:
   - Deleted within 24 hours of session completion (except during disputes)
   - Not sold, shared, or used for any purpose beyond verification
   - Encrypted at rest using AES-256 with separate key rotation

### 3.5 Automated Decision-Making & Profiling

| Decision | Factors Considered | Effect | Right to Human Review |
|----------|-------------------|--------|----------------------|
| **Attention Score** | Gaze data, head pose, tab focus duration, completion rate | Determines Seller payout tier | Yes |
| **Fraud Risk Score** | Behavioral patterns, device fingerprints, IP reputation, account age | May trigger verification challenge or account suspension | Yes |
| **UBI Pool Distribution** | Regional pool contribution, number of active Sellers in region | Determines UBI amount received | No (formula is fixed and transparent) |
| **Campaign Approval** | Content scan results (ClamAV, GuardDuty), policy compliance | May reject or flag campaign for manual review | Yes |

### 3.6 International Data Transfers

Data may be transferred to and processed in countries outside your residence. Each transfer is governed by appropriate safeguards:

| From | To | Safeguard |
|------|----|-----------|
| **EU/EEA** | United Kingdom | Adequacy Decision |
| **EU/EEA** | United States | Standard Contractual Clauses (SCCs) 2021 |
| **UK** | United States | IDTA + Addendum |
| **China** | Outside China | PIPL Security Assessment + SCC |
| **South Korea** | Outside Korea | PIPA Consent + Safeguards |
| **Japan** | Outside Japan | APPI Equivalent Protection |
| **Switzerland** | All countries | Swiss SCCs + FADP |

Primary storage locations:
- **EU/EEA Users**: AWS Frankfurt (eu-central-1)
- **UK Users**: AWS London (eu-west-2)
- **Japan Users**: AWS Tokyo (ap-northeast-1)
- **South Korea Users**: AWS Seoul (ap-northeast-2)
- **All Others**: AWS Frankfurt (eu-central-1)

### 3.7 Data Protection Officer

```
Email: dpo@attnvalue.com
Post: AttnValue Ltd, Data Protection Officer, [Registered Address]
```

### 3.8 Supervisory Authority Complaints

| Country | Authority | Website |
|---------|-----------|---------|
| **UK** | ICO | ico.org.uk |
| **France** | CNIL | cnil.fr |
| **Germany** | BfDI | bfdi.bund.de |
| **Spain** | AEPD | aepd.es |
| **Portugal** | CNPD | cnpd.pt |
| **China** | CAC | cac.gov.cn |
| **Japan** | PPC | ppc.go.jp |
| **South Korea** | PIPC | pipc.go.kr |
| **Brazil** | ANPD | gov.br/anpd |
| **UAE** | UAE Data Office | dataoffice.ae |

### 3.9 Cookie Consent

| Category | Purpose | Consent Required |
|----------|---------|-----------------|
| **Strictly Necessary** | Authentication, session management, fraud prevention | No (legitimate interest) |
| **Functional** | Language preferences, UI customization | Yes |
| **Analytics** | Usage patterns, feature adoption, performance monitoring | Yes |
| **Marketing** | Not used — AttnValue does not employ marketing cookies or third-party ad tracking | N/A |

---

## 4. COUNTRY-SPECIFIC PROVISIONS

### 4.1 United Kingdom (EN)
- Governed by English law. UK GDPR and Data Protection Act 2018 apply.
- Consumer Contracts Regulations 2013 — 14-day cooling-off period for digital services not yet begun
- Cooling-off waived if buyer ticks "I consent to immediate performance" during campaign setup

### 4.2 France (FR)
- Governed by French law. CNIL is the Supervisory Authority.
- Article 82 French Data Protection Act: facial recognition requires specific consent — satisfied by our Biometric Consent dialog
- French language version prevails in case of conflict for French users

### 4.3 Germany (DE)
- Governed by German law (BGB, BDSG, TTDSG)
- TTDSG §25: active opt-in for cookies
- BDSG §22: explicit consent for biometric data processing
- German language version prevails for German users

### 4.4 Spain (ES)
- Governed by Spanish law (LOPDGDD 3/2018)
- LOPDGDD Article 9: explicit consent for biometric data
- Spanish language version prevails for Spanish users

### 4.5 China (ZH — PIPL Compliance)
- PIPL 2021 applies
- Article 28: biometric data is sensitive personal information
- Article 38: cross-border transfer requires CAC security assessment or SCC
- Article 55: DPIA required before processing
- Data localization: Chinese user data stored in mainland China
- AttnValue designates a PIPL Representative in China
- Chinese language version prevails for Chinese users

### 4.6 Japan (JA — APPI Compliance)
- APPI (as amended 2020/2022) applies
- Article 23: sensitive personal information requires opt-in consent
- Article 24: cross-border transfer requires consent + equivalent protection
- AttnValue designates a Japanese Representative
- Japanese language version prevails for Japanese users

### 4.7 South Korea (KO — PIPA Compliance)
- PIPA (2023 amendments) applies
- Article 22: granular consent required (separate for essential, optional, third-party, cross-border)
- Article 23: sensitive information requires separate explicit consent
- Article 28-2: pseudonymization required where possible
- Article 29: breach notification within 72 hours
- AttnValue designates a Korean CPO
- Korean language version prevails for Korean users

### 4.8 Portugal (PT)
- Governed by Portuguese law. CNPD is the Supervisory Authority.
- Law 41/2004 (ePrivacy): cookie consent requirements
- Portuguese language version prevails for Portuguese users

### 4.9 Arabic Markets (AR)
- **UAE**: PDPL 2021 — DPO registered with UAE Data Office, consent + adequacy for cross-border transfer
- **Saudi Arabia**: PDPL 2021 — consent required, data stored in KSA unless exception applies
- **Qatar**: Law No. 13 of 2016
- **Egypt**: Data Protection Law No. 151 of 2020
- Arabic language version of Terms prevails for Arabic users

---

## 5. BUYER TERMS

### 5.1 Campaign Creation
- Buyer represents all uploaded content:
  - Does not contain malware, viruses, or malicious code
  - Does not violate any law or third-party IP
  - Does not contain illegal, obscene, defamatory, or deceptive content
  - Complies with advertising regulations in all targeted countries
  - Contains no subliminal messages or hidden content
- Buyer must have sufficient funds in their Stripe Connect account before campaign launch
- Buyer may cancel before any views are delivered: full refund of campaign value (platform fees non-refundable)
- Buyer may pause an active campaign: delivered views charged, unspent value refunded, platform fees non-refundable

### 5.2 Payment Obligations
- Charges are immediate capture (not pre-authorization)
- All fees are pre-paid and non-refundable except campaign value
- Late/failed payments result in campaign suspension and account restriction

### 5.3 Premium Features
- **Premium Tier**: KYC-verified Buyers with minimum campaign value of $5,000
- **End Card**: 5-second clickable link after video (Premium only)
- Buyer represents linked URL complies with all applicable laws
- AttnValue may remove End Cards that violate these Terms without refund

### 5.4 Buyer Reports
- Email report when campaign completes
- Data available for CSV download for 90 days

### 5.5 Chargebacks & Disputes
- Buyer agrees not to file chargebacks for validly delivered campaigns
- Chargeback filing results in permanent ban of account and all linked accounts
- Stripe Chargeback Protection + Smart Disputes handle evidence submission
- Buyer agrees to attempt resolution through AttnValue dispute process before chargeback

---

## 6. SELLER TERMS

### 6.1 Seller Obligations
- Complete KYC before receiving any payment
- Maintain working webcam/front camera
- Complete Verification during each viewing session
- Prohibited: bots, scripts, automation, multi-accounting, deepfakes, screen sharing, account sharing, fraud

### 6.2 Seller Payment Terms
- **Payout**: 30 days after contract ends
- **Tiers**: New (30d delay, 15% reserve), Established (14d, 10%), Top (7d, 5%)
- **Minimum Payout**: $20.00
- **Payout Fee**: $0.25 deducted from seller
- Tax forms: 1099-K (US), equivalent for other jurisdictions

### 6.3 UBI Pool Terms
- 20% of platform fees allocated to regional UBI pools
- Monthly distribution, pro-rata by region
- Paid as platform credits (not cash)
- Cannot be withdrawn as cash
- AttnValue reserves right to adjust UBI pool % with 30 days' notice

### 6.4 Attention Scoring
- Score based on: gaze, head pose, face presence, tab focus, gyroscope, completion rate
- **Full payment**: Score ≥80%
- **Partial payment**: Score 50-79% (proportional)
- **No payment**: Score <50%

### 6.5 Cooling-Off (EU Sellers)
- 14-day right of withdrawal under EU Consumer Rights Directive
- Extinguished once viewing session is completed (with seller's prior express consent)

---

## 7. FEES & REFUND POLICY

### 7.1 Fee Schedule

| Fee | Calculation | Pre-Paid | Refundable |
|-----|------------|----------|------------|
| **Base Fee** | 5% of campaign value + $0.50 | Yes | No |
| **Video Upload Fee** | $0.025 per video | Yes | No |
| **View Fee (720p)** | $0.0025 per view per seller | Yes | No |
| **View Fee (1080p)** | $0.005 per view per seller | Yes | No |
| **Download Fee (720p)** | $0.0125 per targeted seller | Yes | No |
| **Download Fee (1080p)** | $0.025 per targeted seller | Yes | No |
| **Email Fee** | $1.00 per 100 targeted sellers | Yes | No |
| **Campaign Value** | Seller payout pool | Yes | Yes (unspent) |
| **Stripe Fee** | 2.9% + $0.30 | Yes | No |
| **Chargeback Protection** | 0.4% of volume | Yes | No |

### 7.2 Refund Policy
- Platform fees: non-refundable under any circumstances
- Campaign value: refundable for unspent portion
- Disputes: 14-day window from campaign completion

---

## 8. PLATFORM CONDUCT & PROHIBITED ACTIVITIES

| Activity | Consequence |
|----------|-------------|
| Fraud (bots, deepfakes, automated viewing) | Permanent ban, forfeiture of earnings |
| Multi-accounting | All accounts banned |
| Malware distribution | Ban, reported to authorities |
| Illegal content | Ban, content removed |
| Harassment | Warning → suspension → ban |
| Chargeback abuse | Permanent ban + linked accounts |
| API abuse | Key revocation, IP ban |
| Privacy violation | Ban, legal action |

---

## 9. DISPUTE RESOLUTION & GOVERNING LAW

### 9.1 Internal Process
1. Submit dispute via Platform support
2. AttnValue reviews within 5 business days
3. Either party may escalate to arbitration within 30 days

### 9.2 Arbitration
- London Court of International Arbitration (LCIA), London, UK
- English language, each party bears own costs
- Final and binding

### 9.3 Governing Law
- Laws of England and Wales
- EU/EEA: mandatory consumer protections not overridden
- Other jurisdictions: local mandatory laws apply where not contractually excludable

### 9.4 Jurisdiction-Specific Forums
- **China**: CIETAC (Shanghai)
- **South Korea**: KCAB (Seoul)
- **Japan**: JCAA (Tokyo)
- **UAE**: DIAC (Dubai)
- **Saudi Arabia**: SCCA (Riyadh)
- **EU/EEA**: ODR platform (ec.europa.eu/consumers/odr)

---

## 10. INTELLECTUAL PROPERTY

- Buyer retains IP in uploaded content; grants AttnValue non-exclusive, worldwide license for hosting, transcoding, streaming, and platform analytics
- AttnValue owns Platform name, logo, design, code, algorithms
- Seller attention data owned by AttnValue for Platform operation; seller retains access/portability rights under GDPR

---

## 11. LIMITATION OF LIABILITY

- **UK/EU**: Liability limited to total fees paid in preceding 12 months. Not excluding liability for death, personal injury, fraud, or gross negligence.
- **Other**: Liability limited to $1,000 or total fees paid in preceding 12 months (whichever greater).
- **China**: PIPL Article 69 — burden of proof on AttnValue for data-related claims.
- **South Korea**: Statutory damages up to 3× actual damages for privacy violations under PIPA.
- Platform availability: 99.9% target (not guaranteed). Scheduled maintenance notified 24h in advance.
- Verification accuracy: not guaranteed 100%. Sellers paid based on Platform results absent demonstrated error.

---

## 12. ACCOUNT TERMINATION

### By User
- Terminate anytime via Account Settings
- Outstanding payments processed; pending campaigns cancelled with refund; platform fees non-refundable
- Data retained per retention schedules

### By AttnValue
- Immediate termination for: Terms violation, fraud, illegal activity, failure to complete KYC, 12+ months inactivity
- Termination does not relieve obligations incurred before termination
- Sections 3, 7, 9, 10, 11, 13 survive termination

---

## 13. GENERAL PROVISIONS

- **Entire Agreement**: These Terms constitute the entire agreement
- **Amendments**: 30 days' written notice; material changes via email + in-app notification
- **Severability**: Invalid provisions do not affect remainder
- **Language**: English prevails except where local law requires local language (FR, DE, ES, PT, ZH, KO, JA, AR)

### Contact

```
AttnValue Ltd, [Registered Address]
Support: support@attnvalue.com
Privacy/Data: privacy@attnvalue.com
DPO: dpo@attnvalue.com
Legal: legal@attnvalue.com
```

**Regional Representatives:**

| Region | Contact |
|--------|---------|
| EU/EEA | eu-rep@attnvalue.com |
| China | china-rep@attnvalue.com |
| Japan | japan-rep@attnvalue.com |
| South Korea | korea-rep@attnvalue.com |

---

## SCHEDULE A: JURISDICTIONAL COMPLIANCE MATRIX

| Requirement | UK | FR | DE | ES | PT | CN | JP | KR | UAE | SA |
|-------------|----|----|----|----|----|----|----|----|-----|-----|
| Biometric consent | Art 9 GDPR | Art 9 + CNIL | §22 BDSG | LOPDGDD Art 9 | Art 9 GDPR | Art 28 PIPL | Art 23 APPI | Art 23 PIPA | Art 10 PDPL | Art 6 PDPL |
| Age of consent | 13 | 15 | 16 | 14 | 13 | 14 | 15 | 14 | 18 | 18 |
| Cookie opt-in | PECR | Art 82 CNIL | §25 TTDSG | LSSI | Law 41/2004 | PIPL Art 6 | APPI Art 23 | PIPA Art 22 | PDPL Art 8 | PDPL Art 6 |
| DPO required | Yes | Yes | Yes | Yes | Yes | Per PIPL | No | Yes | Yes | Yes |
| Cross-border transfer | UK IDTA | SCCs | SCCs | SCCs | SCCs | CAC Assess | PPC OK | PIPA 28-8 | PDPL Art 14 | PDPL Art 21 |
| Local storage | No | No | No | No | No | Yes | No | No | Yes | Yes |
| Arbitration seat | London | London | London | London | London | Shanghai | Tokyo | Seoul | Dubai | Riyadh |
