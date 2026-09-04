"""
RecoverIQ - Synthetic Data Generator
Generates ~600 realistic failed-transaction records with fixed seed (42)
for reproducible simulation and benchmarking.

ALL DATA GENERATED IS SYNTHETIC DEMO DATA. NO REAL CUSTOMER OR FINANCIAL DATA.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

SEED = 42

GATEWAYS = ["Razorpay", "HDFC Bank", "ICICI Bank", "Axis Bank", "State Bank of India", "PayTM PG"]
SEGMENTS = ["new", "regular", "high_value"]
SEGMENT_WEIGHTS = [0.25, 0.55, 0.20]

DECLINE_TEMPLATES = {
    "INSUFFICIENT_FUNDS": [
        "Insufficient balance in customer account",
        "Declined: Account balance below required debit limit (51)",
        "Do not honor: Customer balance depleted",
        "Debit refused: Available limit exceeded",
        "05: Customer reported daily debit ceiling reached for current cycle",
    ],
    "CARD_EXPIRED": [
        "Card validity period expired",
        "Expired card details provided by customer (code 54)",
        "Card expired: please update credentials",
        "Transaction rejected: Expired plastic presented",
    ],
    "ISSUER_DECLINE": [
        "Issuer bank declined recurring debit instruction",
        "Decline: 05 - Do Not Honor",
        "Bank policy decline: standing instruction missing or revoked",
        "Mandate inactive: customer authentication required (3DS)",
        "Issuer core banking rejected debit: unspecified rule violation",
    ],
    "INVALID_CVV": [
        "Security code verification failed (CVV/CVC)",
        "Incorrect card verification value entered",
        "CVV mismatch on card validation attempt",
        "Card verification code invalid (code 82)",
    ],
    "NETWORK_TIMEOUT": [
        "Gateway connection timed out awaiting issuer response (91)",
        "Network communication error between acquirer and switch",
        "Timeout reading response from core banking host",
        "Switch ping failed after 45000ms: host unresponsive",
    ],
    "SUSPECTED_FRAUD": [
        "Transaction blocked by risk engine: velocity check failed",
        "Suspected fraudulent activity flagged by issuer fraud switch",
        "High risk score transaction intercepted by gateway",
        "Card flagged on central watchlist: immediate block",
    ],
    "PROCESSING_ERROR": [
        "Internal switch processor fault (code 96)",
        "Temporary database constraint error at issuer gateway",
        "Acquirer processing error - please re-attempt later",
        "System malfunction at card network switch",
    ],
}

DECLINE_CODES = list(DECLINE_TEMPLATES.keys())
DECLINE_WEIGHTS = [0.34, 0.16, 0.18, 0.08, 0.12, 0.04, 0.08]


def generate_synthetic_transactions(seed: int = SEED, count: int = 600) -> List[Dict[str, Any]]:
    """
    Generate deterministic synthetic failed transactions.
    Guarantees reproducible output across runs.
    """
    random.seed(seed)
    records: List[Dict[str, Any]] = []

    base_time = datetime(2026, 8, 15, 9, 0, 0)
    customer_pool = [f"cust_{i:04d}" for i in range(1, 180)]

    # 1. Seeded Edge Case 1: Fraud camouflage
    # Fraud flag is True, but decline message misleadingly looks like an insufficient funds error
    records.append({
        "transaction_id": "tx_edge_fraud_001",
        "customer_id": "cust_edge_9901",
        "customer_segment": "regular",
        "amount": 18500.0,
        "currency": "INR",
        "gateway": "Razorpay",
        "decline_code": "ISSUER_DECLINE",
        "decline_message": "Transaction cannot be processed: balance check failed (code 51)",
        "timestamp": (base_time + timedelta(hours=1, minutes=15)).isoformat(),
        "is_subscription": False,
        "previous_retry_count": 0,
        "fraud_flag": True,  # Critical edge case: Policy Gate must override!
        "is_synthetic": True,
        "edge_case_tag": "fraud_camouflage",
    })

    # 2. Seeded Edge Case 2: High-value customer with expired card but saved backup mandate
    records.append({
        "transaction_id": "tx_edge_exp_backup_002",
        "customer_id": "cust_edge_9902",
        "customer_segment": "high_value",
        "amount": 48000.0,
        "currency": "INR",
        "gateway": "HDFC Bank",
        "decline_code": "CARD_EXPIRED",
        "decline_message": "Primary card lapsed. Secondary mandate on UPI Autopay is linked in customer wallet.",
        "timestamp": (base_time + timedelta(hours=2, minutes=30)).isoformat(),
        "is_subscription": True,
        "previous_retry_count": 0,
        "fraud_flag": False,
        "is_synthetic": True,
        "edge_case_tag": "expired_card_backup_mandate",
    })

    # 3. Seeded Edge Case 3: Retry Storm customer with already maxed-out retries
    records.append({
        "transaction_id": "tx_edge_retry_storm_003",
        "customer_id": "cust_edge_9903",
        "customer_segment": "new",
        "amount": 2999.0,
        "currency": "INR",
        "gateway": "ICICI Bank",
        "decline_code": "INSUFFICIENT_FUNDS",
        "decline_message": "Insufficient balance in customer account",
        "timestamp": (base_time + timedelta(hours=3, minutes=10)).isoformat(),
        "is_subscription": True,
        "previous_retry_count": 3,  # Already at maximum retry limit!
        "fraud_flag": False,
        "is_synthetic": True,
        "edge_case_tag": "max_retries_reached",
    })

    # Generate remaining records
    remaining_count = count - len(records)

    for i in range(1, remaining_count + 1):
        tx_id = f"tx_syn_{i:05d}"
        cust_id = random.choice(customer_pool)
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]

        # Amount distribution based on segment
        if segment == "high_value":
            amount = round(random.uniform(12000.0, 75000.0), 2)
        elif segment == "regular":
            amount = round(random.uniform(1500.0, 18000.0), 2)
        else:
            amount = round(random.uniform(399.0, 6000.0), 2)

        gateway = random.choice(GATEWAYS)
        decline_code = random.choices(DECLINE_CODES, weights=DECLINE_WEIGHTS, k=1)[0]
        decline_message = random.choice(DECLINE_TEMPLATES[decline_code])

        # Rare fraud flag (approx 2% of non-explicit cases, or 100% if code is SUSPECTED_FRAUD)
        if decline_code == "SUSPECTED_FRAUD":
            fraud_flag = True
        else:
            fraud_flag = random.random() < 0.018

        # Retries: 0 (60%), 1 (25%), 2 (10%), 3 (5%)
        prev_retries = random.choices([0, 1, 2, 3], weights=[0.60, 0.25, 0.10, 0.05], k=1)[0]
        is_sub = random.random() < 0.65

        # Timestamp spread over 14 days
        random_minutes = random.randint(0, 14 * 24 * 60)
        tx_time = base_time + timedelta(minutes=random_minutes)

        records.append({
            "transaction_id": tx_id,
            "customer_id": cust_id,
            "customer_segment": segment,
            "amount": amount,
            "currency": "INR",
            "gateway": gateway,
            "decline_code": decline_code,
            "decline_message": decline_message,
            "timestamp": tx_time.isoformat(),
            "is_subscription": is_sub,
            "previous_retry_count": prev_retries,
            "fraud_flag": fraud_flag,
            "is_synthetic": True,
            "edge_case_tag": None,
        })

    return records


def save_dataset(output_path: Path = None, seed: int = SEED, count: int = 600) -> Path:
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "failed_transactions_600.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = generate_synthetic_transactions(seed=seed, count=count)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return output_path


if __name__ == "__main__":
    out = save_dataset()
    print(f"Generated {SEED} seed dataset at: {out}")
