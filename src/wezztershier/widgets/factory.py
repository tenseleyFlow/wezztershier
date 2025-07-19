# :::
# :::: WIDGET FACTORY :: the widget workshop ::::
# ::::: ::::::::::::::::::::::::::::::::::::: :::::
#
# Factory pattern implementation for creating widgets
# from parsed configuration entries. It's like a
# widget vending machine, but free!
#
# :::
# :::: USAGE ::::
# :::::::::::::::::
#
#   @WidgetFactory.register("slider")
#   class MySlider(BaseWezzWidget):
#       ...
#
#   # Later...
#   widget = WidgetFactory.create(config_entry)
#
# Author: @espadonne (mfw)
# ::::

import logging
from typing import Dict, Type, Optional, List, Callable

from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout

from ..core.parser import ConfigEntry
from .base import BaseWezzWidget, WezzWidget, WidgetMetadata

logger = logging.getLogger(__name__)


# :::
# :::: WIDGET FACTORY :: where widgets are born ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Singleton factory that manages widget registration
# and creation. It's the stork of the widget world!
# ::::
class WidgetFactory:
    """Factory for creating widgets from config entries"""
    
    # Class-level registry of widget types
    _registry: Dict[str, Type[BaseWezzWidget]] = {}
    _metadata: Dict[str, WidgetMetadata] = {}
    
    # Fallback widget creator
    _fallback: Optional[Callable[[ConfigEntry], QWidget]] = None
    
    # :::
    # decorator for registering widget classes.
    # makes widget registration as easy as pie!
    # ::::
    @classmethod
    def register(cls, ui_type: str, metadata: Optional[WidgetMetadata] = None):
        """
        Decorator for registering widget implementations.
        
        Usage:
            @WidgetFactory.register("slider")
            class FloatSlider(BaseWezzWidget):
                ...
        """
        def decorator(widget_class: Type[BaseWezzWidget]):
            # Sanity check
            if not issubclass(widget_class, (BaseWezzWidget, QWidget)):
                raise TypeError(
                    f"{widget_class.__name__} must inherit from BaseWezzWidget"
                )
            
            cls._registry[ui_type] = widget_class
            
            # Store metadata if provided
            if metadata:
                cls._metadata[ui_type] = metadata
            elif hasattr(widget_class, 'METADATA'):
                cls._metadata[ui_type] = widget_class.METADATA
            
            logger.info(f"Registered widget: {ui_type} -> {widget_class.__name__}")
            
            return widget_class
        
        return decorator
    
    # :::
    # create a widget instance from a config entry.
    # it's like widget birth, but less messy!
    # ::::
    @classmethod
    def create(cls, entry: ConfigEntry, parent: Optional[QWidget] = None) -> QWidget:
        """Create a widget instance from a parsed config entry"""
        ui_type = entry['ui_type']
        
        widget_class = cls._registry.get(ui_type)
        
        if widget_class:
            try:
                widget = widget_class(entry, parent)
                logger.debug(f"Created {widget_class.__name__} for {entry['key']}")
                return widget
                
            except Exception as e:
                logger.error(f"Failed to create {ui_type} widget: {e}")
                
                # Fall through to fallback
        
        # Use fallback if registered
        if cls._fallback:
            logger.warning(f"Using fallback for unknown widget type: {ui_type}")
            return cls._fallback(entry, parent)
        
        # Last resort - return a label
        logger.error(f"No widget registered for type: {ui_type}")
        return cls._create_error_widget(entry, parent)
    
    # :::
    # register a fallback widget creator
    # for handling unknown widget types
    # ::::
    @classmethod
    def register_fallback(cls, creator: Callable[[ConfigEntry, Optional[QWidget]], QWidget]):
        """Register a fallback widget creator for unknown types"""
        cls._fallback = creator
        logger.info("Registered fallback widget creator")
    
    # :::
    # get list of all registered widget types.
    # useful for debugging and documentation!
    # ::::
    @classmethod
    def get_registered_types(cls) -> List[str]:
        """Get list of all registered widget types"""
        return list(cls._registry.keys())
    
    # :::
    # get metadata for a widget type
    # ::::
    @classmethod
    def get_metadata(cls, ui_type: str) -> Optional[WidgetMetadata]:
        """Get metadata for a widget type"""
        return cls._metadata.get(ui_type)
    
    # :::
    # check if a widget type is registered
    # ::::
    @classmethod
    def is_registered(cls, ui_type: str) -> bool:
        """Check if a widget type is registered"""
        return ui_type in cls._registry
    
    # :::
    # create an error widget for unknown types.
    # at least show something useful!
    # ::::
    @classmethod
    def _create_error_widget(cls, entry: ConfigEntry, parent: Optional[QWidget]) -> QWidget:
        """Create an error widget for unknown widget types"""
        label = QLabel(f"⚠️ Unknown widget type: {entry['ui_type']}")
        label.setStyleSheet("color: #FF6B6B; font-style: italic;")
        label.setToolTip(f"No widget registered for '{entry['ui_type']}'")
        return label
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     for debugging - dumps registry info
    # ::::
    @classmethod
    def debug_dump(cls) -> str:
        """Get debug information about registered widgets"""
        lines = ["=== Widget Factory Registry ==="]
        lines.append(f"Registered widgets: {len(cls._registry)}")
        
        for ui_type, widget_class in cls._registry.items():
            metadata = cls._metadata.get(ui_type)
            if metadata:
                lines.append(f"  {ui_type}: {widget_class.__name__} - {metadata.description}")
            else:
                lines.append(f"  {ui_type}: {widget_class.__name__}")
        
        if cls._fallback:
            lines.append(f"Fallback: {cls._fallback.__name__}")
        
        return "\n".join(lines)


