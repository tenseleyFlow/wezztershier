# :::
# :::: WIDGETS :: where UI elements come to register ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Widget package initialization that handles registration
# and exports. Because apparently we're running a widget
# bureaucracy now.
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
# :::: NOTE: @espadonne (mfw)
# :::::     Import implementations to trigger registration.
# :::::     The @register decorators run on import.
# :::::     It's like a widget roll call.
# ::::

# Import slider implementations
from .sliders import FloatSlider, IntSlider

# Import input implementations
from .inputs import NumericalInput, TextInput

# Import selector implementations
from .selectors import Select, ThemeSelector

logger = logging.getLogger(__name__)

# :::
# log registration status because 
# silent failure is for quitters
# ::::
def _log_registration_status():
    """Log what widgets we've registered"""
    registered = WidgetFactory.get_registered_types()
    logger.info(f"Registered {len(registered)} widget types: {', '.join(registered)}")
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("\n" + WidgetFactory.debug_dump())

# Do the logging
_log_registration_status()

# :::
# :::: PUBLIC API :: what the world sees ::::
# ::::::::::::::::::::::::::::::::::::::::::::::
#
# Export only what's needed. The rest is our
# dirty laundry.
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
    
    # Concrete implementations
    "FloatSlider",
    "IntSlider",
    "NumericalInput",
    "TextInput",
    "Select",
    "ThemeSelector",
]