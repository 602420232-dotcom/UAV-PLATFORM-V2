"""Algorithm Registry - central store for algorithm metadata and classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.models import AlgorithmMetadata


@dataclass
class AlgorithmEntry:
    """Internal entry stored in the registry."""

    algorithm_id: str
    algorithm_class: type
    category: str
    version: str = "1.0.0"
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_metadata(self) -> AlgorithmMetadata:
        """Convert to the public Pydantic model."""
        return AlgorithmMetadata(
            id=self.algorithm_id,
            name=self.algorithm_class.__name__,
            category=self.category,
            version=self.version,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            created_at=self.created_at,
        )


class AlgorithmRegistry:
    """Thread-safe algorithm registry.

    Usage::

        registry = AlgorithmRegistry()
        registry.register(
            algorithm_id="3dvar",
            algorithm_class=ThreeDimensionalVAR,
            category="assimilation",
            version="1.0.0",
            description="3D-VAR data assimilation",
        )
    """

    def __init__(self) -> None:
        self._entries: dict[str, AlgorithmEntry] = {}

    def register(
        self,
        algorithm_id: str,
        algorithm_class: type,
        category: str,
        version: str = "1.0.0",
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> None:
        """Register an algorithm class.

        If an algorithm with the same *algorithm_id* already exists it will
        be overwritten (latest version wins).
        """
        self._entries[algorithm_id] = AlgorithmEntry(
            algorithm_id=algorithm_id,
            algorithm_class=algorithm_class,
            category=category,
            version=version,
            description=description,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
        )

    def get(self, algorithm_id: str) -> type | None:
        """Return the algorithm class for *algorithm_id*, or ``None``."""
        entry = self._entries.get(algorithm_id)
        return entry.algorithm_class if entry else None

    def get_entry(self, algorithm_id: str) -> AlgorithmEntry | None:
        """Return the full :class:`AlgorithmEntry`."""
        return self._entries.get(algorithm_id)

    def list_by_category(self, category: str) -> list[AlgorithmMetadata]:
        """Return metadata for all algorithms in *category*."""
        return [
            e.to_metadata()
            for e in self._entries.values()
            if e.category == category
        ]

    def list_all(self) -> list[AlgorithmMetadata]:
        """Return metadata for every registered algorithm."""
        return [e.to_metadata() for e in self._entries.values()]

    def categories(self) -> list[str]:
        """Return sorted list of unique categories."""
        return sorted({e.category for e in self._entries.values()})

    def list_by_version(self, algorithm_id: str, version: str) -> AlgorithmMetadata | None:
        """Return metadata if the algorithm matches the requested version."""
        entry = self._entries.get(algorithm_id)
        if entry and entry.version == version:
            return entry.to_metadata()
        return None

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, algorithm_id: str) -> bool:
        return algorithm_id in self._entries


# Global singleton
_global_registry = AlgorithmRegistry()


def get_registry() -> AlgorithmRegistry:
    """Return the global algorithm registry singleton."""
    return _global_registry
