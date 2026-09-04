"""
RecoverIQ — Single Entrypoint Runner Script
Runs the entire full-stack application (FastAPI backend + React frontend) on http://127.0.0.1:8000
"""

import sys
import time
import webbrowser
from threading import Timer
import uvicorn

from backend.config import settings
from backend.database import Base, SessionLocal, engine
from backend.models import Transaction, SimulationSummary
from backend.routers.transactions import seed_transactions
from backend.routers.simulation import run_batch_simulation


def prepare_database():
    """Ensure DB tables exist, synthetic data is seeded, and initial simulation is ready."""
    print("=" * 70)
    print(" RecoverIQ - Risk-Adjusted Revenue Recovery Copilot")
    print(" Razorpay AI Buildathon 2026 (Track 03)")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        tx_count = db.query(Transaction).count()
        if tx_count == 0:
            print("[*] Initializing synthetic dataset with 600 records (Seed 42)...")
            seed_transactions(db)
            print("[*] Running initial baseline & AI recovery simulation...")
            run_batch_simulation(db)
            print("[+] Database ready with 600 simulated records.")
        else:
            sim_count = db.query(SimulationSummary).count()
            if sim_count == 0:
                print("[*] Running batch simulation over existing records...")
                run_batch_simulation(db)
            print(f"[+] Loaded existing dataset with {tx_count} records.")
    finally:
        db.close()


def open_browser():
    time.sleep(1.2)
    url = f"http://{settings.HOST}:{settings.PORT}"
    print(f"[*] Opening browser at {url}...")
    webbrowser.open(url)


def main():
    prepare_database()

    # Automatically launch browser in 1.5 seconds
    Timer(1.5, open_browser).start()

    print(f"\n[+] Server starting on http://{settings.HOST}:{settings.PORT}")
    print(f"[+] Interactive Dashboard: http://{settings.HOST}:{settings.PORT}")
    print(f"[+] OpenAPI Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print("[*] Press Ctrl+C to stop the server.\n")

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
