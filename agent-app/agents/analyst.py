"""
ANALYST AGENT — The Thinker

This agent has NO tools. It's a pure reasoning agent.
It takes raw research data and produces structured analysis.

KEY CONCEPT: Not all agents need tools
    - Researcher: needs tools (web search) to gather data
    - Analyst: needs only its brain to analyze data
    - Writer: needs only its brain to write reports

    Agent specialization comes from the SYSTEM PROMPT,
    not just from tools. The same LLM becomes a different
    "expert" based on its instructions.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from llm_provider import get_llm


# No tools for this agent — pure reasoning
llm = get_llm(temperature=0, max_tokens=400)

ANALYST_PROMPT = """You are a Research Analyst. STRICT LIMIT: 80 words max.

Produce a concise analysis with these sections (2-3 bullet points each):
## Key Themes
## Important Findings
## Knowledge Gaps

Rules:
- Bullet points only, no paragraphs
- Focus on patterns and insights, not repeating raw data
- STOP at 80 words — do not exceed this limit"""


async def analyst_node(state: ResearchState) -> dict:
    """
    Analyst node — reads research_data from state, writes analysis to state.

    Notice how this agent doesn't know about the Researcher.
    It just reads from the shared state (the whiteboard).
    This is DECOUPLING — agents don't depend on each other directly.
    """

    messages = [
        SystemMessage(content=ANALYST_PROMPT),
        HumanMessage(content=f"""Topic: {state['query']}

Research data:
{state['research_data']}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "analysis": response.content,
        "messages": [response]
    }
