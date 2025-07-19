# :::
# :::: SELECTORS :: dropdowns and their ilk ::::
# ::::: :::::::::::::::::::::::::::::::::::: :::::
#
# Selection widgets for when users need to pick
# from predefined options. Because free text is
# apparently too much freedom.
#
# Author: @espadonne (mfw)
# ::::

import logging
from typing import Optional, List, Any

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt

from ..core.parser import ConfigEntry
from .base import BaseWezzWidget, WidgetMetadata
from .factory import WidgetFactory

logger = logging.getLogger(__name__)


# :::
# :::: SELECT :: the dropdown that drops ::::
# ::::: ::::::::::::::::::::::::::::::::::: :::::
#
# Basic select/dropdown widget for choosing from
# a list of options. Revolutionary technology from
# the 1980s, now in your terminal configurator.
# ::::
@WidgetFactory.register("select")
class Select(BaseWezzWidget):
    """Dropdown selection widget"""
    
    METADATA = WidgetMetadata(
        ui_type="select",
        display_name="Select Dropdown",
        description="Choose from a list of predefined options",
        supported_params={
            "options": "Comma-separated list of options",
            "default": "Default selection if current value not in options",
            "type": "Data type (usually 'string')"
        },
        example='-- @ui: select(options="Dark, Light, Auto") type=string'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Parse options from params
        self.options = self._parse_options()
        self.current_value = self._parse_current_value()
        
        self._setup_ui()
        
        # Set initial value
        if self.current_value in self.options:
            self.set_value(self.current_value)
        elif self.options:
            self.set_value(self.options[0])
    
    def _parse_options(self) -> List[str]:
        """Parse comma-separated options"""
        options_str = self.params.get("options", "")
        
        if not options_str:
            logger.warning(f"No options provided for {self.key}")
            return ["(no options)"]
        
        # Split and clean up
        options = [opt.strip() for opt in options_str.split(",") if opt.strip()]
        
        if not options:
            logger.warning(f"Empty options list for {self.key}")
            return ["(no options)"]
        
        return options
    
    def _parse_current_value(self) -> str:
        """Parse current value from config"""
        # Remove quotes if present
        value = self.initial_value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        
        return value
    
    def _setup_ui(self) -> None:
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create combo box
        self._combo = QComboBox()
        self._combo.addItems(self.options)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Set size policy so it doesn't
        # :::::     grow unnecessarily wide
        # ::::
        self._combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        
        layout.addWidget(self._combo)
        layout.addStretch()
        
        # Connect signal
        self._combo.currentTextChanged.connect(self._on_selection_changed)
    
    def _on_selection_changed(self, text: str) -> None:
        """Handle selection change"""
        self._emit_value_changed()
    
    def get_value(self) -> str:
        """Get current selection"""
        return self._combo.currentText()
    
    def set_value(self, value: Any) -> None:
        """Set current selection"""
        str_value = str(value)
        
        # Find and set if exists
        index = self._combo.findText(str_value)
        if index >= 0:
            self._combo.setCurrentIndex(index)
        else:
            logger.warning(f"Value '{str_value}' not in options for {self.key}")
            
            # Try to set default or first option
            default = self.params.get("default")
            if default and default in self.options:
                index = self._combo.findText(default)
                self._combo.setCurrentIndex(index)
            elif self._combo.count() > 0:
                self._combo.setCurrentIndex(0)
    
    def get_config_string(self) -> str:
        """Get config file representation"""
        value = self.get_value()
        # Always quote string values for select
        return f'{self.key} = "{value}"'
    
    def validate(self) -> bool:
        """Validate current selection"""
        # Always valid since we can only select from available options
        return True


# :::
# :::: THEME SELECTOR :: select with preview ::::
# ::::: ::::::::::::::::::::::::::::::::::::: :::::
#
# Specialized select for color schemes that could
# show a preview. Currently just inherits from Select
# but ready for enhancement.
# ::::
@WidgetFactory.register("theme_select")
class ThemeSelector(Select):
    """Theme selection with potential preview support"""
    
    METADATA = WidgetMetadata(
        ui_type="theme_select",
        display_name="Theme Selector",
        description="Select color scheme with preview capability",
        supported_params={
            "options": "Comma-separated list of theme names",
            "preview": "Enable preview (true/false)",
            "type": "Data type (usually 'string')"
        },
        example='-- @ui: theme_select(options="Gruvbox Dark, Catppuccin, Nord") type=string'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Future: Add theme preview on hover
        self.preview_enabled = self.params.get("preview", "false").lower() == "true"
        
        if self.preview_enabled:
            # TODO: Implement theme preview
            logger.debug("Theme preview not yet implemented")


# :::
# :::: MULTI SELECT :: when one choice isn't enough ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# For selecting multiple options. Because sometimes
# you want your cake and eat it too.
#
# NOTE: Not yet implemented, placeholder for future
# ::::
class MultiSelect(BaseWezzWidget):
    """Multiple selection widget (future implementation)"""
    
    # TODO: Implement multi-select for flags like
    # window_decorations = "RESIZE|TITLE|NONE"
    
    def _setup_ui(self) -> None:
        pass
    
    def get_value(self) -> Any:
        pass
    
    def set_value(self, value: Any) -> None:
        pass