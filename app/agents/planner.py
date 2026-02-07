"""Planner agent"""
import logging
from typing import Any, Dict
from anthropic import Anthropic
from app.data.maindb import InvestigationDB
from app.utils.claude_to_json import extract_json_from_response
from app.prompts.planner import (
    ZERO_ITERATON_SYSTEM_PROMPT,
    N_ITERATION_SYSTEM_PROMPT,
    get_zero_iteration_user_message,
    get_n_iteration_user_message,
)

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



    def _plan_iteration_zero(self) -> Dict[str, Any]:
        """Generate initial investigation plan based on extracted text and metadata.

        Args:
            investigation_db: Database containing initial text and metadata.

        Returns:
            Dict with 'state' (general context) and 'next_steps' (list of steps).
        """
        initial_text = self.db.get_initial_text()
        metadata = self.db.get_metadata()

        user_message = get_zero_iteration_user_message(initial_text, metadata)

        logger.info("Generating initial investigation plan")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=ZERO_ITERATON_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        response_text = response.content[0].text

        plan = extract_json_from_response(response_text)

        logger.info("Initial plan generated with %d steps", len(plan.get("next_steps", [])))

        return plan


    def _plan_iteration_n(self, iteration: int) -> Dict[str, Any]:
        """Refine investigation plan based on findings from previous iterations.

        Args:
            investigation_db: Database with accumulated investigation data.
            iteration: Current iteration number.

        Returns:
            Dict with 'state' (general context) and 'next_steps' (list of steps).
        """
        state = self.db.get_state_snapshot()
    
        user_message = get_n_iteration_user_message(
            iteration, *state
        )

        logger.info("Generating refinement plan for iteration %d", iteration)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=N_ITERATION_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        response_text = response.content[0].text

        plan = extract_json_from_response(response_text)

        logger.info("Refinement plan generated with %d steps", len(plan.get("next_steps", [])))

        return plan





