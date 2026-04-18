# IoTDash — What to Build for Demos, First Client, and Whether to Seek Investors or Clients First

---

## 1. Investor vs Client First: The Decision

### 1.1 The Two Paths

```
PATH A: Client First (RECOMMENDED)
─────────────────────────────────────
Build MVP → Demo to prospects → Free pilot → Paying client → More clients
→ Revenue proves the model → THEN seek investment if needed

PATH B: Investor First
─────────────────────────────────────
Build pitch deck → Demo to investors → Get funding → Build product
→ THEN find clients

PATH C: Neither First — Just Build Forever
─────────────────────────────────────
Build build build → never demo → never sell → "it's not ready yet"
→ 2 years later, nothing shipped
```

### 1.2 Why Client First Wins

| Factor | Client First | Investor First |
|--------|:---:|:---:|
| What you need to show | Working demo with real data | Pitch deck + TAM/SAM/SOM + team slide |
| What you learn | What clients actually pay for | What investors want to hear |
| What you get | Revenue + validation + case study | Money + pressure + dilution |
| Time to start | Now (you have a working data pipeline) | 3-6 months (deck, networking, meetings) |
| Control | You keep 100% | You give up 10-25% |
| What happens if it doesn't work | You spent evenings building. Low cost. | You spent months pitching. Still no product. |
| What clients/investors want to see | "We have 3 paying clients" | "We have a $50B TAM slide" |

**The irony:** The best way to get investors is to not need them. Investors want traction. Traction means clients. So even if you want investment eventually, get clients first.

### 1.3 When to Talk to Investors

| Situation | Seek Investment? |
|-----------|:---:|
| 0 clients, no MVP | No — nothing to show |
| MVP works, 0 clients | No — get 1-3 clients first |
| 3-5 paying clients, growing | Maybe — if you need capital to grow faster |
| 10+ clients, clear demand | Yes — you have leverage to negotiate good terms |
| You need hardware inventory for 100 clients | Yes — this is a specific capital need with clear ROI |
| You want to quit your job but revenue isn't enough yet | Maybe — but a bank loan or grant might be better |

**Rule: Don't raise money to figure out if the business works. Raise money to scale a business that's already working.**

---

## 2. The Three Demos You Need

You need different demos for different audiences. They are NOT the same thing.

### Demo 1: The Prospect Demo (to get a pilot)

**Goal:** Prospect says "Can we try this on our equipment?"

**Audience:** Operations manager, facility manager, quality manager

**Duration:** 5-10 minutes

**What they need to see:**

```
MUST SHOW:
  ✓ Real data flowing live (not mockups, not screenshots)
  ✓ Dashboard on a phone (they will check on their phone, not a desktop)
  ✓ An alert firing and an email arriving (trigger it live during demo)
  ✓ "This is what YOUR freezer/machine/building would look like"
  ✓ A PDF or CSV report (for compliance people)

NICE TO SHOW:
  ○ Device online/offline status (green/red dot)
  ○ Historical data (zoom into last week, last month)
  ○ Multiple devices on one dashboard

DON'T SHOW:
  ✗ Admin panel (they don't care how you manage it)
  ✗ Architecture diagrams (their eyes will glaze)
  ✗ Grafana directly (they don't know what Grafana is)
  ✗ Terminal/code/config (instantly kills credibility with non-technical buyers)
  ✗ Features that don't work yet
```

**The flow:**
```
"Let me show you what this looks like for a company like yours."

→ Open dashboard on phone
  "Here are 4 temperature sensors. All green — everything's normal."

→ Point at one sensor
  "This one is in Cold Room 2. It's been at -18C all day. Here's the chart."

→ Show the alert
  "I set an alert: if it goes above -15C, I get an email instantly.
   Let me trigger it..."
  [Change threshold to trigger alert on current data]
  "...and here's the email, 30 seconds later."

→ Show the report
  "And here's the weekly report — PDF, ready for your HACCP audit.
   Every reading, every alert, automatic."

→ The ask
  "I'd like to put 2-3 sensors in your facility for 2 weeks, free.
   You'll see your own data like this. When works for you?"
```

