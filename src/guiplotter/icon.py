"""Generates the application icon artwork used by the desktop bundles."""
from __future__ import annotations

import math
from pathlib import Path
from typing import List

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

# Sizes macOS expects inside an .iconset directory, as (pixels, filename) pairs.
ICONSET_SIZES = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

_BACKGROUND = "#1f2933"
_GRID = "#3e4c59"
_LEFT_SERIES = "#4c9aff"
_RIGHT_SERIES = "#ff8f5c"


def _series(count: int, phase: float, decay: float) -> List[float]:
    """Returns a smooth decaying wave so the icon reads as a line plot."""

    return [math.exp(-decay * i / count) * math.sin(phase + 3.4 * i / count) for i in range(count)]


def render_png(path: Path, size: int) -> Path:
    """Renders a square icon of ``size`` pixels to ``path``."""

    figure = Figure(figsize=(1, 1), dpi=size)
    # Attach Agg directly so rendering never depends on the interactive backend.
    FigureCanvasAgg(figure)
    figure.patch.set_alpha(0.0)
    canvas_axes = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    canvas_axes.set_axis_off()
    canvas_axes.set_xlim(0, 1)
    canvas_axes.set_ylim(0, 1)

    # A rounded plate keeps the icon on-brand with other macOS app icons.
    canvas_axes.add_patch(
        FancyBboxPatch(
            (0.06, 0.06),
            0.88,
            0.88,
            boxstyle="round,pad=0,rounding_size=0.20",
            linewidth=0,
            facecolor=_BACKGROUND,
        )
    )

    plot_axes = figure.add_axes((0.20, 0.22, 0.60, 0.52))
    plot_axes.set_facecolor("none")
    for spine in ("top", "right"):
        plot_axes.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        plot_axes.spines[spine].set_color(_GRID)
        plot_axes.spines[spine].set_linewidth(size / 220)
    plot_axes.set_xticks([])
    plot_axes.set_yticks([])

    points = 96
    line_width = max(size / 90, 0.8)
    plot_axes.plot(_series(points, 0.0, 0.9), color=_LEFT_SERIES, linewidth=line_width)
    plot_axes.plot(_series(points, 2.1, 0.4), color=_RIGHT_SERIES, linewidth=line_width)
    plot_axes.margins(x=0.02, y=0.12)

    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, transparent=True, dpi=size)
    return path


def render_iconset(directory: Path) -> Path:
    """Renders every size macOS needs into an ``.iconset`` directory."""

    directory.mkdir(parents=True, exist_ok=True)
    for size, name in ICONSET_SIZES:
        render_png(directory / name, size)
    return directory


__all__ = ["ICONSET_SIZES", "render_iconset", "render_png"]
