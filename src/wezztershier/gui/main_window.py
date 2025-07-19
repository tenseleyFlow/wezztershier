# :::
# :::: MAIN WINDOW :: the gui formerly known as gui.py ::::
# ::::: ::::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# Main window implementation, now with 100% less monolith.
# This is a minimal version to get us started with the
# new widget system.
#
# Author: @espadonne (mfw)
# ::::

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMainWindow, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt

from ..core.backup import WezzBackMachine
from ..core.parser import parse_annotations
from ..widgets import WidgetFactory, WidgetBuilder

logger = logging.getLogger(__name__)


# :::
# :::: WEZZTERSHIER :: the main event ::::
# ::::: :::::::::::::::::::::::::::::: :::::
#
# The main window, now slimmer and using our
# shiny new widget factory. No more manual
# widget creation nonsense.
# ::::
class Wezztershier(QMainWindow):
    """Main window for wezztershier"""
    
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
        
        # Setup UI
        self._init_ui()
        
        # Initialize backup system
        self._init_backup()
        
        logger.info("Wezztershier initialized")
    
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
    
    def _init_ui(self) -> None:
        """Initialize the UI"""
        self.setWindowTitle("wezztershier")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        
        # Add header
        self._add_header(main_layout)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Two-pane layout: controls left, preview right
        # :::::     Just like the sketch!
        # ::::
        content_layout = QHBoxLayout()
        
        # Left side - controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self._add_widget_area(left_layout)
        self._add_controls(left_layout)
        
        # Right side - preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._add_preview_area(right_layout)
        
        # Add to content layout with stretch factors
        content_layout.addWidget(left_widget, 3)  # 3/5 of space
        content_layout.addWidget(right_widget, 2)  # 2/5 of space
        
        main_layout.addLayout(content_layout)
        
        # Set size - wider to accommodate two panes
        self.resize(1000, 600)
    
    def _add_header(self, layout: QVBoxLayout) -> None:
        """Add header section"""
        header = QLabel("WezTerm Configuration Tuner")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        if self.debug_mode:
            debug_label = QLabel("🐛 Debug Mode Active")
            debug_label.setStyleSheet("color: orange; font-style: italic;")
            layout.addWidget(debug_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
    
    def _add_widget_area(self, layout: QVBoxLayout) -> None:
        """Add dynamic widget area"""
        if not self.dynamic_entries:
            no_config = QLabel("No configuration annotations found in wezterm.lua")
            no_config.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            layout.addWidget(no_config)
            return
        
        # Create form layout with proper alignment
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form_layout.setHorizontalSpacing(20)  # Space between label and widget
        form_layout.setVerticalSpacing(10)   # Space between rows
        
        # Build widgets with consistent sizing
        for entry in self.dynamic_entries:
            # Create label with fixed width for alignment
            label = QLabel(entry['key'])
            label.setMinimumWidth(200)  # Consistent label width
            label.setToolTip(entry.get('decorator', ''))
            
            # Create widget
            try:
                widget = WidgetFactory.create(entry, parent=self)
                self.dynamic_widgets[entry['key']] = widget
                
                # :::
                # :::: NOTE: @espadonne (mfw)
                # :::::     Set consistent sizing for widgets
                # :::::     All widgets get same width for alignment
                # ::::
                if hasattr(widget, 'setFixedWidth'):
                    widget.setFixedWidth(250)  # Fixed width for all widgets
                
                form_layout.addRow(label, widget)
                
            except Exception as e:
                logger.error(f"Failed to create widget for {entry['key']}: {e}")
                error_label = QLabel(f"Error: {e}")
                error_label.setStyleSheet("color: red;")
                form_layout.addRow(label, error_label)
        
        # Connect change handlers
        WidgetBuilder.connect_change_handlers(
            self.dynamic_widgets,
            self._on_widget_value_changed
        )
        
        layout.addLayout(form_layout)
        layout.addStretch()  # Push everything to top
    
    def _add_preview_area(self, layout: QVBoxLayout) -> None:
        """Add config preview area"""
        preview_label = QLabel("Configuration Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(preview_label)
        
        self.preview_editor = QTextEdit()
        self.preview_editor.setReadOnly(True)
        self.preview_editor.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                font-size: 12px;
                background-color: #2b2b2b;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.preview_editor)
        
        # Initial sync
        self._sync_config()
    
    def _add_controls(self, layout: QVBoxLayout) -> None:
        """Add control buttons"""
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self._apply_changes)
        button_layout.addWidget(self.apply_button)
        
        if self.debug_mode:
            debug_button = QPushButton("Debug Info")
            debug_button.clicked.connect(self._show_debug_info)
            button_layout.addWidget(debug_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _on_widget_value_changed(self, key: str, value: Any) -> None:
        """Handle widget value changes"""
        logger.debug(f"Widget changed: {key} = {value}")
        
        if self.applied_changes:
            self.applied_changes = False
            self.apply_button.setText("Apply Changes")
        
        self._sync_config()
    
    def _sync_config(self) -> None:
        """Sync widget values to config preview"""
        lines = ["-- <<TUNER-START>>"]
        
        for entry in self.dynamic_entries:
            widget = self.dynamic_widgets.get(entry['key'])
            if widget and hasattr(widget, 'get_config_string'):
                lines.append(entry['decorator'])
                lines.append(widget.get_config_string())
        
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
        self.apply_button.setText("Changes Applied!")
        
        logger.info("Configuration changes applied")
    
    def _show_debug_info(self) -> None:
        """Show debug information"""
        info = [
            "=== Debug Information ===",
            f"Config path: {self.config_path}",
            f"Backup dir: {self.backup_dir}",
            f"Dynamic entries: {len(self.dynamic_entries)}",
            "",
            WidgetFactory.debug_dump()
        ]
        
        logger.info("\n".join(info))
    
    def closeEvent(self, event) -> None:
        """Handle window close"""
        if not self.applied_changes and self.backup_manager:
            logger.info("Reverting unapplied changes")
            self.backup_manager.revert_config()
        
        event.accept()