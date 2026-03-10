"""
Script to set up Supabase database tables.
Run this after installing dependencies: pip install -r requirements.txt
Then run: python setup_database.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client

def setup_database():
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        return

    # Create client with service role key (for admin operations)
    supabase: Client = create_client(supabase_url, service_key)

    # Read SQL file
    with open("database.sql", "r") as f:
        sql = f.read()

    print("Note: Supabase SQL must be run manually in the SQL Editor.")
    print("=" * 60)
    print("Please follow these steps:")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project: eueojlhqdrcuzpkndwye")
    print("3. Click 'SQL Editor' in the left sidebar")
    print("4. Click 'New query'")
    print("5. Copy and paste the contents of database.sql")
    print("6. Click 'Run' or press Ctrl+Enter")
    print("=" * 60)

    # Try to verify connection
    try:
        response = supabase.table("profiles").select("count", count="exact").execute()
        print(f"\nConnection successful! Current profiles count: {response.count}")
    except Exception as e:
        print(f"Could not verify - tables may not exist yet: {e}")

if __name__ == "__main__":
    setup_database()
