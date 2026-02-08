from typing import Any

from app.data.maindb import InvestigationDB
from app.tools.base_tool import BaseTool, ToolResult


class MainDBTool(BaseTool):
    """Tool for detective agents to read from the investigation database.

    Provides read-only access to investigation state including text extraction,
    user corrections, context hints, and validated search results.
    Database modifications are handled by validator or user outside this tool.
    """

    def __init__(self, db: InvestigationDB):
        """Initialize the MainDB tool with a database instance.

        Args:
            db: The InvestigationDB instance to interact with.
        """
        self.db = db

    def get_name(self) -> str:
        """Returns the tool name."""
        return "maindb"

    def get_description(self) -> str:
        """Returns what the tool does."""
        return (
            "Interact with the investigation database. Supports operations: "
            "'get_state' (retrieve investigation state, including initial textual "
            "description from image to text, metadata, wrongs, context, and validated "
            "searches), 'get_field' (retrieve specific field), 'to_dict' (get full "
            "database as dictionary). Available fields: initial_photo, initial_text, "
            "metadata, wrongs, context, history_of_validated_searches, summaries."
        )

    def get_parameters(self) -> dict[str, Any]:
        """Returns the parameter schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "get_state",
                        "get_field",
                        "to_dict",
                    ],
                    "description": "The read-only database operation to perform",
                },
                "field": {
                    "type": "string",
                    "description": (
                        "Field name for get_field action (e.g., 'initial_text', "
                        "'wrongs', 'context', 'metadata', 'initial_photo', "
                        "'history_of_validated_searches', 'summaries')"
                    ),
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs) -> ToolResult:
        """Executes the read-only database operation with given parameters.

        Args:
            action: The operation to perform (get_state, get_field, to_dict)
            field: Field name (for get_field action)

        Returns:
            ToolResult with operation results or error details.
        """
        action = kwargs.get("action")

        try:
            if action == "get_state":
                initial_text, metadata, wrongs, context, validated_searches = (
                    self.db.get_state_snapshot()
                )
                return ToolResult(
                    success=True,
                    data={
                        "initial_text": initial_text,
                        "metadata": metadata,
                        "wrongs": wrongs,
                        "context": context,
                        "validated_searches": validated_searches,
                    },
                    metadata={"action": "get_state"},
                )

            elif action == "get_field":
                field = kwargs.get("field")
                if not field:
                    return ToolResult(
                        success=False,
                        error="'field' parameter is required for get_field action",
                    )

                valid_fields = self.db.keys()
                if field not in valid_fields:
                    return ToolResult(
                        success=False,
                        error=f"Unknown field '{field}'. Valid fields: {', '.join(valid_fields)}",
                    )

                value = self.db.get(field)
                return ToolResult(
                    success=True,
                    data={field: value},
                    metadata={"action": "get_field", "field": field},
                )

            elif action == "to_dict":
                return ToolResult(
                    success=True,
                    data=self.db.to_dict(),
                    metadata={"action": "to_dict"},
                )

            else:
                return ToolResult(
                    success=False,
                    error=(
                        f"Unknown action '{action}'. Valid actions: get_state, get_field, to_dict"
                    ),
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Database operation failed: {str(e)}",
                metadata={"action": action, "exception_type": type(e).__name__},
            )
