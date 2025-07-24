# :::
# :::: MAIN WINDOW :: labels above, beauty below ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Enhanced main window with labels above inputs.
# Sliders centered, everything else right-aligned.
# Because vertical rhythm > horizontal chaos!
#
# Author: @espadonne (mfw)
# ::::

import os
import logging
import math
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMainWindow, QFrame, QFormLayout,
    QScrollArea, QGridLayout, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize

from ..core.backup import WezzBackMachine
from ..core.parser import parse_annotations, ConfigEntry
from ..widgets import WidgetFactory, WidgetBuilder

logger = logging.getLogger(__name__)


# :::
# :::: CONSTANTS :: tweakable layout parameters ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Adjust these to taste. Like seasoning, but for GUIs.
# ::::
WIDGET_COLUMN_WIDTH = 280      # Width per widget column
WINDOW_BASE_WIDTH = 1000       # Minimum window width
WINDOW_MAX_WIDTH = 2400        # Maximum for even high-res monitors
PREVIEW_MIN_WIDTH = 500        # Preview pane minimum width
MAX_WIDGETS_PER_COLUMN = 10    # Before creating new column
MIN_WINDOW_HEIGHT = 600        # Minimum height
MAX_WINDOW_HEIGHT = 1200       # Maximum height


# :::
# :::: WEZZTERSHIER :: the vertical virtuoso ::::
# ::::: ::::::::::::::::::::::::::::::::::::: :::::
#
# Main window with labels-above-inputs layout.
# Clean, vertical, and properly aligned.
# Like a well-organized closet, but for configs!
# ::::
class Wezztershier(QMainWindow):
    """Main window for wezztershier with vertical widget layout"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        debug_mode: bool = False
    ):
        super().__init__()
        
        self.debug_mode = debug_mode
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Using paths from CLI args or defaults
        # ::::
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.backup_dir = Path(backup_dir) if backup_dir else self._get_default_backup_dir()
        
        # Initialize state
        self.config_content = ""
        self.backup_manager: Optional[WezzBackMachine] = None
        self.applied_changes = False
        self.dynamic_widgets: Dict[str, QWidget] = {}
        
        # Load and parse config
        self._load_config()
        self.dynamic_entries = parse_annotations(self.config_content)
        
        # Setup UI with dynamic sizing
        self._init_ui()
        
        # Initialize backup system
        self._init_backup()
        
        logger.info(f"Wezztershier initialized with {len(self.dynamic_entries)} widgets")
    
    def _get_default_config_path(self) -> Path:
        """Get default config path"""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config)
        else:
            config_dir = Path.home() / ".config"
        
        return config_dir / "wezterm" / "wezterm.lua"
    
    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory"""
        return Path.home() / ".local" / "share" / "wezztershier" / "backups"
    
    def _load_config(self) -> None:
        """Load the config file"""
        try:
            self.config_content = self.config_path.read_text()
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config_content = ""
    
    def _init_backup(self) -> None:
        """Initialize backup system"""
        self.backup_manager = WezzBackMachine(
            self.config_path,
            self.backup_dir,
            max_backups=10
        )
        
        self.backup_manager.create_temp_backup()
        self.backup_manager.update_last_applied()
        
        logger.debug("Backup system initialized")
    
    def _calculate_layout_params(self) -> tuple[int, int, int]:
        """
        Calculate optimal number of columns and window dimensions.
        
        Returns (num_columns, window_width, window_height)
        """
        widget_count = len(self.dynamic_entries)
        
        if widget_count == 0:
            return 1, WINDOW_BASE_WIDTH, MIN_WINDOW_HEIGHT
        
        # Calculate ideal number of columns
        columns = math.ceil(widget_count / MAX_WIDGETS_PER_COLUMN)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     For better visual balance, prefer fewer
        # :::::     columns with more widgets per column
        # ::::
        if widget_count <= 8:
            columns = 1
        elif widget_count <= 16:
            columns = 2
        elif widget_count <= 24:
            columns = 3
        elif widget_count <= 32:
            columns = 4
        else:
            columns = min(5, columns)  # Cap at 5 columns max
        
        # Calculate exact width needed for columns
        widget_area_width = columns * WIDGET_COLUMN_WIDTH + 40  # columns + padding
        total_width = widget_area_width + PREVIEW_MIN_WIDTH + 50  # add preview + splitter
        
        # Don't exceed max but don't pad unnecessarily
        total_width = min(total_width, WINDOW_MAX_WIDTH)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     More height per widget now that labels are above
        # ::::
        widgets_per_col = math.ceil(widget_count / columns)
        height = 200 + (widgets_per_col * 80)  # More height for vertical layout
        height = max(MIN_WINDOW_HEIGHT, min(height, MAX_WINDOW_HEIGHT))
        
        logger.debug(f"Layout calc: {widget_count} widgets -> {columns} cols, {total_width}x{height}")
        
        return columns, total_width, height
    
    def _init_ui(self) -> None:
        """Initialize the UI with dynamic layout"""
        self.setWindowTitle("wezztershier")
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Added FramelessWindowHint to prevent resizing
        # :::::     No more layout chaos from window stretching!
        # ::::
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        
        # Calculate layout parameters
        num_columns, window_width, window_height = self._calculate_layout_params()
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        
        # Add header
        self._add_header(main_layout)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Using QSplitter for resizable panes!
        # :::::     Much better than fixed proportions
        # ::::
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - widget columns
        left_widget = self._create_widget_area(num_columns)
        
        # Right side - preview
        right_widget = self._create_preview_area()
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (2:1 ratio)
        widget_area_width = num_columns * WIDGET_COLUMN_WIDTH + 50
        splitter.setSizes([widget_area_width, PREVIEW_MIN_WIDTH])
        
        main_layout.addWidget(splitter)
        
        # Set window size and lock it
        self.resize(window_width, window_height)
        self.setFixedSize(window_width, window_height)  # Lock the window size!
        
        logger.info(f"Window layout: {num_columns} columns, {window_width}x{window_height} (locked)")
    
    def _add_header(self, layout: QVBoxLayout) -> None:
        """Add header section"""
        header = QLabel("WezTerm Configuration Tuner")
        header.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            padding: 15px;
            color: #47B884;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        if self.debug_mode:
            debug_label = QLabel(f"🐛 Debug Mode | {len(self.dynamic_entries)} widgets loaded")
            debug_label.setStyleSheet("color: orange; font-style: italic; text-align: center;")
            debug_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(debug_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
    
    def _create_widget_area(self, num_columns: int) -> QWidget:
        """Create the widget area with proper columns"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        if not self.dynamic_entries:
            no_config = QLabel("No configuration annotations found in wezterm.lua")
            no_config.setStyleSheet("""
                color: gray; 
                font-style: italic; 
                padding: 40px;
                font-size: 14px;
            """)
            no_config.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(no_config)
            return container
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Create a scroll area for the columns
        # :::::     but don't let it stretch vertically
        # ::::
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        columns_layout = QHBoxLayout(scroll_widget)
        columns_layout.setSpacing(20)
        columns_layout.setContentsMargins(10, 10, 10, 10)
        
        # :::
        # :::: THE MAGIC :: true column distribution ::::
        # :::::::::::::::::::::::::::::::::::::::::::::::::
        #
        # Create actual column widgets and distribute
        # entries among them evenly
        # ::::
        columns = []
        for i in range(num_columns):
            col_widget = QWidget()
            col_widget.setFixedWidth(WIDGET_COLUMN_WIDTH)
            col_layout = QVBoxLayout(col_widget)
            col_layout.setSpacing(10)
            columns.append((col_widget, col_layout))
            columns_layout.addWidget(col_widget)
        
        # Add stretch to push columns left
        columns_layout.addStretch()
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Distribute widgets round-robin style
        # :::::     to balance column heights
        # ::::
        widgets_per_column = math.ceil(len(self.dynamic_entries) / num_columns)
        
        for idx, entry in enumerate(self.dynamic_entries):
            col_idx = idx // widgets_per_column
            if col_idx >= num_columns:
                col_idx = num_columns - 1
            
            _, col_layout = columns[col_idx]
            
            # Create widget block with label above
            widget_block = self._create_widget_block(entry)
            if widget_block:
                col_layout.addWidget(widget_block)
        
        # Add stretch to each column to push widgets up
        for _, col_layout in columns:
            col_layout.addStretch()
        
        # Connect change handlers
        WidgetBuilder.connect_change_handlers(
            self.dynamic_widgets,
            self._on_widget_value_changed
        )
        
        scroll.setWidget(scroll_widget)
        
        container_layout.addWidget(scroll, 0)  # Don't give it stretch
        
        # Add control buttons at bottom
        self._add_controls(container_layout)
        
        return container
    
    def _create_widget_block(self, entry: ConfigEntry) -> Optional[QWidget]:
        """Create a widget block with label above input"""
        # Create container frame
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
                margin: 2px;
                background-color: #2a2a2a;
            }
            QFrame:hover {
                border-color: #555;
                background-color: #2f2f2f;
            }
        """)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Vertical layout for label above widget
        # ::::
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Create label - prettier formatting
        key_parts = entry['key'].split('.')
        if len(key_parts) > 1:
            # Show nested keys nicely
            label_text = ' › '.join(key_parts[1:])
        else:
            label_text = key_parts[0]
        
        label_text = label_text.replace('_', ' ').title()
        label = QLabel(label_text)
        label.setStyleSheet("""
            font-weight: bold;
            color: #d4d4d4;
            font-size: 13px;
            margin-bottom: 2px;
        """)
        label.setToolTip(entry.get('decorator', ''))
        
        # Add label (flush left)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Create widget
        try:
            widget = WidgetFactory.create(entry, parent=self)
            self.dynamic_widgets[entry['key']] = widget
            
            # :::
            # :::: NOTE: @espadonne (mfw)
            # :::::     Determine alignment based on widget type
            # :::::     Sliders: full width (they center themselves)
            # :::::     Everything else: right-aligned
            # ::::
            ui_type = entry.get('ui_type', '')
            
            if ui_type in ['slider', 'int_slider']:
                # Sliders take full width - they handle centering internally
                layout.addWidget(widget)
            else:
                # Right-align everything else
                widget_container = QWidget()
                widget_layout = QHBoxLayout(widget_container)
                widget_layout.setContentsMargins(0, 0, 0, 0)
                widget_layout.addStretch()  # Push to right
                widget_layout.addWidget(widget)
                
                # Set reasonable max widths
                if ui_type in ['numerical', 'text']:
                    if hasattr(widget, 'setMaximumWidth'):
                        widget.setMaximumWidth(150)
                elif ui_type in ['select', 'theme_select']:
                    if hasattr(widget, 'setMaximumWidth'):
                        widget.setMaximumWidth(180)
                elif ui_type == 'color_picker':
                    # Color picker needs a bit more room
                    pass  # Let it size naturally
                
                layout.addWidget(widget_container)
            
            return frame
            
        except Exception as e:
            logger.error(f"Failed to create widget for {entry['key']}: {e}")
            error_label = QLabel(f"Error: {e}")
            error_label.setStyleSheet("color: #ff6b6b; font-size: 10px;")
            layout.addWidget(error_label)
            return frame
    
    def _create_preview_area(self) -> QWidget:
        """Create the preview area widget"""
        container = QWidget()
        container.setMinimumWidth(PREVIEW_MIN_WIDTH)
        layout = QVBoxLayout(container)
        
        preview_label = QLabel("Configuration Preview:")
        preview_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px;
            margin-bottom: 5px;
            color: #47B884;
        """)
        layout.addWidget(preview_label)
        
        self.preview_editor = QTextEdit()
        self.preview_editor.setReadOnly(True)
        self.preview_editor.setStyleSheet("""
            QTextEdit {
                font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.preview_editor)
        
        # Initial sync
        self._sync_config()
        
        return container
    
    def _add_controls(self, layout: QVBoxLayout) -> None:
        """Add control buttons"""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 0)
        
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.setMinimumHeight(40)
        self.apply_button.setMinimumWidth(150)
        self.apply_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                padding: 8px 24px;
                background-color: #47B884;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3FA76F;
            }
            QPushButton:pressed {
                background-color: #358F5C;
            }
        """)
        self.apply_button.clicked.connect(self._apply_changes)
        
        if self.debug_mode:
            debug_button = QPushButton("Debug Info")
            debug_button.setMinimumHeight(35)
            debug_button.clicked.connect(self._show_debug_info)
            button_layout.addWidget(debug_button)
            button_layout.addSpacing(10)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _on_widget_value_changed(self, key: str, value: Any) -> None:
        """Handle widget value changes"""
        logger.debug(f"Widget changed: {key} = {value}")
        
        if self.applied_changes:
            self.applied_changes = False
            self.apply_button.setText("Apply Changes")
            self.apply_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 24px;
                    background-color: #47B884;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3FA76F;
                }
            """)
        
        self._sync_config()
    
    def _sync_config(self) -> None:
        """Sync widget values to config preview"""
        lines = ["-- <<TUNER-START>>"]
        
        for entry in self.dynamic_entries:
            widget = self.dynamic_widgets.get(entry['key'])
            if widget and hasattr(widget, 'get_config_string'):
                lines.append(entry['decorator'])
                config_string = widget.get_config_string()
                # Handle multi-line config strings (like table initialization)
                lines.extend(config_string.split('\n'))
                lines.append("")  # Empty line for readability
        
        lines.append("-- <<TUNER-END>>")
        
        tuner_block = "\n".join(lines)
        self.preview_editor.setPlainText(tuner_block)
        
        # Update config file (but don't persist yet)
        if self.backup_manager:
            self.backup_manager.update_config_file(tuner_block)
    
    def _apply_changes(self) -> None:
        """Apply changes to config"""
        if not self.backup_manager:
            return
        
        self.backup_manager.create_persistent_backup()
        self.backup_manager.update_last_applied()
        
        self.applied_changes = True
        self.apply_button.setText("✓ Changes Applied!")
        self.apply_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                padding: 8px 24px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
            }
        """)
        
        logger.info("Configuration changes applied")
    
    def _show_debug_info(self) -> None:
        """Show debug information"""
        from PyQt6.QtWidgets import QMessageBox
        
        info = [
            "=== Debug Information ===",
            f"Config path: {self.config_path}",
            f"Backup dir: {self.backup_dir}",
            f"Dynamic entries: {len(self.dynamic_entries)}",
            f"Registered widgets: {len(self.dynamic_widgets)}",
            "",
            "=== Widget Types ===",
        ]
        
        # Count widget types
        type_counts = {}
        for entry in self.dynamic_entries:
            ui_type = entry['ui_type']
            type_counts[ui_type] = type_counts.get(ui_type, 0) + 1
        
        for ui_type, count in sorted(type_counts.items()):
            info.append(f"  {ui_type}: {count}")
        
        info.extend(["", WidgetFactory.debug_dump()])
        
        msg = QMessageBox()
        msg.setWindowTitle("Debug Information")
        msg.setText("\n".join(info))
        msg.setStyleSheet("QLabel{font-family: monospace;}")
        msg.exec()
        
        logger.info("\n".join(info))
    
    def closeEvent(self, event) -> None:
        """Handle window close"""
        if not self.applied_changes and self.backup_manager:
            logger.info("Reverting unapplied changes")
            self.backup_manager.revert_config()
        
        event.accept()