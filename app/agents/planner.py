"""Planner agent"""
import json
import logging
from typing import Any, Dict
from anthropic import Anthropic
from app.data.maindb import InvestigationDB
from app.utils.claude_to_json import extract_json_from_response

logger = logging.getLogger(__name__)



class PlannerAgent:
    """Planner agent that builds investigation plans based on current system state.
    
    - Iteration 0: Runs initial planning passes to create comprehensive plan
    - Iteration >0: Runs refinement passes based on findings
    """

    def __init__(self, client: Anthropic, db: InvestigationDB,model: str = "claude-opus-4-6"):
        """Initialize planner agent.
        
        Args:
            client: Anthropic API client.
            model: Model name to use for planning.
            db: Investigation system database with current state and findings.
        """
        self.client = client
        self.model = model
        self.db = db

    def plan(
        self,
        iteration: int = 0,
    ) -> Dict[str, Any]:
        """Generate or refine an investigation plan using multi-pass approach.
        
        Args:
            iteration: Current iteration (0 for initial, >0 for refinement).
        Returns:
            Dict with 'state' (general context) and 'next_steps' (list of steps).
        """

        logger.info("Planning for iteration %d", iteration)
        
        if iteration == 0:
            return self._plan_iteration_zero(self.db)
        else:
            return self._plan_iteration_n(self.db, iteration)



    def _plan_iteration_zero(self, investigation_db: InvestigationDB) -> Dict[str, Any]:
        """Generate initial investigation plan based on extracted text and metadata.

        Args:
            investigation_db: Database containing initial text and metadata.

        Returns:
            Dict with 'state' (general context) and 'next_steps' (list of steps).
        """
        initial_text = investigation_db.get_initial_text()
        metadata = investigation_db.get_metadata()

        system_prompt = """You are an expert investigation planner working with an advanced OSINT agent and professional geoguesser player (the Detective Agent).

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

        user_message = f"""Create an investigation plan based on the following information:

INITIAL TEXT EXTRACTION:
{initial_text}

METADATA:
{json.dumps(metadata or "NO METADATA", indent=2)}

Analyze the completeness of this information and structure a detailed investigation plan for the Detective Agent. Focus on what needs to be investigated to identify the location or subject."""

        logger.info("Generating initial investigation plan")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        # Extract the response text
        response_text = response.content[0].text

        # Parse JSON from response
        plan = self._extract_json_from_response(response_text)

        logger.info("Initial plan generated with %d steps", len(plan.get("next_steps", [])))

        return plan


    def _plan_iteration_n(self, investigation_db: InvestigationDB, iteration: int) -> Dict[str, Any]:
        """Refine investigation plan based on findings from previous iterations.

        Args:
            investigation_db: Database with accumulated investigation data.
            iteration: Current iteration number.

        Returns:
            Dict with 'state' (general context) and 'next_steps' (list of steps).
        """
        initial_text = investigation_db.get_initial_text()
        metadata = investigation_db.get_metadata()
        wrongs = investigation_db.get_wrongs()
        context = investigation_db.get_context()
        validated_searches = investigation_db.get_validated_searches()

        system_prompt = """You are an expert investigation planner working with an advanced OSINT agent and professional geoguesser player (the Detective Agent).

You are refining an ongoing investigation. Review what has been tried, what worked, what didn't, and what new information has been discovered. Then create the next phase of the investigation plan.

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
- What has already been validated or disproven
- What new leads have emerged
- What angles haven't been explored yet
- What information would help narrow down the possibilities"""

        user_message = f"""Refine the investigation plan based on accumulated findings (Iteration {iteration}):

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

        logger.info("Generating refinement plan for iteration %d", iteration)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        # Extract the response text
        response_text = response.content[0].text

        # Parse JSON from response
        plan = self._extract_json_from_response(response_text)

        logger.info("Refinement plan generated with %d steps", len(plan.get("next_steps", [])))

        return plan





