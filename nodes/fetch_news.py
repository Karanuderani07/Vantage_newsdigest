"""
nodes/fetch_news.py — Node 1
Planner + Fetcher combined:
  1. LLM breaks the topic into 4 targeted search queries.
  2. NewsAPI fetches up to 6 articles per query.
  3. Deduplication so we don't pass redundant articles downstream.
"""

import json
import time
import requests
from datetime import datetime
from state import AgentState
from utils import llm, log_print, stamp


NEWS_API_URL = "https://newsapi.org/v2/everything"


# ── helpers ──────────────────────────────────────────────────

def _plan_queries(topic: str) -> list[str]:
    """Ask the LLM for 4 search angles on the topic."""
    system = (
        "You are a senior news research strategist. "
        "Given a topic, produce exactly 4 short search queries. "
        "IMPORTANT: Keep queries broad enough to find results in general news outlets. "
        "Avoid overly academic or specific technical jargon unless essential. "
        "Coverage: policy, economy, tech advancements, and social impact. "
        "Return ONLY valid JSON:\n"
        '{"queries": ["q1", "q2", "q3", "q4"]}'
    )
    raw = llm(system, f"Topic: {topic}", json_mode=True)
    queries = json.loads(raw).get("queries", [topic])[:4]
    return queries


def _fetch_for_query(query: str, api_key: str, page_size: int = 8, max_retries: int = 3) -> list[dict]:
    """Call NewsAPI for a single query with exponential backoff retry logic."""
    params = {
        "q":            query,
        "sortBy":       "relevancy",
        "pageSize":     page_size,
        "language":     "en",
        "apiKey":       api_key,
    }
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for attempt in range(max_retries):
        try:
            r = requests.get(NEWS_API_URL, params=params, headers=headers, timeout=10)
            
            # Handle 429 (rate limit) with exponential backoff
            if r.status_code == 429:
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt  # 1s, 2s, 4s
                    log_print(f"⚠  Rate limit hit. Backing off {backoff}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(backoff)
                    continue
                else:
                    log_print(f"⚠  Rate limit hit after {max_retries} retries. Skipping '{query}'")
                    return []
            
            # Check for other errors
            if r.status_code != 200:
                log_print(f"⚠  NewsAPI error (HTTP {r.status_code}): {r.text[:200]}")
                return []
            
            r.raise_for_status()
            data = r.json()
            
            if data.get("status") == "ok":
                articles = [
                    {
                        "title":       a.get("title", "").strip(),
                        "description": (a.get("description") or "").strip(),
                        "content":     (a.get("content") or "")[:600].strip(),
                        "source":      a.get("source", {}).get("name", "Unknown"),
                        "url":         a.get("url", ""),
                        "published":   a.get("publishedAt", ""),
                    }
                    for a in data.get("articles", [])
                    if a.get("title") and "[Removed]" not in a.get("title", "")
                ]
                return articles
            else:
                log_print(f"⚠  NewsAPI error: {data.get('message', 'unknown')}")
                return []
                
        except requests.RequestException as e:
            log_print(f"⚠  Network error fetching '{query}': {e}")
            return []
    
    return []

def _deduplicate(articles: list[dict]) -> list[dict]:
    seen, unique = set(), []
    for a in articles:
        key = a["title"][:70].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


# ── node ─────────────────────────────────────────────────────

def fetch_news_node(state: AgentState, news_api_key: str) -> AgentState:
    """
    LangGraph node.
    Expands the topic into queries, fetches articles, deduplicates.
    Returns updated state with `plan` and `raw_articles` filled.
    """
    topic = state["topic"]
    log_print(f"Planning queries for: '{topic}'")

    queries = _plan_queries(topic)
    print(f"\n  Planned queries:")
    for i, q in enumerate(queries, 1):
        print(f"    {i}. {q}")

    all_articles: list[dict] = []
    for i, q in enumerate(queries):
        log_print(f" Fetching: '{q}' ({i+1}/{len(queries)})")
        articles = _fetch_for_query(q, news_api_key)
        all_articles.extend(articles)
        if i < len(queries) - 1:  # Don't sleep after last query
            log_print(f"  Throttling for {1.5}s (NewsAPI rate limit protection)...")
            time.sleep(1.5)   # Increased throttle to protect against rate limits

    unique = _deduplicate(all_articles)
    print(f"\n  Fetched {len(all_articles)} articles → {len(unique)} unique after dedup")

    return {
        **state,
        "plan":         queries,
        "raw_articles": unique,
        "logs": [
            f"Planner → {queries}",
            f"Fetcher → {len(unique)} unique articles",
        ],
    }