---

### Demo 2: The Investor Demo (to get funding — later)

**Goal:** Investor says "Tell me more about your traction."

**Audience:** Angel investor, accelerator, grant committee

**Duration:** 15-20 minutes (with pitch deck)

**What they need to see:**

```
MUST SHOW:
  ✓ Working product (live demo, not mockups)
  ✓ Paying clients (or active pilots)
  ✓ Client testimonial or quote
  ✓ Revenue or revenue potential (MRR × growth rate)
  ✓ Clear market (who buys this, how big is the market)
  ✓ Why you (team, unfair advantage, full-stack capability)
  ✓ What the money is for (specific: hire X, buy Y, not "general operations")

NICE TO SHOW:
  ○ Unit economics ($29/device/month, cost to serve $3-5, margin 80%+)
  ○ Pipeline (prospects in conversations)
  ○ Competitive landscape (who else, why you win)
  ○ Technical moat (platform + hardware, hard to replicate)

DON'T SHOW:
  ✗ Extensive product roadmap (they don't fund roadmaps)
  ✗ Technical architecture in depth (unless they're technical)
  ✗ Financial projections beyond 18 months (nobody believes them)
```

**You don't need this demo today. Build it when you have 3-5 clients.**

---

### Demo 3: The Partner Demo (to get resellers/installers)

**Goal:** HVAC company / installer says "We want to offer this to our clients."

**Audience:** Business owner of a service company (HVAC, refrigeration, electrical)

**Duration:** 10-15 minutes

**What they need to see:**

```
MUST SHOW:
  ✓ How easy it is to install (partner will do installations)
  ✓ How the dashboard looks to THEIR client (white-label potential)
  ✓ That it makes THEM look good to their clients
  ✓ How they make money (revenue share or margin)
  ✓ That support is handled (they don't want support calls about your software)

NICE TO SHOW:
  ○ How many clients you already have (credibility)
  ○ That you handle updates, maintenance, hosting
  ○ Marketing materials they can use

DON'T SHOW:
  ✗ Pricing to your direct clients (they need their own margin)
  ✗ Your cost structure
  ✗ Technical internals
```

**You don't need this demo today either. Build it at 5-10 direct clients.**

---

## 3. What to Build for Demo 1 (The Only Demo That Matters Now)

### 3.1 The Must-Have List (Build These)

| # | Feature | Why It's Essential | Effort |
|---|---------|-------------------|:---:|
| 1 | **Live data flowing on a dashboard** | If data isn't live, there's nothing to demo | Done (Grafana exists) |
| 2 | **Dashboard embedded in YOUR web app** | Showing raw Grafana looks amateur. Your branded app looks professional | 2-3 days |
| 3 | **Works on mobile (responsive)** | Every prospect will pull out their phone | 1 day |
| 4 | **Login page** | "This is YOUR private dashboard" — creates ownership feeling | 1 day |
| 5 | **Email alert that actually fires** | The "wow" moment of the demo. Trigger it live. | 2-3 days |
| 6 | **2-3 fake devices with realistic names** | "Freezer Room A", "Cold Storage B", "Loading Dock" — not "sensor01" | 1 hour |
| 7 | **One PDF/CSV export** | Compliance people will ask. Have it ready. | 2-3 hours |
| 8 | **Device status (online/offline dot)** | Green dot = trust. First thing they look at. | 2 hours |

**Total effort: ~2-3 weeks of evening/weekend work on top of what you have.**

### 3.2 The Should-Not-Build List (Skip These for Demo)

