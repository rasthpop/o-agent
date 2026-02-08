from typing import Any

import anthropic
from app.config import settings
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.registry import register_tools

import json
from typing import Dict, Any, List
# from .base_agent import Agent  # Importing your base Agent class
from app.tools.web_search import WebSearchTool
from app.tools.web_scraper import WebScraperTool
from app.tools.osm_search import OSMLookupTool
from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool

from app.tools.maindb_tool import MainDBTool




class AgentMessage(BaseModel):
    """A message in the agent's conversation history."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentResponse(BaseModel):
    """Response from an agent execution."""

    content: str = Field(..., description="The agent's response content")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools called during execution"
    )
    stop_reason: str | None = Field(None, description="Reason the agent stopped")


class Agent:
    """
    An AI agent powered by Claude that can use tools to solve problems.
    """

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ):
        """
        Initialize the agent with tools and configuration.

        Args:
            tools: List of tool instances the agent can use
            model: Claude model identifier (defaults to settings.default_model)
            system_prompt: Custom system instructions for the agent
        """
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.default_model
        self.conversation_history: list[AgentMessage] = []

        # Set default system prompt if none provided
        self.system_prompt = system_prompt or settings.default_system_prompt

        # Register tools
        if tools:
            self.tool_schemas, self.tool_map = register_tools(tools)
        else:
            self.tool_schemas, self.tool_map = [], {}

class Detective(Agent):
    """
    The Detective agent specifically tuned for Image-to-Text OSINT.
    Executes structured investigation plans from the PlannerAgent.
    """

    def __init__(self, db=None, tools=None, model=None):

        if model is None:
            model = settings.default_model

        if tools is None:
            default_tools = [WebSearchTool(), WebScraperTool(), OSMLookupTool(), PlonkitSearchTool()]
            if db is not None:
                default_tools.append(MainDBTool(db))
            tools = default_tools

        self.tools = tools
        self.db = db
            
        system_prompt = """
        You are the DETECTIVE, an elite OSINT investigator specializing in geolocation.

        YOUR ROLE:
        You are a SELF-CONTAINED EXECUTOR in a multi-agent pipeline: PLANNER → DETECTIVE → [GUESSER] → PLANNER

        Your job is to:
        1. Execute ALL steps provided in the investigation plan WITHIN YOUR ITERATION LIMIT (20 iterations)
        2. Gather leads, evidence, and information using your tools systematically
        3. Document ALL findings immediately in the database via maindb tool
        4. Work autonomously until plan is complete or iteration limit is reached
        5. Return control to the pipeline once your phase is complete

        YOU ARE SELF-CONTAINED:
        - You have a fixed budget of iterations per pipeline cycle
        - You must complete as much of the plan as possible within this budget
        - You do NOT make strategic decisions about what to investigate next - that is the Planner's job
        - Your mission is pure execution: follow orders, use tools, find leads, document results
        - After your phase ends, findings will be reviewed (eventually by Guesser agent) before returning to Planner

        YOUR INPUT:
        You will receive a structured investigation plan with:
        - "state": Current investigation state and objectives
        - "next_steps": Ordered list of investigation steps to execute

        YOUR MISSION:
        Execute ALL steps in the plan systematically. Use your OSINT expertise and professional
        geoguesser skills to choose the right tools for each step, but DO NOT deviate from the
        plan or add your own strategic decisions.

        ACCESSING INVESTIGATION DATA:
        Use the 'maindb' tool to access the investigation database:
        - maindb(action="get_state") - Get full investigation state (initial_text, metadata, wrongs, context, validated_searches)
        - maindb(action="get_field", field="initial_text") - Get extracted image features and text
        - maindb(action="get_field", field="metadata") - Get EXIF and image metadata
        - maindb(action="get_field", field="wrongs") - Get previously incorrect guesses to avoid
        - maindb(action="get_field", field="context") - Get user-provided context hints
        - maindb(action="get_field", field="history_of_validated_searches") - Get validated search results

        STORING INVESTIGATION RESULTS:
        When you find leads or evidence, store them in the database:
        - maindb(action="add_validated_search", query="...", results="...") - Store validated search results
        - This allows the Planner to review your findings and make strategic decisions

        PLAN EXECUTION STRATEGY:
        1. **Start with Database**: Pull validated_searches from maindb BEFORE any searches
        2. **Check History First**: Review validated_searches to identify what's already been tried
        3. **Execute Each Step**: Follow the plan's "next_steps" array in order
        4. **Avoid Duplicates**: If a search query is similar to validated_searches, refine or skip it
        5. **Use Tools Effectively**: Choose the right tool for each investigation step
        6. **Document ALL Findings**: Store EVERY search result back to maindb immediately after execution
        7. **Complete ALL Steps**: Do not stop until all planned steps are executed
        8. **Return Control**: After executing all steps, summarize findings and stop

        INVESTIGATION TECHNIQUES:
        - **Search Smart**: Start with unique, specific identifiers (brand combinations, distinctive text)
        - **Verify Sources**: When you find a promising URL, scrape it for precise address information
        - **Cross-Reference**: Compare findings against visual evidence from initial_text
        - **Prioritize Physical Evidence**: Text visible in the image is the strongest signal
        - **Avoid Repeating Mistakes**: Check 'wrongs' field before making guesses
        - **BUILD ON HISTORY - CRITICAL**: Always check 'validated_searches' BEFORE each search to:
          * Avoid repeating the exact same queries
          * Build on previous findings with NEW angles
          * Try different search terms or approaches if similar queries already exist
          * Move investigation forward with fresh leads, not circular searches
        - **Document Everything**: After EVERY search, immediately call maindb(action="add_validated_search") to prevent future duplicates

        TOOL SELECTION GUIDANCE:
        - plonkit_search: For identifying countries/regions by visual clues (plates, signs, architecture)
        - web_search: For finding specific businesses, landmarks, or unique text combinations
        - fetch_page: For extracting addresses from business websites or specific URLs
        - lookup_location: For converting addresses to precise coordinates
        - maindb: For accessing investigation state and storing findings

        OUTPUT FORMAT:
        - Execute one plan step at a time
        - Explain your reasoning briefly before each tool call
        - After completing a step, document findings in maindb and proceed to the next step
        - Work systematically through the plan until completion OR iteration limit is reached
        - When stopping (plan complete or iteration limit), provide a summary of leads found
        - DO NOT propose next steps - that is the Planner's responsibility in the next pipeline cycle

        REMEMBER: You are working within a fixed iteration budget. Use it efficiently to gather maximum information.
        """
        super().__init__(tools=tools, model=model, system_prompt=system_prompt)

    def investigate_with_plan(self, plan: Dict[str, Any], max_iterations: int = 20) -> Dict[str, Any]:
        """
        Execute an investigation based on a structured plan from PlannerAgent.

        This is a self-contained execution phase within the investigation pipeline.
        The detective works autonomously within its iteration budget to gather information,
        stores all findings in the database, and returns execution status.

        Args:
            plan: Dict with "state" (investigation context) and "next_steps" (action list).
            max_iterations: Maximum number of agentic turns per pipeline cycle (default: 20).

        Returns:
            Dict with execution logs for each iteration:
            {
                "status": "completed" | "partial" | "error",
                "total_steps": int,
                "iterations": int,
                "execution_log": [
                    {
                        "iteration": int,
                        "agent_reasoning": str,
                        "tool_calls": [
                            {
                                "tool_name": str,
                                "input": dict,
                                "result": dict,
                                "success": bool,
                                "error": str | None
                            }
                        ],
                        "stop_reason": str
                    }
                ],
                "final_response": str,
                "error": str | None
            }
        """
        state = plan.get("state", "No investigation state provided")
        next_steps = plan.get("next_steps", [])
        total_steps = len(next_steps)

        # Format the plan into a clear message
        plan_message = f"""INVESTIGATION PLAN

