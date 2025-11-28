#!/usr/bin/env python3
"""
Database initialization script
Run this manually if needed: python init_db.py
"""
from app.core.database import init_db

if __name__ == "__main__":
    print("🚀 Initializing database...")
    try:
        init_db()
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
