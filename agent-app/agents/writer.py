"""
WRITER AGENT — The Communicator

Takes the analyst's structured analysis and produces a
polished, reader-friendly report.

KEY CONCEPT: Agent Pipeline
    Researcher → Analyst → Writer

    Each agent adds value by transforming the data:
    - Raw search results → Structured analysis → Polished report

    This is like a newsroom:
    - Reporter gathers facts
    - Editor organizes the story
    - Writer makes it readable
"""

from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from llm_provider import get_llm


llm = get_llm(temperature=0.7, max_tokens=250)  # Slightly creative for writing

WRITER_PROMPT = """You are a Report Writer. STRICT LIMIT: 100 words max.

Write a concise research report in markdown with:
- 1-line executive summary
- 3-4 key findings as bullet points
- 1-line conclusion

Rules:
- Professional, clear language
- Include specific facts and numbers from the analysis
- No filler or generic statements
- STOP at 100 words — do not exceed this limit"""


async def writer_node(state: ResearchState) -> dict:
    """
    Writer node — the final agent in the pipeline.

    Reads the analysis from state and produces the final report.
    This is the output the user actually sees.
    """

    messages = [
        SystemMessage(content=WRITER_PROMPT),
        HumanMessage(content=f"""Topic: {state['query']}

Analysis:
{state['analysis']}
""")
    ]

    response = await llm.ainvoke(messages)

    return {
        "final_report": response.content,
        "messages": [response]
    }
