"""Entry points for running the GUI plotter with different loaders."""
from __future__ import annotations

import tkinter as tk

from .data_loader import SpaceDelimitedLoader
from .plot_app import PlotApplication


def space_delimited_main() -> None:
    """Launches the GUI configured for space-delimited column files."""

    root = tk.Tk()
    app = PlotApplication(root, SpaceDelimitedLoader().load)
    app.mainloop()


__all__ = ["space_delimited_main"]
