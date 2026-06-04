"""Evidence model — all ZEA inferences must cite evidence."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    FILE_PATTERN = "file_pattern"
    DIRECTORY_STRUCTURE = "directory_structure"
    PACKAGE_DEPENDENCY = "package_dependency"
    FILE_CONTENT = "file_content"
    NAMING_CONVENTION = "naming_convention"
    CONFIGURATION = "configuration"
    API_ROUTE = "api_route"
    DATABASE_USAGE = "database_usage"
    EVENT_PUBLICATION = "event_publication"
    IMPORT_STATEMENT = "import_statement"


class Evidence(BaseModel):
    """A single piece of evidence supporting an inference."""

    type: EvidenceType
    description: str
    source: str  # File path or pattern that triggered this evidence
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    details: dict[str, str] = Field(default_factory=dict)


class EvidenceSet(BaseModel):
    """Collection of evidence items with aggregate confidence."""

    items: list[Evidence] = Field(default_factory=list)

    @property
    def confidence(self) -> float:
        if not self.items:
            return 0.0
        return min(1.0, sum(e.confidence for e in self.items) / len(self.items))

    def add(self, evidence: Evidence) -> "EvidenceSet":
        self.items.append(evidence)
        return self

    def merge(self, other: "EvidenceSet") -> "EvidenceSet":
        return EvidenceSet(items=self.items + other.items)
