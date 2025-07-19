# :::
# :::: MODULE ENTRY POINT ::::
# ::::::::::::::::::::::::::::::
#
# Allows running as:
#     python -m wezztershier
#
# With exactly the same behavior as the 
# `wezztershier` console command
#
# Author: @espadonne (mfw)
# ::::

from .cli import main

if __name__ == "__main__":
    main()