# WiFi CSI Research Agent
# Run this weekly to gather intelligence on competitors, hardware, patents, and pricing
# Usage: .\research\run_research.ps1
#
# This script outputs the research prompt you should feed to the task agent.
# Copy the output and use: task tool with subagent_type: general

@"
## Research Topics — Week of $(Get-Date -Format "yyyy-MM-dd")

Research each topic and append findings to `research/findings.md` under today's date.

### 1. Hardware Sourcing
Best prices on MT7621/MT7981 routers (Alibaba/Aliexpress). MOQ 10/100/500. Shipping to SA.

### 2. OpenWrt CSI Tools
Recent commits/issues in ath9k-csi, nexmon_csi, ekstra-csi. Any new chipset support.

### 3. Origin AI / ADT Patents
New patent filings near phase-based WiFi sensing. Press/news on Origin AI.

### 4. SA Competitors Activity
Olarm, Venus, IDS Onyyx, Tuya — product/price changes. New entrants.

### 5. WhatsApp Business API
Pricing changes. Template policy. Region availability.

### 6. POPIA Guidance
Security data retention guidance. IoT enforcement.

### 7. CSI Research Papers
New papers on phase-based detection, false alarm reduction, zone occupancy.

Output each finding as a bullet point. If nothing new, say "No changes."
"@
