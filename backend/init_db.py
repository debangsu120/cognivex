#!/usr/bin/env python3
"""
Script to initialize the Supabase database for CogniVex.
Run this script to create all required tables and set up RLS policies.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client

def setup_database():
    """Initialize the database with schema and policies."""

    # Get credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        print("\nTo set environment variables, run:")
        print("  Windows: set SUPABASE_URL=your_url && set SUPABASE_SERVICE_KEY=your_key")
        print("  Linux/Mac: export SUPABASE_URL=your_url && export SUPABASE_SERVICE_KEY=your_key")
        return False

    print(f"Connecting to Supabase: {supabase_url}")

    # Create client with service role key (for admin operations)
    supabase = create_client(supabase_url, service_key)

    # Read SQL file
    try:
        with open("database.sql", "r") as f:
            sql = f.read()
    except FileNotFoundError:
        print("Error: database.sql not found!")
        return False

    print("\n" + "="*60)
    print("IMPORTANT: Supabase SQL must be run manually in the SQL Editor.")
    print("="*60)
    print("\nPlease follow these steps:")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project: eueojlhqdrcuzpkndwye")
    print("3. Click 'SQL Editor' in the left sidebar")
    print("4. Click 'New query'")
    print("5. Copy and paste the contents of database.sql")
    print("6. Click 'Run' or press Ctrl+Enter")
    print("="*60)

    # Try to verify connection
    try:
        response = supabase.table("profiles").select("count", count="exact").execute()
        print(f"\nConnection successful! Current profiles count: {response.count}")
        print("Database tables already exist!")
        return True
    except Exception as e:
        print(f"\nCould not verify - tables may not exist yet: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
