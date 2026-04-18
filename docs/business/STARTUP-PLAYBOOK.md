# IoTDash — Startup Playbook (Two Founders, Keeping Day Jobs)

> **Purpose:** Practical advice for two people building an IoT business on the side. No VC fantasy. Real constraints, real decisions.

---

## 1. Your Starting Position

```
FOUNDER A (You):     Data + Platform — backend, frontend, cloud, analytics
FOUNDER B (Partner): Hardware + Support — sensors, firmware, installation, field support

Combined:            You cover the full IoT stack end-to-end
Missing:             Sales, marketing, business operations, legal, finance
```

**This is a strong founding team.** Most IoT startups fail because they have software people who don't understand hardware, or hardware people who can't build a platform. You have both. That's your unfair advantage.

---

## 2. The Side-Project Startup Model

### 2.1 Rules for Building While Employed

| Rule | Why |
|------|-----|
| **Don't quit your job until revenue covers 50% of your salary** | Runway anxiety kills creativity. Your job is your investor. |
| **Set a fixed weekly budget of hours (10-15h each)** | Prevents burnout. Sustainable pace > heroic sprints. |
| **Work in the mornings or weekends, not after exhausting workdays** | Your best thinking happens when you're fresh, not at 11 PM. |
| **Set a monthly milestone, not a daily to-do list** | Some weeks you'll do 20 hours, some weeks 3. Monthly goals smooth it out. |
| **Check your employment contracts** | Some contracts claim IP you build on your own time. Know what yours says. Clear it in writing if needed. |
| **Don't use employer resources** | No company laptop, no company cloud account, no company time. Clean separation. |

### 2.2 Realistic Timeline (Side-Project Pace)

```
Full-time startup:     MVP in 3 months
Your reality:          MVP in 6-9 months (10-15 hrs/week each)

Full-time startup:     First client in 4-5 months
Your reality:          First client in 9-12 months

Full-time startup:     10 clients in 12 months
Your reality:          10 clients in 18-24 months
```

**That's fine.** You're not burning cash. You have infinite runway because your day jobs fund everything. Speed is nice, but survival is better.

---

## 3. How to Split the Work

### 3.1 Clear Ownership

| Area | Owner | Why |
|------|-------|-----|
| Platform (backend, frontend, cloud) | You | Your expertise |
| Hardware (sensors, firmware, connectivity) | Partner | His expertise |
| Sales & client relationships | **Both** (but assign per client) | Neither of you is a natural salesperson — share the pain |
| Installation & on-site support | Partner | He's the hardware person, he goes on-site |
| Marketing & content | You | You can write, build demos, record videos |
| Finance & admin | Alternate or assign | Someone has to do invoices and taxes. Decide now. |

### 3.2 What NOT to Split

- **Product decisions** — make together. Weekly 30-minute sync.
- **Pricing** — agree once, don't change without discussion.
- **Big client commitments** — both sign off before promising anything.
- **Equity and money** — get this in writing early (see Section 9).

---

## 4. What to Build First (MVP Scope for Side-Project Pace)

### 4.1 The Minimum Sellable Product

Strip down the platform plan to what you can build in 3-4 months of evenings and weekends:

```
MUST HAVE (MVP):
  ✓ 1 type of sensor working end-to-end (temperature)
  ✓ Data flows from sensor → cloud → dashboard
  ✓ Client login (email + password)
  ✓ Client sees their devices and graphs
  ✓ Email alert when threshold crossed
  ✓ Works on phone (responsive)
  ✓ PDF/CSV export for compliance

NICE TO HAVE (v1.1, after first client):
  ○ Admin panel (manage orgs, devices, users via UI)
  ○ Multiple sensor types
  ○ Alert history
  ○ Device online/offline status

DON'T BUILD YET:
  ✗ CI/CD pipeline
  ✗ Azure deployment (use a simple VPS or single container host)
  ✗ Multi-tenant isolation
  ✗ Edge AI
  ✗ Predictive maintenance
  ✗ Public status page
```

**For the MVP, manual setup is fine.** You create orgs and devices via database scripts or a simple admin API. You deploy by SSH-ing into a server. Polish comes after validation.

### 4.2 Partner's Hardware MVP

