import json
from datetime import datetime
from state import AgentState
from utils import llm, log_print

ASSEMBLER_SYSTEM = """You are an expert news editor. Weave these summaries into a polished digest.
Use: ## Headline, ### The Big Picture, ### Key Developments, ### Why It Matters, ### What to Watch Next, and > One-Line Takeaway."""

QC_SYSTEM = """Return ONLY valid JSON: {"score": 8, "pass": true, "issues": []}"""

def _assemble(topic: str, cluster_summaries: list[str]) -> str:
    summaries_block = "\n\n---\n\n".join(cluster_summaries)
    return llm(ASSEMBLER_SYSTEM, f"Topic: {topic}\n\nSummaries:\n{summaries_block}", max_tokens=2000)

def _quality_check(topic: str, digest: str) -> tuple[int, bool, list[str]]:
    raw = llm(QC_SYSTEM, f"Topic: {topic}\n\nDigest:\n{digest[:1200]}", json_mode=True)
    result = json.loads(raw)
    return result.get("score", 7), result.get("pass", True), result.get("issues", [])

def assemble_briefing_node(state: AgentState) -> AgentState:
    # This is where the "handshake" happens
    cluster_summaries = state.get("cluster_summaries", [])

    if not cluster_summaries:
        log_print("⚠ No summaries found in state — returning empty digest")
        new_logs = state.get("logs", []) + ["Assembler → skipped (no summaries)"]
        return {
            **state,
            "digest": "⚠ No articles found for this topic.",
            "logs": new_logs,
        }

    topic = state["topic"]
    log_print("Assembling final digest…")
    digest = _assemble(topic, cluster_summaries)

    # Footer
    sources_str = " · ".join(state.get("sources", []))
    digest += f"\n\n---\n*Sources: {sources_str}*\n*Generated: {datetime.now().strftime('%d %b %Y, %H:%M')} IST*"

    score, passed, issues = _quality_check(topic, digest)
    
    # FIX: Append to logs
    new_logs = state.get("logs", []) + [
        f"Assembler → digest ready ({len(digest)} chars)",
        f"QC → score={score}/10"
    ]

    return {
        **state,
        "digest": digest,
        "quality_score": score,
        "quality_passed": passed,
        "quality_issues": issues,
        "logs": new_logs,
    }