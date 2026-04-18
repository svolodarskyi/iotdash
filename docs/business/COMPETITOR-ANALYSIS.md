# Competitor Analysis — IoT Monitoring Platforms

> Research date: April 2025. Pricing should be verified before using in pitches.
> Market size: Cold chain monitoring alone is projected at $8.3B (2025) → $15B (2030), CAGR 12.6%.

---

## 1. Competitor Landscape Overview

### Tier 1 — Direct Competitors (hardware + software, SMB-friendly)

These are the companies doing almost exactly what we plan to do: sell sensors + cloud dashboard + alerts as a subscription.

| Company | Hardware | Software | Target Industries | Model |
|---------|----------|----------|-------------------|-------|
| **Monnit** | Own sensors ($50-300) | iMonnit cloud | Facilities, food, pharma, HVAC, agriculture | Hardware purchase + software subscription |
| **SmartSense by Digi** | Own sensors | SmartSense cloud | Food retail, pharmacy, healthcare, restaurants | All-inclusive subscription (sensors included) |
| **Dickson** | Own data loggers | DicksonOne cloud | Pharma, food, healthcare, labs | Hardware purchase + subscription ($84-242/yr) |
| **ComplianceMate (Ladle)** | Own wireless sensors | ComplianceMate cloud | Restaurants, food chains, hotels, hospitals | Subscription with hardware ($69-159/mo) |
| **TempCube** | Own WiFi/cellular sensors | TempCube cloud | Wine cellars, server rooms, greenhouses, food | Hardware purchase ($109+), free or $2/mo cellular |
| **Swift Sensors** | Own wireless sensors ($100-200) | Swift Sensors Cloud | Cold storage, warehousing, HVAC, manufacturing | Hardware purchase + $3-5/sensor/mo |
| **SensorPush** | Own BLE/WiFi sensors ($50-100) | SensorPush app + cloud | Wine cellars, greenhouses, cold storage, pharma | Hardware purchase, **no monthly fee** (basic) |
| **Disruptive Technologies** | Tiny peel-and-stick sensors ($20-40) | DT Studio cloud | Smart buildings, cold chain, facility mgmt | Hardware purchase, free basic cloud, 15-yr battery |

### Tier 2 — Enterprise / Large Players

Companies with bigger sales teams, higher prices, and enterprise focus. You'll compete with them eventually but they're not chasing $500/mo accounts.

| Company | Focus | Model | Why They're Not Your Problem Yet |
|---------|-------|-------|----------------------------------|
| **Sensitech (Carrier)** | Pharma cold chain, logistics | Enterprise custom pricing | Fortune 500 clients, $50K+ deals |
| **Samsara** | Fleet + facility IoT | ~$33/device/mo, 3-year contracts | $1B+ company, focused on fleet/logistics |
| **Tive** | Cold chain logistics trackers | Per-shipment pricing | Transit monitoring, not facility monitoring |
| **Controlant** | Pharma supply chain | Chain-as-a-Service (CHaaS) | Enterprise pharma only, custom pricing |
| **Emerson/Copeland** | Industrial refrigeration | Enterprise, bundled with equipment | Sells with their own refrigeration units |

### Tier 3 — IoT Platforms (software-only, DIY)

These sell the platform — you bring your own sensors. They're indirect competitors but relevant because tech-savvy buyers might try to build their own.

| Platform | Pricing | Free Tier | Notes |
|----------|---------|-----------|-------|
| **ThingsBoard** | From $10/mo (10 devices), $49/mo cloud (50 devices), $99/mo (100 devices + white-label) | Community Edition (open source) | Closest platform competitor. Open source core. |
| **Ubidots** | $99/mo Professional | 3 devices free (non-commercial) | Good for prototypes, Latin America roots |
| **Blynk** | $6.99-$599/mo, Pro from $49/mo (40 devices) | Yes, limited | Low-code, mobile-first, popular with makers |
| **Particle.io** | Free (100 devices), $299/mo (100 devices + cellular) | 100 devices free | Hardware + cloud, cellular focus |
| **Losant (SUSE)** | Custom/enterprise pricing | Developer sandbox | Acquired by SUSE, going enterprise |
| **Datacake** | $2-4/device/mo | 2 devices free | LoRaWAN-native, German, popular in EU |
| **TagoIO** | $49-199/mo | 25 devices free | Water/energy/agriculture, strong in LatAm |

