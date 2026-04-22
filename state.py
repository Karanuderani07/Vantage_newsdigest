

from typing import TypedDict, List, Annotated
import operator


class AgentState(TypedDict):
    topic:              str
    plan:               List[str]
    raw_articles:       List[dict]
    filtered_articles:  List[dict]
    clusters:           List[List[dict]]
    cluster_labels:     List[str]          # human-readable cluster names
    cluster_summaries:  List[str]
    digest:             str
    sources:            List[str]
    quality_score:      int
    quality_passed:     bool
    quality_issues:     List[str]
    logs: Annotated[List[str], operator.add]