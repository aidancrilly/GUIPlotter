"""Utilities for parsing supported data sources."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .data_models import DataSet


class DataLoaderError(RuntimeError):
    """Raised when dataset parsing fails."""


class SpaceDelimitedLoader:
    """Reads columnar files with a whitespace delimiter and header line."""

    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def load(self, files: Iterable[str | Path]) -> List[DataSet]:
        datasets: List[DataSet] = []
        for file in files:
            path = Path(file).expanduser().resolve()
            if not path.exists():
                raise DataLoaderError(f"File not found: {path}")
            try:
                df = pd.read_csv(
                    path,
                    sep=r"\s+",
                    engine="python",
                    encoding=self.encoding,
                    comment="#",
                )
            except Exception as exc:  # pragma: no cover - passthrough error message
                raise DataLoaderError(f"Failed to parse {path}: {exc}") from exc

            if df.empty:
                raise DataLoaderError(f"File {path} contains no data")

            datasets.append(DataSet(path=path, columns=df.columns.tolist(), data=df))
        return datasets


__all__ = ["SpaceDelimitedLoader", "DataLoaderError"]