### Tier 4 — Adjacent / Niche

| Company | What They Do | Why They Matter |
|---------|-------------|-----------------|
| **Onset HOBO** | Environmental data loggers | ~$70/yr per logger cloud sub. Scientific/research. Acquired by Emerson 2024. |
| **SafetyCulture** | Inspection/audit platform + sensors | From $19/user/mo. Broader than monitoring — checklists, audits, training. |
| **Teltonika** | Networking devices + RMS platform | Credit-based pricing. Strong in EU, industrial networking focus. |

---

## 2. Deep Dive — 5 Key Competitors

### 2.1 Monnit — The Closest Competitor

**Website:** [monnit.com](https://www.monnit.com)
**Founded:** 2010, Salt Lake City, UT
**Size:** ~100-200 employees

**What they sell:**
- 80+ sensor types (temp, humidity, water leak, door open/close, voltage, pressure, air quality, etc.)
- ALTA wireless sensors: industrial-grade, 300+ ft range, 10+ year battery
- Gateways: Ethernet, cellular, WiFi
- iMonnit cloud platform (dashboards, alerts, reports)

**Pricing model:**
- Sensors: $50-300 each (one-time purchase)
- iMonnit Basic: **Free** with every sensor (basic dashboards, alerts)
- iMonnit Premiere: Enhanced features, low annual cost per sensor
- iMonnit Enterprise: $500-2000+/yr for up to 250 sensors (self-hosted option available)
- No per-device monthly fee on basic plan — revenue is hardware margin

**Target industries:** Facilities management, food service, healthcare, pharma, HVAC, agriculture, data centers

**Strengths:**
- Huge sensor catalog — 80+ types covers almost any use case
- No monthly fee on basic plan — low barrier
- 10+ year battery life on ALTA sensors
- Self-hosted option for enterprises
- FDA/HACCP compliance reporting

**Weaknesses:**
- Dashboard is functional but dated UI
- No mobile app (web-only)
- Limited analytics — basic threshold alerts only
- No predictive capabilities
- Setup requires some technical knowledge
- Reports are basic

**What we can learn:**
- Free basic tier drives adoption — charge for premium features
- Sensor catalog breadth matters — but we can start narrow and expand
- Their weak spot is software quality and analytics — our differentiator

---

### 2.2 SmartSense by Digi — The Enterprise Mid-Market

**Website:** [smartsense.co](https://www.smartsense.co)
**Parent:** Digi International (NASDAQ: DGII, ~$1B market cap)
**Acquired:** 2017

**What they sell:**
- Wireless temperature sensors + digital data loggers
- Cloud platform with automated monitoring, alerting, compliance reports
- Asset monitoring (HVAC equipment health)
- LoRaWAN, WiFi, cellular connectivity options
- Managed service: sensors + connectivity + calibration + support all included

**Pricing model:**
- All-inclusive subscription: sensors, connectivity, NIST calibration, support all bundled
- No upfront hardware cost — everything is in the monthly fee
- Pricing is custom/quote-based — estimated $25-50/sensor/month
- Multi-year contracts typical

**Target industries:** Grocery/food retail, pharmacy (major pharmacy chains), healthcare, restaurants

**Strengths:**
- All-inclusive model — no surprise costs
- NIST-traceable calibration included
- Backed by Digi International (public company, not going anywhere)
- Deep pharmacy/grocery vertical expertise
- Regulatory compliance built in (FDA, HACCP, Joint Commission)

**Weaknesses:**
- Expensive — premium pricing locks out small businesses
- Locked into their hardware
- No DIY/self-service option
- Long sales cycles (enterprise selling)
- Overkill for simple monitoring needs

**What we can learn:**
- All-inclusive pricing is attractive to buyers who hate surprises
- Compliance/regulatory reporting is a must-have for pharma/food
- They're not chasing the small cold storage operator with 5 sensors — that's our space
- NIST calibration is a selling point we should consider

---

### 2.3 Dickson — The Compliance Specialist

**Website:** [dicksondata.com](https://dicksondata.com)
**Founded:** 1923 (100+ years!)
**Headquarters:** Addison, IL

**What they sell:**
- Temperature/humidity data loggers (touchscreen, WiFi/Ethernet connected)
- DicksonOne cloud platform (real-time monitoring, alerting, compliance reports)
- Chart recorders (legacy product line)
- Validation/mapping services

**Pricing model:**
- Data loggers: $200-800 each
- DicksonOne subscription: **$84-242/year** per device
- TotalCare Plus upgrade: extended warranty + 24/7 support
- Monthly, yearly, and multi-year contracts available

**Target industries:** Pharmaceutical, healthcare, food, labs, clean rooms

**Strengths:**
- 100+ year brand trust — huge in pharma/healthcare
- Strong regulatory compliance (FDA 21 CFR Part 11, HACCP, Joint Commission)
- Touchscreen data loggers with local display
- Validation services (temperature mapping)
- 24/7 support option

**Weaknesses:**
- Legacy company feel — slow to innovate
- Limited sensor types (primarily temp/humidity)
- Higher hardware costs
- UI is functional but not modern
- No predictive analytics
- Weak in non-pharma verticals

**What we can learn:**
- $84-242/year per device = $7-20/month — establishes the low end of the market
- Pharma compliance (21 CFR Part 11) is a gate you must pass to enter pharma
- Brand trust and longevity matters — but also means we can out-innovate them
- Their pricing gives us a target: beat Dickson on features at similar price

---

### 2.4 Samsara — The 800-Pound Gorilla

**Website:** [samsara.com](https://www.samsara.com)
**Founded:** 2015, San Francisco
**IPO:** NYSE: IOT (2021), ~$20B market cap
**Employees:** 3,000+

**What they sell:**
- Connected Operations Cloud (fleet, equipment, facility monitoring)
- Temperature monitoring sensors + environmental monitors
- Dash cameras, GPS trackers, ELD devices
- AI-powered analytics, route optimization
- Site visibility (facility sensors)

**Pricing model:**
- ~$33/device/month (ELD example: $99 upfront + $33/mo, 3-year contract mandatory)
- Custom enterprise pricing for large fleets
- 3-year minimum contract
- Per-vehicle or per-site pricing

**Target industries:** Transportation, logistics, food distribution, construction, field services, energy, manufacturing

**Strengths:**
- Massive platform — fleet + site + equipment all in one
- AI/ML analytics built in
- 3,000+ employees, huge sales/support team
- Public company credibility
- Mobile app is excellent
- API ecosystem, integrations

**Weaknesses:**
- **3-year contracts** — customers complain about being locked in
- Expensive for small operators
- Focused primarily on fleet/logistics — facility monitoring is a side feature
- Overkill for someone who just needs temperature alerts
- Sales team pushes for large deals — ignores small fish

**What we can learn:**
- $33/device/month with 3-year contracts = ~$1,200 per device over 3 years
- Customers hate long contracts — offer month-to-month as a differentiator
- Their facility monitoring is a secondary feature — we make it primary
- They prove the market is real and large ($20B company)
- Small operators who get ignored by Samsara's sales team are our customers

---

### 2.5 ComplianceMate (now Ladle) — The Restaurant Specialist

**Website:** [compliancemate.com](https://www.compliancemate.com) / [ladle.com](https://ladle.com)
**Focus:** Food service operations and compliance

**What they sell:**
- Wireless temperature sensors (10-mile range)
- Automated temperature logging
- Digital checklists and line checks
- Compliance reporting (HACCP, health department)
- Cloud dashboard with alerts

**Pricing model:**
- **Lite:** $69/month or $699/year
- **Plus:** $99/month (24-month commitment) or $999/year — includes 2 sensors
- **Pro:** $159/month (24-month commitment) or $1,599/year — includes 2 sensors
- Additional sensors available at extra cost

**Target industries:** Restaurant chains, franchises, hotels, hospitals, assisted living

**Strengths:**
- Purpose-built for food service — understands the workflow
- Combines monitoring + checklists (not just temp, also operational compliance)
- Good mobile experience for restaurant staff
- Health department compliance built in
- Strong in multi-location restaurant chains

**Weaknesses:**
- Narrow vertical — restaurants and food service only
- 24-month commitments on Plus/Pro plans
- Only 2 sensors included — more costs extra
- Limited analytics
- No predictive features
- Doesn't serve cold storage, manufacturing, agriculture

**What we can learn:**
- $69-159/month is a validated price point for restaurant monitoring
- Including sensors in the subscription is attractive (like SmartSense model)
- Combining monitoring + checklists/workflows adds stickiness
- Restaurant chains are a reachable vertical but ComplianceMate owns it
- Their narrow focus is both a strength and a weakness — we can be broader

---

## 3. Pricing Landscape Summary

| Company | Per Device/Month | Hardware Cost | Contract | Free Tier |
|---------|-----------------|---------------|----------|-----------|
| Monnit | Free (basic), ~$2-5 (premium) | $50-300/sensor | None | Yes |
| SmartSense | ~$25-50 (estimated, all-inclusive) | Included | Multi-year | No |
| Dickson | $7-20 | $200-800/logger | Monthly/annual | No |
| ComplianceMate | $35-80 (per location) | Included (2 sensors) | 24 months | No |
| Samsara | ~$33 | ~$99 upfront | 3 years | No |
| TempCube | $0-2 | $109+ | None | Yes (WiFi) |
| ThingsBoard | $1-5 (self-managed) | BYO | Monthly | Yes (open source) |
| Ubidots | ~$5-10 | BYO | Monthly | Yes (3 devices) |
| Blynk | ~$1-5 | BYO | Monthly | Yes |
| Particle | ~$3 | BYO + their boards | Monthly | Yes (100 devices) |
| Swift Sensors | $3-5 | $100-200/sensor | None | Yes (basic cloud) |
| SensorPush | **$0** (basic) | $50-100/sensor + $100 gateway | None | Yes (no monthly fee!) |
| Disruptive Tech | Free (basic cloud) | $20-40/sensor | None | Yes |
| Datacake | $2-4 | BYO | Monthly | Yes (2 devices) |

### Price bands in this market:

| Band | Per Device/Month | Who | Buyer Type |
|------|-----------------|-----|------------|
| **Budget** | $0-5 | Monnit basic, TempCube, SensorPush, Swift Sensors, DIY platforms | Tinkers, small ops |
| **Mid-market** | $10-30 | Dickson, Monnit premium, IoTDash target | SMBs, compliance-driven |
| **Premium** | $30-50 | SmartSense, Samsara, ComplianceMate | Multi-location chains |
| **Enterprise** | $50-100+ | Sensitech, Controlant | Pharma, large logistics |

### Our target: $15-29/device/month

This positions us:
- Above the "free but basic" tier (Monnit basic, TempCube)
- At or below mid-market compliance players (Dickson, ComplianceMate)
- Well below enterprise (SmartSense, Samsara, Sensitech)
- Justified by: better UX, real analytics, no long contracts, easy setup

---

## 4. Competitive Advantages We Can Build

### What competitors do badly (our opportunities):

| Gap | Who Has This Problem | Our Advantage |
|-----|---------------------|---------------|
| **Ugly dashboards** | Monnit, Dickson, HOBO | Modern React UI, customizable |
| **No predictive analytics** | Almost everyone except Samsara | Classical analytics first, ML later |
| **Long contracts** | Samsara (3yr), ComplianceMate (24mo), SmartSense (multi-year) | Month-to-month, cancel anytime |
| **Complex setup** | Monnit, ThingsBoard, Particle | Plug-and-play, 15-min setup |
| **No mobile app** | Monnit, Dickson | Mobile-first responsive dashboard |
| **Software-only OR hardware-only** | ThingsBoard/Ubidots vs Sensitech | Full stack: sensors + cloud + alerts |
| **One vertical only** | ComplianceMate (restaurants), Controlant (pharma) | Multi-vertical with vertical templates |
| **Expensive for small operators** | SmartSense, Samsara | Start with 1 sensor, scale up |
| **No white-label** | Most except ThingsBoard, Blynk | White-label for integrators (future) |

### Features that win deals (from competitor analysis):

1. **Compliance reports** — PDF/Excel export with timestamps, calibration records
2. **Multi-location view** — see all sites on one dashboard
3. **Alert escalation** — if nobody responds in 10 min, call the manager
4. **Audit trail** — who acknowledged what, when (FDA/HACCP requirement)
5. **Easy onboarding** — QR code scan → sensor active in 2 minutes
6. **No contracts** — month-to-month beats everyone except Monnit basic

---

## 5. Positioning Strategy

### Who we target first (where competitors are weakest):

```
Sweet spot = businesses that need:
  ✓ Real monitoring (not a $20 Amazon thermometer)
  ✓ Compliance reporting (health dept, insurance, FDA-lite)
  ✓ Professional dashboard and alerts
  ✗ But can't afford $50/device/mo enterprise solutions
  ✗ And don't want 3-year contracts
  ✗ And don't have IT staff to set up ThingsBoard
```

**Primary targets:**
1. **Independent cold storage operators** (5-50 sensors) — Monnit is too basic, SmartSense too expensive
2. **Restaurant groups** (3-20 locations) — ComplianceMate is good but pricey and narrow
3. **Small pharmacies** — Dickson works but old-school, SmartSense ignores small accounts
4. **Local HVAC companies** — want to offer monitoring to their clients, need white-label

### The pitch against each competitor:

| Against | Our Pitch |
|---------|-----------|
| Monnit | "Same reliability, better software, real analytics, beautiful dashboard" |
| SmartSense | "Same features at half the price, no multi-year lock-in" |
| Dickson | "Modern platform, same compliance, better alerts, easier setup" |
| Samsara | "You don't need a $20B company's solution — simpler, cheaper, focused on what you actually need" |
| ComplianceMate | "More than just restaurants — and no 24-month commitment" |
| ThingsBoard/DIY | "Don't spend 3 months building what we give you on day one" |

---

## 6. Service Companies — Same Business Model as Ours

These are not product companies selling a mass-market SaaS. These are small teams (like us) that build/source sensors + build a platform + deploy monitoring for clients as a service.

### Type A — Small companies doing exactly what we do

| Company | Where | What They Do | Size | Link |
|---------|-------|-------------|------|------|
| **Choovio** | Irvine, CA | Sells LoRaWAN sensors (Milesight, etc.) + monitoring dashboard subscription. Restaurant, cold chain, refrigeration | Tiny startup | [choovio.com](https://www.choovio.com) |
| **IOTezy** | USA | Plug-and-play IoT platform — sensors + dashboard + alerts. Retail, agriculture, logistics, healthcare | Small team | [iotezy.com](https://iotezy.com) |
| **Telemetry2U** | Australia | IoT platform for sensor monitoring. White-labels to resellers/integrators. $300 AUD/device deployment | Small team | [telemetry2u.com](https://telemetry2u.com) |
| **Swift Sensors** | Austin, TX | Own wireless sensors + cloud. Cold storage, HVAC, warehousing, manufacturing. $3-5/sensor/mo | ~20-40 emp | [swiftsensors.com](https://www.swiftsensors.com) |
| **Everactive** | USA (2 founders) | Battery-free IoT sensors + Evercloud. Steam trap monitoring, facility management | VC-backed | [everactive.com](https://everactive.com) |
| **SensorPush** | Brooklyn, NY | Small BLE/WiFi sensors + app + cloud. Started prosumer, growing into commercial. No monthly fee | <20 emp | [sensorpush.com](https://www.sensorpush.com) |
| **Mooko** | UK | Wireless sensors + cloud. Food safety, HACCP, restaurants, healthcare. $5-10/sensor/mo | <30 emp | [mooko.co.uk](https://www.mooko.co.uk) |

### Type B — White-label / ODM companies (potential partners)

These will build sensors and/or platforms to your spec so you can sell under your brand.

| Company | Where | What They Offer | Why It Matters | Link |
|---------|-------|----------------|----------------|------|
| **MOCREO** | Singapore | White-label sensors + ODM/OEM. 100K+ devices sold, 50+ countries. WiFi, BLE, LoRa, NB-IoT | Could source hardware from them instead of building from scratch | [mocreo.com](https://mocreo.com) |
| **2Smart** | — | Ready-made white-label IoT platform. Deploy in weeks | Could use as platform base instead of building | [2smart.com](https://2smart.com) |
| **MOKOSmart** | China | White-label sensor hardware. BLE, LoRa, WiFi. Huge catalog | Cheap hardware sourcing | [mokosmart.com](https://www.mokosmart.com) |
| **DusunIoT** | China | IoT gateways + sensors ODM. Cold chain, smart building | Gateway hardware sourcing | [dusuniot.com](https://www.dusuniot.com) |

### Type C — IoT dev shops (same work, project-based model)

Consultancies that build custom IoT solutions. They charge per project, not subscription. Could be competitors if a client hires them instead of subscribing to you.

| Company | Where | Model | Cost Range | Link |
|---------|-------|-------|------------|------|
| **Softeq** | Houston, TX | Full-stack: hardware + firmware + cloud + dashboard | $5K-$300K/project | [softeq.com](https://www.softeq.com) |
| **Bridgera** | USA | IoT platform (Interscope AI) + custom dev. Free basic tier | Custom pricing | [bridgera.com](https://bridgera.com) |
| **WebbyLab** | Ukraine | Custom IoT dashboard development | Project-based | [webbylab.com](https://webbylab.com) |
| **AgileSoftLabs** | — | Custom IoT development | From $4K | [agilesoftlabs.com](https://www.agilesoftlabs.com) |

### What this means for us

1. **The model works** — dozens of small teams (2-10 people) profitably deploy sensors + platform for clients
2. **Market is fragmented** — Choovio does restaurants in California, Mooko does food safety in the UK. Each serves a local market and 1-2 verticals. Nobody dominates SMB
3. **Most don't build their own hardware** — they source from Milesight, Dragino, MOCREO. Our partner's hardware capability is a real differentiator
4. **Most have weak platforms** — basic dashboards, simple threshold alerts. No analytics, no predictive features. Our platform skills are the moat
5. **The ODM path is real** — companies like MOCREO build sensors to your spec cheaply. Partner designs, they manufacture
6. **Dev shops charge $5K-$300K per project** — our subscription model ($15-29/device/mo) is cheaper for clients long-term and recurring revenue for us

---

## 7. Key Takeaways

1. **The market is real and growing** — $8B+ cold chain alone, 12.6% CAGR
2. **Nobody owns the SMB segment** — enterprise is crowded, SMB is underserved
3. **$15-29/device/month is the right price** — above commodity, below enterprise
4. **Month-to-month is a weapon** — everyone else locks you in
5. **Software quality is the gap** — most competitors have engineers who build hardware, not web apps
6. **Compliance is table stakes** — must have HACCP/FDA reporting from day one
7. **Start narrow, expand** — cold chain first, then HVAC, then manufacturing
8. **Include hardware in subscription** — SmartSense and ComplianceMate prove this model works
9. **Analytics is the moat** — everyone does dashboards, few do insights
10. **Samsara proves the ceiling** — $20B company means the TAM is massive

---

## Sources

- [MarketsAndMarkets — Cold Chain Monitoring Market](https://www.marketsandmarkets.com/Market-Reports/cold-chain-monitoring-market-161738480.html)
- [Monnit — Products & Software](https://www.monnit.com/products/)
- [SmartSense by Digi](https://www.smartsense.co)
- [DicksonOne Subscription](https://dicksondata.com/product/dicksonone-subscription)
- [ComplianceMate / Ladle](https://www.compliancemate.com/)
- [Samsara Review 2026 — Research.com](https://research.com/software/reviews/samsara)
- [ThingsBoard Pricing](https://thingsboard.io/pricing/)
- [Ubidots Pricing](https://ubidots.com/pricing)
- [Blynk Pricing — G2](https://www.g2.com/products/blynk-iot-platform/pricing)
- [Particle.io Pricing](https://www.particle.io/pricing/)
- [TempCube Products](https://tempcube.io/)
- [SafetyCulture Monitoring](https://safetyculture.com/monitoring)
- [Tive Cold Chain](https://www.tive.com/)
- [Sensitech Solutions](https://www.sensitech.com/en/solutions/)
- [Top Cold Chain Monitoring Software — SafetyCulture](https://safetyculture.com/apps/cold-chain-monitoring-software)
- [11 Best IoT Monitoring Platforms 2026 — Atera](https://www.atera.com/blog/best-iot-monitoring-software/)
- [Choovio Refrigeration Monitoring](https://www.choovio.com/refrigeration-monitoring-system/)
- [IOTezy IoT Platform](https://iotezy.com/)
- [Telemetry2U Pricing](https://telemetry2u.com/pricing/plug-and-play-iot-solution)
- [MOCREO White Label Service](https://mocreo.com/white-label-service/)
- [Softeq IoT Solutions](https://www.softeq.com/internet_of_things)
- [Bridgera IoT Remote Monitoring](https://bridgera.com/iot-remote-monitoring/)
- [Everactive — Battery-free IoT](https://www.networkworld.com/article/969972/iot-startup-makes-battery-free-sensors.html)
- [Swift Sensors](https://www.swiftsensors.com)
- [SensorPush](https://www.sensorpush.com)
- [Disruptive Technologies](https://www.disruptive-technologies.com)
