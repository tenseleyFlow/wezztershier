# :::
# :::: WIDGETS :: where UI elements come to life ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Widget package initialization that handles registration
# and exports. All widgets must be imported here to
# trigger their @register decorators!
#
# Author: @espadonne (mfw)
# ::::

import logging

# Import base components first
from .base import (
    BaseWezzWidget,
    NumericWezzWidget,
    WezzWidget,
    WidgetMetadata,
    RegisteredWidget,
)

# Import factory
from .factory import (
    WidgetFactory,
    WidgetBuilder,
    WidgetDiscovery,
)

# :::
# :::: CRITICAL :: Widget Registration Zone ::::
# ::::: ::::::::::::::::::::::::::::::::::: :::::
#
# ALL widget implementations MUST be imported here!
# The @register decorators only run on import.
# Missing an import = widget won't work. Simple as.
# ::::

# Slider implementations
from .sliders import FloatSlider, IntSlider

# Input implementations  
from .inputs import NumericalInput, TextInput

# Selector implementations
from .selectors import Select, ThemeSelector

# :::
# :::: NOTE: @espadonne (mfw)
# :::::     COLOR WIDGETS! These were imported but
# :::::     not exported. That's why they didn't work!
# ::::
from .color import ColorPicker, ColorSchemePicker

# Font widgets
from .font import FontInput, FontPicker, FontConfig

# Table/special widgets (if implemented)
try:
    from .tables import TablePath
except ImportError:
    logger.warning("Table widgets not available")
    TablePath = None

logger = logging.getLogger(__name__)

# :::
# log registration status because 
# silent failure is for quitters
# ::::
def _log_registration_status():
    """Log what widgets we've registered"""
    registered = WidgetFactory.get_registered_types()
    logger.info(f"Registered {len(registered)} widget types: {', '.join(sorted(registered))}")
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     Extra validation to catch registration issues
    # ::::
    expected_types = [
        'slider', 'int_slider', 'numerical', 'text',
        'select', 'theme_select', 'color_picker', 
        'color_scheme', 'font', 'font_picker', 'font_config'
    ]
    
    missing = [t for t in expected_types if t not in registered]
    if missing:
        logger.error(f"Missing expected widget types: {', '.join(missing)}")
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("\n" + WidgetFactory.debug_dump())

# Do the logging
_log_registration_status()

# :::
# :::: PUBLIC API :: what the world sees ::::
# ::::::::::::::::::::::::::::::::::::::::::::::
#
# Export ALL widget classes so they're available
# for use. Missing exports = confused developers!
# ::::
__all__ = [
    # Base classes for extending
    "BaseWezzWidget",
    "NumericWezzWidget", 
    "WezzWidget",
    "WidgetMetadata",
    "RegisteredWidget",
    
    # Factory for widget creation
    "WidgetFactory",
    "WidgetBuilder",
    "WidgetDiscovery",
    
    # Slider widgets
    "FloatSlider",
    "IntSlider",
    
    # Input widgets
    "NumericalInput",
    "TextInput",
    
    # Selector widgets
    "Select",
    "ThemeSelector",
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     COLOR WIDGETS MUST BE EXPORTED!
    # ::::
    "ColorPicker",
    "ColorSchemePicker",
    
    # Font widgets
    "FontInput",
    "FontPicker",
    "FontConfig",
]

# Add optional widgets if available
if TablePath:
    __all__.append("TablePath")