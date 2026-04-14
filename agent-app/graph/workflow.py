"""
THE GRAPH — Parallel Researchers + Conditional Quality Gate

EVOLUTION OF THE GRAPH:
═══════════════════════

Step 1 (Linear):
    START → Researcher → Analyst → Writer → END

Step 2 (Conditional Edge):
    START → Researcher → Analyst → Quality Checker →[decision]→ Writer → END
                ↑                                      |
                +───────── (retry) ────────────────────+

Step 3 (Parallel + Conditional — CURRENT):

                    ┌→ News Researcher ────────┐
    START/Retry ────┼→ Academic Researcher ────┼→ Merger → Analyst → QC →→ Writer → END
                    └→ Stats Researcher ───────┘                     |
                    ↑                                                |
                    +──────────────── (retry) ───────────────────────+
                FAN-OUT                             FAN-IN
               (1 → 3)                            (3 → 1)

THE RETRY PROBLEM WITH PARALLEL NODES:
══════════════════════════════════════

    The conditional edge can only route to ONE node:
        "retry" → "news_researcher"     (only news re-runs? bad!)

    But we need ALL 3 researchers to re-run on retry!

    SOLUTION: Add a lightweight "dispatcher" node.
    The dispatcher is a PASS-THROUGH — it does nothing except exist
    as a single node that fans out to all 3 researchers.

        quality_checker → [retry] → dispatcher → 3 researchers (parallel)

    This is a common pattern in graph-based systems:
    "When you need a single entry point that fans out, add a dispatcher."

    The dispatcher node itself is trivially simple — it just returns
    an empty dict (no state changes). Its only purpose is to be a
    "fork point" in the graph.
"""

from langgraph.graph import StateGraph, START, END
from graph.state import ResearchState
from agents.parallel_researchers import (
    news_researcher_node,
    academic_researcher_node,
    stats_researcher_node,
)
from agents.merger import research_merger_node
from agents.analyst import analyst_node
from agents.writer import writer_node
from agents.quality_checker import quality_checker_node


# ── Maximum retries before forcing the workflow forward ──────────
MAX_RETRIES = 2


async def research_dispatcher_node(state: ResearchState) -> dict:
    """
    Dispatcher — a pass-through node that exists solely as a fan-out point.

    WHY DO WE NEED THIS?
        The conditional edge from quality_checker can only route to ONE node.
        But on retry, we need ALL 3 researchers to re-run in parallel.

        The dispatcher solves this by being a single target that then
        fans out to all 3 researchers:

            quality_checker → [retry] → dispatcher → news_researcher
                                                   → academic_researcher
                                                   → stats_researcher

    This node does NOTHING to the state. It's pure routing infrastructure.
    Think of it like a highway interchange — no one stops there,
    but it's necessary to connect multiple roads.
    """
    return {}


def quality_router(state: ResearchState) -> str:
    """
    Routing function for the quality gate (unchanged from before).
    Returns "proceed" or "retry" based on quality_score and retry_count.
    """

    quality_score = state.get("quality_score", 0)
    retry_count = state.get("retry_count", 0)

    if quality_score >= 7:
        return "proceed"
    elif retry_count >= MAX_RETRIES:
        return "proceed"
    else:
        return "retry"


def create_research_graph():
    """
    Build the parallel research workflow with quality gate.

    FULL GRAPH:
    ═══════════

        START
          │
          ▼
      [dispatcher] ─────────────────────────────────────┐
          │                                             │
          ├──→ [news_researcher]      ──┐               │
          ├──→ [academic_researcher]  ──┼→ [merger]     │
          └──→ [stats_researcher]    ──┘     │          │
                                             ▼          │
                                        [analyst]       │
                                             │          │
                                             ▼          │
                                     [quality_checker]  │
                                         │       │      │
                                  proceed│       │retry  │
                                         ▼       ▼      │
                                     [writer]  [dispatcher] ← loops back!
                                         │
                                         ▼
                                        END

    EDGE COUNT:
        - 1 edge: START → dispatcher
        - 3 edges: dispatcher → 3 researchers (FAN-OUT)
        - 3 edges: 3 researchers → merger (FAN-IN)
        - 1 edge: merger → analyst
        - 1 edge: analyst → quality_checker
        - 1 conditional edge: quality_checker → writer OR dispatcher
        - 1 edge: writer → END
        Total: 11 edges (vs 4 in the original linear graph!)
    """

    graph = StateGraph(ResearchState)

    # ── Add ALL nodes ────────────────────────────────────────────
    graph.add_node("dispatcher", research_dispatcher_node)
    graph.add_node("news_researcher", news_researcher_node)
    graph.add_node("academic_researcher", academic_researcher_node)
    graph.add_node("stats_researcher", stats_researcher_node)
    graph.add_node("research_merger", research_merger_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("quality_checker", quality_checker_node)
    graph.add_node("writer", writer_node)

    # ── Entry point ──────────────────────────────────────────────
    graph.add_edge(START, "dispatcher")

    # ── FAN-OUT: Dispatcher → 3 researchers (run in parallel) ────
    #
    # These 3 edges from the SAME source node tell LangGraph:
    # "After dispatcher, run all 3 nodes AT THE SAME TIME."
    #
    # You don't write any threading code. LangGraph does it for you.
    graph.add_edge("dispatcher", "news_researcher")
    graph.add_edge("dispatcher", "academic_researcher")
    graph.add_edge("dispatcher", "stats_researcher")

    # ── FAN-IN: 3 researchers → merger (wait for all) ────────────
    #
    # These 3 edges TO the SAME target tell LangGraph:
    # "Wait for ALL 3 to complete, THEN run the merger."
    #
    # If news takes 5s, academic takes 8s, stats takes 3s:
    # The merger runs at 8s (when the slowest finishes).
    graph.add_edge("news_researcher", "research_merger")
    graph.add_edge("academic_researcher", "research_merger")
    graph.add_edge("stats_researcher", "research_merger")

    # ── Sequential: merger → analyst → quality_checker ───────────
    graph.add_edge("research_merger", "analyst")
    graph.add_edge("analyst", "quality_checker")

    # ── Quality gate (conditional edge) ──────────────────────────
    # On "proceed" → writer → END
    # On "retry"   → dispatcher (which fans out to all 3 again!)
    graph.add_conditional_edges(
        "quality_checker",
        quality_router,
        {
            "proceed": "writer",
            "retry": "dispatcher",     # goes back to the fan-out point!
        }
    )

    # ── Exit ─────────────────────────────────────────────────────
    graph.add_edge("writer", END)

    # ── Compile ──────────────────────────────────────────────────
    compiled_graph = graph.compile()

    return compiled_graph


# Create a single instance to reuse
research_workflow = create_research_graph()
