"""
nodes/fetch_news.py — Node 1
Planner + Fetcher combined:
  1. LLM breaks the topic into 4 targeted search queries.
  2. GNews API fetches up to 10 articles per query.
     (GNews works from cloud servers unlike NewsAPI free tier)
  3. Deduplication so we don't pass redundant articles downstream.
"""

import json
import time
import requests
from state import AgentState
from utils import llm, log_print


GNEWS_API_URL = "https://gnews.io/api/v4/search"


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


def _fetch_for_query(query: str, api_key: str, max_results: int = 10) -> list[dict]:
    """Call GNews API for a single query."""
    params = {
        "q":        query,
        "lang":     "en",
        "max":      max_results,
        "sortby":   "relevance",
        "token":    api_key,
    }

    try:
        r = requests.get(GNEWS_API_URL, params=params, timeout=10)

        if r.status_code == 403:
            log_print("⚠  GNews: Invalid API key or quota exceeded.")
            return []

        if r.status_code == 429:
            log_print("⚠  GNews: Rate limit hit, waiting 5s...")
            time.sleep(5)
            r = requests.get(GNEWS_API_URL, params=params, timeout=10)

        if r.status_code != 200:
            log_print(f"⚠  GNews error (HTTP {r.status_code}): {r.text[:200]}")
            return []

        data = r.json()
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

    except requests.RequestException as e:
        log_print(f"⚠  Network error fetching '{query}': {e}")
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
        log_print(f"Fetching: '{q}' ({i+1}/{len(queries)})")
        articles = _fetch_for_query(q, news_api_key)
        all_articles.extend(articles)
        log_print(f"  → {len(articles)} articles found")
        if i < len(queries) - 1:
            time.sleep(1)   # light throttle between queries

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