# :::
# :::: WIDGET BUILDER :: high-level widget construction ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Builds form layouts from parsed entries.
# Like LEGO, but for GUIs!
# ::::
class WidgetBuilder:
    """High-level widget construction utilities"""
    
    @staticmethod
    def build_form_layout(
        entries: List[ConfigEntry],
        parent: Optional[QWidget] = None
    ) -> tuple[QFormLayout, Dict[str, QWidget]]:
        """
        Build a form layout from config entries.
        
        Returns:
            (layout, widget_map) where widget_map is {key: widget}
        """
        layout = QFormLayout()
        widget_map: Dict[str, QWidget] = {}
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     could add grouping logic here
        # :::::     based on widget metadata
        # ::::
        
        for entry in entries:
            # Create label
            label = QLabel(entry['key'])
            label.setToolTip(entry.get('decorator', ''))
            
            # Create widget
            try:
                widget = WidgetFactory.create(entry, parent)
                widget_map[entry['key']] = widget
                
                # Add to layout
                layout.addRow(label, widget)
                
            except Exception as e:
                logger.error(f"Failed to create widget for {entry['key']}: {e}")
                error_label = QLabel(f"Error: {e}")
                error_label.setStyleSheet("color: red;")
                layout.addRow(label, error_label)
        
        return layout, widget_map
    
    @staticmethod
    def connect_change_handlers(
        widget_map: Dict[str, QWidget],
        handler: Callable[[str, any], None]
    ) -> None:
        """
        Connect all widgets to a common change handler.
        
        Handler signature: handler(key: str, value: Any)
        """
        for key, widget in widget_map.items():
            if isinstance(widget, BaseWezzWidget):
                widget.value_changed.connect(
                    lambda value, k=key: handler(k, value)
                )
            else:
                logger.warning(f"Widget {key} is not a BaseWezzWidget, skipping handler")


# :::
# :::: AUTO-DISCOVERY :: find widgets automagically ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Future feature: auto-discover widget implementations
# from a directory. Widget plug-and-play!
# ::::
class WidgetDiscovery:
    """Auto-discovery of widget implementations"""
    
    @staticmethod
    def discover_widgets(module_path: str) -> None:
        """
        Discover and register widgets from a module.
        
        TODO: Implement widget auto-discovery
        """
        # This is where we'd implement plugin-style
        # widget discovery in the future
        pass