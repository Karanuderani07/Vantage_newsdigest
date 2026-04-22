import json
from state import AgentState
from utils import llm, log_print

SECTION_SYSTEM = """You are a sharp news analyst.
Write a concise, factual section summary:
- First line: a bold sub-heading (4–7 words).
- 3–5 bullet points of specific facts/numbers.
Format:
**<Sub-heading>**
• <fact>
"""

def _summarize_one_cluster(topic: str, label: str, articles: list[dict]) -> str:
    block = f"Cluster theme: {label}\nMain topic: {topic}\n\n"
    for a in articles:
        block += f"SOURCE: {a['source']}\nTITLE: {a['title']}\nSUMMARY: {a['description']}\n\n"
    return llm(SECTION_SYSTEM, block, max_tokens=600)

def summarize_clusters_node(state: AgentState) -> AgentState:
    clusters = state.get("clusters", [])
    labels = state.get("cluster_labels", [])
    topic = state["topic"]

    if not clusters:
        log_print("⚠ No clusters to summarize")
        # FIX: Append to logs, don't replace
        new_logs = state.get("logs", []) + ["Summarizer → skipped"]
        return {**state, "logs": new_logs}

    summaries: list[str] = []
    for i, (cluster, label) in enumerate(zip(clusters, labels), 1):
        log_print(f" Summarizing cluster {i}/{len(clusters)}: '{label}'")
        summary = _summarize_one_cluster(topic, label, cluster)
        summaries.append(summary)

    # FIX: Explicitly append to logs and ensure cluster_summaries is passed
    new_logs = state.get("logs", []) + [f"Summarizer → {len(summaries)} cluster summaries ready"]
    
    return {
        **state,
        "cluster_summaries": summaries, 
        "logs": new_logs,
    }