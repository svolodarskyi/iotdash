# IoTDash — Predictive Maintenance: Does It Need ML?

> **Purpose:** Break down predictive maintenance into layers. Show what's classical, what needs ML, and the mechanics of each.

---

## 1. The 4 Levels of Maintenance

```
Level 0                Level 1               Level 2               Level 3
REACTIVE              PREVENTIVE            CONDITION-BASED       PREDICTIVE
────────────────────────────────────────────────────────────────────────────►
Fix when broken       Fix on schedule       Fix when degraded     Fix before failure

No data needed        No data needed        Sensor data           Sensor data +
                                            + thresholds          ML models

Cost: Highest         Cost: Medium          Cost: Lower           Cost: Lowest
(downtime)            (unnecessary work)    (targeted work)       (optimized timing)
```

**Most companies jump from Level 0 to Level 3 and fail.** The right path is 0 → 1 → 2 → 3. Level 2 (condition-based) is classical and captures 70-80% of the value.

---

## 2. Level 2 — Condition-Based Maintenance (Classical, No ML)

This is where your IoTDash platform lives today. It works with thresholds, trends, and basic statistics.

### 2.1 Static Threshold Monitoring

**Mechanic:**
```
Step 1: Define known failure thresholds from manufacturer specs
        - Motor bearing temperature: max 95C
        - Vibration amplitude: max 7.1 mm/s (ISO 10816)
        - Current draw: max 15A

Step 2: Set alert at warning level (80% of max)
        - Temperature alert at 76C
        - Vibration alert at 5.7 mm/s

Step 3: When alert fires → schedule maintenance

Result: You catch failures coming, but only when they're close.
```

**No ML. No training data. Works immediately.**

---

### 2.2 Trend / Degradation Tracking

**Mechanic:**
```
Step 1: Record metric over time
        Week 1: vibration = 2.1 mm/s
        Week 2: vibration = 2.3 mm/s
        Week 3: vibration = 2.6 mm/s
        Week 4: vibration = 3.0 mm/s

Step 2: Fit a simple trend line (linear regression)
        y = 0.3x + 1.8  (rising 0.3 mm/s per week)

Step 3: Extrapolate to failure threshold
        Failure at 7.1 mm/s
        (7.1 - 3.0) / 0.3 = ~14 weeks until failure

Step 4: Schedule maintenance within that window

This is LINEAR REGRESSION, not ML.
(Yes, linear regression is technically "machine learning" in textbooks,
but in practice it's basic statistics. You don't need an ML pipeline for this.)
```

**Implementation:** SQL window function + `REGR_SLOPE()`, or Python `numpy.polyfit(x, y, 1)`.

---

### 2.3 Baseline Deviation (SPC)

**Mechanic:**
```
Step 1: Establish baseline during healthy operation
        Vibration: μ = 2.0 mm/s, σ = 0.3 mm/s
        → Control limits: 1.1 to 2.9 mm/s

Step 2: Monitor for shift
        - Single point > 3σ → immediate attention
        - Gradual upward trend (8 consecutive points above mean) → degradation starting
        - Increasing σ (wider spread) → instability developing

Step 3: Western Electric Rules detect subtle shifts
        before the value hits a hard failure threshold
```

**No ML needed.** This is Statistical Process Control — industrial standard since the 1930s.

---

### 2.4 Operating Hour Counters

**Mechanic:**
```
Step 1: Track cumulative operating hours per device
        Motor #7: 4,200 hours since last bearing replacement

Step 2: Compare against known service intervals
        Bearing MTBF (Mean Time Between Failures): 8,000 hours

Step 3: At 80% of MTBF (6,400 hours) → schedule maintenance

Step 4: Adjust based on operating conditions:
        - Heavy load → reduce MTBF by 20%
        - Light load → extend MTBF by 10%
        - High temperature environment → reduce by 30%
```

**No ML.** Multiplication and a calendar.

---

## 3. Level 3 — Predictive Maintenance (Where ML Enters)

Level 3 goes beyond "is it degrading?" to "exactly when will it fail?" and "what will fail?"

### 3.1 Remaining Useful Life (RUL) Prediction

**What:** Estimate precisely how many hours/days until failure.

**Why classical fails:** Degradation isn't always linear. A bearing can degrade slowly for months, then rapidly in the last 2 weeks. Linear extrapolation misses this.

**How ML does it:**