```
MUST HAVE:
  ✓ One reliable sensor (temperature, off-the-shelf or custom)
  ✓ Connects via WiFi to MQTT broker
  ✓ Sends data every 30-60 seconds
  ✓ Survives power cycle (auto-reconnect)
  ✓ Enclosure that looks professional (not a bare PCB with wires)

NICE TO HAVE:
  ○ Battery backup (sends "power lost" alert)
  ○ Multiple sensor inputs per unit
  ○ Cellular (4G/LTE) option for sites without WiFi

DON'T BUILD YET:
  ✗ Custom PCB (use ESP32 dev board + sensor module)
  ✗ Mass manufacturing
  ✗ Certifications (CE, FCC) — needed for selling, but not for pilots
```

---

## 5. Go-to-Market Without Quitting Your Job

### 5.1 The Evening & Weekend Sales Approach

You can't do 50 cold calls a day. You can do this:

| Activity | Time Required | When | Expected Result |
|----------|:---:|------|----------------|
| Send 10 LinkedIn messages | 30 min | Monday evening | 1-2 responses per week |
| One 15-min demo call | 15 min | Lunch break or evening | 1-2 per month |
| One on-site pilot installation | Saturday morning (2-3 hrs) | When a prospect says yes | 1 per month |
| One blog post or LinkedIn post | 1 hour | Sunday | Building credibility over time |
| Client check-in call | 15 min | Evening | Retention + referrals |

**Total sales effort: 3-5 hours/week.** The rest goes to building.

### 5.2 Your First Client Strategy

**Don't look for strangers. Look for people who already trust you.**

| Source | How | Why It Works |
|--------|-----|-------------|
| Partner's existing contacts | He's a hardware/support engineer — he knows facility managers, maintenance teams | They already trust him with their equipment |
| Your professional network | LinkedIn, former colleagues, friends in relevant industries | Warm intro, not cold outreach |
| Local businesses you personally use | Your gym, your local restaurant, your office building | You can walk in and talk to the owner |
| Friends and family connections | "Does anyone you know run a warehouse / restaurant / cold storage?" | Surprisingly effective |

**Your first client should be someone who'll forgive you when things break.** Friends, former colleagues, local businesses. Not a Fortune 500.

### 5.3 Pricing for First Clients

```
Client 1-3:     Free or deeply discounted ($10/device/month)
                In exchange for: testimonial, case study, honest feedback
                Duration: 3-6 months of free/cheap, then normal pricing

Client 4-10:    Discounted ($19/device/month)
                "Early adopter" pricing

Client 11+:     Full price ($29-49/device/month)
                Backed by case studies and references from Client 1-3
```

**Your first clients are NOT revenue sources. They're proof points.** Treat them like co-developers. Their feedback shapes the product.

---

## 6. Protecting Your Ideas (Without Paranoia)

### 6.1 What to Share, What to Keep

| Share Freely | Keep to Yourself |
|-------------|-----------------|
| What the product does (features, benefits) | How you build it (architecture, code, proprietary algorithms) |
| That you monitor temperature / equipment | Your pricing model details (until asked) |
| General approach (cloud monitoring, alerts, dashboards) | Specific client names (until they consent) |
| That you have a working platform | Your cost structure and margins |
| Your industry knowledge and expertise | Your sales pipeline and prospect list |

### 6.2 Reality About Ideas

- **Ideas are worth nothing. Execution is everything.** 100 people have the same idea right now. The two of you building it together is what matters.
- **Competitors will copy your features regardless.** Speed and client relationships are your moat, not secrecy.
- **Talking about your product is marketing, not a risk.** The more people know about it, the more leads you get.
- **If someone can steal your business by hearing a 5-minute pitch, your business isn't defensible.** Your defense is: you built the platform, you have the client relationships, you have the domain expertise.

### 6.3 What IS Worth Protecting

- **Client data** — contractually and technically. This is sacred.
- **Source code** — keep it in a private repo. This is your asset.
- **Client relationships** — these are your real moat.
- **Brand/name** — register a domain and trademark when you're ready to be public.

---

## 7. Do You Need Investors?

### 7.1 Short Answer: Not Yet, Probably Not Ever

