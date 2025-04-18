"""
module entry‑point so one can run

    python -m wezztershier

and get exactly the same behaviour as the `wezztershier` console command.
"""

from .gui import main

if __name__ == "__main__":   # pragma: no cover
    main()