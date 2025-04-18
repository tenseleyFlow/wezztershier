# :::
# :::: WEZZTERSHIER :: dynamic PyQt6 configurator ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::: :::::
#
#
# :::
# :::: DESCRIPTION ::::
# :::::::::::::::::::::::
#
# This is a PyQt6 widget for live editing
# the (mostly) visual effects of my WezTerm
# terminal emulator.
#
#         * this code is a mess
#         * I changed my goalposts several times.
#         * also. I hate docstrings and won't switch to
#         * them unless some other person takes interest
#         * in this thing
#
# It is dynamic, that is, the GUI input elements
# are generated dynamically from static decorations
# added to `$XDG_CONFIG_HOME/wezterm/wezterm.lua`
# For instance, the following sample:
#
#     -- <<TUNER-START>>
#     -- @ui: slider(min=10, max=42, step=1) type=int
#     config.font_size = 17
#     -- @ui: slider(min=0.05, max=1.0, step=0.01) type=float
#     config.window_background_opacity = 0.27
#     -- @ui: select(options="Gruvbox Dark, Gruvbox Light, Catppuccin Mocha") type=string
#     config.color_scheme = "Gruvbox Dark"
#     -- <<TUNER-END>>
#
# Generates two sliders, with one writing back a float to the config,
# and the other writing back an integer, in addition to a select (dropdown)
# for selecting the wezterm theme, with options enumerated.
#
# Parsing is done via recursive descent, and the grammar is given
# both in `wexley.py` and GRAMMAR.md
#
# :::
# :::: TODOs ::::
# :::::::::::::::::
#
#   TODO: the application of theme is a bit jank compared to others
#         ..as in like, it hitches.
#   TODO: more robust exception handling
#   TODO: the generation of the widgets is quite messy.
#   TODO: why is this not under vcs
#   TODO: make it (the gui) less ..not-pretty? labels esp need handling
#   TODO: fallbacks really need rethinking; not really dynamic,
#         but this is just for me, so idk
#   TODO: more refactoring?
#
#
# author: @espadonne (mfw)
# ::::

import os
import sys
import wezzbakmchne
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from wexler import parse_annotations
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSlider, QLabel, QPushButton,
    QTextEdit, QFileDialog, QSpinBox, QDoubleSpinBox, QSizePolicy, QComboBox,
)

# :::
# base settings fallbacks
#
# NOTE: needs rethinking if
#       'portability' (?) ever
#       becomes a concern.
# ::::
FALLBACK_BLUR    = 40
FALLBACK_FONT    = 12
FALLBACK_THEME   = None
FALLBACK_OPACITY = 0.75

# :::
# some ui element constants
# ::::
SCALE_FACTOR = 100
LABEL_MIN_WIDTH = 150

F_DFLT_MIN = 0.0
F_DFLT_MAX = 1.0
F_DFLT_STP = 0.01

I_DFLT_MIN = 0
I_DFLT_MAX = 100
I_DFLT_STP = 1

