#!/usr/bin/env python3
"""
Quick diagnostic to test NewsAPI key directly.
Run: python test_newsapi_key.py
"""

import requests
from dotenv import load_dotenv
import os

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    print("❌ ERROR: NEWS_API_KEY not found in .env")
    exit(1)

print(f"Testing NewsAPI with key: {NEWS_API_KEY[:10]}...")
print()

# Test 1: Simple query
url = "https://newsapi.org/v2/everything"
params = {
    "q": "artificial intelligence",
    "pageSize": 5,
    "language": "en",
    "apiKey": NEWS_API_KEY,
}

print("📡 Making request to NewsAPI...")
try:
    r = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {r.status_code}")
    print()
    
    if r.status_code == 200:
        data = r.json()
        if data.get("status") == "ok":
            articles = data.get("articles", [])
            print(f"✅ SUCCESS! Got {len(articles)} articles")
            if articles:
                print(f"   First article: {articles[0]['title'][:60]}...")
        else:
            print(f"⚠️  API returned error: {data.get('message')}")
    elif r.status_code == 429:
        print("⚠️  429 Rate Limit Error")
        print(f"Response: {r.text[:200]}")
    elif r.status_code == 401:
        print("❌ 401 Unauthorized - Check your API key")
        print(f"Response: {r.text[:200]}")
    else:
        print(f"❌ Error {r.status_code}: {r.text[:200]}")
        
except Exception as e:
    print(f"❌ Network error: {e}")

print()
print("💡 Next steps:")
print("  - If ✅ SUCCESS: The key works! Restart the app.")
print("  - If ⚠️  429: Your key hit the daily limit. Check https://newsapi.org/account")
print("  - If ❌ 401: Invalid API key. Check NEWS_API_KEY in .env")
