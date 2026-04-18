# Email Notification Strategy — IoT Alert Delivery

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Context:** How alert notifications reach clients via email, how to scale email delivery, and which services to use

---

## Table of Contents

1. [How Grafana Sends Emails Natively](#1-how-grafana-sends-emails-natively)
2. [Why Native SMTP Is Not Enough](#2-why-native-smtp-is-not-enough)
3. [Email Service Comparison](#3-email-service-comparison)
4. [Architecture Patterns (Simple → Scale)](#4-architecture-patterns)
5. [Email Queuing](#5-email-queuing)
6. [Deliverability — SPF, DKIM, DMARC](#6-deliverability--spf-dkim-dmarc)
7. [Scaling Thresholds](#7-scaling-thresholds)
8. [Recommendation for IoTDash](#8-recommendation-for-iotdash)

---

## 1. How Grafana Sends Emails Natively

Grafana has a built-in SMTP client. Configure it in `grafana.ini` or via environment variables:

```ini
[smtp]
enabled = true
host = smtp.sendgrid.net:587
user = apikey
password = SG.xxxxx
from_address = alerts@yourdomain.com
from_name = IoTDash Alerts
startTLS_policy = MandatoryStartTLS
```

**Environment variable equivalent (for Docker/Container Apps):**
```bash
GF_SMTP_ENABLED=true
GF_SMTP_HOST=smtp.sendgrid.net:587
GF_SMTP_USER=apikey
GF_SMTP_PASSWORD=SG.xxxxx
GF_SMTP_FROM_ADDRESS=alerts@yourdomain.com
GF_SMTP_FROM_NAME=IoTDash Alerts
```

**How it works internally:**
1. Alert rule evaluates on its interval (e.g., every 1 minute)
2. State changes (Normal → Firing) trigger the notification pipeline
3. Notification policy routing tree is walked, matching contact point is found
4. For email contact points, Grafana opens an SMTP connection and sends **synchronously**
5. One TCP+TLS connection per email. No connection pooling. No internal queue.

---

## 2. Why Native SMTP Is Not Enough

| Limitation | Impact |
|-----------|--------|
| **No send queue** | Emails sent synchronously during alert evaluation. Slow SMTP = blocked evaluation loop. |
| **No retry logic** | Failed SMTP send is logged and dropped. Email is lost. |
| **No bounce handling** | Grafana has zero visibility into whether emails were delivered, bounced, or spam-filtered. |
| **No connection pooling** | Each notification opens a new TCP+TLS+AUTH connection. At 100+ emails/minute this hammers the SMTP server. |
| **Rate limiting is destructive** | Grafana's built-in `notification_rate_limit` throttles by **dropping** notifications, not by queuing them. |
| **Limited templates** | Go `text/template` only. No CSS inlining, limited HTML support. Cannot match your web app branding. |
| **No delivery tracking** | Cannot tell if email was opened, clicked, or bounced. |

**Practical ceiling:** Grafana's native SMTP handles **< 50 alert emails/minute** reliably. Beyond that, evaluation delays and dropped notifications occur.

---

## 3. Email Service Comparison

### 3.1 Pricing at a Glance

| Service | Free Tier | Cost per 100K emails/month | SMTP Relay | API |
|---------|-----------|---------------------------|------------|-----|
| **AWS SES** | 3,000/month (from EC2) | **$10** | Yes | Yes |
| **Azure Communication Services** | 1,000/month | **$25** | Yes (since 2024) | Yes |
| **SendGrid** | 100/day | **$89.95** (Pro plan) | Yes | Yes |
| **Mailgun** | 1,000/month (trial) | **$35** (Foundation) | Yes | Yes |
| **Postmark** | 100/month | **$110** | Yes | Yes |

### 3.2 Detailed Comparison

| Factor | SendGrid | AWS SES | Azure ACS |
|--------|----------|---------|-----------|
| **Easiest Grafana integration** | Best — SMTP relay, 5-min setup | Good — SMTP relay | Good — SMTP relay (since 2024) |
| **Cheapest at volume** | Expensive | **Cheapest** | Middle |
| **Deliverability tools** | **Best** — dashboard, analytics, dedicated IP | Good — Virtual Deliverability Manager | Basic |
| **Rate limits (default)** | Essentials: soft-throttled | Sandbox: 1/sec, 200/day. Production: 14/sec | 30/min, 100/hour (can request increase) |
| **Sandbox friction** | None — works immediately | **High** — must request production access (24-48h review) | Low |
| **Bounce/event handling** | **Best** — webhooks + UI for bounces, drops, spam | Good — SNS notifications | Basic — Event Grid webhooks |
| **Dedicated IP** | Available on Pro ($89.95/mo) | $24.95/mo per IP | Not available |
| **Azure-native** | No | No | **Yes** |
| **AWS-native** | No | **Yes** | No |

### 3.3 Cost at Scale

```
Monthly cost for sending alert emails:

                    1K/month   10K/month   100K/month   1M/month
                    ────────   ─────────   ──────────   ────────
AWS SES             $0.10      $1.00       $10          $100
Azure ACS           $0.25      $2.50       $25          $250
Mailgun             $35        $35         $35          $75
SendGrid            $19.95     $19.95      $89.95       $249
Postmark            $15        $15         $110         $600
```

---

## 4. Architecture Patterns

### Pattern A: Direct SMTP from Grafana (MVP)

```
Grafana Alerting ──SMTP──▶ Email Provider ──▶ Client Inbox
```

| Aspect | Detail |
|--------|--------|
| **Effort** | 15 minutes (configure env vars) |
| **Handles** | < 50 emails/minute |
| **Retry** | None |
| **Branding** | Limited (Go templates) |
| **Best for** | Dev, staging, <10 orgs, <100 alert rules |

**Setup for local dev** — add Mailhog to docker-compose:
```yaml
mailhog:
  image: mailhog/mailhog:latest
  container_name: mailhog
  ports:
    - "8025:8025"  # Web UI
    - "1025:1025"  # SMTP
  networks:
    - iot_net
```
Then set `GF_SMTP_HOST=mailhog:1025` on Grafana. All emails are captured in the Mailhog web UI at `localhost:8025`.

---

### Pattern B: Grafana Webhook → App Backend → Email API (Production)

```
Grafana Alerting                Your Backend               Email Provider
─────────────────              ─────────────               ──────────────
Alert fires
    │
    ▼
Contact Point:
  type = webhook
  url = http://backend:8000
       /api/internal/alerts/webhook
    │
    ▼
                              Receive webhook payload
                              │
                              ├─▶ De-duplicate (same alert in 5 min? skip)
                              ├─▶ Enrich (add device name, org name from DB)
                              ├─▶ Rate limit (per-recipient, per-alert-type)
                              ├─▶ Batch/digest (>10 alerts in 1 min? combine)
                              ├─▶ Render branded HTML template
                              ├─▶ Enqueue to email_queue table
                              │
                              ▼
                           Email Worker
                              │
                              ├─▶ Pick up from queue (SKIP LOCKED)
                              ├─▶ Send via provider API (SendGrid/SES/ACS)
                              ├─▶ Handle response:
                              │     200 → mark sent
                              │     429 → retry with backoff
                              │     5xx → retry (max 3)
                              │     bounce → add to suppression list
                              ▼
                                                          ──▶ Client Inbox
```

**Grafana webhook contact point config:**
```json
{
  "name": "iotdash-backend-webhook",
  "type": "webhook",
  "settings": {
    "url": "http://ca-webapp:8000/api/internal/alerts/webhook",
    "httpMethod": "POST",
    "authorization_scheme": "Bearer",
    "authorization_credentials": "${INTERNAL_WEBHOOK_SECRET}"
  }
}
```

**Grafana webhook payload (what your backend receives):**
```json
{
  "receiver": "iotdash-backend-webhook",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "High Temperature",
        "device_id": "sensor01",
        "metric": "temperature",
        "org": "acme",
        "severity": "warning"
      },
      "annotations": {
        "summary": "Temperature exceeded 30°C on sensor01",
        "description": "Current value: 32.5"
      },
      "startsAt": "2026-04-12T10:00:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "values": { "B": 32.5, "C": 1 },
      "fingerprint": "abc123"
    }
  ],
  "groupLabels": { "alertname": "High Temperature" },
  "commonLabels": { "device_id": "sensor01" },
  "externalURL": "https://grafana.iotdash.example.com"
}
```

**Backend webhook handler pseudocode:**
```python
@app.post("/api/internal/alerts/webhook")
async def handle_grafana_webhook(payload: GrafanaWebhookPayload):
    for alert in payload.alerts:
        device_id = alert.labels.get("device_id")
        org_name = alert.labels.get("org")

        # Look up alert config in our DB to get recipient email
        db_alert = await get_alert_by_grafana_fingerprint(alert.fingerprint)
        if not db_alert:
            continue

        # De-duplicate: skip if we sent for this alert in last 15 min
        if await was_recently_notified(db_alert.id, minutes=15):
            continue

        # Enrich with device/org details from DB
        device = await get_device(db_alert.device_id)
        org = await get_organisation(device.organisation_id)

        # Render branded email
        html = render_alert_email(
            alert_name=db_alert.metric,
            device_name=device.name,
            org_name=org.name,
            current_value=alert.values.get("B"),
            threshold=db_alert.threshold,
            condition=db_alert.condition,
            status=alert.status,  # "firing" or "resolved"
        )

        # Enqueue
        await enqueue_email(
            recipient=db_alert.notification_email,
            subject=f"[{alert.status.upper()}] {device.name}: {db_alert.metric} {db_alert.condition} {db_alert.threshold}",
            body_html=html,
            metadata={"alert_id": str(db_alert.id), "device_id": str(device.id)},
        )
```

| Aspect | Detail |
|--------|--------|
| **Effort** | 1-2 days |
| **Handles** | < 500 emails/minute |
| **Retry** | Yes (queue + worker) |
| **Branding** | Full control (HTML templates) |
| **Best for** | Production, 10-200 orgs, 100-2000 alert rules |

---

### Pattern C: Dedicated Notification Service (Enterprise)

```
┌─────────────┐                   ┌────────────────────────────────────┐
│  Grafana     │──webhook──────▶  │     Notification Service            │
│  (alerting)  │                  │                                    │
├─────────────┤                  │  ┌──────────┐   ┌──────────────┐  │
│  Backend     │──API──────────▶  │  │ Routing  │──▶│ Channel      │  │
│  (app alerts)│                  │  │ Engine   │   │ Workers      │  │
└─────────────┘                  │  └──────────┘   │ ┌────┐┌────┐ │  │
                                  │                  │ │Mail││Slck│ │  │
                                  │  ┌──────────┐   │ ├────┤├────┤ │  │
                                  │  │ User     │   │ │SMS ││Push│ │  │
                                  │  │ Prefs    │   │ └────┘└────┘ │  │
                                  │  └──────────┘   └──────────────┘  │
                                  │                                    │
                                  │  ┌────────────────────────────┐   │
                                  │  │ Queue (Redis / RabbitMQ)   │   │
                                  │  └────────────────────────────┘   │
                                  └────────────────────────────────────┘
```

**When to introduce:**
- Multiple notification channels (email + Slack + SMS + push notifications)
- Per-user notification preferences ("email for warnings, SMS for critical")
- Multiple alert sources (Grafana + app-generated alerts + cron jobs)
- Regulatory audit trail requirements
- > 500 alert emails/minute sustained

**Open-source options:** Novu, ntfy, Apprise

| Aspect | Detail |
|--------|--------|
| **Effort** | 1-2 weeks (or adopt open-source) |
| **Handles** | 10,000+ notifications/minute |
| **Best for** | 200+ orgs, multi-channel, enterprise clients |

---

## 5. Email Queuing

### 5.1 Why You Need a Queue

```
WITHOUT QUEUE:
  Alert fires → Send email synchronously → Hope it works
  ❌ Blocks request handler
  ❌ No retry on failure
  ❌ Email lost if provider is down
  ❌ No rate limiting

WITH QUEUE:
  Alert fires → Enqueue → Worker picks up → Send → Retry on failure
  ✅ Non-blocking
  ✅ Retryable (with exponential backoff)
  ✅ Rate-limit aware
  ✅ Auditable (every email tracked in DB)
```

### 5.2 PostgreSQL-Based Queue (Recommended for IoTDash)

You already have PostgreSQL. No need for Redis or RabbitMQ for email queuing at this scale.

```sql
CREATE TABLE email_queue (
    id            BIGSERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ DEFAULT now(),
    status        VARCHAR(20) DEFAULT 'pending',  -- pending, sending, sent, failed, dead
    retry_count   INTEGER DEFAULT 0,
    max_retries   INTEGER DEFAULT 3,
    next_retry_at TIMESTAMPTZ DEFAULT now(),
    recipient     VARCHAR(255) NOT NULL,
    subject       VARCHAR(500) NOT NULL,
    body_html     TEXT NOT NULL,
    body_text     TEXT,                            -- plain-text fallback
    metadata      JSONB DEFAULT '{}',              -- alert_id, device_id, org_id
    sent_at       TIMESTAMPTZ,
    error         TEXT,
    provider_id   VARCHAR(255)                     -- SendGrid message ID, for tracking
);

CREATE INDEX idx_email_queue_pending
  ON email_queue (next_retry_at)
  WHERE status = 'pending';
```

**Worker query (prevents double-processing with `SKIP LOCKED`):**
```sql
UPDATE email_queue
SET status = 'sending'
WHERE id IN (
    SELECT id FROM email_queue
    WHERE status = 'pending'
      AND next_retry_at <= now()
    ORDER BY created_at
    LIMIT 10
    FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

**Worker logic:**
```python
async def email_worker():
    """Runs as background task or separate process."""
    while True:
        batch = await pick_pending_emails(limit=10)
        if not batch:
            await asyncio.sleep(5)
            continue

        for email in batch:
            try:
                provider_id = await send_via_provider(email)
                await mark_sent(email.id, provider_id)
            except RateLimitError:
                await mark_retry(email.id, backoff_seconds=60)
            except ProviderError as e:
                if email.retry_count >= email.max_retries:
                    await mark_dead(email.id, str(e))
                else:
                    backoff = 30 * (2 ** email.retry_count)  # 30s, 60s, 120s
                    await mark_retry(email.id, backoff_seconds=backoff)
```

### 5.3 Notification Storm Protection

When many alerts fire at once (e.g., network outage causes all devices to go offline):

**Strategy 1: Grafana-level grouping**
```
# Notification policy settings
group_by: [org, severity]     # Batch alerts with same org + severity
group_wait: 30s                # Wait 30s before first notification (collect more)
group_interval: 5m             # Wait 5m before sending updates for same group
repeat_interval: 4h            # Don't re-send for 4 hours if still firing
```

This means: if 50 devices in Org "Acme" go offline within 30 seconds, Grafana sends **1 grouped webhook** to your backend (not 50 separate ones).

**Strategy 2: App-level digest**
```python
# In webhook handler:
# If >10 alerts in the same webhook payload, create a digest email
if len(payload.alerts) > 10:
    html = render_digest_email(
        org_name=org.name,
        alerts=payload.alerts,
        summary=f"{len(payload.alerts)} alerts firing"
    )
    # Send ONE email with all alerts summarized
else:
    # Send individual emails per alert
```

**Strategy 3: Per-recipient rate limiting**
```python
# Before enqueueing:
recent_count = await count_emails_to_recipient(
    recipient=email_address,
    since=datetime.utcnow() - timedelta(minutes=15)
)
if recent_count >= 5:
    # Skip or queue a digest instead
    log.warning(f"Rate limit: {email_address} received {recent_count} emails in 15 min")
    return
```

---

## 6. Deliverability — SPF, DKIM, DMARC

### 6.1 Why This Matters

Without proper email authentication, alert emails land in spam. Your clients miss critical alerts. Equipment overheats. Bad things happen.

### 6.2 Use a Subdomain

**Never send alert emails from your primary domain.**

```
Primary:  yourdomain.com        (business email — protect this)
Alerts:   alerts.yourdomain.com (alert notifications — isolated reputation)
```

If alert email reputation degrades (bounces, spam complaints), your business email is unaffected.

### 6.3 DNS Records to Configure

**SPF** — declares which servers can send email from your domain:
```
alerts.yourdomain.com.  IN  TXT  "v=spf1 include:sendgrid.net ~all"

# For AWS SES:
alerts.yourdomain.com.  IN  TXT  "v=spf1 include:amazonses.com ~all"

# For Azure ACS:
alerts.yourdomain.com.  IN  TXT  "v=spf1 include:spf.protection.outlook.com ~all"
```

**DKIM** — cryptographically signs emails (provider gives you CNAME records):
```
s1._domainkey.alerts.yourdomain.com.  CNAME  s1.domainkey.u12345.wl.sendgrid.net.
s2._domainkey.alerts.yourdomain.com.  CNAME  s2.domainkey.u12345.wl.sendgrid.net.
```

**DMARC** — tells receivers what to do with unauthenticated emails:
```
_dmarc.alerts.yourdomain.com.  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; pct=100"
```

Start with `p=none` (monitor mode), then move to `p=quarantine`, then `p=reject`.

### 6.4 List-Unsubscribe Header

Required by Gmail and Yahoo since February 2024, even for transactional emails:

```
List-Unsubscribe: <https://app.yourdomain.com/unsubscribe?token=xxx>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

For alert emails, "unsubscribe" can mean "disable this alert" — link to the alert management page in your web app.

### 6.5 Reputation Monitoring

| Metric | Target | If Violated |
|--------|--------|-------------|
| Bounce rate | < 2% | Verify email addresses before sending. Remove invalid. |
| Complaint rate | < 0.1% | Reduce volume. Add easy unsubscribe. Use digest mode. |
| Spam trap hits | 0 | Never send to unverified addresses. |

---

## 7. Scaling Thresholds

| Scale | Alert Rules | Emails/Month | Pattern | Email Service |
|-------|-------------|-------------|---------|---------------|
| **Dev/Test** | 1-20 | < 100 | A (Grafana SMTP → Mailhog) | Mailhog (local) |
| **Early Production** | 20-100 | 100-5,000 | A (Grafana SMTP → SendGrid) | SendGrid free (100/day) |
| **Growing** | 100-500 | 5,000-50,000 | B (Webhook → Queue → API) | SendGrid Essentials or AWS SES |
| **Scaling** | 500-2,000 | 50,000-200,000 | B (Webhook → Queue → API) | AWS SES ($20/mo) or Azure ACS ($50/mo) |
| **Large** | 2,000-5,000 | 200,000-1,000,000 | C (Notification Service) | AWS SES ($100/mo) |
| **Enterprise** | 5,000+ | 1,000,000+ | C (Multi-channel) | AWS SES + dedicated IP |

---

## 8. Recommendation for IoTDash

### Phase 1: MVP (Sprint 4)

```
Grafana ──SMTP──▶ SendGrid (free tier: 100 emails/day)
```

- Configure `GF_SMTP_*` environment variables
- Use Mailhog locally for testing
- Total cost: $0
- Time to implement: 15 minutes

### Phase 2: Production Readiness (Sprint 6-7)

```
Grafana ──webhook──▶ Backend ──queue──▶ Worker ──API──▶ SendGrid/SES
```

- Grafana uses webhook contact point (not SMTP)
- Backend receives webhook, enriches, de-duplicates, enqueues
- Worker sends via email API with retry and rate limiting
- Branded HTML email templates
- Total cost: $0-20/month
- Time to implement: 1-2 days

### Phase 3: Scale (When needed)

- Switch from SendGrid to AWS SES (if cost matters) or stay with SendGrid (if tooling matters)
- Add per-recipient rate limiting and digest mode
- Set up SPF, DKIM, DMARC on `alerts.yourdomain.com`
- Monitor deliverability metrics

### Decision: SendGrid vs AWS SES vs Azure ACS

| If... | Choose |
|-------|--------|
| Want fastest setup, best tooling, don't care about cost | **SendGrid** |
| Want cheapest at scale, already on AWS | **AWS SES** |
| Want Azure-native, moderate volume | **Azure Communication Services** |
| Want best deliverability for critical alerts | **SendGrid** (Pro with dedicated IP) or **Postmark** |

**For IoTDash on Azure:** Start with SendGrid (easiest Grafana integration, no sandbox). Switch to Azure Communication Services when you want Azure-native billing consolidation, or AWS SES if cost becomes a concern at volume.

---

*Companion documents: [`GRAFANA-ALERTING-STRATEGY.md`](./GRAFANA-ALERTING-STRATEGY.md), [`SCALING-STRATEGY.md`](./SCALING-STRATEGY.md)*
