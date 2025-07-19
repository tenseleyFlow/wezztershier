# :::
# :::: CLI :: command line interface ::::
# ::::: ::::::::::::::::::::::::::::: :::::
#
# Main entry point for the wezztershier console script.
# Handles argument parsing and application bootstrapping.
#
# :::
# :::: TODOs ::::
# :::::::::::::::::
#
#   TODO: add --config flag for alternate config paths
#   TODO: add --dry-run mode for testing
#   TODO: add --list-widgets to show available widget types
#
# Author: @espadonne (mfw)
# ::::

import sys
import argparse
import logging
from typing import Optional

from . import __version__


# :::
# sets up logging for debug mode
# with our custom format
# ::::
def setup_debug_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(levelname)s] %(name)s :: %(message)s',
        stream=sys.stderr
    )
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     also enable Qt debug output when debugging
    # ::::
    import os
    os.environ['QT_DEBUG_PLUGINS'] = '1'


# :::
# parse command line arguments
# and return the namespace
# ::::
def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='wezztershier',
        description='Dynamic GUI configurator for WezTerm visuals',
        epilog='Built with love for terminal aesthetics'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help='Path to WezTerm config file (default: $XDG_CONFIG_HOME/wezterm/wezterm.lua)'
    )
    
    parser.add_argument(
        '--backup-dir',
        type=str,
        metavar='PATH', 
        help='Directory for config backups (default: ~/.local/share/wezztershier/backups)'
    )
    
    return parser.parse_args(args)


# :::
# main entry point that bootstraps
# the Qt application
# ::::
def main(args: Optional[list[str]] = None) -> None:
    parsed_args = parse_args(args)
    
    if parsed_args.debug:
        setup_debug_logging()
        logging.debug("Debug mode enabled")
        logging.debug(f"Args: {parsed_args}")
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     Qt app initialization must happen
    # :::::     before importing any Qt widgets
    # ::::
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # :::
    # now we can import and create our window
    # ::::
    from .gui.main_window import Wezztershier
    
    window = Wezztershier(
        config_path=parsed_args.config,
        backup_dir=parsed_args.backup_dir,
        debug_mode=parsed_args.debug
    )
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()