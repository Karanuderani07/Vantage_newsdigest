"""
main.py — LangGraph wiring + CLI runner.

Usage:
    python main.py "India AI policy 2025"
    python main.py "climate summit outcomes"
    python main.py                          ← defaults to "AI regulation 2025"
"""

import os
import sys
import time
import functools
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from state import AgentState
from utils import get_client, log_print
from nodes.fetch_news         import fetch_news_node
from nodes.cluster_articles   import cluster_articles_node
from nodes.summarize_clusters import summarize_clusters_node
from nodes.assemble_briefing  import assemble_briefing_node

load_dotenv()

# ── Keys are read at CALL TIME, not module-load time ──────────
# (Module-level reads happen before app.py injects st.secrets
#  into os.environ, so they always return empty strings on cloud)

def _get_groq_key() -> str:
    return os.environ.get("GROQ_API_KEY", "")

def _get_news_key() -> str:
    return os.environ.get("NEWS_API_KEY", "")


def _validate_keys(groq_key: str, news_key: str):
    errors = []
    if not groq_key or "YOUR" in groq_key:
        errors.append("GROQ_API_KEY missing — get a free key at https://console.groq.com")
    if not news_key or "YOUR" in news_key:
        errors.append("NEWS_API_KEY missing — get a free key at https://newsapi.org")
    if errors:
        for e in errors:
            print(f"❌ {e}")
        sys.exit(1)


# ── Graph builder ─────────────────────────────────────────────

def build_graph(news_api_key: str) -> object:
    """Wire up the four-node LangGraph pipeline."""

    # fetch_news_node needs the API key injected; use functools.partial
    fetch_node = functools.partial(fetch_news_node, news_api_key=news_api_key)

    g = StateGraph(AgentState)
    g.add_node("fetch",     fetch_node)
    g.add_node("cluster",   cluster_articles_node)
    g.add_node("summarize", summarize_clusters_node)
    g.add_node("assemble",  assemble_briefing_node)

    g.set_entry_point("fetch")
    g.add_edge("fetch",     "cluster")
    g.add_edge("cluster",   "summarize")
    g.add_edge("summarize", "assemble")
    g.add_edge("assemble",  END)

    return g.compile()


# ── Runner ────────────────────────────────────────────────────

def run(topic: str) -> AgentState:
    """Run the full pipeline for a given topic and return the final state."""
    # Read keys at call time — os.environ is fully populated by now
    groq_key = _get_groq_key()
    news_key = _get_news_key()

    _validate_keys(groq_key, news_key)
    get_client(groq_key)  # initialise the shared Groq client

    _print_banner(topic)
    graph = build_graph(news_key)

    initial_state: AgentState = {
        "topic":             topic,
        "plan":              [],
        "raw_articles":      [],
        "filtered_articles": [],
        "clusters":          [],
        "cluster_labels":    [],
        "digest":            "",
        "sources":           [],
        "quality_score":     0,
        "quality_passed":    True,
        "quality_issues":    [],
        "logs":              [],
    }

    start       = time.time()
    final_state = graph.invoke(initial_state)
    elapsed     = time.time() - start

    _display_digest(final_state, elapsed)
    return final_state


# ── Display helpers ───────────────────────────────────────────

def _print_banner(topic: str):
    print("\n" + "═" * 62)
    print("  📰  AUTONOMOUS NEWS DIGEST AGENT")
    print("  Groq (free) · LangGraph · NewsAPI")
    print("═" * 62)
    print(f"\n  Topic: {topic}\n")


def _display_digest(state: AgentState, elapsed: float):
    print("\n" + "═" * 62)
    print(state["digest"])
    print("═" * 62)
    print("\n📋 Agent Execution Log:")
    for entry in state.get("logs", []):
        print(f"   → {entry}")
    status = "✅ PASSED" if state.get("quality_passed", True) else "⚠  FLAGGED"
    score  = state.get("quality_score", "–")
    print(f"\n   Quality : {status} ({score}/10)")
    print(f"   Sources : {', '.join(state.get('sources', []))}")
    print(f"   ⏱  Time  : {elapsed:.1f}s\n")


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]).strip() or "artificial intelligence regulation 2025"
    run(topic)
