"""Algorithm Adapter - abstract base class for all algorithm wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.models import AlgorithmMetadata


class AlgorithmAdapter(ABC):
    """Abstract base class that every algorithm adapter must inherit.

    Subclasses implement :meth:`execute` to perform the actual computation
    and should override :meth:`validate_input` and :meth:`health_check` as
    appropriate.
    """

    def __init__(self) -> None:
        self._metadata: AlgorithmMetadata | None = None

    @abstractmethod
    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run the algorithm with the given *params* and return results."""

    def validate_input(self, params: dict[str, Any]) -> bool:
        """Validate *params* against the expected input schema.

        Default implementation checks that required keys (from
        ``input_schema.required``) are present.
        """
        if self._metadata and self._metadata.input_schema:
            required = self._metadata.input_schema.get("required", [])
            return all(k in params for k in required)
        return True

    def health_check(self) -> bool:
        """Return ``True`` if the algorithm is ready to execute."""
        return True

    def get_metadata(self) -> AlgorithmMetadata:
        """Return the algorithm metadata."""
        if self._metadata is None:
            raise RuntimeError("Metadata has not been set for this adapter")
        return self._metadata

    def set_metadata(self, metadata: AlgorithmMetadata) -> None:
        """Attach metadata to this adapter instance."""
        self._metadata = metadata
