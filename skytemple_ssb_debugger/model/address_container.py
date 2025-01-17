#  Copyright 2020-2021 Capypara and the SkyTemple Contributors
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
from threading import Lock

from skytemple_ssb_debugger.threadsafe import synchronized_now

container_lock = Lock()


class AddressContainer:
    """A very simple container for a single value (an address)"""
    def __init__(self, address):
        self._address = address

    @synchronized_now(container_lock)
    def get(self):
        return self._address

    @synchronized_now(container_lock)
    def set(self, value):
        self._address = value
