"""
TOOLS — Actions that agents can perform

An agent without tools can only think.
An agent WITH tools can think AND act.

This is the key difference between a chatbot and an agent:
    Chatbot: receives question → generates answer
    Agent:   receives question → decides to search → reads results → generates answer

LangGraph tools are just Python functions decorated with @tool.
The LLM sees the function name + docstring and decides when to call it.
"""

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool


# DuckDuckGo search — free, no API key needed
search_engine = DuckDuckGoSearchResults(max_results=5)


@tool
def web_search(query: str) -> str:
    """Search the web for information on a given query.

    Use this tool when you need to find current information,
    facts, data, or recent developments about any topic.
    """
    results = search_engine.invoke(query)
    return results
