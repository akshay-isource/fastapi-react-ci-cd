"""
PARALLEL RESEARCHERS — The Specialized Research Team (v2 — Targeted Retry)

WHAT CHANGED FROM V1:
    v1: On retry, ALL 3 researchers got the SAME generic feedback.
        → All 3 searched for similar things → duplicate results → no improvement.

    v2: On retry, each researcher reads ONLY ITS OWN targeted feedback.
        → News researcher fills news gaps.
        → Academic researcher fills academic gaps.
        → Stats researcher fills stats gaps.
        → Each fills a DIFFERENT gap → real improvement on retry!

HOW IT WORKS:
    The quality checker writes a dict to state:
        targeted_feedback = {
            "news": "Search for recent cybersecurity AI automation news",
            "academic": "Find studies on IT retraining success rates",
            "stats": "Find statistics on which IT jobs are most automated"
        }

    News researcher reads:     targeted_feedback["news"]
    Academic researcher reads:  targeted_feedback["academic"]
    Stats researcher reads:     targeted_feedback["stats"]

    Each agent gets instructions SPECIFIC to its domain.

COMBINED WITH THE CUSTOM REDUCER:
    The dedupe_by_source reducer in state.py ensures that retry results
    REPLACE the old ones (same source name = overwrite, not append).

    So after retry:
        research_pieces has 3 items (not 6)
        Each item is the IMPROVED version from the targeted search
"""

from langchain_core.messages import SystemMessage, HumanMessage
from tools.search import web_search
from graph.state import ResearchState
from llm_provider import get_llm, supports_tool_calling


llm = get_llm(temperature=0, max_tokens=300)

SUPPORTS_TOOLS = supports_tool_calling()

# ═══════════════════════════════════════════════════════════════════
# AGENT 1: News Researcher — Recent events, trends, breaking news
# ═══════════════════════════════════════════════════════════════════

NEWS_PROMPT = """You are a News Research Specialist. STRICT LIMIT: 50 words max.

Rules:
- Only recent news, announcements, and trends
- Include dates and source names
- Bullet points only, no paragraphs
- STOP at 50 words — do not exceed this limit"""


async def news_researcher_node(state: ResearchState) -> dict:
    """
    Searches for recent news and trends about the topic.

    On retry, reads targeted_feedback["news"] for SPECIFIC instructions
    about what news/trends to search for.
    """

    query = state["query"]
    retry_count = state.get("retry_count", 0)

    # Get THIS researcher's specific feedback (not the generic one!)
    targeted = state.get("targeted_feedback", {})
    my_feedback = targeted.get("news", "")

    # Build search query based on whether this is a retry
    if retry_count > 0 and my_feedback:
        # Targeted retry: search for exactly what the quality checker asked for
        search_query = f"{query} {my_feedback}"
    else:
        # First attempt: broad news search
        search_query = f"{query} latest news recent developments 2024 2025"

    try:
        results = web_search.invoke({"query": search_query})
    except Exception as e:
        results = f"Search failed: {e}"

    # Let LLM synthesize the raw results into a focused news summary
    messages = [
        SystemMessage(content=NEWS_PROMPT),
        HumanMessage(content=f"""Topic: {query}

Raw search results:
{results}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "research_pieces": [{
            "source": "news_researcher",
            "data": response.content
        }],
        "messages": [response]
    }


# ═══════════════════════════════════════════════════════════════════
# AGENT 2: Academic Researcher — Deep knowledge, expert opinions
# ═══════════════════════════════════════════════════════════════════

ACADEMIC_PROMPT = """You are an Academic Research Specialist. STRICT LIMIT: 50 words max.

Rules:
- Only expert opinions, studies, and research findings
- Name experts, institutions, or publications
- Bullet points only, no paragraphs
- STOP at 50 words — do not exceed this limit"""


async def academic_researcher_node(state: ResearchState) -> dict:
    """
    Searches for academic and expert perspectives on the topic.

    On retry, reads targeted_feedback["academic"] for SPECIFIC instructions
    about what studies/expert opinions to search for.
    """

    query = state["query"]
    retry_count = state.get("retry_count", 0)

    targeted = state.get("targeted_feedback", {})
    my_feedback = targeted.get("academic", "")

    if retry_count > 0 and my_feedback:
        search_query = f"{query} {my_feedback}"
    else:
        search_query = f"{query} expert analysis research findings explained"

    try:
        results = web_search.invoke({"query": search_query})
    except Exception as e:
        results = f"Search failed: {e}"

    messages = [
        SystemMessage(content=ACADEMIC_PROMPT),
        HumanMessage(content=f"""Topic: {query}

Raw search results:
{results}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "research_pieces": [{
            "source": "academic_researcher",
            "data": response.content
        }],
        "messages": [response]
    }


# ═══════════════════════════════════════════════════════════════════
# AGENT 3: Stats Researcher — Numbers, data, metrics, comparisons
# ═══════════════════════════════════════════════════════════════════

STATS_PROMPT = """You are a Statistics Research Specialist. STRICT LIMIT: 50 words max.

Rules:
- Only numbers, percentages, metrics, and data points
- Include data source and year for each stat
- Bullet points only, no paragraphs
- STOP at 50 words — do not exceed this limit"""


async def stats_researcher_node(state: ResearchState) -> dict:
    """
    Searches for statistics and quantitative data about the topic.

    On retry, reads targeted_feedback["stats"] for SPECIFIC instructions
    about what numbers/metrics to search for.
    """

    query = state["query"]
    retry_count = state.get("retry_count", 0)

    targeted = state.get("targeted_feedback", {})
    my_feedback = targeted.get("stats", "")

    if retry_count > 0 and my_feedback:
        search_query = f"{query} {my_feedback}"
    else:
        search_query = f"{query} statistics data market size numbers 2024"

    try:
        results = web_search.invoke({"query": search_query})
    except Exception as e:
        results = f"Search failed: {e}"

    messages = [
        SystemMessage(content=STATS_PROMPT),
        HumanMessage(content=f"""Topic: {query}

Raw search results:
{results}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "research_pieces": [{
            "source": "stats_researcher",
            "data": response.content
        }],
        "messages": [response]
    }
