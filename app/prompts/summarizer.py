"""Prompts for the Summarizer agent."""

SUMMARIZER_SYSTEM_PROMPT = """You are an OSINT investigation summarizer.

Your task is to analyze the execution log from a geolocation investigation and extract
key findings into a structured summary.

ANALYSIS APPROACH:
1. Review all tool calls and their results
2. Identify significant evidence (location names, coordinates, unique identifiers)
3. Note confidence levels and validation status
4. Highlight contradictions or uncertainties
5. Extract actionable insights for further investigation

OUTPUT FORMAT:
Return a JSON object with:
{
    "summary": "Brief 2-3 sentence overview of investigation progress",
    "key_points": [
        {
            "category": "location|evidence|hypothesis|contradiction",
            "finding": "Specific finding or conclusion",
        }
    ],
    "next_actions": ["Suggested follow-up actions if investigation incomplete"]
}

GUIDELINES:
- Be concise and factual
- Prioritize unique, specific findings over generic observations
- Mark confidence levels honestly based on evidence quality
- Focus on findings that narrow down the location
- Avoid repeating information that was already in the initial image analysis
"""


def get_summarizer_user_message(detective_response: dict) -> str:
    """Generate user message for summarizer with detective results.

    Args:
        detective_response: Dict from Detective.investigate_with_plan() containing
                          status, iterations, execution_log, and final_response.

    Returns:
        Formatted message for the summarizer.
    """
    status = detective_response.get("status", "unknown")
    iterations = detective_response.get("iterations", 0)
    final_response = detective_response.get("final_response", "")
    execution_log = detective_response.get("execution_log", [])

    message = f"""INVESTIGATION SUMMARY REQUEST

Investigation Status: {status}
Total Iterations: {iterations}

FINAL AGENT RESPONSE:
{final_response}

EXECUTION LOG:
"""

    for log_entry in execution_log:
        iteration = log_entry.get("iteration", "?")
        reasoning = log_entry.get("agent_reasoning", "")
        tool_calls = log_entry.get("tool_calls", [])

        message += f"\n--- Iteration {iteration} ---\n"
        if len(reasoning) > 300:
            message += f"Reasoning: {reasoning[:300]}...\n"
        else:
            message += f"Reasoning: {reasoning}\n"

        for tc in tool_calls:
            tool_name = tc.get("tool_name", "unknown")
            success = tc.get("success", False)
            result = tc.get("result", {})
            error = tc.get("error")

            status_icon = "✓" if success else "✗"
            message += f"  {status_icon} {tool_name}: "

            if error:
                message += f"ERROR - {error}\n"
            else:
                # Truncate result for readability
                result_str = str(result)
                if len(result_str) > 200:
                    message += f"{result_str[:200]}...\n"
                else:
                    message += f"{result_str}\n"

    message += "\nPlease analyze this investigation log and extract key findings."

    return message


SIMILARITY_CHECK_SYSTEM_PROMPT = """You are comparing key findings from OSINT investigations.

Your task is to determine if two sets of investigation findings are substantially similar
(indicating redundant work) or sufficiently different (indicating progress).

SIMILARITY CRITERIA:
- HIGH SIMILARITY (0.8-1.0): Same locations, same evidence, minor rewording
- MEDIUM SIMILARITY (0.4-0.7): Overlapping locations but some new evidence or refinement
- LOW SIMILARITY (0.0-0.3): Different locations, new evidence types, significant progress

OUTPUT FORMAT:
Return a JSON object:
{
    "similarity_score": 0.85,
    "is_redundant": true,
    "reasoning": "Both findings identify the same restaurant with the same address. "
                 "No meaningful progress."
}

GUIDELINES:
- Focus on substantive differences in location precision or evidence
- Geographic refinement (country → city → street) counts as progress
- New evidence types (different tools, different sources) count as progress
- Mere rewording of the same finding is redundant
"""


def get_similarity_check_message(existing_key_points: list, new_key_points: list) -> str:
    """Generate message for similarity comparison.

    Args:
        existing_key_points: Previously saved key points from database.
        new_key_points: Newly generated key points to compare.

    Returns:
        Formatted comparison message.
    """
    message = """SIMILARITY CHECK REQUEST

EXISTING KEY POINTS:
"""
    for i, point in enumerate(existing_key_points, 1):
        message += f"{i}. [{point.get('category', 'unknown')}] {point.get('finding', '')} "
        message += f"(confidence: {point.get('confidence', 'unknown')})\n"

    message += "\nNEW KEY POINTS:\n"
    for i, point in enumerate(new_key_points, 1):
        message += f"{i}. [{point.get('category', 'unknown')}] {point.get('finding', '')} "
        message += f"(confidence: {point.get('confidence', 'unknown')})\n"

    message += "\nAre these findings substantially similar or do they show meaningful progress?"

    return message
