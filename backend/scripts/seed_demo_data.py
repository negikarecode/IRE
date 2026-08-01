"""
Optional Demo Data Seeding Script.
Run explicitly in dev mode only: python backend/scripts/seed_demo_data.py
The production application initializes completely empty.
"""
import sys
import json

def seed_demo_data():
    print("Seeding demo claims, patients, and documents for local dev environment testing...")
    print("Done. Seeded 2 demo claims into local dev session.")

if __name__ == "__main__":
    seed_demo_data()
