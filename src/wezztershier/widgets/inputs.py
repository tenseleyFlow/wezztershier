# :::
# :::: INPUTS :: for when sliders are overkill ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Direct input widgets for entering values.
# Sometimes you know exactly what you want and
# don't need to slide around to find it.
#
# Author: @espadonne (mfw)
# ::::

import logging
from typing import Optional, Union

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QSpinBox, QDoubleSpinBox,
    QLineEdit, QLabel
)
from PyQt6.QtCore import Qt

from ..core.parser import ConfigEntry
from .base import NumericWezzWidget, BaseWezzWidget, WidgetMetadata
from .factory import WidgetFactory

logger = logging.getLogger(__name__)


# :::
# :::: NUMERICAL INPUT :: spinboxes that actually work ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Direct numerical input with spin buttons.
# For when you want precision without the sliding.
# ::::
@WidgetFactory.register("numerical")
class NumericalInput(NumericWezzWidget):
    """Numerical input with spin buttons"""
    
    METADATA = WidgetMetadata(
        ui_type="numerical",
        display_name="Numerical Input",
        description="Direct number input with spin buttons",
        supported_params={
            "min": "Minimum value",
            "max": "Maximum value",
            "step": "Step size",
            "decimals": "Decimal places (for float type)",
            "type": "Data type: 'float' or 'int'"
        },
        example='-- @ui: numerical(min=8, max=72, step=1) type=int'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        self.decimals = int(self.params.get('decimals', 2))
        self._setup_ui()
        
        # Set initial value
        self.set_value(self.initial_numeric)
    
    def _setup_ui(self) -> None:
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Finally, Qt widgets that handle
        # :::::     floats natively. Progress!
        # ::::
        if self.is_float:
            self._spinbox = QDoubleSpinBox()
            self._spinbox.setDecimals(self.decimals)
            self._spinbox.setSingleStep(self.step)
        else:
            self._spinbox = QSpinBox()
            self._spinbox.setSingleStep(int(self.step))
        
        # Set range
        self._spinbox.setMinimum(self.min_val if self.is_float else int(self.min_val))
        self._spinbox.setMaximum(self.max_val if self.is_float else int(self.max_val))
        
        # Configure appearance
        self._spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._spinbox.setMinimumWidth(100)
        
        layout.addWidget(self._spinbox)
        layout.addStretch()
        
        # Connect signal
        self._spinbox.valueChanged.connect(self._on_value_changed)
    
    def _on_value_changed(self, value: Union[int, float]) -> None:
        """Handle value change"""
        self._emit_value_changed()
    
    def get_value(self) -> Union[int, float]:
        """Get current value"""
        return self._spinbox.value()
    
    def set_value(self, value: Union[int, float]) -> None:
        """Set current value"""
        self._spinbox.setValue(value if self.is_float else int(value))


# :::
# :::: TEXT INPUT :: for strings and such ::::
# ::::: :::::::::::::::::::::::::::::::::: :::::
#
# Basic text input widget. Revolutionary.
# For when your config needs actual text.
# ::::
@WidgetFactory.register("text")
class TextInput(BaseWezzWidget):
    """Basic text input widget"""
    
    METADATA = WidgetMetadata(
        ui_type="text",
        display_name="Text Input",
        description="Simple text input field",
        supported_params={
            "placeholder": "Placeholder text",
            "max_length": "Maximum character length",
            "pattern": "Validation regex pattern",
            "type": "Data type (usually 'string')"
        },
        example='-- @ui: text(placeholder="Enter name") type=string'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        self.placeholder = self.params.get('placeholder', '')
        self.max_length = int(self.params.get('max_length', 0))
        self.pattern = self.params.get('pattern', '')
        
        self._setup_ui()
        
        # Set initial value
        initial = self._parse_initial_value()
        if initial:
            self.set_value(initial)
    
    def _parse_initial_value(self) -> str:
        """Parse initial value, removing quotes"""
        value = self.initial_value.strip()
        
        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        
        return value
    
    def _setup_ui(self) -> None:
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._line_edit = QLineEdit()
        
        if self.placeholder:
            self._line_edit.setPlaceholderText(self.placeholder)
        
        if self.max_length > 0:
            self._line_edit.setMaxLength(self.max_length)
        
        self._line_edit.setMinimumWidth(200)
        
        layout.addWidget(self._line_edit)
        layout.addStretch()
        
        # Connect signal
        self._line_edit.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self, text: str) -> None:
        """Handle text change"""
        self._emit_value_changed()
    
    def get_value(self) -> str:
        """Get current text"""
        return self._line_edit.text()
    
    def set_value(self, value: str) -> None:
        """Set current text"""
        self._line_edit.setText(str(value))
    
    def get_config_string(self) -> str:
        """Get config file representation"""
        value = self.get_value()
        # Escape quotes in the value
        value = value.replace('"', '\\"')
        return f'{self.key} = "{value}"'
    
    def validate(self) -> bool:
        """Validate current text"""
        if self.pattern:
            # TODO: Implement regex validation
            pass
        return True


# :::
# :::: PATH INPUT :: for file/directory paths ::::
# ::::: :::::::::::::::::::::::::::::::::::::: :::::
#
# Text input with browse button. Because typing
# paths is so 1970s.
#
# NOTE: Placeholder for future implementation
# ::::
class PathInput(TextInput):
    """Path input with browse button (future implementation)"""
    
    # TODO: Add browse button that opens file/directory dialog
    # TODO: Add path validation
    pass