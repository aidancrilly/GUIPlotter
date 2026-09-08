"""GUIPlotter package initialization."""

from importlib.metadata import PackageNotFoundError, version

from .entrypoints import space_delimited_main

try:
    __version__ = version("guiplotter")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0.dev0"

__all__ = ["__version__", "space_delimited_main"]
