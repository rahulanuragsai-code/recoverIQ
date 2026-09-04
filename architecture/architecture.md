# RecoverIQ System Architecture

## Overview
RecoverIQ is a risk-adjusted payment recovery copilot designed for merchants handling recurring subscriptions and high-value invoices. Unlike legacy payment retry engines that execute fixed, unstratified retries (e.g., retrying 3 times over 3 days regardless of decline root causes), RecoverIQ diagnoses failure causes, models recoverability mathematically, formulates contextual playbooks, and passes all proposed actions through a deterministic Policy Gate.

![RecoverIQ Architecture](./architecture.png)

---

## High-Level System Architecture Diagram

```mermaid
flowchart TD
    classDef input fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef pipeline fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef safety fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#f8fafc;
    classDef store fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef serve fill:#1e293b,stroke:#94a3b8,stroke-width:2px,color:#f8fafc;
    classDef ui fill:#022c22,stroke:#10b981,stroke-width:2px,color:#f8fafc;

    subgraph INGESTION["1. Ingestion Layer"]
        RAW["Payment Decline Events<br/>(Synthetic 600 Records, Seed 42)<br/>Razorpay, HDFC, ICICI, Axis, SBI"]:::input
        EDGE["Seeded Tricky Edge Cases<br/>1. Fraud Camouflaged as Insufficient Funds<br/>2. Expired Card with Saved UPI Mandate"]:::input
        RAW --> EDGE
    end

    subgraph PIPELINE["2. Central 5-Step AI Recovery Pipeline"]
        S1["Step 1: Classifier<br/>Deterministic regex + LLM semantic parser<br/>Maps decline code to root cause"]:::pipeline
        S2["Step 2: Scorer<br/>Deterministic mathematical engine<br/>Produces 0.0-1.0 score + factor breakdown"]:::pipeline
        S3["Step 3: Strategy Generator (LLM)<br/>Agentic step proposing JSON recovery playbook<br/>{action, channel, delay_hours, max_retries}"]:::pipeline
        S4{"Step 4: Deterministic Policy Gate<br/>HARD-CODED CIRCUIT BREAKER<br/>- Fraud Zero-Tolerance<br/>- 12h Cooldown Rule<br/>- Max 3 Retries Cap<br/>- Daily Velocity Limit"}:::safety
        S5["Step 5: Simulator & Baseline Comparator<br/>Monte Carlo simulation (Seed 42)<br/>RecoverIQ vs Naive 3x Retry Baseline"]:::pipeline

        S1 --> S2 --> S3 --> S4
        S4 -->|Validated or Overridden| S5
    end

    subgraph PERSISTENCE["3. Persistence & Audit Layer"]
        DB[("SQLite Database (WAL Mode)<br/>- transactions<br/>- simulation_summaries")]:::store
        AUDIT[("Immutable Audit Log Table<br/>- LLM Proposal vs Final Action<br/>- Fired Policy Rules & Reasons")]:::store
    end

    subgraph SERVING["4. Serving Layer"]
        API["FastAPI REST Backend (Port 8000)<br/>- /api/transactions<br/>- /api/simulate/batch<br/>- /api/metrics<br/>- /api/audit-log"]:::serve
    end

    subgraph DASHBOARD["5. User Presentation Layer"]
        REACT["React 18 + Vite + Tailwind Dashboard<br/>- Overview KPIs (Uplift, Avoided Retries)<br/>- Transaction Explorer (5-Step Trace Drawer)<br/>- Policy Audit Trail (Governance Diffs)"]:::ui
    end

    INGESTION --> S1
    S4 -.->|Persist Policy Interception| AUDIT
    S5 -->|Store Simulation Outcome| DB
    DB --> API
    AUDIT --> API
    API --> REACT
```

---

## Component Breakdown

### 1. Ingestion & Synthetic Data Layer
- **Seed 42 Determinism**: Generates 600 synthetic payment failure transactions representing realistic customer tiers (`high_value`, `regular`, `new`) across major Indian banking gateways (`Razorpay`, `HDFC Bank`, `ICICI Bank`, `Axis Bank`, `State Bank of India`).
- **Seeded Edge Cases**:
  - `tx_edge_fraud_001`: Camouflaged fraud mimicking insufficient funds.
  - `tx_edge_exp_backup_002`: High-value expired card with secondary UPI Autopay mandate.
  - `tx_edge_retry_storm_003`: Card with 3 previous failed attempts hitting lifetime cap.

### 2. The 5-Step AI Pipeline
1. **Root Cause Classifier (`ai/classifier.py`)**: Deterministic regex/code fast-path for unambiguous codes; delegates messy gateway messages to LLM classifier (`INSUFFICIENT_FUNDS`, `CARD_EXPIRED`, `ISSUER_DECLINE`, `INVALID_CVV`, `NETWORK_TIMEOUT`, `SUSPECTED_FRAUD`, `PROCESSING_ERROR`).
2. **Recoverability Scorer (`ai/scorer.py`)**: Transparent formula calculating recoverability probability (`[0.0, 1.0]`) from root cause baseline weights, customer segment modifiers, retry fatigue penalties, and recurring subscription affinity.
3. **Strategy Generator (`ai/strategy_generator.py`)**: Agentic LLM synthesizes transaction context and suggests actionable playbook (`action`, `channel`, `retry_delay_hours`, `max_retries`, `rationale`).
4. **Deterministic Policy Gate (`ai/policy_gate.py`)**: Hard-coded Python layer with zero tolerance on fraud, 12h cooldown, max 3 cumulative retries, and customer daily velocity limits.
5. **Simulator & Baseline Comparator (`ai/simulator.py`)**: Monte Carlo simulation evaluating AI strategy against naive 3x blind retry baseline on the identical dataset.

### 3. Safety & Governance (Policy Gate)
The Policy Gate acts as an impenetrable circuit breaker. The LLM is **never** granted direct execution authority. If an LLM hallucinates an immediate retry on a fraud record or an exhausted card, the Policy Gate intercepts the request, clamps retries to 0, logs the violation to the immutable audit trail, and escalates to human risk ops.
