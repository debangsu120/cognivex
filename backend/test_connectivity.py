#!/usr/bin/env python3
"""
Test script to verify AI service connectivity.
Run: python test_ai.py
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_groq():
    """Test Groq API connectivity."""
    from groq import AsyncGroq
    from app.config import settings

    print("Testing Groq API connectivity...")
    print(f"API Key configured: {'Yes' if settings.groq_api_key else 'No'}")
    print(f"API Key prefix: {settings.groq_api_key[:20] if settings.groq_api_key else 'None'}...")

    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY not configured!")
        return False

    try:
        client = AsyncGroq(api_key=settings.groq_api_key)

        # Simple test prompt
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "Say 'AI connectivity test successful' if you can read this."}
            ],
            max_tokens=50
        )

        if response.choices:
            print(f"\nSUCCESS! Groq API is working.")
            print(f"Response: {response.choices[0].message.content}")
            return True
        else:
            print("ERROR: No response from Groq API")
            return False

    except Exception as e:
        print(f"ERROR connecting to Groq API: {e}")
        return False

async def test_supabase():
    """Test Supabase connectivity."""
    from supabase import create_client

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    print("\nTesting Supabase connectivity...")
    print(f"URL configured: {'Yes' if supabase_url else 'No'}")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not configured!")
        return False

    try:
        supabase = create_client(supabase_url, service_key)

        # Try to query a table
        response = supabase.table("profiles").select("count", count="exact").execute()
        print(f"SUCCESS! Supabase is connected.")
        print(f"Profiles count: {response.count}")
        return True

    except Exception as e:
        print(f"ERROR connecting to Supabase: {e}")
        print("Note: Database tables may not exist yet.")
        return False

async def main():
    """Run all tests."""
    print("="*60)
    print("CogniVex Platform Connectivity Tests")
    print("="*60)

    # Test Groq
    groq_ok = await test_groq()

    # Test Supabase
    supabase_ok = await test_supabase()

    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    print(f"Groq AI:      {'PASS' if groq_ok else 'FAIL'}")
    print(f"Supabase DB:  {'PASS' if supabase_ok else 'FAIL'}")
    print("="*60)

    if not supabase_ok:
        print("\nTo fix Supabase connection:")
        print("1. Go to Supabase SQL Editor")
        print("2. Run the contents of database.sql")

if __name__ == "__main__":
    asyncio.run(main())
