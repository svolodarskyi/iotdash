# IoTDash — Classical vs ML Analytics

> **Purpose:** Which IoT analytics can be solved with classical methods, which genuinely need ML, and how each works mechanically.

---

## 1. The Spectrum: Rule-Based → Statistical → ML → Deep Learning

Not everything needs ML. Most IoT analytics in the early stages are **classical**. The progression:

```
Rule-Based         Statistical         Machine Learning       Deep Learning
(if/else)          (math formulas)     (learned patterns)     (neural networks)
───────────────────────────────────────────────────────────────────────────►
Simplest                                                         Most Complex
Most Explainable                                                 Least Explainable
No Training Data                                                 Lots of Training Data
```

**Rule of thumb:** Start classical. Move to ML only when classical fails or the value justifies the complexity.

---

## 2. What Can Be Done Classically (No ML Needed)

### 2.1 Static Threshold Alerting

**What:** Alert when a value crosses a fixed boundary.

**Example:** Temperature > 80C → alert.

**How it works:**
```
Step 1: Device sends reading          → { "temperature": 85.2 }
Step 2: Compare against threshold     → 85.2 > 80? YES
Step 3: Fire alert                    → Send email
```

**Implementation:** This is what Grafana alerting does. Simple `if` condition. No statistics, no ML.

**When it fails:** When "normal" varies. A freezer at 5C is fine, but 5C in a furnace is a failure. Static thresholds don't adapt.

---

### 2.2 Rate-of-Change Detection

**What:** Alert when a value changes too fast, regardless of absolute value.

**Example:** Temperature rising >5C/minute → alert (even if still within "safe" range).

**How it works:**
```
Step 1: Store last N readings         → [20.0, 20.5, 21.2, 22.8, 25.1]
Step 2: Calculate rate                → delta = (25.1 - 20.0) / 5min = 1.02 C/min
Step 3: Compare rate to threshold     → 1.02 > 0.5 C/min? YES
Step 4: Fire alert                    → "Rapid temperature rise detected"
```

**Implementation:** Simple subtraction and division. Flux/SQL can do this with `difference()` or window functions.

**No ML needed.** Pure arithmetic.

---

### 2.3 Moving Average Smoothing

**What:** Smooth noisy sensor data to see the real trend.

**Example:** Vibration sensor jitters ±10 units every second. Moving average reveals the actual trend.

**How it works:**
```
Step 1: Collect last N readings       → [45, 52, 48, 55, 43, 50, 47, 53]
Step 2: Calculate average             → sum / N = 49.125
Step 3: This is the "smoothed" value
Step 4: Slide window forward by 1, repeat

Types:
  - Simple Moving Average (SMA): equal weight for all N points
  - Exponential Moving Average (EMA): recent points weighted more heavily
  - Weighted Moving Average (WMA): custom weights
```

**Implementation:** InfluxDB `movingAverage()`, SQL `AVG() OVER (ROWS N PRECEDING)`, or 3 lines of Python.

**No ML needed.**

---

### 2.4 Dead-Band / Hysteresis Alerting

**What:** Prevent alert flapping when a value hovers near a threshold.

**Example:** Temperature oscillates between 79-81C. Without dead-band, you get alert-resolve-alert-resolve every minute.

**How it works:**
```
Step 1: Define two thresholds
        - Alert ON  threshold: 80C
        - Alert OFF threshold: 75C (lower, creates a "dead band")
Step 2: Current state = OK
Step 3: Reading = 81C → above ON threshold → state = ALERTING
Step 4: Reading = 79C → below ON but above OFF → state stays ALERTING (no flap)
Step 5: Reading = 74C → below OFF threshold → state = OK
```

**Implementation:** State machine with 2 thresholds. A few lines of code. Grafana supports this natively with `for` duration.

**No ML needed.**

---

### 2.5 Statistical Process Control (SPC)

**What:** Detect when a process goes out of its normal operating range using statistics.

