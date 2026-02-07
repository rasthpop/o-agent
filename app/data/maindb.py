from typing import Any, Dict, List, Optional


class InvestigationDB:
    """Dict-like database for investigation state and history.
    
    Stores investigation artifacts including initial photo, text extraction,
    user corrections, context hints, and validated search results.
    """

    def __init__(
        self,
        initial_photo: str,
        initial_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize investigation database.
        
        Args:
            initial_photo: Path or ID of the initial investigation photo.
            initial_text: Extracted text from image_to_text function.
            metadata: Optional metadata dict (e.g., source, tags, investigation_id).
        """
        self.initial_photo = initial_photo
        self.initial_text = initial_text
        self.metadata = metadata or {}
        self.wrongs: List[Dict[str, Any]] = []
        self.context: List[str] = []
        self.history_of_validated_searches: List[Dict[str, Any]] = []

    # ========== Dict-like Interface ==========

    def __getitem__(self, key: str) -> Any:
        """Access fields via dict-like syntax: db["initial_photo"]"""
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set fields via dict-like syntax: db["wrongs"] = [...]"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Unknown field: {key}")

    def __contains__(self, key: str) -> bool:
        """Check field existence: "wrongs" in db"""
        return hasattr(self, key)

    def __repr__(self) -> str:
        return (
            f"InvestigationDB(photo={self.initial_photo!r}, "
            f"text_len={len(self.initial_text)}, "
            f"wrongs={len(self.wrongs)}, "
            f"context={len(self.context)}, "
            f"validated_searches={len(self.history_of_validated_searches)})"
        )

    def keys(self) -> List[str]:
        """Return list of field names."""
        return [
            "initial_photo",
            "initial_text",
            "metadata",
            "wrongs",
            "context",
            "history_of_validated_searches",
        ]

    def values(self) -> List[Any]:
        """Return list of field values."""
        return [getattr(self, key) for key in self.keys()]

    def items(self) -> List[tuple[str, Any]]:
        """Return list of (key, value) tuples."""
        return [(key, getattr(self, key)) for key in self.keys()]

    def get(self, key: str, default: Any = None) -> Any:
        """Safely get field with default fallback."""
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict."""
        return {key: getattr(self, key) for key in self.keys()}

    # ========== Mutators ==========

    def add_wrong(self, wrong_entry: Dict[str, Any]) -> None:
        """Add a user-corrected wrong guess.
        
        Args:
            wrong_entry: Dict with wrong guess data (e.g., {"guess": "...", "correction": "..."}).
        """
        self.wrongs.append(wrong_entry)

    def add_context(self, hint: str) -> None:
        """Add a user-provided textual context hint.
        
        Args:
            hint: String hint or contextual information.
        """
        self.context.append(hint)

    def add_validated_search(self, search_result: Dict[str, Any]) -> None:
        """Add a validated search result from the validator agent.
        
        Args:
            search_result: Dict with validated search data from detective/validator.
        """
        self.history_of_validated_searches.append(search_result)

    # ========== Accessors ==========

    def get_wrongs(self) -> List[Dict[str, Any]]:
        """Get all recorded wrongs."""
        return self.wrongs

    def get_context(self) -> List[str]:
        """Get all user context hints."""
        return self.context

    def get_validated_searches(self) -> List[Dict[str, Any]]:
        """Get all validated search results."""
        return self.history_of_validated_searches

    def get_initial_text(self) -> str:
        """Get initial extracted text."""
        return self.initial_text

    def get_initial_photo(self) -> str:
        """Get initial photo path/ID."""
        return self.initial_photo

    def get_metadata(self) -> Dict[str, Any]:
        """Get investigation metadata."""
        return self.metadata