| Feature | Why to Skip | What to Do Instead |
|---------|-----------|-------------------|
| Admin panel | Prospect never sees admin. You manage behind the scenes. | Create orgs/devices via script or API call |
| User management UI | You have 1 demo account | Hardcode a demo user in the seed script |
| Alert management UI | For demo, pre-configure 1-2 alerts | Set alerts via Grafana API directly or seed script |
| Multi-org isolation | You're demoing to one prospect at a time | One Grafana org is enough for demo |
| CI/CD pipeline | You deploy manually once. It's a demo server. | `docker compose up` on a VPS |
| Azure Container Apps | Overkill for demo. A $10/month VPS runs everything. | DigitalOcean, Hetzner, or any cheap VPS |
| Terraform | You have one server | SSH + docker compose |
| Custom domain with SSL | Nice but not blocking | Use the VPS IP for now, or a free subdomain |
| Password reset | Demo account — you know the password | Tell them the password |
| Audit log | No compliance need for a demo | Skip entirely |
| Multiple sensor types | Temperature is enough to prove the concept | One type, done well |
| Edge AI / analytics | Way too early | The simple dashboard IS the product |
| Dark mode | Not a selling feature | Skip |

### 3.3 The Demo Environment

```
OPTION A: Your Laptop (Easiest)
  - Run docker-compose locally
  - Demo on your screen or screenshare
  - Pros: Free, fast to set up, works offline
  - Cons: Can't leave it running for prospects to check later

OPTION B: Cheap VPS (Recommended for Pilots) — $10-20/month
  - DigitalOcean Droplet or Hetzner VPS (4GB RAM, 2 vCPU)
  - Docker Compose with all services
  - Accessible from anywhere
  - Pros: "Here's the URL, check it anytime"
  - Cons: Small monthly cost, need to maintain

OPTION C: Your Partner's Lab / Workshop
  - Real sensor connected to real equipment
  - Most impressive demo — actual hardware in action
  - Pros: Tangible, credible
  - Cons: Need to be on-site to demo
```

**Best combo: Option B (always-on demo) + Option C (for on-site meetings).** Run a VPS with fake devices for remote demos. Use real sensors in a lab for in-person demos.

---

## 4. The Demo-Ready Checklist

### 4.1 Before Your First Demo

```
PLATFORM:
  [ ] Web app running with login page
  [ ] Dashboard shows 3-5 devices with realistic names
  [ ] Live data flowing (fake_device.py running continuously)
  [ ] At least one chart type (temperature over time)
  [ ] Last-reading card showing current value
  [ ] Green/red online status per device
  [ ] Works on mobile (test on your phone)
  [ ] Email alert configured and tested
  [ ] PDF or CSV export working for at least one device

HARDWARE (Partner):
  [ ] One physical sensor working (real ESP32 + temp probe)
  [ ] Sends data to the same dashboard as fake devices
  [ ] Looks reasonably professional (enclosure, not bare wires)
  [ ] Can be installed in 15 minutes on-site
  [ ] Survives power cycle (auto-reconnects)

SALES MATERIALS:
  [ ] 1-page PDF pitch (see SALES-AND-GO-TO-MARKET.md)
  [ ] ROI calculator spreadsheet
  [ ] 3-minute screen recording of the dashboard (for email follow-ups)
  [ ] Your business email (not gmail — yourname@yourdomain.com)

YOU:
  [ ] Practiced the 5-minute demo flow 3 times
  [ ] Can trigger an alert live in under 30 seconds
  [ ] Have answers for: "How much?", "How long to install?", "Is my data safe?"
  [ ] Have the pilot proposal ready: "2-3 sensors, 2 weeks, free"
```

### 4.2 What the Demo Should Feel Like

```
CLIENT SHOULD FEEL:          CLIENT SHOULD NOT FEEL:
─────────────────────        ──────────────────────────
"This is simple"             "This is complicated"
"I understand what I see"    "What does that number mean?"
"This would work for us"     "This is someone's science project"
"I want this running now"    "Maybe in 6 months when it's ready"
"These people know my pain"  "These are tech people who don't get my world"
"I can trust these people"   "What if they disappear next month?"
```

---

## 5. The Pilot: What to Build Beyond the Demo

Once a prospect says "yes, let's try it" — you need a few more things:

### 5.1 Pilot Requirements (Build These Between Demo and Pilot)