```
Step 1: COLLECT FAILURE DATA (this is the hard part)
        You need examples of equipment going from healthy → failure.
        Minimum: 10-20 failure events for the same failure mode.
        Ideal: 50+ failure events with full sensor history.

        Data shape per failure event:
        [timestamp, temp, vibration, current, pressure, ...]
        from installation/last-repair through to failure moment.

Step 2: FEATURE ENGINEERING
        For each time window (e.g., every hour):
        - Rolling statistics: mean, std, min, max, skew, kurtosis
        - Frequency domain: FFT peak frequencies, energy bands
        - Cross-variable: temp × vibration, current/voltage ratio
        - Time features: hours since last maintenance, operating hours

Step 3: LABEL CREATION
        For each sample, label = time remaining until failure
        - 30 days before failure → label = 30
        - 5 days before failure → label = 5
        - At failure → label = 0

        Common approach: cap at maximum (e.g., 125 days)
        because "far from failure" all looks the same.

Step 4: TRAIN MODEL
        Options (increasing complexity):
        a) Random Forest / Gradient Boosting (XGBoost, LightGBM)
           - Input: feature vector from Step 2
           - Output: predicted RUL in days
           - Pros: fast, interpretable, works with small data
           - Cons: doesn't capture temporal patterns well

        b) LSTM (Long Short-Term Memory neural network)
           - Input: sequence of feature vectors (last 50 time steps)
           - Output: predicted RUL
           - Pros: captures temporal degradation patterns
           - Cons: needs more data, harder to train, black box

        c) Survival Analysis (Cox Proportional Hazards)
           - Input: current feature values + time
           - Output: probability of failure within next N days
           - Pros: statistically grounded, handles censored data
           - Cons: assumes proportional hazards

Step 5: DEPLOY
        - Run model on new data periodically (hourly/daily)
        - Output: "Motor #7 predicted to fail in 12 ± 3 days"
        - Alert when RUL drops below maintenance lead time
```

**The blocker:** You need failure data. If you've never had a failure, you can't train a failure predictor. This is why most companies start with Level 2 (condition-based) and collect data for 1-2 years before attempting Level 3.

---

### 3.2 Failure Mode Classification

**What:** Not just "something is wrong" but "the bearing is failing" vs "the belt is slipping" vs "the motor is overloaded."

**How ML does it:**
```
Step 1: Collect labeled failure examples
        Failure mode A (bearing): vibration spectrum has peak at 120Hz
        Failure mode B (belt slip): current spikes + speed drops
        Failure mode C (overload): sustained high current + high temp

Step 2: Extract features (same as RUL)

Step 3: Train multi-class classifier
        - Random Forest or XGBoost
        - Input: feature vector
        - Output: failure mode (A, B, C, or "healthy")

Step 4: In production:
        - Classify every N hours
        - If predicted failure mode != "healthy" → alert with diagnosis
        - "Motor #7: bearing failure likely (confidence 87%)"
```

**Why this needs ML:** Different failure modes have overlapping symptoms. Temperature rises in both overload AND bearing failure. ML learns the distinguishing patterns.

---

### 3.3 Anomaly Detection for Unknown Failures

**What:** Detect problems you've never seen before.

**How ML does it:**
```
Step 1: Train ONLY on healthy/normal data (no failure labels needed)
        Use autoencoder or Isolation Forest (see CLASSICAL-VS-ML-ANALYTICS.md)

Step 2: In production:
        - Feed new data through model
        - If reconstruction error high → "something unusual is happening"
        - You don't know WHAT — but you know something changed

Step 3: Human investigates, labels the anomaly
        Over time, build up a failure mode library (feeds into 3.2)
```

**Advantage:** Works without failure data. Good bridge between Level 2 and full Level 3.

---

## 4. Mechanics: Step-by-Step Implementation Path

### Phase 1 — Classical Condition Monitoring (Sprint 2, your current plan)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│ IoT Device  │────►│ EMQX/Telegraf│────►│ InfluxDB     │────►│ Grafana │
│ (sensors)   │     │ (ingest)     │     │ (store)      │     │ (alert) │
└─────────────┘     └──────────────┘     └──────────────┘     └────┬────┘
                                                                    │
                                                              Threshold
                                                              Rate-of-change
                                                              → Email alert
```

**What you build:**
- Static thresholds (Grafana alert rules)
- Rate-of-change alerts (Grafana `math` expression: `$B - $A`)
- Operating hour counters (InfluxDB `elapsed()` aggregation)
- Basic trend display (Grafana time-series panel with trend line)

**No new infrastructure needed.** Works with your current stack.

---

### Phase 2 — Statistical Condition Monitoring (Stage 2, 100-1K devices)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ IoT Device  │────►│ Ingest       │────►│ TimescaleDB  │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │ Cron Job     │
                                          │ (Python)     │
                                          │              │
                                          │ - Recalc μ,σ │
                                          │ - SPC checks │
                                          │ - Trend fit  │
                                          │ - RUL linear │
                                          └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │ Alert if     │
                                          │ degradation  │
                                          │ detected     │
                                          └──────────────┘
```

