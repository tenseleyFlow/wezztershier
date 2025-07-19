# :::
# :::: BASE WIDGETS :: the widget foundry ::::
# ::::: ::::::::::::::::::::::::::::::::::: :::::
#
# Base classes and protocols for all wezztershier widgets.
# Every widget is a special snowflake, but they all
# share some common DNA.
#
# Author: @espadonne (mfw)
# ::::

import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QObject

from ..core.parser import ConfigEntry

logger = logging.getLogger(__name__)


# :::
# :::: METACLASS RESOLUTION :: because Qt and ABC don't play nice ::::
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
# PyQt has its own metaclass, ABC has its own metaclass.
# They fight. We mediate. Modern problems require modern solutions.
# ::::
class WezzWidgetMeta(type(QWidget), ABCMeta):
    """Metaclass that combines Qt and ABC metaclasses"""
    pass


# :::
# :::: WIDGET PROTOCOL :: the widget contract ::::
# ::::: ::::::::::::::::::::::::::::::::::::::: :::::
#
# What every widget must promise to do.
# It's like a pinky promise, but for code!
# ::::
@runtime_checkable
class WezzWidget(Protocol):
    """Protocol defining the interface for all wezztershier widgets"""
    
    def get_value(self) -> Any:
        """Get the current widget value"""
        ...
    
    def set_value(self, value: Any) -> None:
        """Set the widget value"""
        ...
    
    def get_config_string(self) -> str:
        """Get the config file representation of current value"""
        ...
    
    def validate(self) -> bool:
        """Validate current value"""
        ...


# :::
# :::: BASE WIDGET :: the widget ancestor ::::
# ::::: :::::::::::::::::::::::::::::::::: :::::
#
# Abstract base class that provides common functionality
# for all widgets. Like a widget grandparent that
# gives good advice and candy.
# ::::
class BaseWezzWidget(QWidget, metaclass=WezzWidgetMeta):
    """Base class for all wezztershier widgets"""
    
    # Signal emitted when value changes
    value_changed = pyqtSignal(object)  # emits (new_value,)
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.entry = entry
        self.key = entry['key']
        self.params = entry['params']
        self.initial_value = entry['value']
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     subclasses should call _setup_ui()
        # :::::     after their own initialization
        # ::::
        
        logger.debug(f"Creating {self.__class__.__name__} for {self.key}")
    
    @abstractmethod
    def get_value(self) -> Any:
        """Get current widget value"""
        pass
    
    @abstractmethod
    def set_value(self, value: Any) -> None:
        """Set widget value"""
        pass
    
    @abstractmethod
    def _setup_ui(self) -> None:
        """Setup widget UI - must be implemented by subclasses"""
        pass
    
    # :::
    # get config string representation.
    # can be overridden for custom formatting
    # ::::
    def get_config_string(self) -> str:
        """Get config file representation"""
        value = self.get_value()
        data_type = self.params.get('type', 'string')
        
        if data_type == 'string':
            return f'{self.key} = "{value}"'
        else:
            return f'{self.key} = {value}'
    
    # :::
    # basic validation - override for
    # widget-specific validation
    # ::::
    def validate(self) -> bool:
        """Validate current value"""
        return True
    
    # :::
    # emit value changed signal.
    # subclasses should call this when value changes
    # ::::
    def _emit_value_changed(self) -> None:
        """Emit value changed signal with current value"""
        value = self.get_value()
        self.value_changed.emit(value)
        logger.debug(f"{self.key} value changed to: {value}")


# :::
# :::: NUMERIC WIDGET BASE :: for number lovers ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Base class for widgets dealing with numeric values.
# Because numbers need love too!
# ::::
class NumericWezzWidget(BaseWezzWidget):
    """Base class for numeric widgets"""
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Parse numeric parameters
        self.data_type = self.params.get('type', 'float')
        self.is_float = self.data_type == 'float'
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     parse_param handles safe casting
        # :::::     with defaults if parsing fails
        # ::::
        self.min_val = self._parse_param('min', 0.0)
        self.max_val = self._parse_param('max', 100.0)
        self.step = self._parse_param('step', 1.0)
        
        # Parse initial value
        try:
            self.initial_numeric = float(self.initial_value)
        except (ValueError, TypeError):
            self.initial_numeric = self.min_val
    
    def _parse_param(self, name: str, default: float) -> float:
        """Safely parse numeric parameter"""
        try:
            value = float(self.params.get(name, default))
            return value if self.is_float else int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid {name} parameter, using default: {default}")
            return default
    
    def validate(self) -> bool:
        """Validate numeric value is within bounds"""
        value = self.get_value()
        return self.min_val <= value <= self.max_val


# :::
# :::: WIDGET METADATA :: widget self-description ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::: :::::
#
# Widgets can describe themselves for debugging
# and factory registration purposes
# ::::
class WidgetMetadata:
    """Metadata for widget registration"""
    
    def __init__(
        self,
        ui_type: str,
        display_name: str,
        description: str,
        supported_params: Dict[str, str],
        example: str
    ):
        self.ui_type = ui_type
        self.display_name = display_name  
        self.description = description
        self.supported_params = supported_params
        self.example = example
    
    def __repr__(self) -> str:
        return f"<WidgetMetadata: {self.ui_type} - {self.display_name}>"


# :::
# :::: WIDGET REGISTRY MIXIN :: for self-registration ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Mixin that allows widgets to register themselves
# with the factory. It's like widget self-service!
# ::::
class RegisteredWidget:
    """Mixin for self-registering widgets"""
    
    # Subclasses should override this
    METADATA: Optional[WidgetMetadata] = None
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Auto-register if metadata is provided
        if cls.METADATA:
            # This will be connected to factory in __init__.py
            logger.debug(f"Widget {cls.__name__} ready for registration")