# IoTDash Documentation

## planning/

Core project planning, architecture, and development guidance.

| Document | Description |
|----------|-------------|
| [PLANNING.md](planning/PLANNING.md) | Master plan — current state audit, gap analysis, DB schema, implementation phases |
| [ARCHITECTURE.md](planning/ARCHITECTURE.md) | System diagrams, MQTT topics, data flows, multi-tenancy model |
| [API-SPEC.md](planning/API-SPEC.md) | Full REST API specification |
| [TECH-LEAD-PLAYBOOK.md](planning/TECH-LEAD-PLAYBOOK.md) | Sprint-by-sprint dev sequence (2-week sprints), decision log, risk register |
| [SKILLS-AND-FEATURES-BREAKDOWN.md](planning/SKILLS-AND-FEATURES-BREAKDOWN.md) | Every tool + feature to learn, organized by sprint |
| [SENIOR-DEV-PROJECT-MANAGEMENT-GUIDE.md](planning/SENIOR-DEV-PROJECT-MANAGEMENT-GUIDE.md) | 30 project management practices for senior devs |
| [TRIVIAL-AND-OUT-OF-BOX-FEATURES.md](planning/TRIVIAL-AND-OUT-OF-BOX-FEATURES.md) | 33 low-effort high-value features to sprinkle across sprints |

## Strategy

### technical/

Scaling, infrastructure, alerting, and deployment architecture.

| Document | Description |
|----------|-------------|
| [SCALING-STRATEGY.md](technical/SCALING-STRATEGY.md) | Growth stages, when to introduce Kafka/Flink, AWS vs Azure, managed IoT |
| [GRAFANA-ALERTING-STRATEGY.md](technical/GRAFANA-ALERTING-STRATEGY.md) | Grafana alerting API, multi-org, scaling characteristics |
| [ALERTING-BEYOND-GRAFANA.md](technical/ALERTING-BEYOND-GRAFANA.md) | 7 alternatives if Grafana alerting is dropped |
| [EMAIL-NOTIFICATION-STRATEGY.md](technical/EMAIL-NOTIFICATION-STRATEGY.md) | Email architecture, provider comparison, storm protection |
| [SINGLE-TENANT-DEPLOYMENT-STRATEGY.md](technical/SINGLE-TENANT-DEPLOYMENT-STRATEGY.md) | Per-client isolation, 3 architecture options, cost analysis |

### business/

Sales, market research, competitors, founder playbooks, and operations.

| Document | Description |
|----------|-------------|
| [SALES-AND-GO-TO-MARKET.md](business/SALES-AND-GO-TO-MARKET.md) | Who to sell to, how to pitch, pricing, objection handling, common mistakes |
| [WHY-THEY-BUY.md](business/WHY-THEY-BUY.md) | Understanding business pain, discovery questions, buying signals, industry breakdowns |
| [COMPETITOR-ANALYSIS.md](business/COMPETITOR-ANALYSIS.md) | 20+ competitors mapped, 5 deep dives, pricing landscape, service companies, positioning |
| [CANADIAN-MARKET-RESEARCH.md](business/CANADIAN-MARKET-RESEARCH.md) | Canadian verticals, market sizes, regulations, government funding (SR&ED/IRAP), go-to-market |
| [DEMO-AND-FIRST-CLIENT-STRATEGY.md](business/DEMO-AND-FIRST-CLIENT-STRATEGY.md) | What to build for demos, pilot-to-client pipeline, investor vs client first |
| [PROTECTING-YOUR-DEMO.md](business/PROTECTING-YOUR-DEMO.md) | What to show vs hide in demos, onion model, demo environment setup, audience-specific rules |
| [STARTUP-PLAYBOOK.md](business/STARTUP-PLAYBOOK.md) | Two-founder side-project model, work split, equity, milestones, honest math |
| [FOUNDER-NOTES-PLATFORM-VALUE.md](business/FOUNDER-NOTES-PLATFORM-VALUE.md) | Internal only — platform vs hardware value, protecting position, navigating uncertainty |
| [INVESTORS-ADVISORS-AND-TEAM-BUILDING.md](business/INVESTORS-ADVISORS-AND-TEAM-BUILDING.md) | What investors bring, 8 types of people to attract, advisor equity, when to raise |
| [NETWORKING-STRATEGY.md](business/NETWORKING-STRATEGY.md) | Do you need networking, how to do it, what value to bring, introvert-friendly tactics |
| [TIME-MANAGEMENT-AND-AI-DELEGATION.md](business/TIME-MANAGEMENT-AND-AI-DELEGATION.md) | Time math, weekly schedule, AI delegation matrix, baby-month planning, energy management |

## analytics/

Edge computing, ML, and data analytics strategy.

| Document | Description |
|----------|-------------|
| [CLASSICAL-VS-ML-ANALYTICS.md](analytics/CLASSICAL-VS-ML-ANALYTICS.md) | Which IoT analytics are classical vs need ML, mechanics of each |
| [PREDICTIVE-MAINTENANCE.md](analytics/PREDICTIVE-MAINTENANCE.md) | 4 levels of maintenance, does it need ML, implementation path |
| [EDGE-AI-STRATEGY.md](analytics/EDGE-AI-STRATEGY.md) | Edge vs cloud, TinyML, gateway patterns, architecture changes |
