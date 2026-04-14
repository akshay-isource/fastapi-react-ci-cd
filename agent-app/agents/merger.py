"""
RESEARCH MERGER — The Fan-in Node

This node is the FAN-IN point of the parallel execution pattern.

WHAT IS FAN-IN?
    Fan-out = one node triggers MULTIPLE parallel nodes (1 → many)
    Fan-in  = multiple parallel nodes CONVERGE into one (many → 1)

    The merger is where the parallel branches come back together.

        News ──────┐
        Academic ──┼──→ MERGER ──→ Analyst
        Stats ─────┘
              fan-in point

HOW DOES LANGGRAPH KNOW TO WAIT?
    LangGraph automatically waits for ALL incoming edges to complete
    before running the merger. You don't need to write any "wait" logic.

    If News takes 5s, Academic takes 8s, and Stats takes 3s:
    - Stats finishes at 3s ✓ (waits)
    - News finishes at 5s  ✓ (waits)
    - Academic finishes at 8s ✓ (ALL done!)
    - Merger runs at 8s

    This is handled by LangGraph internally — you just wire the edges.

WHAT DOES THE MERGER DO?
    It reads research_pieces (a list of dicts from all 3 researchers)
    and combines them into a single research_data string.

    This is a PURE PYTHON node — no LLM call needed.
    It's just string formatting. Fast and cheap.

    Not every node needs an LLM! Use LLMs for reasoning/generation,
    use plain Python for data transformation.
"""

from graph.state import ResearchState


async def research_merger_node(state: ResearchState) -> dict:
    """
    Combines research from all parallel researchers into one string.

    This node does NOT call an LLM — it's pure data transformation.
    Not every node in your graph needs to be an "agent" with an LLM.
    Some nodes are just code that reshapes data.

    Reads: research_pieces (list of dicts from 3 researchers)
    Writes: research_data (single string for the Analyst)
    """

    pieces = state.get("research_pieces", [])

    if not pieces:
        return {"research_data": "No research data collected."}

    # Combine all research pieces into a structured string
    # Each piece is a dict: {"source": "news_researcher", "data": "..."}
    sections = []
    for piece in pieces:
        source = piece.get("source", "unknown").replace("_", " ").title()
        data = piece.get("data", "No data")
        sections.append(f"## {source}\n\n{data}")

    combined = "\n\n---\n\n".join(sections)

    # Add a header showing how many sources contributed
    header = f"# Combined Research ({len(pieces)} sources)\n\n"

    return {
        "research_data": header + combined
    }
