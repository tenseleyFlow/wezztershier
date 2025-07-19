# :::
# :::: BACKUP :: configuration backup management ::::
# ::::: :::::::::::::::::::::::::::::::::::::::: :::::
#
# Handles backup creation, restoration, and pruning
# for WezTerm configuration files. Manages both
# temporary (session) and persistent (timestamped) backups.
#
# :::
# :::: FEATURES ::::
# ::::::::::::::::::::
#
#   * Temporary backups for session safety
#   * Timestamped persistent backups  
#   * Deduplication via SHA256 hashing
#   * Automatic pruning of old backups
#   * Safe config file updates with markers
#
# Author: @espadonne (mfw)
# ::::

import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# :::
# :::: CONSTANTS ::::
# :::::::::::::::::::::
DEFAULT_MAX_BACKUPS = 10
TEMP_BACKUP_SUFFIX = "wezterm_backup_TEMP.lua"
BACKUP_PREFIX = "wezterm_backup_"
BACKUP_SUFFIX = ".lua"

# Config file markers
TUNER_START_MARKER = "-- <<TUNER-START>>"
TUNER_END_MARKER = "-- <<TUNER-END>>"


# :::
# :::: WEZZBACKMACHINE :: the time lord ::::
# ::::: :::::::::::::::::::::::::::::::: :::::
#
# Manages configuration backups with both
# temporary (for session recovery) and 
# persistent (timestamped) strategies.
#
# Author: @espadonne (mfw)
# ::::
class WezzBackMachine:
    def __init__(
        self, 
        config_path: str | Path,
        backup_dir: str | Path,
        max_backups: int = DEFAULT_MAX_BACKUPS
    ):
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     using Path objects internally for
        # :::::     better cross-platform handling
        # ::::
        self.config_path = Path(config_path)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        
        # Session state
        self.temp_backup_path: Optional[Path] = None
        self.current_backup_path: Optional[Path] = None
        self.last_applied_content: Optional[str] = None
        
        logger.debug(f"WezzBackMachine initialized: config={self.config_path}, backups={self.backup_dir}")
    
    # :::
    # creates a temporary backup
    # of the config file that can be
    # used to revert changes when 
    # exiting without applying them.
    # ::::
    def create_temp_backup(self) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            current_config_bytes = self.config_path.read_bytes()
            temp_backup = self.backup_dir / TEMP_BACKUP_SUFFIX
            
            temp_backup.write_bytes(current_config_bytes)
            
            self.temp_backup_path = temp_backup
            self.current_backup_path = temp_backup
            
            logger.debug(f"Created temporary backup at {temp_backup}")
            
        except Exception as e:
            logger.error(f"Failed to create temp backup: {e}")
            raise
    
    # :::
    # creates a timestamped backup
    # of the config file in backup_dir.
    # if the new backup hash matches the current
    # configuration, no new backup is created. Old
    # backups are pruned if they exceed the max allowed.
    # ::::
    def create_persistent_backup(self) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            current_config_bytes = self.config_path.read_bytes()
            current_hash = hashlib.sha256(current_config_bytes).hexdigest()
            
            # Get existing backups
            backups = self._get_backup_list()
            
            # Check if latest backup matches current config
            if backups and self._is_duplicate_backup(backups[-1], current_hash):
                logger.debug("Skipping backup - identical to latest")
                self.current_backup_path = self.backup_dir / backups[-1]
                self._prune_backups(backups)
                return
            
            # Create new backup
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{BACKUP_PREFIX}{timestamp}{BACKUP_SUFFIX}"
            backup_path = self.backup_dir / backup_name
            
            backup_path.write_bytes(current_config_bytes)
            
            self.current_backup_path = backup_path
            backups.append(backup_name)
            
            logger.info(f"Created persistent backup: {backup_name}")
            
            # Prune old backups
            self._prune_backups(backups)
            
        except Exception as e:
            logger.error(f"Failed to create persistent backup: {e}")
            raise
    
    # :::
    # retrieves sorted list of backup filenames
    # excluding temporary backups
    # ::::
    def _get_backup_list(self) -> List[str]:
        if not self.backup_dir.exists():
            return []
        
        backups = [
            f.name for f in self.backup_dir.iterdir()
            if f.name.startswith(BACKUP_PREFIX) 
            and f.name.endswith(BACKUP_SUFFIX)
            and "TEMP" not in f.name
        ]
        
        return sorted(backups)
    
    # :::
    # checks if a backup file has the
    # same content hash as provided
    # ::::
    def _is_duplicate_backup(self, backup_name: str, compare_hash: str) -> bool:
        try:
            backup_path = self.backup_dir / backup_name
            backup_bytes = backup_path.read_bytes()
            backup_hash = hashlib.sha256(backup_bytes).hexdigest()
            return backup_hash == compare_hash
        except Exception:
            return False
    
    # :::
    # given a list of backup filenames,
    # removes the oldest until the number
    # of backups is within self.max_backups.
    # ::::
    def _prune_backups(self, backups: List[str]) -> None:
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            oldest_path = self.backup_dir / oldest
            
            try:
                if oldest_path.exists():
                    oldest_path.unlink()
                    logger.debug(f"Pruned old backup: {oldest}")
            except Exception as e:
                logger.warning(f"Failed to prune backup {oldest}: {e}")
    
    # :::
    # reads the current configuration file,
    # replaces the tuner block delimited by
    # TUNER_START_MARKER and TUNER_END_MARKER
    # with new_tuner_block, and writes back.
    #
    # returns None on success or an error message string.
    # ::::
    def update_config_file(self, new_tuner_block: str) -> Optional[str]:
        try:
            config_content = self.config_path.read_text()
            
            start_index = config_content.find(TUNER_START_MARKER)
            end_index = config_content.rfind(TUNER_END_MARKER)
            
            if start_index == -1 or end_index == -1:
                error_msg = "Config file missing tuner markers"
                logger.error(error_msg)
                return error_msg
            
            # :::
            # :::: NOTE: @espadonne (mfw)
            # :::::     we want to preserve everything outside
            # :::::     the markers, including the markers themselves
            # ::::
            prefix = config_content[:start_index]
            suffix = config_content[end_index + len(TUNER_END_MARKER):]
            updated_content = prefix + new_tuner_block + suffix
            
            self.config_path.write_text(updated_content)
            logger.debug("Config file updated successfully")
            
            return None
            
        except Exception as e:
            error_msg = f"Error updating config: {e}"
            logger.error(error_msg)
            return error_msg
    
    # :::
    # reads and stores the current config
    # file content as the last applied state.
    # ::::
    def update_last_applied(self) -> None:
        try:
            self.last_applied_content = self.config_path.read_text()
            logger.debug("Updated last applied content")
        except Exception as e:
            logger.error(f"Failed to update last applied: {e}")
            raise
    
    # :::
    # reverts the config file
    # to the last applied content.
    # ::::
    def revert_config(self) -> None:
        if not self.last_applied_content:
            logger.warning("No last applied content to revert to")
            return
        
        try:
            self.config_path.write_text(self.last_applied_content)
            logger.info("Reverted config to last applied state")
        except Exception as e:
            logger.error(f"Failed to revert config: {e}")
            raise
    
    # :::
    # cleanup temporary backups
    # (useful for explicit cleanup)
    # ::::
    def cleanup_temp_backup(self) -> None:
        if self.temp_backup_path and self.temp_backup_path.exists():
            try:
                self.temp_backup_path.unlink()
                logger.debug("Cleaned up temporary backup")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp backup: {e}")
        
        self.temp_backup_path = None