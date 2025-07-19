# :::
# :::: COLOR WIDGETS :: for when hex isn't just for witches ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Color selection widgets for terminal color schemes.
# Because #FF0000 means more than just "very red".
#
# Author: @espadonne (mfw)
# ::::

import logging
import re
from typing import Optional, Dict, Tuple

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QColorDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

from ..core.parser import ConfigEntry
from .base import BaseWezzWidget, WidgetMetadata
from .factory import WidgetFactory

logger = logging.getLogger(__name__)


# :::
# :::: COLOR PICKER :: because typing hex codes is tedious ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# A proper color picker widget that shows a preview
# and opens a color dialog. Finally, visual feedback
# for color configuration!
# ::::
@WidgetFactory.register("color_picker")
class ColorPicker(BaseWezzWidget):
    """Color picker with preview and dialog"""
    
    METADATA = WidgetMetadata(
        ui_type="color_picker",
        display_name="Color Picker",
        description="Visual color selection with preview",
        supported_params={
            "format": "Color format: 'hex', 'rgb', 'rgba'",
            "alpha": "Enable alpha channel (true/false)",
            "palette": "Preset palette name",
            "preview_size": "Preview box size in pixels",
            "type": "Data type (usually 'color')"
        },
        example='-- @ui: color_picker(format="hex", alpha=false) type=color'
    )
    
    # Custom signal for color changes
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Parse parameters
        self.format = self.params.get('format', 'hex')
        self.alpha_enabled = self.params.get('alpha', False)
        if isinstance(self.alpha_enabled, str):
            self.alpha_enabled = self.alpha_enabled.lower() == 'true'
        self.preview_size = int(self.params.get('preview_size', 30))
        
        # Parse initial color
        self.current_color = self._parse_color(self.initial_value)
        
        self._setup_ui()
    
    def _parse_color(self, value: str) -> QColor:
        """Parse color from various formats"""
        value = value.strip().strip('"\'')
        
        # Hex format
        if value.startswith('#'):
            return QColor(value)
        
        # RGB format: rgb(r, g, b)
        rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', value)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return QColor(r, g, b)
        
        # RGBA format: rgba(r, g, b, a)
        rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', value)
        if rgba_match:
            r, g, b, a = rgba_match.groups()
            color = QColor(int(r), int(g), int(b))
            color.setAlphaF(float(a))
            return color
        
        # Default to black if parsing fails
        logger.warning(f"Failed to parse color: {value}")
        return QColor(0, 0, 0)
    
    def _setup_ui(self) -> None:
        """Setup the color picker UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Color preview frame
        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(self.preview_size, self.preview_size)
        self.preview_frame.setFrameStyle(QFrame.Shape.Box)
        self.preview_frame.setStyleSheet(
            f"QFrame {{ background-color: {self.current_color.name()}; "
            f"border: 1px solid #555; border-radius: 4px; }}"
        )
        
        # Color value label
        self.value_label = QLabel()
        self.value_label.setMinimumWidth(80)
        self._update_label()
        
        # Pick button
        self.pick_button = QPushButton("Pick...")
        self.pick_button.clicked.connect(self._open_color_dialog)
        
        layout.addWidget(self.preview_frame)
        layout.addWidget(self.value_label)
        layout.addWidget(self.pick_button)
        layout.addStretch()
    
    def _open_color_dialog(self) -> None:
        """Open color picker dialog"""
        options = QColorDialog.ColorDialogOption.DontUseNativeDialog
        if self.alpha_enabled:
            options |= QColorDialog.ColorDialogOption.ShowAlphaChannel
        
        color = QColorDialog.getColor(
            self.current_color,
            self,
            "Pick a Color",
            options
        )
        
        if color.isValid():
            self.set_value(color)
            self._emit_value_changed()
            self.color_changed.emit(color)
    
    def _update_label(self) -> None:
        """Update the value label"""
        self.value_label.setText(self._format_color(self.current_color))
    
    def _format_color(self, color: QColor) -> str:
        """Format color according to specified format"""
        if self.format == 'rgb':
            return f"rgb({color.red()}, {color.green()}, {color.blue()})"
        elif self.format == 'rgba':
            return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alphaF():.2f})"
        else:  # hex
            if self.alpha_enabled and color.alpha() < 255:
                return color.name(QColor.NameFormat.HexArgb)
            else:
                return color.name(QColor.NameFormat.HexRgb)
    
    def get_value(self) -> str:
        """Get current color value"""
        return self._format_color(self.current_color)
    
    def set_value(self, value) -> None:
        """Set color value"""
        if isinstance(value, QColor):
            self.current_color = value
        else:
            self.current_color = self._parse_color(str(value))
        
        # Update UI
        self.preview_frame.setStyleSheet(
            f"QFrame {{ background-color: {self.current_color.name(QColor.NameFormat.HexArgb)}; "
            f"border: 1px solid #555; border-radius: 4px; }}"
        )
        self._update_label()
    
    def get_config_string(self) -> str:
        """Get config file representation"""
        value = self.get_value()
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Handle nested table paths like config.colors.background
        # :::::     by ensuring parent tables exist
        # ::::
        lines = []
        path_parts = self.key.split('.')
        
        # If we have a nested path, ensure parent tables exist
        if len(path_parts) > 2:
            for i in range(2, len(path_parts)):
                table_path = '.'.join(path_parts[:i])
                lines.append(f"{table_path} = {table_path} or {{}}")
        
        # Add the actual color assignment
        lines.append(f'{self.key} = "{value}"')
        
        return '\n'.join(lines)


# :::
# :::: COLOR SCHEME PICKER :: for full terminal themes ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Widget for selecting complete color schemes with
# multiple colors. Because terminals need more than
# one color to look good.
# ::::
@WidgetFactory.register("color_scheme")
class ColorSchemePicker(BaseWezzWidget):
    """Color scheme picker for terminal themes"""
    
    METADATA = WidgetMetadata(
        ui_type="color_scheme",
        display_name="Color Scheme Picker",
        description="Pick a complete terminal color scheme",
        supported_params={
            "colors": "Dict of color names to values",
            "preview": "Show color preview grid",
            "type": "Data type (usually 'color_scheme')"
        },
        example='-- @ui: color_scheme(colors={fg: "#FFFFFF", bg: "#000000"}) type=color_scheme'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # TODO: Implement full color scheme picker
        # This would show a grid of colors for:
        # - foreground, background
        # - black, red, green, yellow, blue, magenta, cyan, white
        # - bright variants of each
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup color scheme UI"""
        layout = QHBoxLayout(self)
        label = QLabel("Color scheme picker coming soon!")
        layout.addWidget(label)
    
    def get_value(self) -> Dict[str, str]:
        """Get color scheme dict"""
        return {}
    
    def set_value(self, value: Dict[str, str]) -> None:
        """Set color scheme"""
        pass