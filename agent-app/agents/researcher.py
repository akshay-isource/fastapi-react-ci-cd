"""
RESEARCHER AGENT — The Information Gatherer

This agent has ONE job: search the web and collect raw information.

TWO MODES depending on the LLM's capabilities:

    Mode 1 — Tool Calling (Anthropic, OpenAI):
        LLM decides WHEN to search and WHAT to search for.
        This is the "true agent" loop: Think → Act → Observe → Repeat.

    Mode 2 — No Tool Calling (Sarvam, some local models):
        We search first, then pass results to the LLM to synthesize.
        The LLM is a "reasoner" not a "tool user" in this mode.

    Both modes produce the same output — the agents downstream
    (Analyst, Writer) don't care how the research was gathered.

KEY LEARNING:
    Not all LLMs support tool calling. A good multi-agent system
    should gracefully handle this. The fallback pattern is:
    "do the action yourself, give results to LLM for reasoning."
"""

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from tools.search import web_search
from graph.state import ResearchState
from llm_provider import get_llm, supports_tool_calling


llm = get_llm(temperature=0)

# Explicitly check if the provider supports tool calling
# bind_tools() won't fail for OpenAI-compatible APIs (like Sarvam)
# but the actual API call will — so we check the provider directly
SUPPORTS_TOOLS = supports_tool_calling()
llm_with_tools = llm.bind_tools([web_search]) if SUPPORTS_TOOLS else None

RESEARCHER_PROMPT = """You are a Research Specialist. Your job is to gather
comprehensive, factual information on the given topic.

Instructions:
- Compile ALL findings into a structured summary
- Include sources/references where possible
- Be thorough — the Analyst agent depends on your research quality

Output your findings as a structured text with clear sections."""

RESEARCHER_PROMPT_WITH_TOOLS = """You are a Research Specialist. Your job is to gather
comprehensive, factual information on the given topic.

Instructions:
- Use the web_search tool multiple times to gather diverse information
- Search for different aspects of the topic (facts, statistics, expert opinions, recent developments)
- Compile ALL your findings into a structured summary
- Include sources/references where possible
- Be thorough — the Analyst agent depends on your research quality

Output your findings as a structured text with clear sections."""


async def _research_with_tools(state: ResearchState) -> dict:
    """Mode 1: LLM decides when to search (tool calling supported)."""

    feedback = state.get("feedback", "")
    retry_count = state.get("retry_count", 0)

    # On retry, tell the LLM what specific gaps to fill
    if retry_count > 0 and feedback:
        user_msg = (
            f"Research this topic thoroughly: {state['query']}\n\n"
            f"IMPORTANT — Previous research was insufficient. "
            f"The quality reviewer said: {feedback}\n"
            f"Focus your searches on filling these specific gaps."
        )
    else:
        user_msg = f"Research this topic thoroughly: {state['query']}"

    messages = [
        SystemMessage(content=RESEARCHER_PROMPT_WITH_TOOLS),
        HumanMessage(content=user_msg)
    ]

    response = await llm_with_tools.ainvoke(messages)

    # Tool calling loop:
    # Anthropic requires: tool_use → tool_result (for EACH tool call)
    # We append the AI response, then a ToolMessage for each tool call
    while response.tool_calls:
        # Add the AI's response (contains tool_use blocks)
        messages.append(response)

        # Execute each tool and add a proper ToolMessage for each
        for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                result = web_search.invoke(tool_call["args"])
            else:
                result = f"Unknown tool: {tool_call['name']}"

            # ToolMessage must reference the tool_call id — this is how
            # the LLM knows which tool_use this result belongs to
            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            ))

        # Ask LLM again — it sees the results and decides: search more or done?
        response = await llm_with_tools.ainvoke(messages)

    return {
        "research_data": response.content,
        "messages": [response]
    }


async def _research_without_tools(state: ResearchState) -> dict:
    """
    Mode 2: We search first, LLM synthesizes (no tool calling).

    Steps:
        1. Generate multiple search queries from the topic
        2. Run all searches ourselves
        3. Pass raw results to LLM to synthesize into a report

    NEW: On retries, we use the quality checker's feedback to
    search for SPECIFIC missing information instead of repeating
    the same generic searches. This is what makes retries useful —
    without targeted feedback, looping back would just produce the
    same results again.
    """

    query = state["query"]
    feedback = state.get("feedback", "")
    retry_count = state.get("retry_count", 0)

    # Step 1: Search with multiple angles on the topic
    # On retry, use the feedback to create targeted search queries
    if retry_count > 0 and feedback:
        # Retry mode: search for what the quality checker said was missing
        search_queries = [
            f"{query} {feedback}",
            f"{query} detailed analysis",
            f"{query} expert opinions statistics",
        ]
    else:
        # First attempt: broad search
        search_queries = [
            query,
            f"{query} latest developments",
            f"{query} statistics and data",
        ]

    all_results = []
    for sq in search_queries:
        try:
            result = web_search.invoke({"query": sq})
            all_results.append(f"Search: '{sq}'\nResults:\n{result}")
        except Exception as e:
            all_results.append(f"Search: '{sq}'\nError: {e}")

    raw_search_data = "\n\n---\n\n".join(all_results)

    # Step 2: Let the LLM synthesize the search results
    # On retry, include the previous research so the LLM can BUILD on it
    # rather than starting from scratch
    previous_research = state.get("research_data", "")
    retry_context = ""
    if retry_count > 0 and previous_research:
        retry_context = f"""
PREVIOUS RESEARCH (build on this, don't repeat it):
{previous_research[:2000]}

QUALITY FEEDBACK (address these gaps):
{feedback}
"""

    messages = [
        SystemMessage(content=RESEARCHER_PROMPT),
        HumanMessage(content=f"""Research this topic: {query}

Here are web search results I've gathered for you. Analyze and compile
them into a comprehensive, structured research summary.
{retry_context}
RAW SEARCH RESULTS:
{raw_search_data}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "research_data": response.content,
        "messages": [response]
    }


async def researcher_node(state: ResearchState) -> dict:
    """
    Router — picks the right mode based on LLM capabilities.
    Downstream agents don't know or care which mode was used.
    """
    if SUPPORTS_TOOLS:
        return await _research_with_tools(state)
    else:
        return await _research_without_tools(state)
