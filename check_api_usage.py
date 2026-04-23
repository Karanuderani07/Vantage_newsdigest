#!/usr/bin/env python3
"""
Check API usage for Groq and NewsAPI.
Run: python check_api_usage.py
"""

import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

print("=" * 60)
print("API USAGE STATUS CHECK")
print("=" * 60)
print(f"Current Time (UTC): {datetime.utcnow().isoformat()}")
print()

# ── Groq API ─────────────────────────────────────────────────

print("📊 GROQ API (LLM)")
print("-" * 60)
if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not found in .env")
else:
    print(f"✅ Key found: {GROQ_API_KEY[:10]}...")
    print()
    print("💡 Groq Free Tier Limits:")
    print("   • Rate Limit: 30 requests/minute")
    print("   • Daily Limit: ~10,000 tokens/day (varies)")
    print("   • Status: Check https://console.groq.com/admin/billing/overview")
    print()
    print("🔗 Dashboard: https://console.groq.com/")
    print()

# ── NewsAPI ──────────────────────────────────────────────────

print()
print("📰 NEWSAPI")
print("-" * 60)
if not NEWS_API_KEY:
    print("❌ NEWS_API_KEY not found in .env")
else:
    print(f"✅ Key found: {NEWS_API_KEY[:10]}...")
    print()
    
    # Test with a simple request to see if key works
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "test",
        "pageSize": 1,
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }
    
    try:
        print("Testing NewsAPI key...")
        r = requests.get(url, params=params, timeout=5)
        
        if r.status_code == 200:
            print("✅ Key is VALID and working")
        elif r.status_code == 401:
            print("❌ Key is INVALID or EXPIRED")
        elif r.status_code == 429:
            print("⚠️  Rate limit hit - Daily quota exhausted")
        else:
            print(f"⚠️  Status {r.status_code}: {r.text[:100]}")
            
    except Exception as e:
        print(f"❌ Network error: {e}")
    
    print()
    print("📊 NewsAPI Free Tier Limits:")
    print("   • Requests/Day: 100")
    print("   • Requests/Minute: 10")
    print("   • Per Search: 4 queries × articles")
    print("   • Estimated Briefings/Day: ~25")
    print()
    print("🔗 Dashboard: https://newsapi.org/account")
    print()

# ── Usage Estimate ───────────────────────────────────────────

print()
print("📈 USAGE ESTIMATES")
print("-" * 60)
print()
print("Per Briefing:")
print("  • NewsAPI calls: 4 queries")
print("  • Groq tokens: ~2,400 tokens (optimized)")
print()
print("Daily Limits:")
print("  • NewsAPI: 100 requests ÷ 4 = 25 briefings max")
print("  • Groq: ~10,000 tokens ÷ 2,400 = ~4 briefings max")
print()
print("⚠️  BOTTLENECK: Groq is more limiting!")
print()
print("💡 Optimization Tips:")
print("  1. Reuse searches (caching helps)")
print("  2. Consider Groq paid tier for more tokens")
print("  3. Monitor token usage in app logs")
print()

print("=" * 60)
print()