| # | Feature | Why | Effort |
|---|---------|-----|:---:|
| 1 | **Real sensor hardware ready to install** | Can't pilot with fake devices | Partner handles |
| 2 | **Separate client login** | They need their own account, not your demo account | 1-2 hours |
| 3 | **Their devices show up on their dashboard** | Not mixed with your demo devices | 1-2 hours |
| 4 | **Alert configured for their thresholds** | "Alert me if Freezer 1 goes above -15C" | 30 min (manual config) |
| 5 | **Alert goes to THEIR email** | Not your email | 30 min |
| 6 | **System runs 24/7 reliably for 2 weeks** | If it crashes during the pilot, you lose trust | Test stability beforehand |
| 7 | **You can see their data too** (admin view) | Monitor the pilot, spot issues before they do | Already have access |

### 5.2 Pilot Timeline

```
DAY 0 (Saturday morning):
  Partner installs 2-3 sensors at client site (1-2 hours)
  You verify data flowing on your phone within 15 minutes
  Send client: "Your monitoring is live. Here's your login: [url]"

DAY 1:
  Check data is flowing. Fix any connectivity issues.
  Text client: "Everything looks good. Your Freezer 1 has been at -18.2C all day."

DAY 3:
  Send first mini-summary: "3 days of data, all readings within range, no alerts triggered."
  Ask: "Are the thresholds right? Anything you'd like to adjust?"

DAY 7:
  Send weekly summary (manual or auto-generated)
  Include: min/max/avg, any alerts, uptime percentage
  Call or text: "How's it going? Any feedback?"

DAY 10:
  If no alerts fired naturally, trigger a test alert:
  "I'd like to test the alert system — I'll lower the threshold temporarily
   so you can see what an alert looks like. OK?"
  → They get the email → They see it works → Trust increases

DAY 14:
  Send pilot summary report
  Schedule call: "Here's what we found over 2 weeks. Ready to talk about next steps?"
  The ask: "Would you like to continue with [N] more sensors? Here's the pricing."
```

### 5.3 What NOT to Build for the Pilot

| Feature | Why to Skip |
|---------|-----------|
| Self-service alert configuration | You configure alerts for them manually. Takes 5 minutes. |
| User management | You create their account manually. |
| Multiple dashboards per device | One chart per device is enough. |
| Historical data beyond 2 weeks | The pilot IS the history. |
| Fancy UI polish | Functional > beautiful at this stage. |
| Automated onboarding | You're onboarding 1 client. Do it by hand. |
| Billing / payments | Invoice them manually. PayPal, bank transfer, whatever. |

---

## 6. From Pilot to Paying Client

### 6.1 The Conversion Conversation

```
"Over the past 2 weeks, your system has been running at 99.9% uptime.
 Your 3 sensors recorded [N] data points. We caught [event, if any].

 Without monitoring, that [event] would have gone unnoticed for [hours].

 To continue and expand, here's what I'd suggest:
   - Keep the 3 pilot sensors running (they're already installed)
   - Add [N] more to cover [areas they mentioned]
   - Total: [N] sensors at $29/device/month = $[total]/month

 That's [$X per day], less than a single manual temperature check.

 If a compressor fails and you catch it 4 hours earlier, the sensors
 pay for themselves for [N] years.

 Want to go ahead?"
```

### 6.2 What to Build Between Pilot Client 1 and Client 2

Only build what broke or was painful during the first pilot:

```
PROBABLY NEED:
  ○ Easier way to create new client accounts (simple script, not full admin UI)
  ○ Alert template per industry ("standard cold storage thresholds")
  ○ Fix whatever was flaky during pilot (connectivity, alerting lag, etc.)

PROBABLY DON'T NEED:
  ✗ Full admin panel
  ✗ Self-service registration
  ✗ Automated billing
  ✗ Marketing website
```

---

## 7. Feature Build Priorities (What Order, What Stage)

### 7.1 The Build Ladder

