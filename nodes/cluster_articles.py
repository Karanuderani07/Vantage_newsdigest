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

    raw      = llm(system, f"Topic: {topic}\n\nArticles:\n{summaries}", json_mode=True)
    # FIX: Cast indices to int because LLMs sometimes return strings
    try:
        selected = [int(i) for i in json.loads(raw).get("selected", [])]
    except (ValueError, TypeError):
        selected = list(range(min(max_keep, len(articles))))
        
    return [articles[i] for i in selected if i < len(articles)]


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

    raw  = llm(system, f"Topic: {topic}\n\nArticles:\n{titles_list}", json_mode=True)
    data = json.loads(raw)

    idx_clusters = data.get("clusters", [list(range(len(articles)))])
    labels       = data.get("labels", [f"Section {i+1}" for i in range(len(idx_clusters))])

    clusters = []
    for group in idx_clusters:
        # FIX: Cast index 'i' to int to avoid TypeError
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

    # pad / trim labels to match clusters
    while len(labels) < len(clusters):
        labels.append(f"Section {len(labels)+1}")
    labels = labels[: len(clusters)]

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