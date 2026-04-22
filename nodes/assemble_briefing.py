import json
import hashlib
from datetime import datetime
from state import AgentState
from utils import llm, log_print

# ── Token Optimization: Shorter, More Efficient Prompts ──────

COMBINED_ANALYSIS_SYSTEM = """Analyze the topic comprehensively. Provide:

ANALYSIS:
- Key trends and patterns
- Industry/market impact
- Winners and losers
- Geopolitical implications

IMPACT:
- Immediate (0-3 months) effects
- Medium-term (3-12 months) changes
- Long-term (1+ years) consequences
- Stakeholder perspectives

TIMELINE:
- Precursor events
- Key milestones
- Recent developments
- Anticipated next steps

Be specific with data, names, and predictions. Avoid generic statements."""

ASSEMBLER_SYSTEM = """Create executive briefing with: THE BIG PICTURE (trends), DEEP ANALYSIS (insights), IMPACT ASSESSMENT (who affected), TIMELINE, WHAT TO WATCH, KEY TAKEAWAY. Be concise but insightful.

### 💡 WHAT TO WATCH
[3-4 upcoming critical developments]

### 🎯 KEY TAKEAWAY
[Single powerful insight in 1-2 sentences]

Make it compelling, specific, and actionable. Use data and trends."""

QC_SYSTEM = """Return ONLY JSON: {"score": 8, "pass": true, "issues": []}. Rate depth 1-10."""

# ── Caching Mechanism ─────────────────────────────────────────
_BRIEFING_CACHE = {}

def _get_cache_key(topic: str, summaries: list[str]) -> str:
    """Generate cache key from topic + summaries hash."""
    content = f"{topic}|{'|'.join(summaries)}"
    return hashlib.md5(content.encode()).hexdigest()

def _load_cached_briefing(topic: str, summaries: list[str]) -> dict | None:
    """Return cached briefing if exists."""
    key = _get_cache_key(topic, summaries)
    return _BRIEFING_CACHE.get(key)

def _save_briefing_cache(topic: str, summaries: list[str], briefing_data: dict):
    """Cache generated briefing."""
    key = _get_cache_key(topic, summaries)
    _BRIEFING_CACHE[key] = briefing_data

# ── Enhanced Assembly Functions with Token Optimization ───────

def _generate_combined_analysis(topic: str, cluster_summaries: list[str]) -> dict:
    """Generate analysis, impact, and timeline in ONE LLM call (token optimized)."""
    summaries_block = "\n\n---\n\n".join(cluster_summaries[:5])  # Limit to first 5 summaries
    
    prompt = f"""Topic: {topic}

Article Summaries:
{summaries_block}

{COMBINED_ANALYSIS_SYSTEM}"""
    
    response = llm(COMBINED_ANALYSIS_SYSTEM, prompt, max_tokens=800)  # Reduced from 1700 total
    
    # Parse the response into sections
    sections = response.split('\n\n')
    analysis = ""
    impact = ""
    timeline = ""
    
    current_section = None
    for section in sections:
        if section.upper().startswith('ANALYSIS:'):
            current_section = 'analysis'
            analysis = section.replace('ANALYSIS:', '').strip()
        elif section.upper().startswith('IMPACT:'):
            current_section = 'impact'
            impact = section.replace('IMPACT:', '').strip()
        elif section.upper().startswith('TIMELINE:'):
            current_section = 'timeline'
            timeline = section.replace('TIMELINE:', '').strip()
        elif current_section and section.strip():
            if current_section == 'analysis':
                analysis += '\n\n' + section
            elif current_section == 'impact':
                impact += '\n\n' + section
            elif current_section == 'timeline':
                timeline += '\n\n' + section
    
    return {
        'analysis': analysis.strip(),
        'impact': impact.strip(),
        'timeline': timeline.strip()
    }

def _assemble(topic: str, cluster_summaries: list[str], combined_data: dict) -> str:
    """Combine all into final briefing (reduced tokens)."""
    context = f"""Topic: {topic}

SUMMARIES:
{chr(10).join(cluster_summaries[:3])}

ANALYSIS: {combined_data['analysis'][:300]}
IMPACT: {combined_data['impact'][:250]}
TIMELINE: {combined_data['timeline'][:200]}"""
    
    return llm(ASSEMBLER_SYSTEM, context, max_tokens=1500)

def _quality_check(topic: str, digest: str) -> tuple[int, bool, list[str]]:
    """Check quality (reduced tokens)."""
    raw = llm(QC_SYSTEM, f"Topic: {topic}\nDigest:\n{digest[:800]}", json_mode=True, max_tokens=150)  # Reduced
    result = json.loads(raw)
    return result.get("score", 7), result.get("pass", True), result.get("issues", [])


def assemble_briefing_node(state: AgentState) -> AgentState:
    """Generate enriched briefing with caching & optimized tokens."""
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
    
    # Check cache first
    cached = _load_cached_briefing(topic, cluster_summaries)
    if cached:
        log_print("✅ Returning cached briefing (token savings!)")
        new_logs = state.get("logs", []) + ["Assembler → used cache (+50% token savings)"]
        return {
            **state,
            "digest": cached["digest"],
            "quality_score": cached["quality_score"],
            "quality_passed": cached["quality_passed"],
            "quality_issues": cached["quality_issues"],
            "logs": new_logs,
        }
    
    log_print("🔍 Generating comprehensive analysis (analysis + impact + timeline)...")
    combined_data = _generate_combined_analysis(topic, cluster_summaries)
    
    log_print("✍️  Assembling executive briefing...")
    digest = _assemble(topic, cluster_summaries, combined_data)

    # Footer with sources
    sources_str = " · ".join(state.get("sources", []))
    digest += f"\n\n---\n*Sources: {sources_str}*\n*Generated: {datetime.now().strftime('%d %b %Y, %H:%M')} IST*"

    score, passed, issues = _quality_check(topic, digest)
    
    # Cache the result
    briefing_data = {
        "digest": digest,
        "quality_score": score,
        "quality_passed": passed,
        "quality_issues": issues,
    }
    _save_briefing_cache(topic, cluster_summaries, briefing_data)
    
    new_logs = state.get("logs", []) + [
        f"Assembler → combined analysis generated (analysis + impact + timeline)",
        f"Assembler → digest assembled ({len(digest)} chars)",
        f"QC → score={score}/10, passed={passed}",
        f"Cache → briefing cached for future use"
    ]

    return {
        **state,
        "digest": digest,
        "quality_score": score,
        "quality_passed": passed,
        "quality_issues": issues,
        "logs": new_logs,
    }