"""
nodes/cluster_articles.py — Node 2
Filter + Cluster:
  1. LLM picks the 7 best articles from the raw pool.
  2. LLM groups them into 2–4 thematic clusters with labels.
"""

import json
from state import AgentState
from utils import llm, log_print


# ── helpers ──────────────────────────────────────────────────

def _filter_best(topic: str, articles: list[dict], max_keep: int = 7) -> list[dict]:
    """Ask the LLM to select the most informative, diverse articles."""
    if not articles:
        return []

    # If we have few enough articles, keep them all
    if len(articles) <= max_keep:
        log_print(f"  ℹ️  Keeping all {len(articles)} articles (less than max {max_keep})")
        return articles

    summaries = "\n".join(
        f"{i}: [{a['source']}] {a['title']} | {a['description'][:120]}"
        for i, a in enumerate(articles[:20])
    )

    system = (
        "You are a news editor. Select the most informative, diverse, and credible "
        f"articles from the list — pick exactly {max_keep} (or fewer if there aren't enough). "
        "Prefer recent, specific, high-signal articles over vague ones. "
        f'Return ONLY valid JSON: {{"selected": [0,1,2,3,4,5,6]}} — indices only, no explanation.'
    )

    try:
        raw = llm(system, f"Topic: {topic}\n\nArticles:\n{summaries}", json_mode=True)
        data = json.loads(raw)
        selected = [int(i) for i in data.get("selected", [])]
        
        if selected:
            result = [articles[i] for i in selected if i < len(articles)]
            if result:
                log_print(f"  ℹ️  LLM selected {len(result)} articles")
                return result
    except Exception as e:
        log_print(f"  ⚠️  Filter error: {type(e).__name__}. Using fallback.")
    
    # Fallback: pick first max_keep articles
    log_print(f"  ℹ️  Using fallback: first {max_keep} articles")
    return articles[:max_keep]


def _cluster_articles(topic: str, articles: list[dict]) -> tuple[list[list[dict]], list[str]]:
    """
    Group articles into 2–4 thematic clusters.
    Returns (clusters_of_articles, cluster_label_strings).
    """
    if not articles:
        return [], []

    titles_list = "\n".join(f"{i}: {a['title']}" for i, a in enumerate(articles))

    system = (
        "Group these articles into 2–4 meaningful thematic clusters. "
        "Each cluster must represent a distinct sub-topic or angle of the main topic. "
        "Also give each cluster a short, punchy label (4–6 words max). "
        "Return ONLY valid JSON:\n"
        '{"clusters": [[0,1,2],[3,4],[5,6]], "labels": ["Label A", "Label B", "Label C"]}'
        "\nNo explanation, no markdown."
    )

    try:
        raw  = llm(system, f"Topic: {topic}\n\nArticles:\n{titles_list}", json_mode=True)
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log_print(f"⚠  Cluster JSON parse error: {e}. Using simple grouping.")
        data = {"clusters": [[i] for i in range(len(articles))], "labels": []}

    idx_clusters = data.get("clusters", [list(range(len(articles)))])
    labels       = data.get("labels", [])

    clusters = []
    for group in idx_clusters:
        cluster = []
        for i in group:
            try:
                idx = int(i)
                if idx < len(articles):
                    cluster.append(articles[idx])
            except (ValueError, TypeError):
                continue
        
        if cluster:
            clusters.append(cluster)

    # Ensure we have labels for all clusters
    while len(labels) < len(clusters):
        labels.append(f"Section {len(labels)+1}")
    labels = labels[: len(clusters)]

    # Fallback: if no clusters formed, create one per article
    if not clusters and articles:
        clusters = [[a] for a in articles]
        labels = [f"Article {i+1}" for i in range(len(articles))]

    return clusters, labels


# ── node ─────────────────────────────────────────────────────

def cluster_articles_node(state: AgentState) -> AgentState:
    """
    LangGraph node.
    Filters raw articles to the best 7, then clusters them thematically.
    """
    raw = state["raw_articles"]
    if not raw:
        log_print("⚠  No articles to cluster — check your NewsAPI key / query")
        return {
            **state,
            "filtered_articles": [],
            "clusters":           [],
            "cluster_labels":     [],
            "sources":            [],
            "logs":              state.get("logs", []) + ["Cluster → skipped (no articles)"],
        }

    topic = state["topic"]
    log_print("Filtering to best articles…")
    filtered = _filter_best(topic, raw)
    sources  = sorted({a["source"] for a in filtered})
    print(f"   Kept {len(filtered)} articles | Sources: {', '.join(sources)}")

    log_print("Clustering into themes…")
    clusters, labels = _cluster_articles(topic, filtered)
    print(f"   Formed {len(clusters)} clusters: {labels}")

    return {
        **state,
        "filtered_articles": filtered,
        "clusters":           clusters,
        "cluster_labels":     labels,
        "sources":            sources,
        "logs": state.get("logs", []) + [
            f"Filter → {len(filtered)} articles from {len(sources)} sources",
            f"Cluster → {len(clusters)} groups: {labels}",
        ],
    }