**Example:** Motor vibration normally averages 50 ± 8 units. If it shifts to 65, something changed.

**How it works:**
```
Step 1: Collect baseline data (e.g., 30 days of normal operation)
Step 2: Calculate mean (μ) and standard deviation (σ)
        μ = 50, σ = 8
Step 3: Set control limits:
        UCL (Upper Control Limit) = μ + 3σ = 74
        LCL (Lower Control Limit) = μ - 3σ = 26
Step 4: For each new reading:
        - Within [26, 74] → in control
        - Outside → out of control → alert

Western Electric Rules (optional, more sensitive):
  - 1 point beyond 3σ → alert
  - 2 of 3 points beyond 2σ → alert
  - 4 of 5 points beyond 1σ → alert
  - 8 consecutive points on one side of mean → alert
```

**Implementation:** Calculate μ and σ from historical data (SQL/Flux), apply control limits. Can be recalculated periodically (weekly/monthly). A SQL query + a cron job.

**No ML needed.** This is 1920s statistics (Walter Shewhart). Still used in every factory today.

---

### 2.6 Anomaly Detection via Z-Score

**What:** Flag readings that are statistically unusual.

**Example:** A device usually reports every 30 seconds. One report comes after 5 minutes — anomaly.

**How it works:**
```
Step 1: Calculate mean and std dev of the metric (from history)
        μ = 30s, σ = 3s
Step 2: New reading interval = 300s
Step 3: Z-score = (300 - 30) / 3 = 90
Step 4: |Z| > 3? YES → anomaly
```

**Implementation:** One formula. SQL or Python one-liner.

**No ML needed.** But only works for single variables with roughly normal distribution. For multi-variable anomaly detection, you may need ML (see Section 3).

---

### 2.7 Duty Cycle / Uptime Tracking

**What:** Calculate how long a device has been running, idle, or offline.

**Example:** Compressor ran 18 out of 24 hours → 75% duty cycle.

**How it works:**
```
Step 1: Define states from data
        - "running" = current > 0.5A
        - "idle" = current ≤ 0.5A
        - "offline" = no data for > 2 minutes
Step 2: For each time window (1 hour, 1 day):
        Count time in each state
Step 3: Duty cycle = running_time / total_time × 100%
```

**Implementation:** Time-series aggregation query. InfluxDB `elapsed()` + `filter()`, or SQL window functions.

**No ML needed.**

---

### 2.8 Correlation Detection (Simple)

**What:** Check if two metrics move together.

**Example:** When ambient temperature rises, does motor temperature rise too? (Expected.) When ambient temperature rises, does vibration increase? (Unexpected — possible problem.)

**How it works:**
```
Step 1: Collect paired readings over time
        ambient: [20, 22, 25, 28, 30]
        motor:   [45, 48, 52, 55, 58]
Step 2: Calculate Pearson correlation coefficient (r)
        r = covariance(ambient, motor) / (σ_ambient × σ_motor)
        r = 0.99 → strong positive correlation
Step 3: If r > 0.8 → correlated. If r changes suddenly → investigate.
```

**Implementation:** `numpy.corrcoef()` or SQL with `CORR()` aggregate.

**No ML needed** for pairwise correlation. For finding unexpected correlations across many variables → ML helps.

---

### 2.9 Seasonality Detection

**What:** Identify repeating patterns (daily, weekly, seasonal).

**Example:** Office temperature peaks at 2PM daily, dips overnight. This is normal — don't alert on it.

**How it works:**
```
Step 1: Collect ≥2 full cycles of data (e.g., 2 weeks for weekly patterns)
Step 2: Decompose signal:
        observed = trend + seasonal + residual
Step 3: Methods:
        - Simple: average by hour-of-day / day-of-week
        - Classical decomposition (moving average to extract trend)
        - STL decomposition (Seasonal-Trend-Loess)
Step 4: Alert on the RESIDUAL (what's left after removing trend + season)
        not on the raw value
```