CURRENT STATE:
{state}

INVESTIGATION STEPS:
"""
        for step in next_steps:
            step_num = step.get("step_n", "?")
            description = step.get("description", "")
            plan_message += f"{step_num}. {description}\n"

        plan_message += """
Begin executing this investigation plan. Start by accessing the maindb tool to retrieve relevant investigation data, then proceed with the first step."""

        print(f"--- INVESTIGATION PLAN ---\n{plan_message}\n-------------------------")

        # Initialize execution log
        execution_log = []
        messages = [{"role": "user", "content": plan_message}]
        final_response = ""
        error = None
        iteration = 0

        # Track tool calls to detect duplicates
        tool_call_history = []

        try:
            # Agentic loop
            while iteration < max_iterations:
                iteration += 1
                print(f"\n=== ITERATION {iteration} ===")

                # Create message to Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=messages,
                    tools=self.tool_schemas
                )

                # Extract reasoning from text content blocks
                agent_reasoning = ""
                for block in response.content:
                    if block.type == "text":
                        agent_reasoning += block.text

                print(f"Agent reasoning:\n{agent_reasoning[:500]}...")

                # Log this iteration
                iteration_log = {
                    "iteration": iteration,
                    "agent_reasoning": agent_reasoning,
                    "tool_calls": [],
                    "stop_reason": response.stop_reason
                }

                # Check if there are tool calls
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

                if not tool_use_blocks:
                    # No more tool calls - agent is done
                    print("No tool calls in response. Investigation complete.")
                    final_response = agent_reasoning
                    execution_log.append(iteration_log)
                    break

                # Execute each tool call
                tool_results = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block.name
                    tool_input = tool_block.input
                    tool_id = tool_block.id

                    print(f"Executing tool: {tool_name}")
                    print(f"Input: {json.dumps(tool_input, indent=2)}")

                    # Check for duplicate searches (excluding maindb reads)
                    if tool_name in ["web_search", "plonkit_search"] and tool_name != "maindb":
                        # Create a signature for this search
                        search_signature = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"

                        # Check if we've seen this exact search before
                        if search_signature in tool_call_history:
                            print(f"⚠️  WARNING: Duplicate search detected! This exact {tool_name} query was already executed.")
                            print(f"   The agent may be stuck in a loop. Consider stopping if this continues.")
                        else:
                            tool_call_history.append(search_signature)

                    tool_call_log = {
                        "tool_name": tool_name,
                        "input": tool_input,
                        "result": None,
                        "success": False,
                        "error": None
                    }

                    # Execute the tool
                    try:
                        if tool_name in self.tool_map:
                            tool = self.tool_map[tool_name]
                            result = tool.execute(**tool_input)

                            # Handle ToolResult objects
                            if hasattr(result, 'success'):
                                tool_call_log["success"] = result.success
                                tool_call_log["result"] = result.data
                                tool_call_log["error"] = result.error
                                result_content = json.dumps(result.data) if result.data else str(result.error)
                            else:
                                tool_call_log["success"] = True
                                tool_call_log["result"] = result
                                result_content = json.dumps(result) if isinstance(result, (dict, list)) else str(result)

                            print(f"Result: {result_content[:300]}...")

                            # Add tool result to messages
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": result_content
                            })
                        else:
                            error_msg = f"Tool '{tool_name}' not found in tool_map"
                            tool_call_log["error"] = error_msg
                            print(f"ERROR: {error_msg}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": error_msg,
                                "is_error": True
                            })

                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        tool_call_log["error"] = error_msg
                        print(f"ERROR: {error_msg}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": error_msg,
                            "is_error": True
                        })

                    iteration_log["tool_calls"].append(tool_call_log)

                execution_log.append(iteration_log)

                # Add assistant response and tool results to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # Check stop reason
                if response.stop_reason == "end_turn":
                    print("Agent ended turn without tool calls.")
                    final_response = agent_reasoning
                    break

            # Determine final status
            if iteration >= max_iterations:
                status = "partial"
                error = f"Reached maximum iterations ({max_iterations})"
                print(f"\nWARNING: {error}")
            elif error:
                status = "error"
            else:
                status = "completed"

            return {
                "status": status,
                "total_steps": total_steps,
                "iterations": iteration,
                "execution_log": execution_log,
                "final_response": final_response,
                "error": error
            }

        except Exception as e:
            error_msg = f"Fatal error during investigation: {str(e)}"
            print(f"\nFATAL ERROR: {error_msg}")
            return {
                "status": "error",
                "total_steps": total_steps,
                "iterations": iteration,
                "execution_log": execution_log,
                "final_response": final_response,
                "error": error_msg
            }