```
LEVEL 1: DEMO-READY (build now)
──────────────────────────────
  ✓ Branded web app with login
  ✓ Live dashboard with embedded charts
  ✓ Mobile responsive
  ✓ Email alerts
  ✓ Device online/offline status
  ✓ Basic export (CSV)
  ✓ 1 sensor type (temperature)
  ✓ Fake device simulator running 24/7

LEVEL 2: PILOT-READY (build when prospect says yes)
────────────────────────────────────────────────────
  ○ Separate client accounts
  ○ Per-client device isolation
  ○ Alert goes to client's email
  ○ System stable for 14 days continuous
  ○ Real sensor hardware works reliably

LEVEL 3: FIRST-CLIENT-READY (build during/after first pilot)
────────────────────────────────────────────────────────────
  ○ Weekly summary report (PDF or email)
  ○ Alert history
  ○ Multiple devices per client (5-10)
  ○ Script to onboard new client in <30 minutes
  ○ Basic monitoring of your own infrastructure

LEVEL 4: SCALING (build at 3-5 clients)
───────────────────────────────────────
  ○ Admin panel (manage clients, devices, users)
  ○ Self-service alert configuration
  ○ Multiple sensor types
  ○ Device groups / tags
  ○ Proper CI/CD
  ○ Azure deployment (or stay on VPS if it works)

LEVEL 5: GROWTH (build at 10+ clients)
──────────────────────────────────────
  ○ Automated onboarding flow
  ○ Billing integration (Stripe)
  ○ Marketing website
  ○ API for integrations
  ○ Webhook on alert
  ○ White-label / reseller support

LEVEL 6: MATURE (build at 25+ clients)
──────────────────────────────────────
  ○ Multi-region deployment
  ○ SLA dashboard / public status page
  ○ Advanced analytics (SPC, trends)
  ○ Mobile app (or just ensure PWA works)
  ○ Automated PDF compliance reports
```

### 7.2 The Anti-Build List (Things That Feel Productive But Aren't)

| Activity | Why It Feels Productive | Why It's Not |
|----------|----------------------|-------------|
| Designing a logo | Visual progress | Zero clients care about your logo |
| Building a marketing website | "We need a web presence" | You're selling to 5 people via LinkedIn, not to the internet |
| Writing a business plan | "Investors need this" | You're not talking to investors yet |
| Setting up CI/CD | "Best practice" | You have one server and deploy monthly |
| Choosing between React UI libraries for 3 weeks | Feels like research | Any component library works. Pick one in 30 minutes. |
| Building multi-tenant isolation | "We'll need it eventually" | You have 0-1 clients. One Grafana org is fine. |
| Writing tests for features that might change | "Quality matters" | The feature itself might get removed after client feedback |
| Optimizing database queries | "Performance matters" | You have 3 devices generating 3 rows/minute |
| Learning Kubernetes | "We'll need it at scale" | A $10 VPS runs your entire stack right now |
| Designing the data model for 50 sensor types | "Future-proofing" | You have 1 sensor type and 0 clients |
| Researching edge AI | Interesting | Irrelevant until you have 100+ devices |
| Reading about IoT market trends | "Market research" | You already know the market. Go talk to a prospect. |
| Comparing 5 email services | "Due diligence" | Pick SendGrid. Move on. Change later if needed. |

**The test:** "Will this help me get a demo in front of a prospect THIS MONTH?" If no, it's not Level 1 priority.

---

## 8. Two-Person Sprint Plan (Demo-Ready in 4 Weeks)

Assuming 10-15 hours/week each:

### Week 1: Platform Foundation

```
YOU:
  [ ] Add PostgreSQL to docker-compose
  [ ] Scaffold FastAPI backend with /api/health
  [ ] Create database schema (orgs, users, devices)
  [ ] Seed script: 1 org, 1 user, 3 devices with real names
  [ ] Update fake_device.py to simulate 3 named devices

PARTNER:
  [ ] Select ESP32 board + temperature sensor
  [ ] Build first prototype (breadboard OK)
  [ ] Get MQTT publishing working to your local EMQX
  [ ] Test: data from real sensor appears in Grafana
```

### Week 2: Web App + Embedding