**What you build:**
- Scheduled Python job (cron or Celery beat, hourly/daily)
- Baseline calculation per device (μ, σ from last 30 days)
- SPC control chart monitoring (Western Electric rules)
- Linear trend extrapolation to failure threshold
- Dashboard showing predicted maintenance window

**New infrastructure:** One Python cron job. No ML framework.

---

### Phase 3 — ML-Based Prediction (Stage 3-4, 1K+ devices, 1+ years of data)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ IoT Device  │────►│ Ingest       │────►│ TimescaleDB  │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │ Feature      │
                                          │ Pipeline     │
                                          │ (scheduled)  │
                                          └──────┬───────┘
                                                 │
                    ┌────────────────┐     ┌──────▼───────┐
                    │ Model Registry │◄───►│ ML Service   │
                    │ (MLflow)       │     │ (FastAPI)    │
                    └────────────────┘     │              │
                                          │ - RUL pred   │
                                          │ - Anomaly    │
                                          │ - Classify   │
                                          └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │ Web App      │
                                          │ "Motor #7:   │
                                          │  14 days to  │
                                          │  failure"    │
                                          └──────────────┘
```

**What you build:**
- Feature extraction pipeline (Python, scheduled)
- Model training pipeline (Jupyter → script → scheduled retraining)
- Model serving (FastAPI endpoint or separate ML service)
- Model registry (MLflow, or simple versioned files)
- UI: predicted RUL display, maintenance scheduling

**New infrastructure:** ML framework (scikit-learn or PyTorch), MLflow, compute for training (can use Azure ML or just a VM).

---

## 5. Data Requirements by Approach

| Approach | Historical Data Needed | Failure Examples Needed | Compute |
|----------|:---:|:---:|:---:|
| Static thresholds | None (use manufacturer specs) | None | None |
| Rate-of-change | 1 hour | None | Negligible |
| SPC / Control Charts | 30 days | None | Negligible |
| Linear trend extrapolation | 30-90 days | None | Negligible |
| Isolation Forest anomaly | 30-60 days (healthy only) | None | Low |
| Autoencoder anomaly | 60-90 days (healthy only) | None | Medium |
| RUL with Random Forest | 6+ months | 10-20 failures | Medium |
| RUL with LSTM | 1+ year | 30-50 failures | High |
| Failure mode classification | 6+ months | 5+ per failure mode | Medium |

---

## 6. Answering the Question: Does Predictive Maintenance Need ML?

| What You Want to Do | ML Needed? | What to Use Instead |
|---------------------|:---:|---------|
| Alert when temperature too high | No | Static threshold |
| Alert when vibration increasing | No | Rate-of-change + trend |
| Detect when a metric drifts from normal | No | SPC control charts |
| Estimate weeks until failure (rough) | No | Linear trend extrapolation |
| Estimate days until failure (precise) | **Yes** | Random Forest / LSTM |
| Identify which component will fail | **Yes** | Multi-class classifier |
| Detect never-before-seen anomalies | **Yes** | Autoencoder / Isolation Forest |
| Schedule optimal maintenance timing | **Depends** | Classical if linear degradation, ML if non-linear |

**Bottom line:** Call it "predictive maintenance" and deliver 80% of the value with classical methods. Add ML when you have the data (1+ year) and customer demand.

---

## 7. What to Sell at Each Stage

| Stage | What You Offer | What Powers It | What You Call It |
|-------|---------------|---------------|-----------------|
| MVP | Threshold alerts + trend charts | Grafana + InfluxDB | "Real-time monitoring & alerting" |
| Growth | SPC alerts + degradation tracking + maintenance windows | Python cron + statistics | "Condition-based maintenance" |
| Scale | RUL predictions + anomaly detection | ML models | "Predictive maintenance" |
| Enterprise | Failure mode diagnosis + optimal scheduling | ML + optimization | "AI-powered predictive maintenance" |

Each stage builds on the last. Same data pipeline, progressively smarter analysis.

---

*Companion: [`CLASSICAL-VS-ML-ANALYTICS.md`](./CLASSICAL-VS-ML-ANALYTICS.md) — full catalog of classical vs ML analytics techniques.*
