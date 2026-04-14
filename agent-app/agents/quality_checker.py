"""
QUALITY CHECKER AGENT — The Gatekeeper (v2 — Targeted Feedback)

WHAT CHANGED FROM V1:
    v1: Produced ONE generic feedback string for ALL researchers.
        → All 3 searched for the same thing → duplicate effort → no improvement.

    v2: Produces TARGETED feedback for EACH researcher.
        → News researcher gets news-specific gaps to fill.
        → Academic researcher gets academic-specific gaps to fill.
        → Stats researcher gets stats-specific gaps to fill.
        → Each one searches for DIFFERENT missing info → real improvement!

WHY THIS MATTERS:
    Think of it like a manager reviewing work from 3 employees.

    BAD manager: "The report needs more detail." (to everyone)
        → Everyone adds the same generic detail.

    GOOD manager:
        - "Reporter A: I need more recent news about the court ruling."
        - "Reporter B: Find that MIT study on automation rates."
        - "Reporter C: Get me the exact job loss numbers from BLS."
        → Each person fills a DIFFERENT gap.

    The same principle applies to AI agents.
    Specific instructions → specific (better) results.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from graph.state import ResearchState
from llm_provider import get_llm


llm = get_llm(temperature=0, max_tokens=300)  # Precise evaluation, no creativity


# ── Structured Output Schema ──────────────────────────────────────
# Instead of asking the LLM to output text in a specific format and
# then parsing it with string splitting (fragile!), we define a
# Pydantic model and use with_structured_output().
#
# HOW IT WORKS:
#   1. We define a Pydantic model with typed fields
#   2. LangChain sends the schema to the LLM as a tool/function call
#   3. The LLM returns JSON that matches the schema EXACTLY
#   4. LangChain validates it and gives us a Pydantic object
#
# WHY THIS IS BETTER:
#   - No string parsing → no parsing bugs
#   - Guaranteed types (score is always an int, not "SCORE: 8")
#   - Fields can have descriptions that guide the LLM
#   - Works consistently across providers (Anthropic, OpenAI, Google)

class QualityEvaluation(BaseModel):
    """Structured output from the quality checker agent."""
    score: int = Field(
        description="Quality score from 1-10. "
                    "7+ means ready for final report. "
                    "Below 7 means retry needed."
    )
    feedback: str = Field(
        description="One sentence overall assessment (max 15 words)"
    )
    news_feedback: str = Field(
        description="Search instructions for news researcher, or 'none' if adequate. Max 15 words."
    )
    academic_feedback: str = Field(
        description="Search instructions for academic researcher, or 'none' if adequate. Max 15 words."
    )
    stats_feedback: str = Field(
        description="Search instructions for stats researcher, or 'none' if adequate. Max 15 words."
    )


# Create a version of the LLM that always returns QualityEvaluation
# This replaces the raw text response with a validated Pydantic object
structured_llm = llm.with_structured_output(QualityEvaluation)

QUALITY_CHECKER_PROMPT = """You are a Research Quality Evaluator.

Score the analysis 1-10 based on: depth, evidence quality, structure, completeness.
Provide targeted feedback for each researcher type if score < 7.
Keep all feedback under 15 words each."""


async def quality_checker_node(state: ResearchState) -> dict:
    """
    Quality checker node — evaluates the Analyst's work and provides
    TARGETED feedback for each specialist researcher.

    Uses STRUCTURED OUTPUT (Pydantic model) instead of text parsing.
    The LLM returns a QualityEvaluation object directly — no string
    splitting needed. This is more reliable and cost-efficient.

    Writes to state:
        - quality_score: 1-10 rating
        - feedback: overall assessment (for logging/display)
        - targeted_feedback: dict with per-researcher instructions
        - retry_count: incremented by 1
    """

    messages = [
        SystemMessage(content=QUALITY_CHECKER_PROMPT),
        HumanMessage(content=f"""Query: {state['query']}

Analysis:
{state['analysis']}

Retry count: {state.get('retry_count', 0)}/2
""")
    ]

    # structured_llm returns a QualityEvaluation object, not raw text
    result: QualityEvaluation = await structured_llm.ainvoke(messages)

    # Clamp score to valid range
    score = max(1, min(10, result.score))

    current_retries = state.get("retry_count", 0)

    # Build the targeted feedback dict
    targeted = {
        "news": "" if result.news_feedback.lower() == "none" else result.news_feedback,
        "academic": "" if result.academic_feedback.lower() == "none" else result.academic_feedback,
        "stats": "" if result.stats_feedback.lower() == "none" else result.stats_feedback,
    }

    return {
        "quality_score": score,
        "feedback": result.feedback,
        "targeted_feedback": targeted,
        "retry_count": current_retries + 1,
    }