**Implementation:** Python `statsmodels.tsa.seasonal_decompose()` or manual averaging in SQL. STL is a statistical method from 1990 — not ML.

**Borderline classical.** Simple seasonality (fixed daily/weekly cycles) is fully classical. Complex multi-period seasonality may benefit from ML (e.g., Prophet, which is technically a statistical model marketed as ML).

---

## 3. What Genuinely Benefits from ML

### 3.1 Predictive Maintenance (see companion doc)

**What:** Predict equipment failure before it happens.

**Can it be done classically?** Partially. See `PREDICTIVE-MAINTENANCE.md` for a full breakdown.

**Short answer:**
- **Threshold-based maintenance** (classical) handles 60-70% of cases
- **Statistical degradation tracking** (classical) handles another 15-20%
- **True remaining-useful-life prediction** needs ML (the last 10-20%)

---

### 3.2 Multi-Variable Anomaly Detection

**What:** Detect anomalies when no single variable is abnormal, but the *combination* is unusual.

**Example:** Temperature = 65C (normal), pressure = 3 bar (normal), vibration = 40 (normal). But this specific combination of all three at once has never occurred → anomaly.

**Why classical fails:** Z-score works per variable. Checking every possible combination of N variables explodes combinatorially.

**How ML does it:**

```
Step 1: Collect training data — weeks/months of NORMAL operation
        Shape: [timestamp, temp, pressure, vibration, current, humidity, ...]

Step 2: Train an autoencoder (neural network)
        - Encoder compresses N variables → small latent representation
        - Decoder reconstructs N variables from latent representation
        - Trained to minimize reconstruction error on NORMAL data

Step 3: In production, for each new reading:
        - Feed through autoencoder
        - Calculate reconstruction error
        - If error > threshold → anomaly
        (The model can't reconstruct a pattern it's never seen)

Alternative approaches:
  - Isolation Forest (tree-based, no neural network, simpler)
  - One-Class SVM
  - DBSCAN clustering
```

**When you need it:** 5+ correlated variables, subtle interaction effects, no clear rules for what "abnormal combination" looks like.

**When you don't:** If you can write the rules ("if temp > 80 AND pressure < 2 → bad"), just write the rules.

---

### 3.3 Demand / Usage Forecasting

**What:** Predict future values of a metric.

**Example:** Predict tomorrow's energy consumption to optimize grid/HVAC scheduling.

**Why classical partially works:** Linear regression, ARIMA, exponential smoothing can forecast simple trends and seasonality.

**When ML helps:**

```
Classical (ARIMA/ETS):
  - Works for: single variable, clear seasonality, linear trend
  - Fails for: multiple external factors (weather, occupancy, holidays)

ML (Gradient Boosting / LSTM):
  Step 1: Collect features
          - Historical consumption (lag features: yesterday, last week, last year)
          - Time features (hour, day-of-week, month, holiday flag)
          - External features (weather forecast, occupancy schedule)
  Step 2: Train model on historical data
          - Input: features from Step 1
          - Output: next-hour / next-day consumption
  Step 3: In production:
          - Generate features for target time
          - Model predicts consumption
          - Compare to actual → adjust
```

**Threshold:** If the pattern is "consumption is higher on weekdays" → classical. If the pattern involves weather + occupancy + equipment state + season → ML.

---

### 3.4 Device Fingerprinting / Classification

**What:** Automatically identify what type of device is connected based on its data pattern.

**Example:** A new device connects and sends data. Is it a temperature sensor, a vibration sensor, or a power meter? Classify automatically.

**How ML does it:**
```
Step 1: Collect labeled examples
        - Device A (temperature): sends {temp: float} every 30s, range 15-85
        - Device B (vibration): sends {x, y, z: float} every 100ms, range 0-1000
        - Device C (power): sends {watts: float, voltage: float} every 1s

Step 2: Extract features from first N messages
        - Number of fields, data types, value ranges
        - Message frequency, payload size
        - Field name patterns

Step 3: Train classifier (Random Forest, simple neural net)

Step 4: New device connects → classify within first 10 messages
```

