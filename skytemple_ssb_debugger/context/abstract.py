#  Copyright 2020 Parakoopa
#
#  This file is part of SkyTemple.
#
#  SkyTemple is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SkyTemple is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SkyTemple.  If not, see <https://www.gnu.org/licenses/>.
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from skytemple_files.common.ppmdu_config.data import Pmd2Data
from skytemple_files.common.project_file_manager import ProjectFileManager
from skytemple_files.common.script_util import ScriptFiles

if TYPE_CHECKING:
    from skytemple_ssb_debugger.model.ssb_files.file_manager import SsbFileManager

PROJECT_DIR_SUBDIR_NAME = 'debugger'
PROJECT_DIR_MACRO_NAME = 'Macros'


class AbstractDebuggerControlContext(ABC):
    """
    Context that controls what options are available in the UI, where the UI get's it's data from,
    and hooks to handle some events.

    This is used to allow the debugger GUI to be available as a standalone application and as a UI managed by
    the SkyTemple main application.
    """

    @abstractmethod
    def allows_interactive_file_management(self) -> bool:
        """Returns whether or not this context allows the user to load ROMs via the UI"""

    @abstractmethod
    def before_quit(self) -> bool:
        """Handles quit requests. If False is returned, the quit is aborted."""

    @abstractmethod
    def on_quit(self):
        """Handles the quit of the debugger."""

    @abstractmethod
    def open_rom(self, filename: str):
        """
        Opens a ROM project.
        May raise NotImplementedError if self.allows_interactive_file_management() returns False.
        """

    @abstractmethod
    def get_project_dir(self) -> str:
        """Returns the project directory."""

    def get_project_debugger_dir(self) -> str:
        """Returns the debugger directory inside the project."""
        return os.path.join(self.get_project_dir(), PROJECT_DIR_SUBDIR_NAME)

    def get_project_macro_dir(self) -> str:
        """Returns the Macros directory inside the project."""
        return os.path.join(self.get_project_dir(), PROJECT_DIR_MACRO_NAME)

    @abstractmethod
    def load_script_files(self) -> ScriptFiles:
        """Returns the information of the script files inside the ROM."""

    @abstractmethod
    def is_project_loaded(self) -> bool:
        """Returns whether or not a ROM is loaded."""

    @abstractmethod
    def get_rom_filename(self) -> str:
        """Returns the filename of the ROM loaded."""

    @abstractmethod
    def save_rom(self):
        """Saves the ROM."""

    @abstractmethod
    def get_static_data(self) -> Pmd2Data:
        """Returns the PPMDU configuration for the currently open ROM."""

    @abstractmethod
    def get_project_filemanager(self) -> ProjectFileManager:
        """Returns the project file manager for the currently open ROM."""

    @abstractmethod
    def get_ssb(self, filename, ssb_file_manager: 'SsbFileManager'):
        """Returns the SSB with the given filename from the ROM."""

    @abstractmethod
    def save_ssb(self, filename, ssb_model):
        """Updates an SSB model in the ROM and then saves the ROM."""