"""ZEA core configuration."""
from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field


class ZEAConfig(BaseModel):
    """Global ZEA configuration."""

    output_dir: Path = Field(default=Path(".zea"), description="Output directory for artifacts")
    verbose: bool = False
    max_file_size_kb: int = 512  # Skip files larger than this
    exclude_dirs: list[str] = Field(
        default_factory=lambda: [
            ".git", ".hg", ".svn",
            "node_modules", "__pycache__", ".venv", "venv", "env",
            ".tox", "dist", "build", ".eggs", "*.egg-info",
            ".mypy_cache", ".ruff_cache", ".pytest_cache",
            "coverage", ".coverage",
        ]
    )

    def output_path(self, filename: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / filename
