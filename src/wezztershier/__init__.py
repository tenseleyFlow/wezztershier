"""
wezztershier package initialiser.
  * marks this directory as an importable package.
  * re‑exports main() so the console‑script stub can just do
          `import wezztershier; wezztershier.main()`
  * __version__ for --version flags, crash "reports", etc.
"""

from .gui import main
__all__ = ["main", "__version__"]

try:
    from importlib.metadata import version, PackageNotFoundError
    __version__: str = version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"