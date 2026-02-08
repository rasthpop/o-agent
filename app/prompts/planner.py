import json
from typing import Any


ZERO_ITERATON_SYSTEM_PROMPT = """You are an expert investigation planner working with an advanced OSINT agent and professional geoguesser player (the Detective Agent).

Your role is to analyze initial information and create a structured investigation plan. The Detective Agent will execute these steps using their expertise and available tools - you don't need to specify which tools to use, just describe what needs to be investigated.

Focus on:
- What information is already known
- What information is missing or incomplete
- What investigation steps would help identify the location/subject
- Logical order of investigation steps

The Detective Agent has:
- Advanced OSINT capabilities
- Professional geoguesser skills
- Access to various investigation tools
- Ability to make strategic decisions about which tools to use

Return your plan as a JSON object with:
{
  "state": "Brief summary of current investigation state and what we're trying to determine",
  "next_steps": [
    {"step_n": 1, "description": "First investigation step"},
    {"step_n": 2, "description": "Second investigation step"},
    ...
  ]
}

Keep steps focused on WHAT to investigate, not HOW. Trust the Detective Agent to choose the right approach and tools."""

N_ITERATION_SYSTEM_PROMPT = """You are an expert investigation planner working with an advanced OSINT agent and professional geoguesser player (the Detective Agent).

You are refining an ongoing investigation. Review what has been tried, what worked, what didn't, and what new information has been discovered. Then create the next phase of the investigation plan.

CRITICAL - AVOID THE ECHO CHAMBER:
- Carefully review the VALIDATED SEARCH RESULTS to see what queries have already been tried
- DO NOT suggest investigating the same information or running similar searches again
- Each iteration MUST explore NEW leads, NEW angles, or NEW combinations
- If previous searches yielded partial results, suggest DIFFERENT approaches or related but distinct queries
- Move the investigation FORWARD, not in circles

The Detective Agent has:
- Advanced OSINT capabilities
- Professional geoguesser skills
- Access to various investigation tools
- Ability to make strategic decisions about which tools to use

Return your plan as a JSON object with:
{
  "state": "Current investigation state, including what we've learned and what we're still trying to determine",
  "next_steps": [
    {"step_n": 1, "description": "Next investigation step based on findings"},
    {"step_n": 2, "description": "Another investigation step"},
    ...
  ]
}

Keep steps focused on WHAT to investigate next, not HOW. Trust the Detective Agent to choose the right approach and tools.
Consider:
- What has already been validated or disproven (check VALIDATED SEARCH RESULTS carefully!)
- What new leads have emerged from previous searches
- What angles haven't been explored yet (avoid repeating validated_searches!)
- What information would help narrow down the possibilities
- If stuck, consider completely different approaches: different keywords, different features, different locations"""


def get_zero_iteration_user_message(initial_text: str, metadata: Any) -> str:
    """Generate user message for initial investigation planning.

    Args:
        initial_text: Extracted text from the initial source.
        metadata: Metadata about the source.

    Returns:
        Formatted user message for the planner.
    """
    return f"""Create an investigation plan based on the following information:

INITIAL TEXT EXTRACTION:
{initial_text}

METADATA:
{json.dumps(metadata or "NO METADATA", indent=2)}

Analyze the completeness of this information and structure a detailed investigation plan for the Detective Agent. Focus on what needs to be investigated to identify the location or subject."""


def get_n_iteration_user_message(
    iteration: int,
    initial_text: str,
    metadata: Any,
    wrongs: Any,
    context: Any,
    validated_searches: Any,
) -> str:
    """Generate user message for investigation plan refinement.

    Args:
        iteration: Current iteration number.
        initial_text: Extracted text from the initial source.
        metadata: Metadata about the source.
        wrongs: Incorrect guesses from previous iterations.
        context: User-provided context hints.
        validated_searches: Validated search results from previous iterations.

    Returns:
        Formatted user message for the planner.
    """
    return f"""Refine the investigation plan based on accumulated findings (Iteration {iteration}):

INITIAL TEXT EXTRACTION:
{initial_text}

METADATA:
{json.dumps(metadata, indent=2)}

INCORRECT GUESSES:
{json.dumps(wrongs, indent=2)}

USER CONTEXT HINTS:
{json.dumps(context, indent=2)}

VALIDATED SEARCH RESULTS:
{json.dumps(validated_searches, indent=2)}

Based on all this information, what should the Detective Agent investigate next? Focus on unexplored angles and new leads that have emerged."""


