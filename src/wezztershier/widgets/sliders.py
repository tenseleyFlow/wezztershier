# :::
# :::: SLIDERS :: because Qt forgot about floats ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Native float slider implementation that doesn't 
# require multiplying everything by 100 like some
# kind of percentage-obsessed accountant.
#
# Author: @espadonne (mfw)
# ::::

import logging
from typing import Optional, Union
from math import floor, ceil

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QStyle
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPaintEvent, QMouseEvent

from ..core.parser import ConfigEntry
from .base import NumericWezzWidget, WidgetMetadata
from .factory import WidgetFactory

logger = logging.getLogger(__name__)


# :::
# :::: FLOAT SLIDER :: the slider Qt forgot ::::
# ::::: ::::::::::::::::::::::::::::::::::::: :::::
#
# A proper float slider that handles floats natively.
# No more SCALE_FACTOR nonsense. Just pure, 
# unadulterated floating point goodness.
#
# Yes, we're implementing our own because apparently
# float sliders are too exotic for 2024.
# ::::
@WidgetFactory.register("slider")
class FloatSlider(NumericWezzWidget):
    """A slider that actually understands floating point values"""
    
    METADATA = WidgetMetadata(
        ui_type="slider",
        display_name="Float Slider",
        description="A slider for float values without the hacky scale factor",
        supported_params={
            "min": "Minimum value (float)",
            "max": "Maximum value (float)", 
            "step": "Step size (float)",
            "precision": "Decimal places to display (int)",
            "type": "Data type: 'float' or 'int'"
        },
        example='-- @ui: slider(min=0.0, max=1.0, step=0.01) type=float'
    )
    
    # Custom signal that emits actual float values
    float_value_changed = pyqtSignal(float)
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Additional parameters
        self.precision = int(self.params.get('precision', 2))
        
        # Internal state
        self._value = self.initial_numeric
        self._is_pressed = False
        
        self._setup_ui()
        self.set_value(self.initial_numeric)
    
    def _setup_ui(self) -> None:
        """Setup the custom slider UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the actual slider widget
        self._slider_widget = _FloatSliderWidget(
            min_val=self.min_val,
            max_val=self.max_val,
            step=self.step,
            precision=self.precision,
            is_int=not self.is_float
        )
        
        # Value label - because users like to see numbers
        self._value_label = QLabel()
        self._value_label.setMinimumWidth(60)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._update_label()
        
        layout.addWidget(self._slider_widget)
        layout.addWidget(self._value_label)
        
        # Connect signals
        self._slider_widget.value_changed.connect(self._on_value_changed)
    
    def _on_value_changed(self, value: float) -> None:
        """Handle internal value changes"""
        self._value = value
        self._update_label()
        self._emit_value_changed()
        self.float_value_changed.emit(value)
    
    def _update_label(self) -> None:
        """Update the value label"""
        if self.is_float:
            text = f"{self._value:.{self.precision}f}"
        else:
            text = str(int(self._value))
        self._value_label.setText(text)
    
    def get_value(self) -> Union[float, int]:
        """Get current value"""
        return self._value if self.is_float else int(self._value)
    
    def set_value(self, value: Union[float, int]) -> None:
        """Set current value"""
        self._value = float(value)
        self._slider_widget.set_value(self._value)
        self._update_label()


# :::
# :::: FLOAT SLIDER WIDGET :: the actual slider ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Custom painted slider widget that handles floats.
# Because sometimes you have to do everything yourself.
# ::::
class _FloatSliderWidget(QWidget):
    """Internal slider widget with custom painting"""
    
    value_changed = pyqtSignal(float)
    
    def __init__(
        self, 
        min_val: float,
        max_val: float,
        step: float,
        precision: int = 2,
        is_int: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.precision = precision
        self.is_int = is_int
        
        self._value = min_val
        self._hover = False
        self._pressed = False
        
        # Visual constants - because design matters
        self.setMinimumHeight(24)
        self.setMinimumWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
    
    def set_value(self, value: float) -> None:
        """Set the slider value"""
        # Clamp to bounds
        value = max(self.min_val, min(self.max_val, value))
        
        # Snap to step
        if self.step > 0:
            steps = round((value - self.min_val) / self.step)
            value = self.min_val + steps * self.step
            
            # Ensure we don't exceed bounds after snapping
            value = max(self.min_val, min(self.max_val, value))
        
        if value != self._value:
            self._value = value
            self.update()
    
    def get_value(self) -> float:
        """Get current value"""
        return self._value
    
    # :::
    # convert value to pixel position.
    # basic linear interpolation, nothing fancy
    # ::::
    def _value_to_pos(self, value: float) -> float:
        """Convert value to x position"""
        if self.max_val == self.min_val:
            return self._get_track_rect().left()
        
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        track_rect = self._get_track_rect()
        
        return track_rect.left() + ratio * track_rect.width()
    
    # :::
    # convert pixel position to value.
    # the reverse of the above, equally unfancy
    # ::::
    def _pos_to_value(self, x: float) -> float:
        """Convert x position to value"""
        track_rect = self._get_track_rect()
        
        if track_rect.width() == 0:
            return self.min_val
        
        # Clamp x to track bounds
        x = max(track_rect.left(), min(track_rect.right(), x))
        
        ratio = (x - track_rect.left()) / track_rect.width()
        value = self.min_val + ratio * (self.max_val - self.min_val)
        
        # Ensure we don't exceed bounds due to float precision
        return max(self.min_val, min(self.max_val, value))
    
    def _get_track_rect(self) -> QRectF:
        """Get the track rectangle"""
        margin = 10
        height = 4
        y = (self.height() - height) / 2
        
        return QRectF(margin, y, self.width() - 2 * margin, height)
    
    def _get_handle_rect(self) -> QRectF:
        """Get the handle rectangle"""
        x = self._value_to_pos(self._value)
        radius = 8 if self._hover else 7
        
        return QRectF(x - radius, self.height() / 2 - radius, 2 * radius, 2 * radius)
    
    # :::
    # paint event - where the magic happens.
    # or rather, where we manually draw everything
    # because Qt's built-in slider is integer-only
    # ::::
    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom painting"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors - because aesthetics matter
        track_color = QColor(100, 100, 100, 100)
        fill_color = QColor(71, 184, 224) if self._pressed else QColor(71, 164, 204)
        handle_color = QColor(255, 255, 255)
        
        # Draw track
        track_rect = self._get_track_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, 2, 2)
        
        # Draw filled portion
        fill_rect = QRectF(
            track_rect.left(),
            track_rect.top(),
            self._value_to_pos(self._value) - track_rect.left(),
            track_rect.height()
        )
        painter.setBrush(fill_color)
        painter.drawRoundedRect(fill_rect, 2, 2)
        
        # Draw handle
        handle_rect = self._get_handle_rect()
        painter.setBrush(handle_color)
        painter.setPen(QPen(fill_color, 2))
        painter.drawEllipse(handle_rect)
        
        # Draw value text on hover - because tooltips are so 2010
        if self._hover:
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Courier", 9))
            
            if self.is_int:
                text = str(int(self._value))
            else:
                text = f"{self._value:.{self.precision}f}"
            
            text_rect = QRectF(handle_rect.x() - 20, handle_rect.y() - 20, 40, 15)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
    
    # :::
    # mouse events - because interaction is key.
    # even if we have to implement it ourselves
    # ::::
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._update_value_from_pos(event.pos().x())
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release"""
        self._pressed = False
        self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move"""
        if self._pressed:
            self._update_value_from_pos(event.pos().x())
        
        # Update hover state
        old_hover = self._hover
        self._hover = self._get_handle_rect().contains(QPointF(event.pos()))
        
        if old_hover != self._hover:
            self.update()
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter"""
        self._hover = True
        self.update()
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave"""
        self._hover = False
        self._pressed = False
        self.update()
    
    def _update_value_from_pos(self, x: float) -> None:
        """Update value from mouse position"""
        new_value = self._pos_to_value(x)
        old_value = self._value
        self.set_value(new_value)
        
        # Only emit if value actually changed
        if self._value != old_value:
            self.value_changed.emit(self._value)


# :::
# :::: INTEGER SLIDER :: for when decimals are too much ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Just wraps the float slider but ensures integer values.
# Because sometimes you really do want exactly 17, not 17.0
# ::::
@WidgetFactory.register("int_slider") 
class IntSlider(FloatSlider):
    """Integer-only slider"""
    
    METADATA = WidgetMetadata(
        ui_type="int_slider",
        display_name="Integer Slider",
        description="A slider that only produces integer values",
        supported_params={
            "min": "Minimum value (int)",
            "max": "Maximum value (int)",
            "step": "Step size (int)"
        },
        example='-- @ui: int_slider(min=8, max=72, step=1) type=int'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        # Force integer type
        entry['params']['type'] = 'int'
        super().__init__(entry, parent)