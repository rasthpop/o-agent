"""Orchestrates investigations with progress tracking for web interface."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel

from app.agents.detective import Detective
from app.agents.planner import PlannerAgent
from app.agents.summarizer import Summarizer
from app.config import settings
from app.data.maindb import InvestigationDB
from app.tools.image_to_text.image_to_text import extract_json_description_and_metadata
from app.tools.maindb_tool import MainDBTool
from app.tools.osm_search import OSMLookupTool
from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool
from app.tools.web_scraper import WebScraperTool
from app.tools.web_search import WebSearchTool


class ProgressUpdate(BaseModel):
    """Model for progress updates sent to web frontend."""

    phase: str  # "extracting", "planning", "investigating", "summarizing", "complete"
    message: str  # Human-readable progress message
    details: dict[str, Any] | None = None  # Optional additional data
    current_lead: str | None = None  # Short lead summary (e.g., "Currently considering Bosnia")
    terminal_output: str | None = None  # Terminal log line to display
    complete: bool = False  # Whether investigation is finished


class InvestigationRunner:
    """
    Runs investigations with progress tracking for the web interface.

    Wraps the existing investigation pipeline (extract → plan → investigate → summarize)
    and emits progress updates via an async queue.
    """

    def __init__(self, image_path: str):
        """
        Initialize investigation runner.

        Args:
            image_path: Path to image file to investigate
        """
        self.image_path = image_path
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.progress_queue: asyncio.Queue[ProgressUpdate] = asyncio.Queue()
        self.db: InvestigationDB | None = None
        self.final_summary: dict[str, Any] | None = None

    async def emit_progress(self, update: ProgressUpdate) -> None:
        """
        Emit a progress update to the queue.

        Args:
            update: Progress update to emit
        """
        await self.progress_queue.put(update)

    async def progress_stream(self) -> AsyncIterator[ProgressUpdate]:
        """
        Async generator yielding progress updates.

        Yields:
            ProgressUpdate objects as they become available
        """
        while True:
            update = await self.progress_queue.get()
            yield update
            if update.complete:
                break

    async def run(self) -> dict[str, Any]:
        """
        Run the full investigation pipeline with progress updates.

        Returns:
            Final summary dict from the investigation
        """
        try:
            # Phase 1: Extract features from image
            await self.emit_progress(
                ProgressUpdate(
                    phase="extracting",
                    message="Extracting features from image using vision API...",
                    terminal_output=f"[EXTRACT] Loading image: {self.image_path}",
                )
            )

            await self.emit_progress(
                ProgressUpdate(
                    phase="extracting",
                    message="Extracting features from image using vision API...",
                    terminal_output="[EXTRACT] Running vision API (text pass)...",
                )
            )

            features, _, metadata = await asyncio.to_thread(
                extract_json_description_and_metadata, self.image_path
            )

            # Count features across all categories
            feature_count = sum(
                len(features.get(category, {})) if isinstance(features.get(category), dict) else 0
                for category in ["textual_features", "architecture_features", "infrastructure_features"]
            )

            await self.emit_progress(
                ProgressUpdate(
                    phase="extracting",
                    message="Image analysis complete",
                    details={"features_found": feature_count},
                    terminal_output=f"[EXTRACT] ✓ Extracted {feature_count} features from image",
                )
            )

            # Initialize database
            self.db = InvestigationDB(
                initial_photo=self.image_path, initial_text=features, metadata=metadata
            )

            # Initialize agents
            planner = PlannerAgent(self.client, self.db, model=settings.default_model)
            detective = Detective(
                db=self.db,
                tools=[
                    MainDBTool(self.db),
                    WebSearchTool(),
                    WebScraperTool(),
                    OSMLookupTool(),
                    PlonkitSearchTool(),
                ],
            )
            summarizer = Summarizer(self.client, self.db, model=settings.default_model)

            # Investigation loop
            max_outer_loops = 5
            investigation_complete = False
            outer_iteration = 0

            while not investigation_complete and outer_iteration < max_outer_loops:
                outer_iteration += 1

                # Phase 2: Planning
                await self.emit_progress(
                    ProgressUpdate(
                        phase="planning",
                        message=(
                            f"Planning investigation strategy "
                            f"(cycle {outer_iteration}/{max_outer_loops})..."
                        ),
                        terminal_output=f"[PLAN] Starting investigation cycle {outer_iteration}/{max_outer_loops}",
                    )
                )

                planner_response = await asyncio.to_thread(
                    planner.plan, iteration=outer_iteration - 1
                )

                if not planner_response.get("next_steps"):
                    await self.emit_progress(
                        ProgressUpdate(
                            phase="planning",
                            message="No more steps needed",
                            terminal_output="[PLAN] No additional steps required - investigation complete",
                        )
                    )
                    investigation_complete = True
                    break

                steps_count = len(planner_response.get("next_steps", []))
                await self.emit_progress(
                    ProgressUpdate(
                        phase="planning",
                        message=f"Plan created with {steps_count} investigation steps",
                        terminal_output=f"[PLAN] ✓ Generated plan with {steps_count} steps",
                    )
                )

                # Log individual steps
                for i, step in enumerate(planner_response.get("next_steps", [])[:3], 1):
                    step_preview = step[:80] + "..." if len(step) > 80 else step
                    await self.emit_progress(
                        ProgressUpdate(
                            phase="planning",
                            message=f"Plan created with {steps_count} investigation steps",
                            terminal_output=f"[PLAN]   Step {i}: {step_preview}",
                        )
                    )

                # Phase 3: Investigation (Detective with tool tracking)
                await self.emit_progress(
                    ProgressUpdate(
                        phase="investigating",
                        message="Executing investigation plan...",
                        terminal_output="[DETECTIVE] Starting investigation execution",
                    )
                )

                detective_response = await self._run_detective_with_progress(
                    detective, planner_response
                )

                await self.emit_progress(
                    ProgressUpdate(
                        phase="investigating",
                        message="Investigation execution complete",
                        terminal_output="[DETECTIVE] ✓ Investigation complete",
                    )
                )

                # Phase 4: Summarization
                await self.emit_progress(
                    ProgressUpdate(
                        phase="summarizing",
                        message="Analyzing findings and extracting key insights...",
                        terminal_output="[SUMMARIZE] Extracting key findings from investigation",
                    )
                )

                summary = await asyncio.to_thread(
                    summarizer.summarize, detective_response, check_similarity=True
                )

                # Extract current lead from summary
                current_lead = self._extract_lead_from_summary(summary)

                key_points_count = len(summary.get("key_points", []))
                await self.emit_progress(
                    ProgressUpdate(
                        phase="summarizing",
                        message="Summary generated",
                        current_lead=current_lead,
                        details={
                            "key_points": key_points_count,
                            "is_redundant": summary.get("is_redundant", False),
                        },
                        terminal_output=f"[SUMMARIZE] ✓ Found {key_points_count} key points",
                    )
                )

                # Check for convergence
                if summary.get("is_redundant", False):
                    await self.emit_progress(
                        ProgressUpdate(
                            phase="summarizing",
                            message="Findings converged - investigation complete",
                            terminal_output="[SUMMARIZE] Findings converged with previous cycle - stopping",
                        )
                    )
                    investigation_complete = True
                    self.final_summary = summary
                    self.db.add_summary(summary)
                    break

                await self.emit_progress(
                    ProgressUpdate(
                        phase="summarizing",
                        message="Summary saved to database",
                        terminal_output="[SUMMARIZE] Summary saved - preparing next cycle",
                    )
                )

                self.db.add_summary(summary)
                self.final_summary = summary

            # Phase 5: Complete
            reason = "Findings converged" if investigation_complete else "Maximum cycles reached"
            await self.emit_progress(
                ProgressUpdate(
                    phase="complete",
                    message="Investigation complete",
                    terminal_output=f"[COMPLETE] Investigation finished after {outer_iteration} cycles ({reason})",
                    complete=True,
                    details={
                        "final_summary": self.final_summary,
                        "total_cycles": outer_iteration,
                        "reason": reason,
                    },
                )
            )

            return self.final_summary or {}

        except Exception as e:
            await self.emit_progress(
                ProgressUpdate(
                    phase="error",
                    message=f"Investigation failed: {str(e)}",
                    complete=True,
                    details={"error": str(e)},
                )
            )
            raise

    async def _run_detective_with_progress(
        self, detective: Detective, plan: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Run detective investigation with progress updates.

        Args:
            detective: Detective agent instance
            plan: Investigation plan from PlannerAgent

        Returns:
            Detective execution response
        """
        # Run investigation in thread with 20 max iterations
        result = await asyncio.to_thread(detective.investigate_with_plan, plan, max_iterations=20)

        # Extract tool usage details from execution log
        if result.get("execution_log"):
            iteration_count = len(result["execution_log"])
            await self.emit_progress(
                ProgressUpdate(
                    phase="investigating",
                    message="Processing investigation results",
                    terminal_output=f"[DETECTIVE] Completed {iteration_count} reasoning iterations",
                )
            )

            # Log tool usage from execution log
            for i, log_entry in enumerate(result["execution_log"], 1):
                tool_calls = log_entry.get("tool_calls", [])
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("tool_name", "unknown")
                        tool_display = self._tool_name_to_display(tool_name)
                        await self.emit_progress(
                            ProgressUpdate(
                                phase="investigating",
                                message="Processing investigation results",
                                terminal_output=f"[DETECTIVE]   Iteration {i}: {tool_display}",
                            )
                        )

        return result

    def _tool_name_to_display(self, tool_name: str) -> str:
        """Convert tool name to human-readable display name."""
        displays = {
            "web_search": "web search",
            "plonkit_search": "plonkit database lookup",
            "fetch_page": "web scraper",
            "lookup_location": "OSM location lookup",
            "maindb": "database query",
        }
        return displays.get(tool_name, tool_name)

    def _extract_lead_from_summary(self, summary: dict[str, Any]) -> str | None:
        """
        Extract a short lead sentence from summary key points.

        Args:
            summary: Summary dict from Summarizer

        Returns:
            Short lead string like "Currently considering Bosnia" or None
        """
        key_points = summary.get("key_points", [])
        if not key_points:
            return None

        # Find highest confidence location finding
        location_points = [p for p in key_points if p.get("category") == "location"]

        if location_points:
            # Use highest confidence location
            top_location = max(
                location_points,
                key=lambda p: self._confidence_to_score(p.get("confidence", "low")),
            )
            finding = top_location.get("finding", "")

            # Extract location name (simple heuristic: look for country/city names)
            words = finding.split()
            # Capitalize important words to identify place names
            location = next((w for w in words if w[0].isupper() and len(w) > 3), None)

            if location:
                return f"Currently considering {location}"

        # Fallback to summary text
        summary_text = summary.get("summary", "")
        if summary_text:
            # Take first sentence
            first_sentence = summary_text.split(".")[0]
            if len(first_sentence) < 100:
                return first_sentence

        return "Analyzing findings"

    def _confidence_to_score(self, confidence: str) -> int:
        """Convert confidence string to numeric score."""
        mapping = {"high": 3, "medium": 2, "low": 1}
        return mapping.get(confidence.lower(), 0)
