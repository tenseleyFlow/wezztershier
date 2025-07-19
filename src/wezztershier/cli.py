# :::
# :::: CLI :: command line interface with diagnostics ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Enhanced CLI that shows widget registration status
# before launching the GUI. Helps debug missing widgets!
#
# Author: @espadonne (mfw)
# ::::

import sys
import argparse
import logging
from typing import Optional
from pathlib import Path

from . import __version__


# :::
# sets up logging for debug mode
# with our custom format
# ::::
def setup_debug_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(name)s :: %(message)s',
        stream=sys.stderr
    )
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     also enable Qt debug output when debugging
    # ::::
    if verbose:
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
        '--check-widgets',
        action='store_true',
        help='Check widget registration and exit'
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
        help='Directory for config backups (default: ~/.local/share/wezttershier/backups)'
    )
    
    parser.add_argument(
        '--test-config',
        action='store_true',
        help='Test config parsing without launching GUI'
    )
    
    return parser.parse_args(args)


# :::
# check widget registration status
# ::::
def check_widgets() -> None:
    """Check and report widget registration status"""
    print("=== Wezztershier Widget Status ===\n")
    
    # Import triggers registration
    from .widgets import WidgetFactory
    
    registered = WidgetFactory.get_registered_types()
    print(f"Total registered widgets: {len(registered)}\n")
    
    # Expected widgets
    expected = {
        'slider': 'Float/Int Slider',
        'int_slider': 'Integer Slider',
        'numerical': 'Numerical Input',
        'text': 'Text Input',
        'select': 'Select Dropdown',
        'theme_select': 'Theme Selector',
        'color_picker': 'Color Picker',
        'color_scheme': 'Color Scheme Picker',
        'font': 'Font Input',
        'font_picker': 'Font Picker',
    }
    
    print("Widget Registration:")
    for ui_type, description in expected.items():
        if ui_type in registered:
            print(f"  ✓ {ui_type:<15} {description}")
        else:
            print(f"  ✗ {ui_type:<15} {description} [MISSING!]")
    
    # Check for unexpected widgets
    unexpected = set(registered) - set(expected.keys())
    if unexpected:
        print(f"\nUnexpected widgets: {', '.join(unexpected)}")


# :::
# test config file parsing
# ::::
def test_config(config_path: Optional[str] = None) -> None:
    """Test parsing a config file"""
    from pathlib import Path
    from .core.parser import parse_annotations
    
    if not config_path:
        # Use default
        import os
        xdg = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        config_path = Path(xdg) / 'wezterm' / 'wezterm.lua'
    else:
        config_path = Path(config_path)
    
    print(f"=== Testing Config: {config_path} ===\n")
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return
    
    try:
        content = config_path.read_text()
        entries = parse_annotations(content)
        
        print(f"Found {len(entries)} widget annotations:\n")
        
        # Group by type
        by_type = {}
        for entry in entries:
            ui_type = entry['ui_type']
            if ui_type not in by_type:
                by_type[ui_type] = []
            by_type[ui_type].append(entry['key'])
        
        # Display
        for ui_type, keys in sorted(by_type.items()):
            print(f"{ui_type}:")
            for key in keys:
                print(f"  - {key}")
            print()
            
    except Exception as e:
        print(f"✗ Error parsing config: {e}")


# :::
# main entry point that bootstraps
# the Qt application
# ::::
def main(args: Optional[list[str]] = None) -> None:
    parsed_args = parse_args(args)
    
    # Setup logging first
    setup_debug_logging(parsed_args.debug)
    
    # Handle diagnostic commands
    if parsed_args.check_widgets:
        check_widgets()
        sys.exit(0)
    
    if parsed_args.test_config:
        test_config(parsed_args.config)
        sys.exit(0)
    
    if parsed_args.debug:
        logging.debug("Debug mode enabled")
        logging.debug(f"Args: {parsed_args}")
        # Also run widget check in debug mode
        print("\n" + "="*50 + "\n")
        check_widgets()
        print("\n" + "="*50 + "\n")
    
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