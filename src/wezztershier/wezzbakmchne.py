import os
import time
import hashlib

DFAULT_MAX_BK = 10

# :::
# TODO: document me post-refactor
# ::::
class WezzBackMachine:
    def __init__(self, config_path, backup_dir, max_backups=DFAULT_MAX_BK):
        self.backup_dir = backup_dir
        self.config_path = config_path
        self.max_backups = max_backups

        self.temp_backup_path = None
        self.current_backup_path = None
        self.last_applied_content = None

    # :::
    # creates a temporary backup
    # of the config file that can be
    # used to revert changes when I
    # exit without applying them.
    # ::::
    def create_temp_backup(self):
        os.makedirs(self.backup_dir, exist_ok=True)

        with open(self.config_path, "rb") as f:
            current_config_bytes = f.read()

        temp_backup = os.path.join(self.backup_dir, "wezterm_backup_TEMP.lua")

        with open(temp_backup, "wb") as f:
            f.write(current_config_bytes)

        self.temp_backup_path = temp_backup
        self.current_backup_path = temp_backup

    # :::
    # creates a timestamped backup
    # of the config file in backup_dir.
    # if the new backup hash matches the current
    # configuration, no new backup is created. Old
    # backups are pruned if they exceed the max allowed.
    # ::::
    def create_persistent_backup(self):
        os.makedirs(self.backup_dir, exist_ok=True)

        with open(self.config_path, "rb") as f:
            current_config_bytes = f.read()

        current_hash = hashlib.sha256(current_config_bytes).hexdigest()

        backups = [
            f for f in os.listdir(self.backup_dir)
            if f.startswith("wezterm_backup_") and f.endswith(".lua") and "TEMP" not in f
        ]
        backups.sort()

        if backups:
            last_backup_path = os.path.join(self.backup_dir, backups[-1])
            with open(last_backup_path, "rb") as bf:
                last_backup_bytes = bf.read()
                
            last_backup_hash = hashlib.sha256(last_backup_bytes).hexdigest()
            if last_backup_hash == current_hash:
                self.current_backup_path = last_backup_path
                self.prune_backups(backups)
                return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"wezterm_backup_{timestamp}.lua")

        with open(backup_file, "wb") as bf:
            bf.write(current_config_bytes)

        self.current_backup_path = backup_file
        backups.append(f"wezterm_backup_{timestamp}.lua")

        backups.sort()
        self.prune_backups(backups)

    # :::
    # given a list of backups
    # filenames, removes the oldest until the
    # number of backups is within self.max_backups.
    # ::::
    def prune_backups(self, backups):
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            oldest_path = os.path.join(self.backup_dir, oldest)

            if os.path.exists(oldest_path):
                os.remove(oldest_path)

    # :::
    # reads the current configuration 
    # file, replaces the tuner block, delimited by 
    #           "-- <<TUNER-START>>" and "-- <<TUNER-END>>"
    # with new_tuner_block, and writes back to the config file.

    # returns None on success or an error message string.
    # ::::
    def update_config_file(self, new_tuner_block):
        try:
            with open(self.config_path, "r") as f:
                config_content = f.read()

            start_marker = "-- <<TUNER-START>>"
            end_marker = "-- <<TUNER-END>>"
            start_index = config_content.find(start_marker)
            end_index   = config_content.rfind(end_marker)

            if start_index != -1 and end_index != -1:
                prefix = config_content[:start_index]
                suffix = config_content[end_index + len(end_marker):]
                updated_content = prefix + new_tuner_block + suffix

                with open(self.config_path, "w") as f:
                    f.write(updated_content)

        except Exception as e:
            return f"Error: {e}"

        return None

    # :::
    # reads and stores the current config
    # file content as the last applied state.
    # ::::
    def update_last_applied(self):
        with open(self.config_path, "r") as f:
            self.last_applied_content = f.read()

    # :::
    # reverts the config file
    # to the last applied content.
    # ::::
    def revert_config(self):
        if self.last_applied_content:
            with open(self.config_path, "w") as f:
                f.write(self.last_applied_content)
