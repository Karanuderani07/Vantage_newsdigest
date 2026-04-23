"""
nodes/cluster_articles.py — Node 2
Filter + Cluster:
  1. LLM picks the best articles from the raw pool (up to 15).
  2. LLM groups them into 3–5 thematic clusters with labels.
"""

import json
from state import AgentState
from utils import llm, log_print


# ── helpers ──────────────────────────────────────────────────

def _filter_best(topic: str, articles: list[dict], max_keep: int = 15) -> list[dict]:
    """Ask the LLM to select the most informative, diverse articles."""
    if not articles:
        return []

    if len(articles) <= max_keep:
        log_print(f"  ℹ️  Keeping all {len(articles)} articles (under max {max_keep})")
        return articles

    # Show LLM up to 30 candidates to pick from
    candidates = articles[:30]
    summaries = "\n".join(
        f"{i}: [{a['source']}] {a['title']} | {a['description'][:100]}"
        for i, a in enumerate(candidates)
    )

    system = (
        "You are a news editor. Select the most informative, diverse, and credible "
        f"articles — pick exactly {max_keep} indices (or fewer if not enough quality ones). "
        "Prefer recent, specific, high-signal articles over vague ones. "
        "Maximise SOURCE diversity — don't pick 5 articles from the same outlet. "
        f'Return ONLY valid JSON: {{"selected": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]}} — indices only.'
    )

    try:
        raw = llm(system, f"Topic: {topic}\n\nArticles:\n{summaries}", json_mode=True)
        data = json.loads(raw)
        selected = [int(i) for i in data.get("selected", [])]
        if selected:
            result = [candidates[i] for i in selected if i < len(candidates)]
            if result:
                log_print(f"  ℹ️  LLM selected {len(result)} articles")
                return result
    except Exception as e:
        log_print(f"  ⚠️  Filter error: {type(e).__name__}. Using fallback.")

    log_print(f"  ℹ️  Fallback: keeping first {max_keep} articles")
    return articles[:max_keep]


def _cluster_articles(topic: str, articles: list[dict]) -> tuple[list[list[dict]], list[str]]:
    """
    Group articles into 3–5 thematic clusters.
    Returns (clusters_of_articles, cluster_label_strings).
    """
    if not articles:
        return [], []

    titles_list = "\n".join(f"{i}: {a['title']}" for i, a in enumerate(articles))

    system = (
        "Group these articles into 3–5 meaningful thematic clusters. "
        "Each cluster must represent a distinct sub-topic or angle of the main topic. "
        "Spread articles evenly — avoid putting everything in one cluster. "
        "Give each cluster a short, punchy label (4–6 words max). "
        "Return ONLY valid JSON:\n"
        '{"clusters": [[0,1,2],[3,4,5],[6,7,8],[9,10],[11,12]], "labels": ["Label A", "Label B", "Label C", "Label D", "Label E"]}'
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

    while len(labels) < len(clusters):
        labels.append(f"Section {len(labels)+1}")
    labels = labels[:len(clusters)]

    if not clusters and articles:
        clusters = [[a] for a in articles]
        labels   = [f"Article {i+1}" for i in range(len(articles))]

    return clusters, labels


# ── node ─────────────────────────────────────────────────────

def cluster_articles_node(state: AgentState) -> AgentState:
    raw = state["raw_articles"]
    if not raw:
        log_print("⚠  No articles to cluster — check your GNews API key / query")
        return {
            **state,
            "filtered_articles": [],
            "clusters":          [],
            "cluster_labels":    [],
            "sources":           [],
            "logs": state.get("logs", []) + ["Cluster → skipped (no articles)"],
        }

    topic = state["topic"]
    log_print(f"Filtering best articles from {len(raw)} candidates…")
    filtered = _filter_best(topic, raw, max_keep=15)
    sources  = sorted({a["source"] for a in filtered})
    print(f"   Kept {len(filtered)} articles | Sources: {', '.join(sources)}")

    log_print("Clustering into themes…")
    clusters, labels = _cluster_articles(topic, filtered)
    print(f"   Formed {len(clusters)} clusters: {labels}")

    return {
        **state,
        "filtered_articles": filtered,
        "clusters":          clusters,
        "cluster_labels":    labels,
        "sources":           sources,
        "logs": state.get("logs", []) + [
            f"Filter → {len(filtered)} articles from {len(sources)} sources",
            f"Cluster → {len(clusters)} groups: {labels}",
        ],
    }
