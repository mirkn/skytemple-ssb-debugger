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
from abc import abstractmethod, ABC

from desmume.emulator import DeSmuME_Memory


def pos_for_display_camera(pos: int, camera_pos: int) -> float:
    """Subtracts the camera positon, but also turns the 'subpixel' position into a float"""
    # TODO: is this actually correct...?
    pos_abs = (pos >> 8) - camera_pos
    pos_sub = (pos & 0xFF) / 0xFF
    return pos_abs + pos_sub


class AbstractScriptRuntimeState(ABC):
    """TODO: For more see sandbox.sandbox. """
    def __init__(self, mem: DeSmuME_Memory, pnt: int):
        self.mem = mem
        self.pnt = pnt

    @property
    @abstractmethod
    def _script_struct_offset(self):
        pass

    @property
    def current_script_hanger(self):
        return self.mem.unsigned.read_short(self.pnt + self._script_struct_offset + 0x10)