**Do you need this now?** No. You're manually registering devices. This is a "nice-to-have at 10K+ devices" feature.

---

### 3.5 Natural Language Alerting (LLM-based)

**What:** Let users describe alerts in plain English instead of configuring thresholds.

**Example:** User types "Alert me if the freezer is getting warmer than usual" → system creates the right alert rule.

**How it works:**
```
Step 1: User types natural language description
Step 2: LLM (GPT-4, Claude) interprets intent
        → device: freezer
        → metric: temperature
        → condition: above normal (need baseline, use SPC)
        → threshold: μ + 2σ from historical data
Step 3: System creates alert rule via Grafana API
Step 4: User confirms: "I'll alert you when freezer temp exceeds 2 standard
        deviations above its 30-day average (currently -18 ± 2C, so > -14C)"
```

**This is a product differentiator, not a necessity.** Cool feature for later stages.

---

## 4. Decision Matrix: Classical vs ML

| Use Case | Classical Enough? | ML Adds Value? | When to Upgrade |
|----------|:-:|:-:|---------|
| Static threshold alerts | Yes | No | Never — this is the right tool |
| Rate-of-change detection | Yes | No | Never |
| Moving averages / smoothing | Yes | No | Never |
| Hysteresis / dead-band | Yes | No | Never |
| Statistical Process Control | Yes | Marginal | If control limits drift frequently |
| Single-variable anomaly (Z-score) | Yes | No | Never for single variables |
| Duty cycle tracking | Yes | No | Never |
| Simple correlation | Yes | No | Never for known variable pairs |
| Seasonality removal | Yes | Marginal | If multiple overlapping seasons |
| **Multi-variable anomaly detection** | Partial | **Yes** | When >5 correlated variables matter |
| **Predictive maintenance (RUL)** | Partial | **Yes** | When degradation patterns are subtle |
| **Demand forecasting** | Partial | **Yes** | When external factors dominate |
| **Device classification** | No | **Yes** | At 10K+ devices with diverse types |
| **NLP-based alerting** | No | **Yes** | Product differentiator, any stage |

---

## 5. Implementation Complexity Comparison

| Approach | Training Data | Compute Cost | Expertise | Time to Implement |
|----------|:---:|:---:|:---:|:---:|
| Static threshold | None | Negligible | Junior dev | Hours |
| Rate-of-change | None | Negligible | Junior dev | Hours |
| SPC (control charts) | 30 days baseline | Negligible | Intermediate | 1-2 days |
| Z-score anomaly | 30 days baseline | Negligible | Intermediate | 1 day |
| Seasonality decomposition | 2+ full cycles | Low | Intermediate | 2-3 days |
| Isolation Forest | 30+ days labeled | Low | Data engineer | 1 week |
| Autoencoder anomaly | 60+ days clean | Medium | ML engineer | 2-3 weeks |
| LSTM forecasting | 6+ months history | Medium-High | ML engineer | 3-4 weeks |
| Predictive maintenance (full) | Failure examples | High | ML engineer | 1-2 months |

---

## 6. Recommended Progression for IoTDash

| Stage | Devices | Analytics Approach |
|-------|---------|-------------------|
| **MVP** (now) | 1-100 | Static thresholds, rate-of-change. All classical. |
| **Growth** (100-1K) | 100-1,000 | Add SPC, Z-score, seasonality removal. Still classical. |
| **Scale** (1K-10K) | 1,000-10,000 | Add Isolation Forest for multi-variable anomaly. First ML model. |
| **Enterprise** (10K+) | 10,000+ | Predictive maintenance, forecasting, autoencoder anomaly. Full ML pipeline. |

**For your current stage:** Everything you need is classical. Don't build ML infrastructure until you have the data and the customer demand.

---

*Companion: [`PREDICTIVE-MAINTENANCE.md`](./PREDICTIVE-MAINTENANCE.md) for a deep dive on predictive maintenance specifically.*
