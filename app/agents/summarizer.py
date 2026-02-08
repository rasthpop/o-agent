"""Summarizer agent for extracting key findings from investigation results."""

import logging
from typing import Any

from anthropic import Anthropic

from app.data.maindb import InvestigationDB
from app.prompts.summarizer import (
    SIMILARITY_CHECK_SYSTEM_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
    get_similarity_check_message,
    get_summarizer_user_message,
)
from app.utils.claude_to_json import extract_json_from_response

logger = logging.getLogger(__name__)


class Summarizer:
    """Summarizer agent that extracts key findings from investigation results.

    Analyzes Detective execution logs and produces structured summaries with key points.
    Includes similarity checking to avoid redundant summaries.
    """

    def __init__(
        self, client: Anthropic, db: InvestigationDB, model: str = "claude-sonnet-4-20250514"
    ):
        """Initialize summarizer agent.

        Args:
            client: Anthropic API client.
            db: Investigation database for accessing previous summaries.
            model: Model name to use for summarization.
        """
        self.client = client
        self.db = db
        self.model = model

    def summarize(
        self, detective_response: dict[str, Any], check_similarity: bool = True
    ) -> dict[str, Any]:
        """Generate summary with key points from detective investigation results.

        Args:
            detective_response: Dict from Detective.investigate_with_plan() containing
                              status, iterations, execution_log, and final_response.
            check_similarity: If True, check similarity with previous summaries and
                            set is_redundant flag.

        Returns:
            Dict with:
                - summary (str): Brief overview of findings
                - key_points (list): Structured key findings
                - next_actions (list): Suggested follow-up actions
                - is_redundant (bool): True if findings are too similar to previous
                - similarity_score (float): Similarity score if check was performed
        """
        logger.info("Generating summary from detective results")

        user_message = get_summarizer_user_message(detective_response)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SUMMARIZER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text
        summary_data = extract_json_from_response(response_text)

        logger.info("Summary generated with %d key points", len(summary_data.get("key_points", [])))

        if check_similarity:
            existing_summaries = self._get_existing_key_points()
            if existing_summaries:
                similarity_result = self._check_similarity(
                    existing_summaries, summary_data.get("key_points", [])
                )
                summary_data["is_redundant"] = similarity_result.get("is_redundant", False)
                summary_data["similarity_score"] = similarity_result.get("similarity_score", 0.0)
                logger.info(
                    "Similarity check: score=%.2f, redundant=%s",
                    summary_data.get("similarity_score", 0.0),
                    summary_data.get("is_redundant", False),
                )
            else:
                summary_data["is_redundant"] = False
                summary_data["similarity_score"] = 0.0
                logger.info("No existing summaries to compare against")
        else:
            summary_data["is_redundant"] = False
            summary_data["similarity_score"] = 0.0

        return summary_data

    def _get_existing_key_points(self) -> list[dict[str, Any]]:
        """Retrieve existing key points from database.

        Returns:
            List of key points from previous summaries, or empty list if none exist.
        """
        try:
            summaries = self.db.get("summaries", [])
            if not summaries:
                return []

            all_key_points = []
            for summary in summaries:
                if isinstance(summary, dict) and "key_points" in summary:
                    all_key_points.extend(summary["key_points"])

            return all_key_points

        except Exception as e:
            logger.warning("Could not retrieve existing summaries: %s", str(e))
            return []

    def _check_similarity(
        self, existing_key_points: list[dict[str, Any]], new_key_points: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Check if new key points are too similar to existing ones.

        Args:
            existing_key_points: Previously saved key points.
            new_key_points: Newly generated key points.
        """
        logger.info(
            "Checking similarity: %d existing vs %d new key points",
            len(existing_key_points),
            len(new_key_points),
        )

        user_message = get_similarity_check_message(existing_key_points, new_key_points)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=SIMILARITY_CHECK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text
        similarity_data = extract_json_from_response(response_text)

        similarity_score = similarity_data.get("similarity_score", 0.0)
        similarity_score = max(0.0, min(1.0, similarity_score))

        is_redundant = similarity_score >= 0.42

        return {
            "similarity_score": similarity_score,
            "is_redundant": is_redundant,
            "reasoning": similarity_data.get("reasoning", ""),
        }
