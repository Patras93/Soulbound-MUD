# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.atlascodex_part01 as _sb420_src_01
# SessionAtlasCodexMixin.item_runtime_description -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.format_item_description -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.room_special_features -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.find_description_entry -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.atlas_resource_requirement_rows -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.atlas_group_level -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.send_atlas_group_with_levels -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.send_complete_atlas_list -> player/session_methods_v4200/atlascodex_part01.py
# SessionAtlasCodexMixin.show_profession_atlas_v1602 -> player/session_methods_v4200/atlascodex_part01.py
import player.session_methods_v4200.atlascodex_part02 as _sb420_src_02
# SessionAtlasCodexMixin.show_atlas -> player/session_methods_v4200/atlascodex_part02.py
# SessionAtlasCodexMixin.codex_relic_ids -> player/session_methods_v4200/atlascodex_part02.py
# SessionAtlasCodexMixin.send_codex_name_list -> player/session_methods_v4200/atlascodex_part02.py
# SessionAtlasCodexMixin.bestiary_drop_lines -> player/session_methods_v4200/atlascodex_part02.py
# SessionAtlasCodexMixin.show_bestiary -> player/session_methods_v4200/atlascodex_part02.py
import player.session_methods_v4200.atlascodex_part03 as _sb420_src_03
# SessionAtlasCodexMixin.show_world_codex -> player/session_methods_v4200/atlascodex_part03.py
# SessionAtlasCodexMixin.describe_target -> player/session_methods_v4200/atlascodex_part03.py

# -*- coding: utf-8 -*-
"""Descriptions, atlas, bestiary and world codex."""
from core.bootstrap_economy_professions import currency_price_text

class SessionAtlasCodexMixin:

    def item_runtime_description(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method item_runtime_description")

    def format_item_description(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method format_item_description")

    def room_special_features(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method room_special_features")

    def normalize_description_query(self, value):
            table = str.maketrans(
                "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
                "acelnoszzACELNOSZZ"
            )
            return value.strip().lower().translate(table)

    def find_description_entry(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method find_description_entry")

    def atlas_fish_min_level(self, item_id, habitat):
            """Najniższy level Wędki, przy którym gatunek realnie trafia do puli."""
            item = ITEMS.get(item_id, {})
            base_id = item.get("base_resource_id", item_id)
            for level in range(1, TOOL_MAX_LEVEL + 1):
                if base_id in self.fishing_available_pool(level, habitat):
                    return level
            return None

    def atlas_resource_requirement_rows(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method atlas_resource_requirement_rows")

    def atlas_item_locations(self, item_id):
            result = []
            seen = set()
            for place, _tool, _level in self.atlas_resource_requirement_rows(item_id):
                if place not in seen:
                    seen.add(place)
                    result.append(place)
            return result

    def atlas_resource_min_level(self, item_id):
            rows = self.atlas_resource_requirement_rows(item_id)
            if not rows:
                return None, None
            tool = rows[0][1]
            level = min(row[2] for row in rows)
            return tool, level

    def atlas_group_level(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method atlas_group_level")

    async def send_atlas_group_with_levels(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send_atlas_group_with_levels")

    def atlas_names(self, item_ids):
            return ", ".join(
                sorted(
                    (ITEMS[item_id]["name"] for item_id in item_ids),
                    key=str.lower,
                )
            )

    async def send_complete_atlas_list(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send_complete_atlas_list")

    async def show_profession_atlas_v1602(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_profession_atlas_v1602")

    async def show_atlas(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_atlas")

    def codex_boss_ids(self):
            result = set()
            for mob_id, mob in MOB_TEMPLATES.items():
                if (
                    mob_id.startswith("crypt_boss_")
                    or mob_id.startswith("astral_boss_")
                    or mob_id.startswith("mythic_crypt_boss_")
                    or mob_id.startswith("mythic_astral_boss_")
                    or mob.get("world_boss")
                    or mob.get("boss_mechanic")
                ):
                    result.add(mob_id)
            return result

    def codex_relic_ids(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method codex_relic_ids")

    async def send_codex_name_list(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send_codex_name_list")

    def bestiary_spawn_room_ids(self, mob_template_id):
            base_id = canonical_bestiary_template_id(mob_template_id)
            return tuple(sorted(BESTIARY_SPAWN_ROOMS.get(base_id, ())))

    def bestiary_drop_lines(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method bestiary_drop_lines")

    async def show_bestiary(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_bestiary")

    async def show_world_codex(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_world_codex")

    async def describe_target(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method describe_target")

    async def show_name_declension(self):
            await self.send(f"ODMIANA IMIENIA: {self.character.name_nom}")
            await self.send(f"Mianownik: {self.character.name_nom}.")
            await self.send(f"Dopełniacz: {self.character.name_gen}.")
            await self.send(f"Celownik: {self.character.name_dat}.")
            await self.send(f"Biernik: {self.character.name_acc}.")
            await self.send(f"Narzędnik: {self.character.name_ins}.")
            await self.send(f"Miejscownik: {self.character.name_loc}.")
            await self.send(f"Wołacz: {self.character.name_voc}.")

# v4.20.0: exact historical implementations rebound onto original class.
SessionAtlasCodexMixin.item_runtime_description = _sb420_bind(_sb420_src_01.item_runtime_description, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.format_item_description = _sb420_bind(_sb420_src_01.format_item_description, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.room_special_features = _sb420_bind(_sb420_src_01.room_special_features, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.find_description_entry = _sb420_bind(_sb420_src_01.find_description_entry, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.atlas_resource_requirement_rows = _sb420_bind(_sb420_src_01.atlas_resource_requirement_rows, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.atlas_group_level = _sb420_bind(_sb420_src_01.atlas_group_level, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.send_atlas_group_with_levels = _sb420_bind(_sb420_src_01.send_atlas_group_with_levels, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.send_complete_atlas_list = _sb420_bind(_sb420_src_01.send_complete_atlas_list, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.show_profession_atlas_v1602 = _sb420_bind(_sb420_src_01.show_profession_atlas_v1602, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.show_atlas = _sb420_bind(_sb420_src_02.show_atlas, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.codex_relic_ids = _sb420_bind(_sb420_src_02.codex_relic_ids, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.send_codex_name_list = _sb420_bind(_sb420_src_02.send_codex_name_list, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.bestiary_drop_lines = _sb420_bind(_sb420_src_02.bestiary_drop_lines, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.show_bestiary = _sb420_bind(_sb420_src_02.show_bestiary, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.show_world_codex = _sb420_bind(_sb420_src_03.show_world_codex, globals(), "SessionAtlasCodexMixin")
SessionAtlasCodexMixin.describe_target = _sb420_bind(_sb420_src_03.describe_target, globals(), "SessionAtlasCodexMixin")

