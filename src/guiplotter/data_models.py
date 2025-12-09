"""Data models for GUIPlotter."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class DataSet:
    """Represents a loaded dataset with associated metadata."""

    path: Path
    columns: Sequence[str]
    data: "pd.DataFrame"

    @property
    def name(self) -> str:
        return self.path.stem


@dataclass(slots=True)
class SeriesSelection:
    """Tracks a user-selected series for plotting."""

    dataset_index: int
    column: str
    axis: str  # "left" or "right"
    label: str
    color: str | None = None


__all__ = ["DataSet", "SeriesSelection"]
