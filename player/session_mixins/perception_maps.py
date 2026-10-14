# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.perceptionmaps_part01 as _sb420_src_01
# SessionPerceptionMapsMixin.visible_companion_for_look_v1801 -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.visible_player_for_look -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.visible_mob_for_look -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.visible_item_for_look -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.look_at_player -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.look_at_npc -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.look_at_mob -> player/session_methods_v4200/perceptionmaps_part01.py
# SessionPerceptionMapsMixin.look_at_item -> player/session_methods_v4200/perceptionmaps_part01.py
import player.session_methods_v4200.perceptionmaps_part02 as _sb420_src_02
# SessionPerceptionMapsMixin.look -> player/session_methods_v4200/perceptionmaps_part02.py
# SessionPerceptionMapsMixin.show_global_generator_v025 -> player/session_methods_v4200/perceptionmaps_part02.py
# SessionPerceptionMapsMixin.show_exits -> player/session_methods_v4200/perceptionmaps_part02.py
# SessionPerceptionMapsMixin.show_instance_map_summary -> player/session_methods_v4200/perceptionmaps_part02.py
import player.session_methods_v4200.perceptionmaps_part03 as _sb420_src_03
# SessionPerceptionMapsMixin.show_instance_map -> player/session_methods_v4200/perceptionmaps_part03.py
# SessionPerceptionMapsMixin.discover_instance_secret -> player/session_methods_v4200/perceptionmaps_part03.py
# SessionPerceptionMapsMixin.world_secrets_command_v1190 -> player/session_methods_v4200/perceptionmaps_part03.py
# SessionPerceptionMapsMixin.show_map -> player/session_methods_v4200/perceptionmaps_part03.py
# SessionPerceptionMapsMixin.show_crypt_info -> player/session_methods_v4200/perceptionmaps_part03.py
# SessionPerceptionMapsMixin.show_astral_info -> player/session_methods_v4200/perceptionmaps_part03.py

# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: perception_maps."""

from core.progression_600 import soul_tier_title_for_class
from datetime import datetime, timezone
from systems.mercenary_taverns import mercenary_follow_notice_v12210
from world.world_secrets_v1190 import (
    secret_room_id_v1190, secret_room_identity_v1190, world_secret_roll_v1190,
    SECRET_ARCHIVISTS_V1190,
)

class SessionPerceptionMapsMixin:
    def visible_companion_for_look_v1801(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method visible_companion_for_look_v1801")

    def visible_player_for_look(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method visible_player_for_look")

    def visible_npc_for_look(self, query):
            current = v0160_npcs_in_room(self.character.room_id)
            return self.find_description_entry(current, query)

    def visible_mob_for_look(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method visible_mob_for_look")

    def visible_item_for_look(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method visible_item_for_look")

    async def look_at_player(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method look_at_player")

    async def look_at_npc(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method look_at_npc")

    async def look_at_mob(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method look_at_mob")

    async def look_at_item(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method look_at_item")

    async def look(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method look")

    async def show_global_generator_v025(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_global_generator_v025")

    async def show_exits(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_exits")

    async def show_instance_map_summary(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_instance_map_summary")

    async def show_instance_map(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_instance_map")

    async def discover_instance_secret(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method discover_instance_secret")

    async def world_secrets_command_v1190(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method world_secrets_command_v1190")

    async def show_map(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_map")

    async def show_crypt_info(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_crypt_info")

    async def show_astral_info(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_astral_info")

# v4.20.0: exact historical implementations rebound onto original class.
SessionPerceptionMapsMixin.visible_companion_for_look_v1801 = _sb420_bind(_sb420_src_01.visible_companion_for_look_v1801, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.visible_player_for_look = _sb420_bind(_sb420_src_01.visible_player_for_look, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.visible_mob_for_look = _sb420_bind(_sb420_src_01.visible_mob_for_look, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.visible_item_for_look = _sb420_bind(_sb420_src_01.visible_item_for_look, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.look_at_player = _sb420_bind(_sb420_src_01.look_at_player, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.look_at_npc = _sb420_bind(_sb420_src_01.look_at_npc, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.look_at_mob = _sb420_bind(_sb420_src_01.look_at_mob, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.look_at_item = _sb420_bind(_sb420_src_01.look_at_item, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.look = _sb420_bind(_sb420_src_02.look, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_global_generator_v025 = _sb420_bind(_sb420_src_02.show_global_generator_v025, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_exits = _sb420_bind(_sb420_src_02.show_exits, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_instance_map_summary = _sb420_bind(_sb420_src_02.show_instance_map_summary, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_instance_map = _sb420_bind(_sb420_src_03.show_instance_map, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.discover_instance_secret = _sb420_bind(_sb420_src_03.discover_instance_secret, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.world_secrets_command_v1190 = _sb420_bind(_sb420_src_03.world_secrets_command_v1190, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_map = _sb420_bind(_sb420_src_03.show_map, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_crypt_info = _sb420_bind(_sb420_src_03.show_crypt_info, globals(), "SessionPerceptionMapsMixin")
SessionPerceptionMapsMixin.show_astral_info = _sb420_bind(_sb420_src_03.show_astral_info, globals(), "SessionPerceptionMapsMixin")

