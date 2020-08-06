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
import logging
from threading import Lock
from typing import Optional

from gi.repository import Gtk, GLib, GdkPixbuf

from skytemple_files.common.ppmdu_config.data import Pmd2Data
from skytemple_files.container.bin_pack.model import BinPack
from skytemple_files.container.dungeon_bin.model import DungeonBinPack
from skytemple_files.data.md.model import Md
from skytemple_files.dungeon_data.mappa_bin.trap_list import MappaTrapType
from skytemple_files.graphics.dpc.model import Dpc
from skytemple_files.graphics.dpci.model import Dpci
from skytemple_files.graphics.dpl.model import Dpl
from skytemple_ssb_debugger.context.abstract import AbstractDebuggerControlContext
from skytemple_ssb_debugger.dungeon.model import pil_to_cairo_surface
from skytemple_ssb_debugger.dungeon.model.dungeon_state import DungeonState
from skytemple_ssb_debugger.dungeon.model.entity import DungeonEntityType
from skytemple_ssb_debugger.dungeon.model.entity_ext.monster import EntityExtMonster
from skytemple_ssb_debugger.dungeon.model.field import DungeonFieldStairType
from skytemple_ssb_debugger.dungeon.model.map import MAP_HEIGHT, MAP_WIDTH
from skytemple_ssb_debugger.dungeon.pixbuf.full_map import FullMapPixbufProvider
from skytemple_ssb_debugger.dungeon.pixbuf.small_map_icons import SmallMapPixbufProvider
from skytemple_ssb_debugger.dungeon.pixbuf import PixbufProviderTerrainType, PixbufProviderFloorType, \
    PixbufProviderMonsterType
from skytemple_ssb_debugger.emulator_thread import EmulatorThread
from skytemple_ssb_debugger.threadsafe import synchronized


dungeon_data_lock = Lock()
logger = logging.getLogger(__name__)