| Factor | Your Situation | Implication |
|--------|---------------|-------------|
| Development cost | Your time (free — you're employed) | No need for dev funding |
| Infrastructure cost | $50-200/month (VPS + managed DB + domain) | Trivially affordable |
| Hardware cost | $20-50 per sensor prototype | Fund from savings |
| Sales cost | Your evenings + partner's Saturdays | No need for a sales team |
| Runway | Infinite (day jobs) | No burn rate pressure |

**You need investors when:** You want to grow faster than organic revenue allows. Specifically:
- Hiring employees (first hire: $50-80K/year)
- Marketing spend (paid ads, trade shows: $10-30K/year)
- Inventory (pre-buying 500 sensors: $10-25K)
- Certifications (CE, FCC: $5-15K per product)

**That's $75-150K.** You could either:
1. Self-fund from revenue once you have 20-30 clients ($7-15K MRR)
2. Take a small loan or government grant
3. Find an angel investor (not VC)

### 7.2 Types of Funding (If You Eventually Need It)

| Type | Amount | What You Give Up | Good For |
|------|:---:|---------|---------|
| **Bootstrapping** (revenue) | $0 | Nothing | Your current path. Best option. |
| **Friends & family** | $5-30K | Personal relationships at risk | Bridging a specific gap (first batch of hardware) |
| **Government grants** | $10-100K | Time (applications), reporting obligations | R&D, innovation programs. Many countries have IoT/Industry 4.0 grants. |
| **Angel investor** | $25-200K | 5-20% equity, board seat/advisory | When you have 10+ clients and want to accelerate |
| **Accelerator** | $20-150K | 5-10% equity, 3-month program | Mentorship + network. Good ones: Y Combinator, Techstars, industry-specific. |
| **VC (Seed)** | $500K-2M | 15-25% equity, board control, pressure to scale fast | Only if you want to build a $50M+ company and grow 3x/year |

**For two founders with day jobs building a lifestyle/SMB business:** Bootstrap → Grants → Angel if needed. Skip VC unless you want the high-growth pressure.

---

## 8. Do You Need Partners (Business Partners, Not Co-Founder)?

### 8.1 Types of Partners

| Partner Type | What They Do | When You Need Them | How to Find |
|-------------|-------------|-------------------|-------------|
| **Reseller / Installer** | Sells and installs your system as part of their service | When you can't do installations yourself (geography, volume) | HVAC companies, refrigeration companies, electrical contractors |
| **Sensor manufacturer** | Supplies hardware at scale | When custom hardware is too expensive or slow to produce | Alibaba, trade shows, industry contacts |
| **System integrator** | Integrates your platform into larger projects (building management, SCADA) | When enterprise clients need your platform alongside other systems | Industry conferences, LinkedIn |
| **Channel partner** | Refers clients in exchange for commission | When you want leads without doing outreach | Industry associations, consultants |

### 8.2 What's Right for Your Stage

```
NOW (0-5 clients):     No partners needed. You two do everything.
SOON (5-20 clients):   One reseller/installer partner in a different city.
                       Model: they install + support, you run the platform.
LATER (20-50 clients): Multiple reseller partners. Maybe a sensor supplier deal.
MUCH LATER (50+):      Channel partner program, system integrator partnerships.
```

**Don't partner prematurely.** Partners add complexity (revenue sharing, support alignment, quality control). Build the product and process first. Partner when YOU can't scale, not before.

### 8.3 Reseller Model (Most Likely First Partnership)

```
Your role:
  - Build and run the platform
  - Provide hardware (or hardware specs for them to source)
  - Provide training and documentation
  - Handle L2/L3 support (platform issues)

Reseller's role:
  - Find and close clients in their region
  - Install sensors on-site
  - Handle L1 support (client questions, basic troubleshooting)
  - Handle billing (or you bill directly, they get commission)

Revenue split options:
  A) Reseller buys at wholesale (60-70% of retail), sells at retail
  B) You bill client directly, reseller gets 20-30% commission
  C) Reseller pays a monthly per-client platform fee to you

Best for your stage: Option B (you keep the client relationship)
```

---

## 9. Founder Agreement (Do This Now)

### 9.1 What to Agree in Writing

Even if your partner is your best friend, get these in writing. A simple document signed by both is enough — you don't need a lawyer for the first version.

| Topic | What to Decide |
|-------|---------------|
| **Equity split** | 50/50 is simple and fair if contribution is equal. If not, agree on what's fair. |
| **Vesting** | 4-year vesting with 1-year cliff. If one person leaves after 3 months, they don't keep 50%. |
| **Decision making** | Who decides what? Deadlocks? (With 2 founders, deadlocks are real.) |
| **Time commitment** | "Each founder commits a minimum of 10 hours/week." What happens if one stops contributing? |
| **Money in** | Is either person investing cash? How is that tracked? |
| **Money out** | When do you start paying yourselves? How are profits split? |
| **IP ownership** | The company owns the code and hardware designs, not the individuals. |
| **Exit scenarios** | What if one wants to quit? What if one wants to sell? What if you disagree on direction? |
| **Expenses** | How are costs split? Who pays for cloud hosting, hardware, domains? |
| **Day job conflict** | What if one person's employer claims a conflict? |

### 9.2 Vesting Example

```
Total equity: 100 shares (50 each)
Vesting period: 4 years
Cliff: 1 year

Year 0-1:  No shares vested. If someone leaves, they get nothing.
Year 1:    12.5 shares vest (25% of their allocation — the "cliff")
Year 1-4:  ~1.04 shares vest per month

If Founder B leaves after 2 years:
  → Founder B keeps 25 shares (50% of their allocation)
  → Remaining 25 shares return to the company pool
  → Founder A continues with full control
```

**Why this matters:** Without vesting, if your partner quits after 1 month, they still own 50% of the company forever. Vesting protects both of you.

---

## 10. How to Structure the Business

### 10.1 Legal Entity Options

| Structure | When | Cost | Complexity |
|-----------|------|:---:|:---:|
| **Informal partnership** (handshake) | Building/testing, no revenue yet | Free | None |
| **Simple partnership agreement** (written, not incorporated) | First pilots, small revenue | $0-500 | Low |
| **LLC / Ltd company** | First paying client | $200-2000 (varies by country) | Medium |
| **Corporation** (if seeking investment) | When taking outside money | $1000-5000 | High |

**Action now:** Write a simple partnership agreement (Section 9.1). Incorporate an LLC when you land your first paying client.

### 10.2 Bank and Finance

```
Stage 1 (pre-revenue):  Split costs personally. Track in a shared spreadsheet.
Stage 2 (first revenue): Open a business bank account. All revenue in, all costs out.
Stage 3 (growing):       Accounting software (Wave — free, or Xero). Quarterly bookkeeping.
Stage 4 (serious):       Hire an accountant. Monthly bookkeeping. Tax planning.
```

---

## 11. Milestones: When to Make Big Decisions

| Milestone | Decision to Make |
|-----------|-----------------|
| **MVP works end-to-end** | Start talking to potential clients. Not before. |
| **First pilot running** | Incorporate the company (LLC/Ltd). |
| **First paying client** | Open business bank account. Get basic liability insurance. |
| **3 paying clients** | Start building case studies. Begin systematic outreach. |
| **$3K MRR (10 clients)** | Consider: reduce day job to 4 days/week? Start reseller program? |
| **$8K MRR (25 clients)** | Consider: one person goes full-time? Hire part-time support? |
| **$15K MRR (50 clients)** | Both go full-time. Hire first employee (support/sales). |
| **$30K MRR (100 clients)** | Seek growth funding if needed. Expand to new regions/industries. |

**Don't make any big decision before its milestone.** Don't quit your job at 3 clients. Don't hire at 10 clients. Don't raise money at 25 clients. Let the revenue pull you forward.

---

## 12. Common Mistakes by Technical Founders

| Mistake | Why It Happens | What to Do Instead |
|---------|---------------|-------------------|
| **Building for 6 months without talking to anyone** | "It's not ready yet." It never feels ready. | Talk to potential clients with a demo after month 2. Even if it's ugly. |
| **Building what you think clients need** | You're an engineer, not the user. | Ask 5 potential clients "what's your biggest pain?" before building anything beyond MVP. |
| **Perfecting the architecture before getting a client** | It feels productive but generates zero revenue. | Good enough architecture + 1 client beats perfect architecture + 0 clients. |
| **Avoiding sales because it's uncomfortable** | Engineers hate rejection. | Sales is a skill. It gets easier after 10 conversations. The first 5 are the worst. |
| **50/50 equity without vesting** | "We trust each other." | Trust AND verify. Vesting protects both of you. |
| **Not charging enough** | "Nobody will pay $29/month for this." They will. A prevented $5K freezer loss makes $29/month look like nothing. | Charge more than feels comfortable. You can always discount. You can never raise prices on existing clients. |
| **Building features instead of selling** | Building is fun, selling is hard. So you build another feature instead of making another call. | Set a rule: no new feature without client feedback requesting it. Alternate weeks: build week, sell week. |
| **Not documenting wins** | A client says "this is great!" and you forget to write it down. | Every positive comment → screenshot/quote → testimonial folder. You'll need these for sales materials. |
| **Trying to serve everyone** | "We can do cold storage AND manufacturing AND agriculture AND smart cities!" | Pick ONE industry for the first 10 clients. Dominate that niche. Expand later. |
| **Not setting deadlines** | Side projects drift forever without time pressure. | "We will demo to a real prospect by [date]." Tell someone. Accountability. |

---

## 13. Your Two-Person Weekly Rhythm

```
MONDAY EVENING (30 min, together):
  - Quick sync: what did we each do last week?
  - What's the priority this week?
  - Any blockers?

WEEKDAYS (individually, 1-2 hrs/day):
  You:     Platform work (code, config, docs)
  Partner: Hardware work (firmware, sensor testing, enclosure)

SATURDAY MORNING (2-3 hrs, one of you or together):
  - Client pilot installation (if scheduled)
  - OR: testing, integration, demo prep
  - OR: sales outreach batch (10 LinkedIn messages)

SUNDAY (1 hr, optional):
  - Blog post, LinkedIn post, or video
  - Or rest. Rest is productive too.

MONTHLY (1 hr, together):
  - Review: did we hit our milestone?
  - Pipeline: who are we talking to?
  - Finance: what did we spend? Any revenue?
  - Next month's goal (one sentence)
```

---

## 14. The Honest Math

```
YOUR COST TO RUN THIS:
  Cloud hosting (VPS + managed DB):    $50-100/month
  Domain + email:                      $15/month
  Hardware prototypes (sensors):       $200-500 one-time
  LinkedIn Sales Navigator:            $80/month (optional)
  LLC registration:                    $200-500 one-time
  Insurance (basic liability):         $30-50/month
                                       ──────────────
  Monthly operating cost:              ~$200-300/month
  Shared between two people:           ~$100-150/month each

YOUR REVENUE AT EACH STAGE:
  5 clients × 5 devices × $29  =      $725/month
  10 clients × 10 devices × $29 =     $2,900/month
  25 clients × 15 devices × $25 =     $9,375/month
  50 clients × 20 devices × $22 =     $22,000/month

YOUR TAKE-HOME (after costs, before tax):
  5 clients:   $725 - $250 costs = $475 → $237 each
  10 clients:  $2,900 - $400 costs = $2,500 → $1,250 each
  25 clients:  $9,375 - $800 costs = $8,575 → $4,287 each
  50 clients:  $22,000 - $2,000 costs = $20,000 → $10,000 each

BREAK-EVEN (covers your operating costs):    2 clients
MEANINGFUL SIDE INCOME ($1K+/month each):    10-15 clients
REPLACE SALARY ($5K+/month each):            30-40 clients
```

**At 10 clients you have a validated business. At 30 clients you can quit your job. At 50 clients you're hiring.**

---

## 15. Action Items (Do This Week)

```
[ ] 1. Write a 1-page partnership agreement (Section 9.1)
[ ] 2. Set your MVP scope (Section 4.1 — print it, stick it on the wall)
[ ] 3. Pick ONE target industry (cold chain recommended — Section 1.2)
[ ] 4. List 10 people you know who might know someone in that industry
[ ] 5. Set a monthly milestone for next month
[ ] 6. Set your weekly sync time (Monday evening — Section 13)
[ ] 7. Agree on: who owns what area (Section 3.1)
[ ] 8. Create a shared spreadsheet for expenses
```

---

*Companion documents:*
- *[`SALES-AND-GO-TO-MARKET.md`](./SALES-AND-GO-TO-MARKET.md) — detailed sales strategy, pitches, objection handling*
- *[`TECH-LEAD-PLAYBOOK.md`](../planning/TECH-LEAD-PLAYBOOK.md) — sprint-by-sprint build plan*
- *[`TRIVIAL-AND-OUT-OF-BOX-FEATURES.md`](../planning/TRIVIAL-AND-OUT-OF-BOX-FEATURES.md) — features that sell well with minimal effort*
