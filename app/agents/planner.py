import base64
import json
import logging
import re
from typing import Any, Dict

from anthropic import Anthropic

from app.data.maindb import InvestigationDB

logger = logging.getLogger(__name__)


def safe_json_load(raw_text):
    """Safely parse JSON from raw text, handling parse errors gracefully."""
    try:
        return json.loads(raw_text)
    except:
        pass

    # Try extracting JSON from markdown
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return {
        "parse_error": True,
        "raw_response": raw_text
    }


class PlannerAgent:
    """Multi-pass planner that builds investigation plans based on iteration count.
    
    - Iteration 0: Runs initial planning passes to create comprehensive plan
    - Iteration N: Runs refinement passes based on findings
    
    Uses multi-pass architecture to gather different perspectives on the investigation.
    """

    def __init__(self, client: Anthropic, model: str = "claude-opus-4-6"):
        """Initialize planner agent.
        
        Args:
            client: Anthropic API client.
            model: Model name to use for planning.
        """
        self.client = client
        self.model = model

    def plan(
        self,
        investigation_db: InvestigationDB,
        iteration: int = 0,
    ) -> Dict[str, Any]:
        """Generate or refine an investigation plan using multi-pass approach.
        
        Args:
            investigation_db: The investigation database with current state.
            iteration: Current iteration (0 for initial, >0 for refinement).
            
        Returns:
            Plan dict with keys: "status", "plan", "reasoning", "passes", "iteration".
        """
        logger.info("Planning for iteration %d", iteration)
        
        if iteration == 0:
            return self._plan_iteration_zero(investigation_db)
        else:
            return self._plan_iteration_n(investigation_db, iteration)

    def _plan_iteration_zero(self, db: InvestigationDB) -> Dict[str, Any]:
        """Initial planning: Run multiple passes to build comprehensive plan."""
        logger.info("Building initial plan using multi-pass approach")
        
        metadata = db.get_metadata()
        initial_text = db.get_initial_text()

        # ----- PASS 1: INVESTIGATION TYPE & SCOPE -----
        logger.info("Pass 1: Determining investigation type and scope")
        scope_pass = self._run_scope_pass(metadata, initial_text)

        # ----- PASS 2: INVESTIGATION STEPS -----
        logger.info("Pass 2: Building investigation steps")
        steps_pass = self._run_steps_pass(metadata, initial_text, scope_pass)

        # ----- MERGE -----
        result = {
            "status": "planned",
            "iteration": 0,
            "reasoning": scope_pass.get("reasoning", ""),
            "investigation_type": scope_pass.get("investigation_type", "unknown"),
            "plan": steps_pass.get("steps", []),
            "passes": {
                "scope": scope_pass,
                "steps": steps_pass,
            },
            "meta": {
                "planning_warnings": []
            }
        }

        # Safety checks
        if "parse_error" in scope_pass:
            result["meta"]["planning_warnings"].append("Scope pass JSON parse error")

        if "parse_error" in steps_pass:
            result["meta"]["planning_warnings"].append("Steps pass JSON parse error")

        return result

    def _plan_iteration_n(self, db: InvestigationDB, iteration: int) -> Dict[str, Any]:
        """Refinement planning: Run passes based on prior findings."""
        logger.info("Refining plan for iteration %d", iteration)
        
        validated_searches = db.get_validated_searches()
        wrongs = db.get_wrongs()
        context = db.get_context()

        # ----- PASS 1: FINDINGS ANALYSIS -----
        logger.info("Pass 1: Analyzing findings")
        analysis_pass = self._run_analysis_pass(db, iteration, validated_searches, wrongs, context)

        # ----- PASS 2: NEXT STEPS -----
        logger.info("Pass 2: Planning next steps")
        next_steps_pass = self._run_next_steps_pass(db, iteration, validated_searches, wrongs, context, analysis_pass)

        # ----- MERGE -----
        result = {
            "status": "refined",
            "iteration": iteration,
            "reasoning": analysis_pass.get("reasoning", ""),
            "plan": next_steps_pass.get("steps", []),
            "passes": {
                "analysis": analysis_pass,
                "next_steps": next_steps_pass,
            },
            "meta": {
                "planning_warnings": []
            }
        }

        # Safety checks
        if "parse_error" in analysis_pass:
            result["meta"]["planning_warnings"].append("Analysis pass JSON parse error")

        if "parse_error" in next_steps_pass:
            result["meta"]["planning_warnings"].append("Next steps pass JSON parse error")

        return result

    def _run_scope_pass(self, metadata: Dict[str, Any], initial_text: str) -> Dict[str, Any]:
        """Run PASS 1 for iteration 0: Determine investigation type and scope."""
        metadata_json = json.dumps(metadata, indent=2)
        
        prompt = f"""You are an investigation scope analyzer for an OSINT system.

Analyze the following investigation metadata and extracted text to determine the investigation type and scope.

METADATA:
{metadata_json}

EXTRACTED TEXT:
{initial_text}

Determine:
1. What type of investigation is this? (person, company, domain, location, event, etc.)
2. What is the primary target or subject?
3. What are the key attributes to investigate?
4. What is the investigation scope (local, regional, global)?

Return ONLY valid JSON with this structure:
{{
    "investigation_type": "person|company|domain|location|event|other",
    "target": "Primary subject/target",
    "key_attributes": ["attr1", "attr2", "attr3"],
    "scope": "local|regional|global",
    "reasoning": "Brief analysis of the investigation scope"
}}

Return JSON only, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            
            raw = response.content[0].text
            return safe_json_load(raw)
        except Exception as e:
            logger.exception("Error in scope pass: %s", e)
            return {
                "parse_error": True,
                "raw_response": str(e)
            }

    def _run_steps_pass(self, metadata: Dict[str, Any], initial_text: str, scope_pass: Dict[str, Any]) -> Dict[str, Any]:
        """Run PASS 2 for iteration 0: Build investigation steps."""
        metadata_json = json.dumps(metadata, indent=2)
        scope_json = json.dumps(scope_pass, indent=2)
        
        prompt = f"""You are an investigation step planner for an OSINT system.

