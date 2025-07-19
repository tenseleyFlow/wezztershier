# :::
# :::: WEZZTERSHIER :: the clever configurator ::::
# ::::: :::::::::::::::::::::::::::::::::::::: :::::
#
# Package initializer that:
#   * marks src/wezztershier as the main package
#   * handles version discovery 
#   * exports the minimal public API
#
# Author: @espadonne (mfw)
# ::::

# :::
# :::: NOTE: @espadonne (mfw)
# :::::     Version first to avoid circular imports
# :::::     because Python's import system is... special
# ::::
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__: str = version(__name__)
except PackageNotFoundError:
    __version__ = "0.2.0.dev0"

# Now we can import main
from .cli import main

__all__ = ["main", "__version__"]