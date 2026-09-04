# RecoverIQ — Development & Demo Notes

This document captures development findings, real-world failure modes encountered during building and testing, and how RecoverIQ solved them.

---

## 1. What Broke During Development & How It Was Fixed

### Issue 1: Windows Terminal UTF-8 Encoding Crash on Indian Rupee Symbol (`\u20b9`)
- **Symptom**: When executing batch benchmark verification scripts in Windows PowerShell, Python crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9' in position 16: character maps to <undefined>` under code page `cp1252`.
- **Root Cause**: The default standard output stream for Windows non-UTF8 terminals fails on multi-byte currency symbols when formatted in CLI logs.
- **Fix**: Updated CLI output formatting and logging scripts to use ASCII-safe currency designations (`INR`) for terminal logs while rendering formatted `₹` symbols natively in the React DOM.

### Issue 2: Pydantic V2 Deprecation Warnings on Model Configuration
- **Symptom**: Running `pytest tests/` generated `PydanticDeprecatedSince20` warnings regarding `class Config: from_attributes = True`.
- **Root Cause**: Pydantic V2 replaced nested `Config` classes with `model_config = ConfigDict(from_attributes=True)` or dictionary definitions.
- **Fix**: Modernized all API schemas in `backend/schemas.py` to use `model_config = {"from_attributes": True}`.

### Issue 3: Python 3.13 Timezone UTC Deprecation Warnings
- **Symptom**: `datetime.utcnow()` triggered deprecation warnings in test suites under Python 3.13.
- **Root Cause**: `utcnow()` is deprecated in Python 3.12+ in favor of timezone-aware UTC timestamps.
- **Fix**: Replaced all occurrences with `datetime.now(timezone.utc)` across `models.py`, `transactions.py`, and `simulation.py`.

### Issue 4: Vite TypeScript Strict Type Import Requirements (`verbatimModuleSyntax`)
- **Symptom**: Frontend build failed with `TS1484: ... is a type and must be imported using a type-only import`.
- **Root Cause**: Vite's default TypeScript config enabled `verbatimModuleSyntax: true` and `erasableSyntaxOnly: true`, which rejected type imports combined with value imports.
- **Fix**: Standardized `frontend/tsconfig.app.json` and converted all TypeScript type imports to explicit `import type { ... }` syntax.

---

## 2. Deep Dive: The 2 Seeded Tricky Edge Cases

### Edge Case 1: Fraud Camouflaged as Insufficient Funds
- **Transaction ID**: `tx_edge_fraud_001`
- **Customer ID**: `cust_edge_9901` (Regular Customer)
- **Amount**: ₹18,500.00
- **Gateway**: Razorpay
- **Decline Code**: `ISSUER_DECLINE`
- **Decline Message**: `"Transaction cannot be processed: balance check failed (code 51)"`
- **Underlying Risk Signal**: `fraud_flag = True` (flagged on card network risk switch)
- **The Problem / Potential Failure**:
  - The decline message misleadingly reads like an insufficient funds error ("balance check failed").
  - An unconstrained or naive LLM prompt might classify this as an account balance shortfall and propose `retry_scheduled` in 24 hours to recover ₹18,500.
  - In legacy systems, a blind retry would hit the network again, generating a cardholder dispute, chargeback penalty fee, and merchant risk warning from the card network.
- **How RecoverIQ Handled It**:
  1. **Step 1 (Classifier)** reads the message and identifies the balance-like text.
  2. **Step 2 (Scorer)** checks the fraud flag and hard-clamps recoverability score to `0.0`.
  3. **Step 3 (Strategy Generator)** generates a playbook proposal.
  4. **Step 4 (Policy Gate)** evaluates the proposal against `RULE_FRAUD_ZERO_TOLERANCE`. The rule fires unconditionally:
     - Proposed retry action is immediately **overridden** to `escalate_human`.
     - `max_retries` is strictly clamped to `0`.
     - Notification channel is set to `none`.
     - An audit entry is persisted with the reason: *"Security Policy Violation: Transaction is flagged for suspected fraud. Automated retries strictly prohibited."*
  5. **Step 5 (Simulator)** skips retries entirely (`simulated_outcome_ai: SKIPPED`), while the Naive Baseline retries 3 times and fails (`simulated_outcome_baseline: FAILED`).
  6. **Result**: 3 false retries avoided, 0 chargeback penalties incurred.

---

### Edge Case 2: High-Value Customer with Expired Card & Linked Backup Mandate
- **Transaction ID**: `tx_edge_exp_backup_002`
- **Customer ID**: `cust_edge_9902` (High-Value Tier)
- **Amount**: ₹48,000.00
- **Gateway**: HDFC Bank
- **Decline Code**: `CARD_EXPIRED`
- **Decline Message**: `"Primary card lapsed. Secondary mandate on UPI Autopay is linked in customer wallet."`
- **Previous Retries**: 0
- **Subscription**: True (Annual SaaS billing)
- **The Problem / Potential Failure**:
  - The customer's primary credit card expired at the end of the month.
  - A naive retry engine will blindly execute 3 retries against the expired plastic. Every retry is guaranteed to fail (`p=0%`), annoying the high-value client and eventually churning an annual subscription worth ₹48,000.
- **How RecoverIQ Handled It**:
  1. **Step 1 (Classifier)** recognizes the primary card expired.
  2. **Step 2 (Scorer)** notes that the customer is high-value with an active recurring subscription, boosting baseline recoverability from 0.35 to 0.60.
  3. **Step 3 (Strategy Generator)** identifies the linked backup mandate from the context and proposes:
     - `action: notify_customer`
     - `channel: whatsapp`
     - `retry_delay_hours: 0`
     - `max_retries: 0`
     - Rationale: *"Primary card expired but customer has linked UPI Autopay. Trigger WhatsApp 1-click fallback notification to switch mandate without blind gateway retries."*
  4. **Step 4 (Policy Gate)** verifies the playbook. Because `action == notify_customer` and `max_retries == 0`, no retry limits are violated. The verdict is `PASSED`.
  5. **Step 5 (Simulator)** simulates the customer response. With 1-click WhatsApp fallback, the customer authorizes the switch with a 92% conversion rate.
  6. **Outcome**: Recovered ₹48,000.00 with 0 blind retries, while the baseline burned 3 useless retries and lost the customer.

---

## 3. Seeded Edge Case 3: Retry Storm Prevention on Maxed-Out Card
- **Transaction ID**: `tx_edge_retry_storm_003`
- **Customer ID**: `cust_edge_9903`
- **Previous Retries**: 3 (Already at hard lifetime cap)
- **Decline Code**: `INSUFFICIENT_FUNDS`
- **Policy Gate Verdict**: `OVERRIDDEN` via `RULE_MAX_RETRIES_CAP_EXCEEDED`.
- **Enforcement**: Any further attempt to retry is blocked, stopping infinite loop retry storms that cause customer fatigue and gateway rate limits.
