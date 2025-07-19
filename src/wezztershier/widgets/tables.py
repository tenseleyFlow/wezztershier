# :::
# :::: TABLE WIDGETS :: for Lua's nested nightmares ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Widgets for handling Lua table structures in config.
# Because sometimes a simple value just won't do.
#
# Author: @espadonne (mfw)
# ::::

import logging
import re
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ..core.parser import ConfigEntry
from .base import BaseWezzWidget, WidgetMetadata
from .factory import WidgetFactory

logger = logging.getLogger(__name__)


# :::
# :::: TABLE PATH :: for nested table assignment ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::: :::::
#
# Handles config paths like config.colors.background
# by ensuring parent tables exist before assignment.
# ::::
@WidgetFactory.register("table_path")
class TablePath(BaseWezzWidget):
    """Widget that handles nested table paths"""
    
    METADATA = WidgetMetadata(
        ui_type="table_path",
        display_name="Table Path Handler",
        description="Ensures parent tables exist for nested assignments",
        supported_params={
            "type": "Data type of the value"
        },
        example='-- @ui: table_path() type=string'
    )
    
    def __init__(self, entry: ConfigEntry, parent: Optional[QWidget] = None):
        super().__init__(entry, parent)
        
        # Parse the table path
        self.path_parts = self.key.split('.')
        self.needs_table_init = len(self.path_parts) > 2
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI - just a label for now"""
        layout = QHBoxLayout(self)
        label = QLabel("Table path handling")
        layout.addWidget(label)
    
    def get_value(self) -> str:
        """Get the value"""
        return self.initial_value
    
    def set_value(self, value: Any) -> None:
        """Set the value"""
        pass
    
    def get_config_string(self) -> str:
        """Get config with table initialization"""
        lines = []
        
        # Build table initialization if needed
        if self.needs_table_init:
            # For config.colors.background, we need:
            # config.colors = config.colors or {}
            for i in range(2, len(self.path_parts)):
                table_path = '.'.join(self.path_parts[:i])
                lines.append(f"{table_path} = {table_path} or {{}}")
        
        # Add the actual assignment
        lines.append(f'{self.key} = "{self.get_value()}"')
        
        return '\n'.join(lines)