Based on the investigation scope and metadata, create concrete actionable investigation steps.

INVESTIGATION TYPE & SCOPE:
{scope_json}

METADATA:
{metadata_json}

EXTRACTED TEXT:
{initial_text}

Build a step-by-step investigation plan:
1. Each step should be specific and actionable
2. Steps should be ordered by logical progression
3. Assign priority levels to each step
4. Suggest information sources and tools for each step

Return ONLY valid JSON with this structure:
{{
    "steps": [
        {{
            "order": 1,
            "description": "Specific action to take",
            "priority": "high|medium|low",
            "tools": ["tool1", "tool2"],
            "expected_output": "What to look for"
        }}
    ],
    "reasoning": "Brief explanation of the investigation approach"
}}

Return JSON only, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            
            raw = response.content[0].text
            return safe_json_load(raw)
        except Exception as e:
            logger.exception("Error in steps pass: %s", e)
            return {
                "parse_error": True,
                "raw_response": str(e)
            }

    def _run_analysis_pass(self, db: InvestigationDB, iteration: int, validated_searches: list, wrongs: list, context: list) -> Dict[str, Any]:
        """Run PASS 1 for iteration N: Analyze findings and identify gaps."""
        metadata_json = json.dumps(db.get_metadata(), indent=2)
        searches_json = json.dumps(validated_searches[-5:], indent=2)
        wrongs_json = json.dumps(wrongs, indent=2) if wrongs else "[]"
        context_json = json.dumps(context, indent=2) if context else "[]"
        
        prompt = f"""You are an investigation analyst for an OSINT system.

Analyze the current investigation findings and identify gaps and contradictions.

ITERATION: {iteration}

ORIGINAL METADATA:
{metadata_json}

VALIDATED FINDINGS (last searches):
{searches_json}

USER CORRECTIONS / CONFLICTS:
{wrongs_json}

USER PROVIDED CONTEXT:
{context_json}

Analyze:
1. What information has been confirmed so far?
2. What gaps remain in the investigation?
3. Are there contradictions between findings?
4. Do user corrections indicate a different direction?

Return ONLY valid JSON with this structure:
{{
    "confirmed_information": {{"key": "value"}},
    "remaining_gaps": ["gap1", "gap2", "gap3"],
    "contradictions": ["contradiction1", "contradiction2"],
    "user_feedback_indicates": "Description of direction shift or confirmation",
    "reasoning": "Analysis of current investigation state"
}}

Return JSON only, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            
            raw = response.content[0].text
            return safe_json_load(raw)
        except Exception as e:
            logger.exception("Error in analysis pass: %s", e)
            return {
                "parse_error": True,
                "raw_response": str(e)
            }

    def _run_next_steps_pass(self, db: InvestigationDB, iteration: int, validated_searches: list, wrongs: list, context: list, analysis_pass: Dict[str, Any]) -> Dict[str, Any]:
        """Run PASS 2 for iteration N: Plan next steps based on analysis."""
        metadata_json = json.dumps(db.get_metadata(), indent=2)
        analysis_json = json.dumps(analysis_pass, indent=2)
        
        prompt = f"""You are an investigation step planner for an OSINT system.

Based on the findings analysis, plan the next investigation steps to fill gaps and address contradictions.

ITERATION: {iteration}

ORIGINAL METADATA:
{metadata_json}

ANALYSIS OF FINDINGS:
{analysis_json}

Determine:
1. What are the highest priority gaps to fill?
2. Which contradictions need resolving first?
3. What new investigation angles should be explored?
4. Should we continue investigating or consolidate findings?

Return ONLY valid JSON with this structure:
{{
    "next_steps": [
        {{
            "order": 1,
            "description": "Next action based on findings",
            "priority": "high|medium|low",
            "tools": ["tool1"],
            "expected_output": "What to look for",
            "addresses_gap": "Which gap this step addresses"
        }}
    ],
    "should_continue": true|false,
    "reasoning": "Explanation of next steps strategy"
}}

Return JSON only, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            
            raw = response.content[0].text
            parsed = safe_json_load(raw)
            # Map 'next_steps' to 'steps' for consistency
            if "next_steps" in parsed:
                parsed["steps"] = parsed.pop("next_steps")
            return parsed
        except Exception as e:
            logger.exception("Error in next steps pass: %s", e)
            return {
                "parse_error": True,
                "raw_response": str(e)
            }

    def _refine_plan(self, db: InvestigationDB, iteration: int) -> Dict[str, Any]:
        """Refine plan based on prior findings, wrongs, and user context.
        
        Pulls history of validated searches and user corrections to
        adaptively refine next steps.
        """
        return self._plan_iteration_n(db, iteration)