class DungeonStateController:
    def __init__(self, context: AbstractDebuggerControlContext, emu_thread: EmulatorThread, builder: Gtk.Builder):
        self.context = context
        self.emu_thread = emu_thread
        self.builder = builder
        self.is_loaded = False

        self._rom_data: Optional[Pmd2Data] = None
        self.addr_current_dungeon_id = None
        self.pnt_dungeon_data = None

        self._dungeon_state: Optional[DungeonState] = None

        self.small_map_model: Optional[Gtk.ListStore] = None
        self.full_map_model: Optional[Gtk.ListStore] = None

        self._current_cached_tilemap_id = None
        self._current_cached_full_map_provider: Optional[FullMapPixbufProvider] = None

        self._dungeon_bin: Optional[DungeonBinPack] = None
        self._monster_bin: Optional[BinPack] = None
        self._monster_md: Optional[Md] = None

        self._init_maps()

        # Try to refresh the maps every 2 seconds:
        GLib.timeout_add_seconds(2, self._update_maps)

        # todo


    @property
    @synchronized(dungeon_data_lock)
    def rom_data(self):
        return self._rom_data

    @rom_data.setter
    @synchronized(dungeon_data_lock)
    def rom_data(self, value):
        self._rom_data = value

    @property
    @synchronized(dungeon_data_lock)
    def dungeon_state(self):
        return self._dungeon_state

    @dungeon_state.setter
    @synchronized(dungeon_data_lock)
    def dungeon_state(self, value):
        self._dungeon_state = value

    def enable(self, rom_data: Pmd2Data):
        self.is_loaded = True
        self._rom_data = rom_data
        self.addr_current_dungeon_id = rom_data.binaries['arm9.bin'].blocks["DungeonCurrentId"].begin_absolute
        self.pnt_dungeon_data = rom_data.binaries['arm9.bin'].pointers["DungeonData"]

        self.dungeon_state = DungeonState(
            self.emu_thread, self.pnt_dungeon_data.begin_absolute, self.addr_current_dungeon_id
        )

        self._dungeon_bin = self.context.get_dungeon_bin()
        self._monster_bin = self.context.get_monster_bin()
        self._monster_md = self.context.get_monster_md()

    def disable(self):
        self.is_loaded = False
        self.rom_data = None

    def _init_maps(self):
        small_map: Gtk.IconView = self.builder.get_object('dungeon_state_small_map')
        full_map: Gtk.IconView = self.builder.get_object('dungeon_state_full_map')
        self.small_map_model: Gtk.ListStore = Gtk.ListStore(GdkPixbuf.Pixbuf)
        self.full_map_model: Gtk.ListStore = Gtk.ListStore(GdkPixbuf.Pixbuf)
        small_map.set_model(self.small_map_model)
        small_map.set_pixbuf_column(0)
        full_map.set_model(self.full_map_model)
        full_map.set_pixbuf_column(0)

    def _update_maps(self):
        # TODO: Boost.
        # Clear the map views.
        self.small_map_model.clear()
        self.full_map_model.clear()
        if self.is_loaded and self.dungeon_state.valid:
            try:
                map = self.dungeon_state.load_map()
                full_pixbuf_provider = self._get_current_full_map_provider()
                # TODO: Pre-fill and iterate over the two icon models and replace them in GLib.idle_add
                for y in range(0, MAP_HEIGHT):
                    for x in range(0, MAP_WIDTH):
                        map_field = map.get(x, y)

                        terrain_type = PixbufProviderTerrainType(map_field.terrain_type.value)
                        if map_field.is_impassable_wall:
                            terrain_type = PixbufProviderTerrainType.IMPASSABLE_WALL
                        elif map_field.is_natural_junction:
                            terrain_type = PixbufProviderTerrainType.JUNCTION
                        elif map_field.is_in_monster_house:
                            terrain_type = PixbufProviderTerrainType.MONSTER_HOUSE
                        elif map_field.is_in_kecleon_shop:
                            terrain_type = PixbufProviderTerrainType.KECLEON_SHOP

                        floor_type = PixbufProviderFloorType.NONE
                        entity_on_floor = map_field.entity_on_floor
                        if entity_on_floor:
                            if entity_on_floor.entity_type == DungeonEntityType.ITEM:
                                # Items
                                floor_type = PixbufProviderFloorType.ITEM
                            else:
                                # Traps
                                if entity_on_floor.load_extended_data().trap_id == MappaTrapType.WONDER_TILE.value:
                                    # Wonder Tile
                                    floor_type = PixbufProviderFloorType.WONDER_TILE
                                else:
                                    # Other Traps
                                    floor_type = PixbufProviderFloorType.OTHER_TRAP
                            # TODO: Hidden stairs?
                        elif map_field.stair_type != DungeonFieldStairType.NONE:
                            floor_type = PixbufProviderFloorType.STAIRS

                        monster_type = PixbufProviderMonsterType.NONE
                        monster_on_tile = map_field.monster_on_tile
                        if monster_on_tile:
                            monster_data: EntityExtMonster = monster_on_tile.load_extended_data()
                            if monster_data.enemy_flag:
                                monster_type = PixbufProviderMonsterType.ENEMY
                            elif monster_data.ally_flag == 1:
                                monster_type = PixbufProviderMonsterType.ALLY_ENEMY
                            elif monster_data.teamleader_flag:
                                monster_type = PixbufProviderMonsterType.TEAM_LEADER
                            else:
                                monster_type = PixbufProviderMonsterType.ALLY
                        pixbuf = SmallMapPixbufProvider.get(terrain_type, floor_type, monster_type)
                        self.small_map_model.append([pixbuf])

                        full_map_pixbuf = full_pixbuf_provider.get(
                            map_field.texture_index, floor_type, monster_type,
                            entity_on_floor, monster_on_tile
                        )
                        self.full_map_model.append([full_map_pixbuf])

            except BaseException as ex:
                # TODO: Log the error & mark as invalid / not in dungeon
                logger.warning("Error rendering the dungeon map", exc_info=ex)
                pass

        GLib.timeout_add_seconds(2, self._update_maps)

    def _get_current_full_map_provider(self) -> FullMapPixbufProvider:
        # TODO: We don't know the tileset yet.
        # TODO: Handle MapBG tilesets.
        tilemap_id = 1
        if self._current_cached_tilemap_id == tilemap_id and self._current_cached_full_map_provider:
            return self._current_cached_full_map_provider
        self._current_cached_tilemap_id = tilemap_id
        pil_image = self._get_dpc(1).chunks_to_pil(self._get_dpci(1), self._get_dpl(1).palettes, 1)
        self._current_cached_full_map_provider = FullMapPixbufProvider(
            pil_to_cairo_surface(pil_image.convert('RGBA')),
            self._monster_bin, self._monster_md
        )
        return self._current_cached_full_map_provider

    def _get_dpc(self, idx) -> Dpc:
        return self._dungeon_bin.get(f'dungeon{idx}.dpc')

    def _get_dpci(self, idx) -> Dpci:
        return self._dungeon_bin.get(f'dungeon{idx}.dpci')

    def _get_dpl(self, idx) -> Dpl:
        return self._dungeon_bin.get(f'dungeon{idx}.dpl')

