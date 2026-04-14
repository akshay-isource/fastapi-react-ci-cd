"""
SHARED STATE — The Whiteboard

This is the data structure that flows through the entire graph.
Every agent can READ from it and WRITE to it.

UPDATED FLOW (with parallel researchers):
    - User writes the "query"
    - 3 Researchers run IN PARALLEL, each writes to "research_pieces"
    - Merger combines research_pieces into "research_data"
    - Analyst reads "research_data", writes "analysis"
    - Quality Checker reads "analysis", decides: retry or proceed
    - Writer reads "analysis", writes "final_report"

REDUCERS — Built-in vs Custom:
═══════════════════════════════

    A REDUCER tells LangGraph how to COMBINE writes from parallel nodes.

    BUILT-IN REDUCERS:
        operator.add  → concatenates lists: [a] + [b] = [a, b]
        add_messages  → appends messages (with dedup by ID)

    THE PROBLEM WITH operator.add FOR RETRIES:
        First pass:  [news_v1] + [academic_v1] + [stats_v1] = 3 items ✓
        After retry: 3 old items + [news_v2] + [academic_v2] + [stats_v2] = 6 items!

        The Analyst now sees DUPLICATED data — old AND new research from
        the same sources. The retry barely helps because the Analyst is
        reading the same information twice.

    CUSTOM REDUCER (dedupe_by_source):
        Instead of blindly concatenating, it checks the "source" field.
        If a new piece has the same source as an existing one, it REPLACES it.

        First pass:  news_v1, academic_v1, stats_v1 → 3 items ✓
        After retry: news_v2 REPLACES news_v1, etc. → still 3 items ✓

        The Analyst always sees exactly 3 pieces — the LATEST from each researcher.

    KEY LEARNING:
        A custom reducer is just a function: (old_list, new_list) → merged_list
        You can put ANY logic inside — dedup, sort, filter, cap size, etc.
        This is MUCH more powerful than operator.add.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


def dedupe_by_source(existing: list, new: list) -> list:
    """
    Custom reducer for research_pieces.

    Instead of blindly appending (operator.add), this REPLACES
    old pieces that have the same "source" as new pieces.

    HOW IT WORKS:
        1. Build a dict keyed by source: {"news_researcher": {...}, ...}
        2. Insert existing pieces first
        3. Insert new pieces — if same source exists, it OVERWRITES
        4. Return the dict values as a list

    EXAMPLE:
        existing = [{"source": "news_researcher", "data": "old news"}]
        new      = [{"source": "news_researcher", "data": "BETTER news"}]
        result   = [{"source": "news_researcher", "data": "BETTER news"}]
                                                          ↑ replaced!

    WHY A DICT?
        Dicts have unique keys. By using source as the key, we get
        automatic deduplication. This is a common Python pattern.
    """
    result_map = {}

    # First, add all existing pieces
    for piece in existing:
        source = piece.get("source", f"unknown_{id(piece)}")
        result_map[source] = piece

    # Then, add new pieces — same source OVERWRITES the old one
    for piece in new:
        source = piece.get("source", f"unknown_{id(piece)}")
        result_map[source] = piece

    return list(result_map.values())


class ResearchState(TypedDict):
    """
    Each field is a slot on the whiteboard.

    Agents will fill these slots one by one as the workflow progresses.
    """

    # The user's original question/topic
    query: str

    # ── PARALLEL RESEARCH FIELDS ─────────────────────────────────
    #
    # research_pieces: Uses our CUSTOM reducer (dedupe_by_source).
    #   - First pass: 3 researchers write 3 pieces → list has 3 items
    #   - On retry: 3 researchers write 3 NEW pieces → old ones get REPLACED
    #   - The Analyst always sees exactly 3 fresh pieces, never duplicates
    research_pieces: Annotated[list, dedupe_by_source]
    research_data: str

    # Analyst agent fills this — structured analysis of the research
    analysis: str

    # Writer agent fills this — the final polished report
    final_report: str

    # Message history — tracks the conversation flow
    messages: Annotated[list, add_messages]

    # ── Quality Control Fields ───────────────────────────────────
    retry_count: int
    quality_score: int
    feedback: str

    # ── NEW: Targeted Feedback Per Researcher ────────────────────
    #
    # OLD approach: One generic feedback string for ALL researchers.
    #   → All 3 search for the same thing → similar results → no improvement
    #
    # NEW approach: A dict with specific feedback for EACH researcher.
    #   → Each one searches for different missing information → real improvement
    #
    # Example:
    #   targeted_feedback = {
    #       "news": "Search for recent cybersecurity AI automation news",
    #       "academic": "Find studies on IT retraining success rates",
    #       "stats": "Find statistics on which IT jobs are most automated"
    #   }
    targeted_feedback: dict
