# Ligerwave Research Agent — Morning Report

Run every morning to generate a build progress + market intelligence report.

## How to run
```
task "Run morning research report. Use research/research_config.md. Append to research/daily-report.md." subagent_type:general
```

## Report Sections

### 1. Build Progress
Run `git log --oneline -5` and check AGENTS.md product status table. Report:
- What shipped yesterday
- What's in progress today
- Outstanding blockers
- Estimated completion date

### 2. Competitor Activity
Monitor:
- **Origin AI / ADT** — any new patents, products, or price changes
- **Olarm** — SA alarm market changes
- **Blackline Safety** — mining lone worker updates
- **MSA Safety** — new wearables
- **Honeywell** — industrial safety portfolio
- **Raveon** — mining GPS tracking
- **TP-Link / Ubiquiti** — new OpenWrt-compatible hardware

### 3. Legislation Changes
Monitor:
- **POPIA** — any new SA Information Regulator rulings on surveillance/sensing
- **GDPR** — EU changes that affect future expansion
- **DMR (Mining)** — new safety regulations, fatigue management requirements
- **OHS Act (Construction)** — construction safety regulation changes
- **SAPS procurement** — any new policies on surveillance tech procurement
- **Prison regulations** — any new rules on inmate monitoring
- **POPIA Section 6(1)(c)** — law enforcement exemption rulings

### 4. Cybersecurity
Analyse the current platform for:
- **Supabase access** — are RLS policies correctly scoped?
- **API key exposure** — any keys in source code or git history?
- **WebSocket security** — any unauthenticated WS connections?
- **Dependency vulnerabilities** — check Python packages for CVEs
- **Data encryption** — CSI data in transit + at rest
- **Authentication** — JWT expiry, MFA enforcement, brute force protection
- **Network exposure** — any ports/services exposed unnecessarily

### 5. Feature Ideas
Based on market research:
- What new features could existing products benefit from?
- What new product verticals make sense?
- What do competitors do that we don't?
- What do customers complain about in competitor reviews?

### 6. Go-to-Market Intelligence
- Which products should go to market first?
- Recommended pricing vs competitor pricing
- Distribution channels (direct, wholesale, government tender)
- Ideal launch partners (e.g., pilot prison, pilot mine)
- Regulatory approval needed before launch per product
