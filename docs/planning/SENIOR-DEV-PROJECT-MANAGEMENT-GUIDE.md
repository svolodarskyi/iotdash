# Software Engineering Project Management Practices

> A reference guide for senior/lead developers on the artifacts, analyses, and disciplines used to plan, execute, and deliver software projects.

---

## Table of Contents

1. [Discovery & Analysis Practices](#1-discovery--analysis-practices)
2. [Planning Artifacts](#2-planning-artifacts)
3. [Architecture & Design Artifacts](#3-architecture--design-artifacts)
4. [Execution & Delivery Practices](#4-execution--delivery-practices)
5. [Quality Practices](#5-quality-practices)
6. [Operations & Post-Delivery Practices](#6-operations--post-delivery-practices)
7. [People & Process Practices](#7-people--process-practices)
8. [When to Use What](#8-when-to-use-what)

---

## 1. Discovery & Analysis Practices

These practices help you understand **what exists**, **what's needed**, and **what's in the way** before you write any code.

---

### 1.1 Current State Audit (As-Is Assessment)

**What it is:**
A factual inventory of what exists right now — code, infrastructure, tools, processes, team capabilities. No opinions, just facts.

**Purpose:**
You cannot plan a journey without knowing where you are. The audit prevents you from building something that already exists, breaking something you didn't know about, or making assumptions about the codebase.

**What it covers:**
- Existing services, versions, and their status (working, broken, deprecated)
- Infrastructure (where things run, how they're deployed)
- Data stores and their schemas
- External dependencies and integrations
- Technical debt and known issues
- Team skills and capacity

**Output:** A table or document listing every component, its version, status, and relevant notes.

**When to use:** At the start of every project, engagement, or when joining an existing codebase.

**Common mistake:** Skipping it because "I already know the codebase." You don't. Things change. Document it.

---

### 1.2 Gap Analysis

**What it is:**
A structured comparison between the **current state** (what you have) and the **target state** (what you need). Each gap is a specific thing that's missing or insufficient.

**Purpose:**
Turns a vague sense of "we need to build a lot" into a concrete, prioritised list of work items. It's the bridge between audit and planning. Without it, you'll miss things or build in the wrong order.

**Structure:**

| Gap | Current State | Target State | Priority | Effort |
|-----|--------------|--------------|----------|--------|
| G1: User auth | No auth exists | JWT login + role-based access | P0 | Medium |
| G2: CI/CD | Manual deployment | GitHub Actions → Azure | P1 | Medium |

**Priority scale:**
- **P0 (Blocker):** Cannot ship without it. No workaround.
- **P1 (Critical):** Must have for production, but can demo without it.
- **P2 (Important):** Should have. Can launch without it and add later.
- **P3 (Nice to have):** Build only if time permits.

**When to use:** After the current state audit, before creating a roadmap or backlog.

**Common mistake:** Listing gaps without prioritising them. An unprioritised gap list is just a wish list.

---

### 1.3 Requirements Gathering

**What it is:**
The process of defining what the system must do (functional requirements) and how well it must do it (non-functional requirements).

**Purpose:**
Ensures you build what's actually needed, not what you assume is needed. Creates an agreement between stakeholders and builders.

**Types:**

| Type | Description | Example |
|------|-------------|---------|
| **Functional Requirements (FR)** | What the system does | "Users can create alerts with email notifications" |
| **Non-Functional Requirements (NFR)** | Quality attributes | "Dashboard loads in under 3 seconds" |
| **Constraints** | Fixed boundaries | "Must deploy to Azure, budget is $X/month" |
| **Assumptions** | Things you believe to be true | "Clients will have fewer than 50 devices each" |

**Output:** A requirements document, user stories, or acceptance criteria — depending on formality needed.

**When to use:** Before designing a solution. Revisit when requirements change.

**Common mistake:** Treating requirements as immutable. They will change. The practice is iterative.

---

### 1.4 Stakeholder Analysis

**What it is:**
Identifying everyone who has an interest in the project, what they care about, and how much influence they have.

**Purpose:**
Different people need different things from you. Your client cares about dashboards. Your ops person cares about deployment. Your future self cares about code quality. If you don't identify stakeholders, you'll optimise for the wrong audience.

**For solo/small teams:** Your stakeholders are still real — they're just fewer. Typically: you (developer), your clients, your future hires, your ops concerns.

**When to use:** At project kickoff. For solo projects, do it mentally in 5 minutes — it still sharpens focus.

---

### 1.5 Risk Assessment / Risk Register

**What it is:**
A list of things that could go wrong, how likely they are, how bad they'd be, and what you'll do about them.

**Purpose:**
Forces you to think about failure before it happens. A risk you've identified and mitigated is just a task. A risk you didn't identify is a crisis.

**Structure:**

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|-----------|--------|-----------|-------|
| Grafana embed blocked by CORS | Medium | High | Test embedding on Day 6 before building more UI | Dev |
| MQTT broker can't handle 1000 devices | Low | High | Load test at Sprint 5 | Dev |

**Likelihood:** Low / Medium / High
**Impact:** Low / Medium / High / Critical

**When to use:** At project start, reviewed at each sprint/milestone. Add new risks as you discover them.

**Common mistake:** Writing it once and never updating it. Risks change as the project evolves.

---

### 1.6 Feasibility Study / Proof of Concept (PoC)

**What it is:**
A small, time-boxed experiment to answer a specific technical question before committing to a full implementation.

**Purpose:**
De-risks the unknowns. Instead of building an entire alert system and then discovering the Grafana API doesn't support what you need, you spend 2 hours testing the API first.

**Rules for a good PoC:**
- **Time-boxed:** 2 hours to 2 days. Never more.
- **One question:** Each PoC answers exactly one question.
- **Throwaway code:** The output is knowledge, not production code. Delete it after.

**Examples:**
- "Can Grafana panels be embedded in an iframe across origins?"
- "Can Telegraf parse our new MQTT topic scheme?"
- "Can Azure Container Apps handle TCP ingress for MQTT?"

**When to use:** Whenever a gap analysis reveals a dependency on unproven technology or integration.

**Common mistake:** Turning the PoC into the real implementation. PoC code has no tests, no error handling, no structure. Throw it away and rebuild properly.

---

## 2. Planning Artifacts

These artifacts define **what you'll build**, **in what order**, and **how you'll know it's done**.

---

### 2.1 Project Charter / Project Brief

**What it is:**
A one-page summary of the project: what it is, why it matters, who it's for, what success looks like, and the boundaries.

**Purpose:**
Alignment. When you're deep in code at 2 AM, the charter reminds you what you're actually building and why. It prevents scope creep and keeps you honest.

**Template:**

```
Project:      [Name]
Objective:    [One sentence: what problem does this solve?]
Users:        [Who uses this?]
Success:      [How do you know it worked?]
Scope:        [What's IN scope]
Out of scope: [What's explicitly NOT in scope]
Constraints:  [Budget, timeline, technology, team]
```

**When to use:** Start of every project. Even solo ones. Especially solo ones — you have no one to keep you honest except this document.

---

### 2.2 Roadmap

**What it is:**
A high-level timeline showing major milestones and when they'll roughly be delivered. Not a detailed task list — a strategic view of the journey.

**Purpose:**
Communicates the plan to stakeholders (including future you). Shows what comes first and what depends on what. Helps you say "no" to requests that don't align with the current phase.

**Format:** Usually time-based phases or milestones:

```
Phase 1 (Weeks 1-2): Foundation — repo, DB, API skeleton
Phase 2 (Weeks 3-4): Core App — frontend, Grafana embedding
Phase 3 (Weeks 5-6): Alerts — alert engine, email delivery
Phase 4 (Weeks 7-8): Deployment — Azure, CI/CD, DNS
```

**When to use:** After gap analysis, before sprint planning.

**Common mistake:** Making it too granular. A roadmap with 200 tasks is a backlog, not a roadmap. Keep it to 4-8 milestones.

---

### 2.3 Work Breakdown Structure (WBS)

**What it is:**
A hierarchical decomposition of all the work needed, broken down from large deliverables into small, actionable tasks.

**Purpose:**
Makes large projects manageable. You can't estimate, assign, or track "Build the platform." You can estimate "Create the alerts database table."

**Structure:**
```
1. Backend API
   1.1 Project scaffold
       1.1.1 FastAPI project setup
       1.1.2 Docker configuration
       1.1.3 Database connection
   1.2 Authentication
       1.2.1 Login endpoint
       1.2.2 JWT middleware
       1.2.3 Password hashing
   1.3 Device management
       ...
```

**Rule of thumb:** Break down until each leaf task is 2-8 hours of work. Anything larger should be decomposed further.

**When to use:** After roadmap, to populate your backlog/sprint.

**Common mistake:** Going too deep too early. Break down the next 2 weeks in detail, future work in rough strokes.

---

### 2.4 Backlog

**What it is:**
An ordered list of all work items (user stories, tasks, bugs) that need to be done. The top items are refined and ready to work on. The bottom items are rough ideas.

**Purpose:**
Single source of truth for "what needs to be built." Prevents things from being forgotten. Provides a queue to pull from when you finish a task.

**Backlog item format (user story):**
```
As a [client user],
I want to [create an alert for a temperature threshold],
So that [I get notified when my equipment overheats].

Acceptance criteria:
- [ ] Can select a device and metric
- [ ] Can set condition (above/below) and threshold
- [ ] Can enter notification email
- [ ] Alert appears in alert list after creation
- [ ] Grafana alert rule is created
```

**When to use:** Always. Even solo projects. A text file, GitHub Issues, or a project board — the format doesn't matter. Having one does.

---

### 2.5 Sprint Planning / Iteration Planning

**What it is:**
Selecting a set of backlog items to commit to for a fixed time period (usually 1-2 weeks).

**Purpose:**
Creates focus. Instead of "I'm building the whole platform," you're saying "This week I'm shipping login and device list." It creates deadlines, which create momentum.

**For solo devs:**
You don't need a formal Scrum ceremony. Just write down 3-5 things you'll finish this week, every Monday. Review on Friday. Adjust.

**When to use:** Weekly or bi-weekly.

---

### 2.6 Definition of Done (DoD)

**What it is:**
A checklist that defines when a piece of work is truly finished — not just "code works on my machine."

**Purpose:**
Prevents half-done work from piling up. "It works" is not the same as "it's done."

**Example DoD:**
```
- [ ] Code is written and working
- [ ] Tests pass (unit + integration where applicable)
- [ ] No hardcoded secrets
- [ ] API endpoint documented in API-SPEC.md
- [ ] Tested manually via Swagger or frontend
- [ ] Code committed and pushed
```

**When to use:** Define once at project start. Apply to every task.

---

### 2.7 Decision Log (Architecture Decision Records — ADRs)

**What it is:**
A running log of every significant technical decision: what you decided, what alternatives you considered, and why you chose what you chose.

**Purpose:**
Future you will forget why you chose FastAPI over Django, or why you used tag-based InfluxDB isolation instead of bucket-per-org. The decision log preserves your reasoning so you (or future team members) don't re-debate settled questions.

**Format (lightweight ADR):**

```
## ADR-001: Use FastAPI for backend
- Date: 2026-04-12
- Status: Accepted
- Context: Need a Python web framework for the API layer.
- Options considered:
  - Django REST Framework: full-featured but heavy, comes with ORM opinions
  - Flask: lightweight but no async, no built-in validation
  - FastAPI: async, auto OpenAPI docs, Pydantic validation, modern
- Decision: FastAPI
- Rationale: Already using Python. Async matters for Grafana API calls.
  Auto-generated Swagger UI accelerates development.
- Consequences: Team must learn Pydantic and dependency injection pattern.
```

**When to use:** Every time you make a "this or that" technology/architecture choice. Takes 5 minutes to write. Saves hours of future debate.

---

## 3. Architecture & Design Artifacts

These artifacts define **how the system is structured** and **how components interact**.

---

### 3.1 Architecture Diagram (System Context / C4 Model)

**What it is:**
Visual representation of the system at different zoom levels. The C4 model defines 4 levels:

| Level | Shows | Audience |
|-------|-------|----------|
| **L1: System Context** | Your system as a box, surrounded by users and external systems | Everyone |
| **L2: Container** | The major runtime units (web app, database, message broker, etc.) | Developers, DevOps |
| **L3: Component** | Internal structure of each container (modules, services, controllers) | Developers |
| **L4: Code** | Class/function level detail | Developers (rarely needed) |

**Purpose:**
Shared understanding of how the system fits together. Without diagrams, everyone holds a different mental model. Diagrams align the team (even if the team is just you and your future self).

**When to use:** L1 and L2 for every project. L3 for complex services. L4 almost never.

---

### 3.2 Data Model / Entity Relationship Diagram (ERD)

**What it is:**
The schema of your persistent data: tables, columns, types, relationships, constraints.

**Purpose:**
The data model is the foundation of the entire application. Get this wrong and everything built on top is wrong. It deserves its own focused design.

**What to document:**
- Tables and their columns with types
- Primary keys, foreign keys, constraints
- Indexes (for performance-critical queries)
- Relationships (1:1, 1:N, N:M)
- Explanation of non-obvious fields

**When to use:** Before writing any application code. Review whenever requirements change.

---

### 3.3 API Specification

**What it is:**
The contract between frontend and backend (and any external consumers): every endpoint, its method, path, request format, response format, error codes, and auth requirements.

**Purpose:**
Frontend and backend can be developed in parallel once the API is agreed on. Without a spec, you'll constantly be surprised by what the API returns or expects. It also serves as documentation for future integrations.

**Formats:** OpenAPI/Swagger (generated by FastAPI), or a manual markdown spec.

**When to use:** Before building frontend. Updated as endpoints change.

---

### 3.4 Sequence Diagrams

**What it is:**
A diagram showing the order of interactions between components for a specific user action or flow.

**Purpose:**
Some flows involve many components (user creates alert → backend saves to DB → backend calls Grafana API → Grafana creates rule → Grafana sends email). A sequence diagram makes the flow explicit and reveals edge cases.

**When to use:** For complex multi-system flows. Not needed for simple CRUD.

---

### 3.5 Infrastructure Diagram / Deployment Architecture

**What it is:**
A diagram of how your system is deployed: what runs where, network topology, ingress/egress points, storage.

**Purpose:**
Code architecture and deployment architecture are different things. A service might be one codebase but deployed as three containers. This diagram shows the runtime reality.

**When to use:** Before any cloud/infrastructure work. Essential for Terraform planning.

---

## 4. Execution & Delivery Practices

Practices that keep the project moving during active development.

---

### 4.1 Version Control Strategy (Git Flow / Trunk-Based)

**What it is:**
The rules for how you use git: branching strategy, commit conventions, PR process, merge policy.

**Common strategies:**

| Strategy | Description | Best for |
|----------|-------------|----------|
| **Trunk-based** | Everyone commits to `main`. Short-lived feature branches (hours/days). | Small teams, fast iteration |
| **Git Flow** | `main`, `develop`, `feature/*`, `release/*`, `hotfix/*` branches | Large teams, formal releases |
| **GitHub Flow** | `main` + feature branches + PRs. Simple. | Most projects |

**For solo dev:** Trunk-based or GitHub Flow. Don't overcomplicate it.

**Commit message convention:**
```
feat: add alert creation endpoint
fix: correct Grafana embed URL construction
docs: add API spec for alert endpoints
chore: update docker-compose with postgres
refactor: extract GrafanaClient service
```

---

### 4.2 Continuous Integration (CI)

**What it is:**
Automated checks that run on every push/PR: linting, type checking, tests, build verification.

**Purpose:**
Catches bugs before they reach `main`. Enforces code quality standards automatically so you don't have to remember.

**Minimum CI pipeline:**
```
1. Lint (ruff, eslint)
2. Type check (mypy, tsc)
3. Unit tests (pytest, vitest)
4. Build (docker build, vite build)
```

**When to set up:** Sprint 0 or 1. The earlier CI exists, the more value it provides.

---

### 4.3 Continuous Deployment (CD)

**What it is:**
Automated deployment triggered by merge to `main` (or a release branch). Code goes from git push to running in production without manual steps.

**Purpose:**
Eliminates "it works on my machine" and manual deployment errors. Makes shipping fast and safe.

**When to set up:** After the first successful manual deployment to your target environment.

---

### 4.4 Environment Strategy

**What it is:**
The definition of which environments exist and what they're for.

**Typical setup:**

| Environment | Purpose | Deployed by | Data |
|-------------|---------|-------------|------|
| **Local** | Developer machine (docker-compose) | Manual | Fake/seed data |
| **Dev/Staging** | Integration testing, demos | CI/CD on merge to `main` | Test data |
| **Production** | Real users, real data | CI/CD on tag/release or manual approval | Real data |

**When to define:** Before first deployment. Start with local + one cloud environment.

---

## 5. Quality Practices

---

### 5.1 Testing Strategy

**What it is:**
A plan for what types of tests you'll write, at what ratio, and for which parts of the system.

**The Testing Pyramid:**

```
         /  E2E Tests  \        Few, slow, expensive
        /───────────────\
       / Integration Tests \    Some, medium speed
      /─────────────────────\
     /      Unit Tests       \  Many, fast, cheap
    /─────────────────────────\
```

**For this project:**
- **Unit tests:** Business logic (alert threshold evaluation, embed URL construction, auth token validation)
- **Integration tests:** API endpoints with test database, Grafana API client with mock
- **E2E tests:** (Later) Playwright/Cypress for critical user flows (login → view dashboard → create alert)

**When to define:** Sprint 1. Start writing tests from the first endpoint.

---

### 5.2 Code Review

**What it is:**
Having another person (or your future self, via PR) review code before it merges.

**For solo devs:** Create PRs even for yourself. The PR diff view often reveals things you miss in the editor. Review your own PR the next morning before merging.

---

### 5.3 Technical Debt Tracking

**What it is:**
A conscious list of shortcuts you've taken that need to be fixed later.

**Purpose:**
All projects accumulate shortcuts ("hardcode this for now," "skip validation here," "TODO: add error handling"). If you don't track them, they become invisible rot. If you do track them, they're manageable.

**Format:** A `TODO.md` file, GitHub issues tagged `tech-debt`, or `# TODO:` comments with corresponding issue numbers.

**Rule:** Every shortcut gets logged. Review the list monthly. Pay down the worst ones before they compound.

---

## 6. Operations & Post-Delivery Practices

---

### 6.1 Runbook

**What it is:**
Step-by-step instructions for common operational tasks: how to deploy, how to roll back, how to check logs, how to restart a service, how to onboard a new client.

**Purpose:**
Operational knowledge should not live only in your head. When you're on vacation, sick, or have hired someone, the runbook lets anyone operate the system.

**When to write:** After first deployment. Update as procedures change.

---

### 6.2 Monitoring & Alerting Strategy

**What it is:**
What you monitor (metrics, logs, health checks), where you monitor it (dashboards, alerting), and who gets notified when things break.

**The 4 Golden Signals (from Google SRE):**

| Signal | What it measures | Example metric |
|--------|-----------------|----------------|
| **Latency** | How long requests take | p95 response time |
| **Traffic** | How much demand exists | Requests per second |
| **Errors** | How often things fail | 5xx rate |
| **Saturation** | How full your resources are | CPU, memory, disk usage |

**When to set up:** During deployment sprint. Basic health checks from day one.

---

### 6.3 Incident Response Plan

**What it is:**
What to do when the system goes down: how to detect it, how to communicate it, how to fix it, how to prevent recurrence.

**For solo dev / small team:** Keep it simple:
1. Alert fires (from monitoring)
2. Check logs (`az containerapp logs show`)
3. Identify root cause
4. Fix or roll back
5. Write a brief post-mortem (what happened, why, what you changed to prevent recurrence)

---

### 6.4 Backup & Recovery Strategy

**What it is:**
How your data is backed up, how often, where backups are stored, and how to restore from them. Includes RTO (Recovery Time Objective — how long recovery takes) and RPO (Recovery Point Objective — how much data you can afford to lose).

**When to define:** Before going to production with real customer data.

---

## 7. People & Process Practices

---

### 7.1 RACI Matrix

**What it is:**
A table that defines who is **R**esponsible, **A**ccountable, **C**onsulted, and **I**nformed for each major area.

**Purpose:**
Even on a solo project, it clarifies which hat you're wearing. More importantly, it's ready for when you hire or bring on collaborators.

| Area | Responsible | Accountable | Consulted | Informed |
|------|------------|-------------|-----------|----------|
| Backend development | You | You | — | Client |
| Infrastructure | You | You | — | — |
| Client onboarding | You | You | Client | — |
| Alert configuration | Client | Client | You | — |

**When to use:** When team grows beyond 1 person. For solo projects, useful for client communication.

---

### 7.2 Retrospective

**What it is:**
A periodic review (end of sprint, end of phase) asking three questions:
1. What went well?
2. What didn't go well?
3. What will I change?

**Purpose:**
Continuous improvement. Without reflection, you repeat the same mistakes.

**For solo dev:** Spend 15 minutes every Friday writing 3 bullet points for each question. It compounds.

---

### 7.3 Communication Plan

**What it is:**
Who you communicate with, how often, through what channel, and about what.

**For solo dev with clients:**

| Audience | Channel | Frequency | Content |
|----------|---------|-----------|---------|
| Clients | Email | Bi-weekly | Progress update, demo screenshots |
| Yourself | Decision log | Per-decision | ADRs |
| Future hires | Docs | Ongoing | Architecture, runbook, README |

---

## 8. When to Use What

### By Project Phase

| Phase | Practices to Apply |
|-------|-------------------|
| **Idea / Kickoff** | Project Charter, Stakeholder Analysis, Requirements Gathering |
| **Analysis** | Current State Audit, Gap Analysis, Risk Assessment, Feasibility/PoC |
| **Planning** | Roadmap, WBS, Backlog, Definition of Done, Decision Log |
| **Design** | Architecture Diagrams, Data Model, API Spec, Sequence Diagrams |
| **Development** | Sprint Planning, CI, Version Control, Testing, Code Review, Tech Debt Tracking |
| **Deployment** | CD, Environment Strategy, Infrastructure Diagram, Runbook |
| **Operations** | Monitoring, Incident Response, Backup Strategy |
| **Ongoing** | Retrospectives, Risk Register updates, Decision Log updates |

### By Team Size

| Practice | Solo | 2-5 people | 6+ people |
|----------|------|-----------|-----------|
| Current State Audit | Do it | Do it | Do it |
| Gap Analysis | Do it | Do it | Do it |
| Risk Register | Do it | Do it | Do it |
| Project Charter | Lightweight | Do it | Formal |
| Stakeholder Analysis | Mental exercise | Lightweight | Formal |
| Decision Log | Do it | Do it | Do it (ADR format) |
| Roadmap | Do it | Do it | Do it |
| WBS | Optional | Do it | Do it |
| Backlog | Text file or issues | Project board | Full tool (Jira, Linear) |
| Sprint Planning | Weekly self-check | Weekly meeting | Formal ceremony |
| Code Review | Self-review PRs | Peer review required | Peer review + approval gates |
| CI/CD | Do it | Do it | Do it |
| Runbook | Do it | Do it | Do it |
| RACI | Skip | Do it | Do it |
| Retrospective | Personal journal | Team meeting | Facilitated session |

---

## Summary: The Minimum Viable Process

If you do nothing else, do these 7 things:

1. **Audit** what exists (Current State Audit)
2. **List** what's missing (Gap Analysis)
3. **Identify** what could go wrong (Risk Register)
4. **Decide** the order (Roadmap with phases)
5. **Record** your decisions (Decision Log)
6. **Define** when things are done (Definition of Done)
7. **Reflect** on what's working (Weekly retrospective)

Everything else is an amplifier on top of these fundamentals.

---

*This guide is methodology-agnostic. It applies whether you use Scrum, Kanban, Shape Up, or no formal methodology at all. The practices are tools — use the ones that help, skip the ones that don't, and revisit as your project and team evolve.*