# :::
# dynamic widget for 
# controlling wezterm visuals
#
# Author: @espadonne (mfw)
# ::::
class Wezztershier(QWidget):
    def __init__(self):
        super().__init__()

        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     I'm using env var for better
        # :::::     portability, but I think better
        # :::::     fallback searching should be done
        self.config_path = os.path.join(
            os.environ.get("XDG_CONFIG_HOME",
                os.path.join(os.path.expanduser("~"), ".config")),
                "wezterm",
                "wezterm.lua",
        )

        # :::
        # :::: NOTE: @espadonne (mfw) 
        # :::::     Trying to stick to FHS/common
        # :::::     bakup directory structure locales
        self.currentBackupDir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            "weztershire",
            "backups"
        )

        self.load_config()

        # :::
        # :::: NOTE: @espadonne (mfw) backups refactored out
        # :::::
        # :::: NOTE: @espadonne (mfw)
        # :::::     Backup strategy is as follows:
        # :::::     Upon launching the widget, save the state
        # :::::     If the user does not apply changes, revert to
        # :::::     this saved state on exit.
        # :::::     If the user applies changes, backup the state to
        # :::::     the directory described above.
        # self.temp_backup_path     = None
        # self.current_backup_path  = None
        # self.last_applied_content = self.config_content
        self.backup_manager = None
        self.applied_changes = False

        self.dynamic_entries = parse_annotations(self.config_content)
        self.dynamic_entries_map = {e['key']: e for e in self.dynamic_entries}

        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     disable ui during backup
        self.init_ui()
        self.setEnabled(False)
        self.init_backup_manager()
        self.backup_manager.create_temp_backup()
        self.sync_tuner_block()
        self.setEnabled(True)

    # :::
    # reset base config attributes
    # to established fallbacks, but not portable
    #
    # NOTE: needs rethinking if anyone but mfw uses
    # ::::
    def reset_base_attr(self):
        self.config_content  = ""
        self.blur_value      = FALLBACK_BLUR
        self.font_size_value = FALLBACK_FONT
        self.selected_theme  = FALLBACK_THEME
        self.opacity_value   = FALLBACK_OPACITY

    # :::
    # helper that just cuts
    # down on repeated unsafe cast handling
    # ::::
    def parse_param(self, params, name, default, cast=float):
        try:
            return cast(params.get(name, default))
        except (ValueError, TypeError):
            return default

    # :::
    # atttempt to read in the config
    # fallback to defaults and empty string
    # ::::
    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config_content = f.read()
                # ::: NOTE: @espadonne (mfw) old
                # self.parse_config(self.config_content)
        except Exception:
            self.reset_base_attr()

    # :::
    # just instantiate the
    # backup manager, to well,
    # begin the backup control flow
    # described elsewhere
    # ::::
    def init_backup_manager(self):
        max_backups = wezzbakmchne.DFAULT_MAX_BK
        self.backup_manager = wezzbakmchne.WezzBackMachine(
            self.config_path, self.currentBackupDir, max_backups
        )
        self.backup_manager.update_last_applied()

    # :::
    # from parsed entries,
    # build/add to the dynamic ui
    # ::::
    def init_dynamic_ui(self, parent_layout):

        # TODO: eh this is odd
        dynamic_entries = self.dynamic_entries
        self.dynamic_widget_mapping = {}

        # Map UI types to function
        # pointers or w. w/ever python calls em
        widget_creators = {
            "select": self.create_select_widget,
            "slider": self.create_slider_widget,
            "numerical": self.create_numerical_widget,
        }

        # make room and add
        # the things post-parsely
        if dynamic_entries:
            for entry in dynamic_entries:
                label = QLabel(entry['key'])
                creator = widget_creators.get(entry['ui_type'])

                if not creator:
                    continue
                
                widget = creator(entry)
                self.dynamic_widget_mapping[entry['key']] = widget
                parent_layout.addRow(label, widget)
        else:
            notice = QLabel("No dynamic config annotations found.")
            parent_layout.addRow(notice, QLabel(""))

    # :::
    # called when any dynamic
    # widget sees a change in value
    #
    # may expand later into a general signal handler
    # ::::
    def dynamic_value_changed(self, key, value):
        if self.applied_changes:
            self.applied_changes = False
            self.saveButton.setText("apply changes")
        self.sync_tuner_block()

    # :::
    # generate a tuner block
    # from the current widget values
    # ::::
    def sync_tuner_block(self):
        lines = []

        for key, widget in self.dynamic_widget_mapping.items():
            entry = self.dynamic_entries_map.get(key)
            if not entry:
                continue

            lines.append(entry['decorator'])
            data_type = entry['params'].get('type', 'float')

            if isinstance(widget, QComboBox):
                val = widget.currentText()
                line = f'{key} = "{val}"'
            elif isinstance(widget, QSlider):
                if data_type == 'int':
                    val = int(widget.value())
                    line = f"{key} = {val}"
                else:
                    val = widget.value() / SCALE_FACTOR
                    line = f"{key} = {val}"
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                val = widget.value()

                if data_type == 'int':
                    val = int(val)

                line = f"{key} = {val}"
            else:
                continue

            lines.append(line)

        tuner_block = "-- <<TUNER-START>>\n" + \
            "\n".join(lines) + \
            "\n-- <<TUNER-END>>"

        self.tuner_block_editor.setPlainText(tuner_block)
        self.update_config_file(tuner_block)

    # :::
    # Generate a slider widget
    # from the parsed decoration
    # 
    # :::: NOTE: @espadon (mfw) on casts (but not crews)
    # :::::       afaik there is no slider that natively supports
    # :::::       floats in pyqt6
    # :::::       there is trickery done to cast around and ensure
    # :::::       are typed appropriately in the wezterm config.
    # :::::       I'm planning to write a wrapper maybe idk
    # ::::
    def create_slider_widget(self, entry):
        params    = entry['params']
        value_str = entry['value']
        data_type = params.get('type', 'float')
        widget    = QSlider(Qt.Orientation.Horizontal)

        is_float = data_type == 'float' or '.' in value_str

        if is_float:
            step = float(params.get("step"))   or F_DFLT_STP
            min_val = float(params.get("min")) or F_DFLT_MIN
            max_val = float(params.get("max")) or F_DFLT_MAX

            widget.setMinimum(int(min_val * SCALE_FACTOR))
            widget.setMaximum(int(max_val * SCALE_FACTOR))
            widget.setSingleStep(int(step * SCALE_FACTOR))

            try:
                init_val = float(value_str)
            except ValueError:
                init_val = min_val

            widget.setValue(int(init_val * SCALE_FACTOR))
            widget.valueChanged.connect(
                lambda v, k=entry['key']: self.dynamic_value_changed(k, v / SCALE_FACTOR)
            )
        else:
            step = int(params.get("step"))   or I_DFLT_STP
            min_val = int(params.get("min")) or I_DFLT_MIN
            max_val = int(params.get("max")) or I_DFLT_MAX

            widget.setMinimum(min_val)
            widget.setMaximum(max_val)
            widget.setSingleStep(step)

            try:
                init_val = int(float(value_str))
            except ValueError:
                init_val = min_val

            widget.setValue(init_val)
            widget.valueChanged.connect(
                lambda val, k=entry['key']: self.dynamic_value_changed(k, val)
            )

        return widget

    # :::
    # Generate a numerical
    # input from a parsed decorator
    #
    # NOTE: this needs reapproaching and is mostly
    #       this way now because I have things default
    #       to float if not typed. Mistake. Big Mistake. Pain.
    # ::::
    def create_numerical_widget(self, entry):
        params   = entry['params']
        val_str  = entry['value']
        is_float = params.get("type", "float") == "float"
        # data_type = params.get("type", "float")

        step = self.parse_param(params, "step", 1, float)
        min_val = self.parse_param(params, "min", 0.0, float)
        max_val = self.parse_param(params, "max", 100.0, float)

        try:
            init_val = float(val_str)
        except Exception:
            init_val = min_val

        if is_float:
            widget = QDoubleSpinBox()
            widget.setDecimals(2)
        else:
            widget = QSpinBox()

        widget.setValue(init_val if is_float else int(init_val))
        widget.setSingleStep(step if is_float else int(step))
        widget.setMinimum(min_val if is_float else int(min_val))
        widget.setMaximum(max_val if is_float else int(max_val))
        widget.valueChanged.connect(lambda val, k=entry['key']: self.dynamic_value_changed(k, val))

        return widget

    # :::
    # Generate a select widget
    # from the parsed decoration
    # ::::
    def create_select_widget(self, entry):
        widget = QComboBox()
        params = entry['params']
        value_str = entry['value']
        current_val = value_str.strip("\"'")
        options = [opt.strip()
            for opt in params.get("options", "").split(",")
            if opt.strip()
        ]

        widget.addItems(options)

        if current_val in options:
            widget.setCurrentText(current_val)
        else:
            widget.setCurrentIndex(0)

        return widget

    # :::
    # Build the UI elements/
    # inputs controlling backup behavior
    # ::::
    def init_backup_controls(self, layout):
        max_backups_layout = QHBoxLayout()
        maxBackupsLabel = QLabel("Max Backups:")
        max_backups_layout.addWidget(maxBackupsLabel)
        self.maxBackupsSpin = QSpinBox()

        self.maxBackupsSpin.setValue(10)
        self.maxBackupsSpin.setMinimum(1)
        self.maxBackupsSpin.setMaximum(999)

        self.maxBackupsSpin.setFixedWidth(60)
        self.maxBackupsSpin.setAlignment(Qt.AlignmentFlag.AlignRight)

        max_backups_layout.addWidget(self.maxBackupsSpin)
        max_backups_layout.addStretch()
        layout.addLayout(max_backups_layout)

        backup_dir_layout = QHBoxLayout()
        backupDirLabel = QLabel("Backup Directory:")
        backup_dir_layout.addWidget(backupDirLabel)
        browseButton = QPushButton("Browse...")

        browseButton.clicked.connect(self.browse_for_directory)
        backup_dir_layout.addWidget(browseButton)

        self.backupDirPathLabel = QLabel("")
        self.backupDirPathLabel.setStyleSheet("font-style: italic; font-size: 9px; letter-spacing: 1.4px; color: #C78726; font-weight: 150")
        self.backupDirPathLabel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.backupDirPathLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        backup_dir_layout.addWidget(self.backupDirPathLabel, 1)
        layout.addLayout(backup_dir_layout)

    # :::
    # build dynamic controls
    # form layourt from parsed annotations
    # by adding each label-widget pair to the form
    # ::::
    def init_dynamic_controls(self, layout):
        dynamic_label = QLabel("Dynamic Config Editor:")
        layout.addWidget(dynamic_label)
        # dynamic_ui_layout = QVBoxLayout()
        dynamic_ui_layout = QFormLayout()
        dynamic_ui_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        dynamic_ui_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        dynamic_ui_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.init_dynamic_ui(dynamic_ui_layout)
        layout.addLayout(dynamic_ui_layout)

    # :::
    # area for the
    # tuning block preview
    # ::::
    def init_writeback_area(self, layout):
        self.tuner_block_editor = QTextEdit()
        self.tuner_block_editor.setReadOnly(True)
        layout.addWidget(self.tuner_block_editor)

        self.saveButton = QPushButton("apply changes")
        self.saveButton.clicked.connect(self.writeback)
        layout.addWidget(self.saveButton)

    # :::
    # initializes main UI elements:
    # backup controls, dynamically generated ones,
    # the writeback preview area
    # ::::
    def init_ui(self):
        self.setWindowTitle("wezztershier")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout()

        self.init_backup_controls(layout)
        self.init_dynamic_controls(layout)
        self.init_writeback_area(layout)

        self.setLayout(layout)
        self.resize(780, 420)
        # self.sync_tuner_block()
        self.update_backup_dir_label()

    # :::
    # opens what should be
    # default system file dialog
    # ::::
    def browse_for_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if directory:
            self.currentBackupDir = directory
            self.update_backup_dir_label()

    # :::
    # updates displayed path 
    # for the current backup dir
    # checks for width constraint but need to
    # get rid of the magic number...
    # ::::
    def update_backup_dir_label(self):
        if not hasattr(self, 'backupDirPathLabel'):
            return

        fm = QFontMetrics(self.backupDirPathLabel.font())
        label_width = int(self.backupDirPathLabel.width() * 0.7) or LABEL_MIN_WIDTH
        elided = fm.elidedText(self.currentBackupDir, Qt.TextElideMode.ElideMiddle, label_width)
        self.backupDirPathLabel.setText(elided)

    # :::
    # use the backup manager to update 
    # the configuration file with the new tuner block.
    # ::::
    def update_config_file(self, new_tuner_block):
        err = self.backup_manager.update_config_file(new_tuner_block)
        if err:
            self.saveButton.setText(err)

    # :::
    # writes current config (preview)
    # to the config file, creates (persistent)
    # backup, and updates
    #
    # NOTE: one could make a case this is kinda cosmetic
    # ::::
    def writeback(self):
        self.update_config_file(self.tuner_block_editor.toPlainText())
        self.backup_manager.create_persistent_backup()
        self.backup_manager.update_last_applied()
        self.applied_changes = True
        self.saveButton.setText("changes applied!")

    # :::
    # before closing a window, revert
    # the config to the pre-launch state
    # ::::
    def closeEvent(self, event):
        if not self.applied_changes:
            self.backup_manager.revert_config()

        # ::: NOTE: acknowledge and proceed w. close
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Wezztershier()
    window.show()
    sys.exit(app.exec())