```
YOU:
  [ ] Scaffold React frontend (Vite + TanStack Router)
  [ ] Login page (hardcoded credentials OK for now)
  [ ] Dashboard page: list devices with status
  [ ] Device detail page: embedded Grafana panels
  [ ] Test on mobile (responsive layout)
  [ ] Configure Grafana for iframe embedding

PARTNER:
  [ ] Get sensor into a basic enclosure
  [ ] Test reliability: 48 hours continuous, auto-reconnect after power cycle
  [ ] Document: what sensor, what probe, what enclosure, what cost
```

### Week 3: Alerts + Export

```
YOU:
  [ ] Set up Grafana alerting (API or manual)
  [ ] Configure email alerts (Mailhog locally, real SMTP for demo server)
  [ ] Trigger alert → verify email arrives
  [ ] CSV export endpoint for device data
  [ ] Device online/offline status (green/red dot)

PARTNER:
  [ ] Build second sensor unit (identical to first)
  [ ] Test both sensors reporting simultaneously
  [ ] Test range / WiFi reliability in a real-world-like setting
```

### Week 4: Demo Polish + Deploy

```
YOU:
  [ ] Deploy to a VPS (DigitalOcean/Hetzner, docker-compose up)
  [ ] Verify everything works remotely
  [ ] Practice the 5-minute demo 3 times
  [ ] Record a 3-minute screen recording
  [ ] Prepare 1-page PDF pitch

PARTNER:
  [ ] Sensor demo kit ready (2 sensors, cables, enclosures)
  [ ] Can install in <15 minutes at a client site
  [ ] Written install instructions (for when you scale beyond just him)
  [ ] Practice explaining the hardware in 2 minutes (non-technical)

TOGETHER:
  [ ] End-to-end test: install real sensor → data in dashboard → alert fires → email arrives
  [ ] Identify 5 prospects to demo to
  [ ] Send first 5 outreach messages
```

**End of Week 4: You have a working demo and 5 prospects in your pipeline.**

---

## 9. The Decision Tree

```
START HERE
    │
    ▼
Do you have a working demo?
    │
    ├── NO → Build it (Section 3 + Section 8). Stop reading everything else.
    │
    └── YES
         │
         ▼
    Have you shown it to 5 real prospects?
         │
         ├── NO → Show it. Today. This week. Even if it's ugly.
         │
         └── YES
              │
              ▼
         Did anyone say "I want to try this"?
              │
              ├── NO → Ask them why. What's missing? What would make them try it?
              │         Build THAT, not what you think they need.
              │
              └── YES
                   │
                   ▼
              Run the pilot (Section 5).
                   │
                   ▼
              Did they convert to paid?
                   │
                   ├── NO → Ask why. Price? Features? Trust? Fix it.
                   │
                   └── YES
                        │
                        ▼
                   Repeat. Get to 3 clients.
                        │
                        ▼
                   NOW consider: investors, partners, hiring, scaling.
                   Not before.
```

---

## 10. Summary

```
BUILD for demo:       Login, dashboard, live data, alerts, export, mobile. That's it.
DON'T BUILD for demo: Admin panel, CI/CD, cloud infra, multi-tenancy, billing, analytics.

GET a client first:   Proves the product works, generates revenue, creates case studies.
GET an investor later: Only to scale what's already working, not to discover if it works.

DEMO to prospects:    Show real data, trigger a real alert, offer a free pilot.
DEMO to investors:    Show paying clients, revenue, growth. (Do this at 3-5 clients.)

THE ONLY QUESTION:    "Can I demo this to a real prospect this month?"
                      If yes → do it.
                      If no → build only what's needed to say yes.
```

---

*Companion documents:*
- *[`SALES-AND-GO-TO-MARKET.md`](./SALES-AND-GO-TO-MARKET.md) — detailed pitch scripts, objection handling*
- *[`STARTUP-PLAYBOOK.md`](./STARTUP-PLAYBOOK.md) — two-founder operating model, milestones, honest math*
- *[`TECH-LEAD-PLAYBOOK.md`](../planning/TECH-LEAD-PLAYBOOK.md) — full sprint plan for the platform*
