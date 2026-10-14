# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.inventoryequipment_part01 as _sb420_src_01
# SessionInventoryEquipmentMixin.parse_player_currency_transfer -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.give_player -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.inventory -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.inspect_equipped_v1225 -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.equipment -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.show_class_sets -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.equipment_item_score -> player/session_methods_v4200/inventoryequipment_part01.py
# SessionInventoryEquipmentMixin.auto_equipment_stat_weight_v11196 -> player/session_methods_v4200/inventoryequipment_part01.py
import player.session_methods_v4200.inventoryequipment_part02 as _sb420_src_02
# SessionInventoryEquipmentMixin.auto_equipment_property_weight_v11196 -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.auto_equipment_score_v03040 -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.auto_equip_best_v03040 -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.owned_armor_for_slot -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.explicit_dual_slot_and_item_query -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.equipped_jewelry -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.jewelry_socket_text -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.return_socketed_gems -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.show_geodes -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin._find_owned_geode -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.open_geode -> player/session_methods_v4200/inventoryequipment_part02.py
# SessionInventoryEquipmentMixin.show_gems -> player/session_methods_v4200/inventoryequipment_part02.py
import player.session_methods_v4200.inventoryequipment_part03 as _sb420_src_03
# SessionInventoryEquipmentMixin.cut_gem -> player/session_methods_v4200/inventoryequipment_part03.py
# SessionInventoryEquipmentMixin.socket_gem -> player/session_methods_v4200/inventoryequipment_part03.py
# SessionInventoryEquipmentMixin.show_socketed_gems -> player/session_methods_v4200/inventoryequipment_part03.py
# SessionInventoryEquipmentMixin.automatic_dual_slot_v03020 -> player/session_methods_v4200/inventoryequipment_part03.py
# SessionInventoryEquipmentMixin.equip_shortcut_dual_v03020 -> player/session_methods_v4200/inventoryequipment_part03.py
# SessionInventoryEquipmentMixin.equip_shortcut_slot_v03016 -> player/session_methods_v4200/inventoryequipment_part03.py
import player.session_methods_v4200.inventoryequipment_part04 as _sb420_src_04
# SessionInventoryEquipmentMixin.equip_item -> player/session_methods_v4200/inventoryequipment_part04.py
# SessionInventoryEquipmentMixin.unequip_item -> player/session_methods_v4200/inventoryequipment_part04.py
# SessionInventoryEquipmentMixin.consumable_resource_restore_v11196 -> player/session_methods_v4200/inventoryequipment_part04.py
# SessionInventoryEquipmentMixin.find_consumable_for_use -> player/session_methods_v4200/inventoryequipment_part04.py
# SessionInventoryEquipmentMixin.restore_missing_eren_map_v0714 -> player/session_methods_v4200/inventoryequipment_part04.py
import player.session_methods_v4200.inventoryequipment_part05 as _sb420_src_05
# SessionInventoryEquipmentMixin.use_item -> player/session_methods_v4200/inventoryequipment_part05.py

# -*- coding: utf-8 -*-
"""Inventory, equipment, consumables, gems and player transfers."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import random
from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, currency_reading_text, currency_unit_multiplier
from core.mines_threat import EQUIPMENT_SLOT_ALIASES, EQUIPMENT_SLOT_NAMES, ITEMS, is_character_bound_item
from core.progression_600 import CHARACTER_MAX_LEVEL, CLASS_MASTERY_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_MAX_TIER, soul_tier_title_for_class
from network.protocol_gameplay_utils import (
    V03042_EQ_UPGRADE_MAX,
    find_by_name,
    normalize_lookup_text,
    v03042_upgrade_defense_bonus,
    v03042_upgrade_primary_stat,
    v03042_upgrade_stat_bonus,
    v03042_upgraded_display_name,
)
from player.session_mixins.equipment_stats import moogle_board_stat_bonus_v0313
from systems.crafting_quality import ensure_crafting_quality_variant_v0332, player_item_display_name_v0335
from systems.dungeons_regions import CRYPT_AFFIXES
from systems.equipment_crafting import (
    CLASS_SET_STAT_NAMES,
    class_equipment_base_stat_pair,
    CUT_GEM_IDS,
    GEM_AFFIX_NAMES,
    GEM_DEFINITIONS,
    GEM_QUALITY_ORDER,
    GEODE_DEFINITIONS,
    GEODE_IDS,
    JEWELCRAFT_RECIPES,
    gem_quality_item_id,
    jewelry_socket_capacity,
)
from systems.items_resources import CLASS_EQUIPMENT_SETS
from systems.equipment_multiclass_v3001 import crossover_bonus_v3001, crossover_text_v3001
from world.generation_systems import V014_TREASURE_MAP_ITEM, V0243_EREN_SECRET_MAP_ITEM


class SessionInventoryEquipmentMixin:
    # v0.71.7: hot inventory paths operate on the player's small owned set
    # instead of scanning the 30k+ global ITEMS catalog and issuing item_qty()
    # once per catalog entry.
    def _owned_inventory_quantities_v0717(self):
            return {
                str(row["item_id"]): int(row["quantity"] or 0)
                for row in self.server.db.inventory(self.account_id)
                if int(row["quantity"] or 0) > 0
            }

    def _equipped_counts_v0717(self):
            counts = {}
            for row in self.server.db.equipment(self.account_id):
                item_id = str(row["item_id"])
                counts[item_id] = counts.get(item_id, 0) + 1
            return counts

    def _free_inventory_quantities_v0717(self):
            quantities = self._owned_inventory_quantities_v0717()
            for item_id, count in self._equipped_counts_v0717().items():
                if ITEMS.get(item_id, {}).get("type") == "armor":
                    quantities[item_id] = max(0, quantities.get(item_id, 0) - count)
            return quantities

    def equipped_quantity_of_item(self, item_id):
            return sum(
                1 for row in self.server.db.equipment(self.account_id)
                if row["item_id"] == item_id
            )

    def free_equipment_quantity(self, item_id):
            return max(
                0,
                self.server.db.item_qty(self.account_id, item_id)
                - self.equipped_quantity_of_item(item_id),
            )

    def resolve_transferable_equipment(self, query):
            free = self._free_inventory_quantities_v0717()
            transferable = {
                item_id: ITEMS[item_id]
                for item_id, qty in free.items()
                if (
                    qty > 0
                    and item_id in ITEMS
                    and ITEMS[item_id].get("type") == "armor"
                    and not is_character_bound_item(item_id)
                )
            }
            return find_by_name(transferable, query)

    def free_transferable_quantity(self, item_id):
            total = self.server.db.item_qty(self.account_id, item_id)
            item = ITEMS.get(item_id, {})
            if item.get("type") == "armor":
                total -= self.equipped_quantity_of_item(item_id)
            return max(0, int(total))

    def resolve_transferable_inventory_item(self, query):
            free = self._free_inventory_quantities_v0717()
            transferable = {
                item_id: ITEMS[item_id]
                for item_id, qty in free.items()
                if (
                    qty > 0
                    and item_id in ITEMS
                    and not is_character_bound_item(item_id)
                    and ITEMS[item_id].get("type") != "quest"
                )
            }
            return find_by_name(transferable, query)

    def parse_player_currency_transfer(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method parse_player_currency_transfer")

    async def give_player(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method give_player")

    async def give_equipment(self, raw):
            # Zgodność wsteczna z dawną nazwą handlera v0.9.17.
            await self.give_player(raw)

    async def inventory(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method inventory")

    async def inspect_equipped_v1225(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method inspect_equipped_v1225")

    async def equipment(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equipment")

    async def show_class_sets(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_class_sets")

    def equipment_item_score(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equipment_item_score")

    def auto_equipment_stat_weight_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_equipment_stat_weight_v11196")

    def auto_equipment_property_weight_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_equipment_property_weight_v11196")

    def auto_equipment_score_v03040(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_equipment_score_v03040")

    def auto_equipment_eligible_v03040(self, item):
            if not item or item.get("type") != "armor":
                return False
            required_level = max(0, int(item.get("required_level", 0) or 0))
            if required_level and int(self.character.character_level) < required_level:
                return False
            required_class = None if item.get("universal_all_classes") else item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                return False
            if not self.equipment_mastery_requirement_met(item):
                return False
            return True

    async def auto_equip_best_v03040(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_equip_best_v03040")

    def owned_armor_for_slot(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method owned_armor_for_slot")

    def resolve_equipment_for_equip(self, query):
            """Resolve only an explicitly selected item.

            v0.9.16 deliberately does not pick the strongest item for the player.
            Slot-only commands are handled in equip_item so they can list choices.
            """
            owned_armor = {
                item_id: ITEMS[item_id]
                for item_id, qty in self._owned_inventory_quantities_v0717().items()
                if qty > 0 and item_id in ITEMS and ITEMS[item_id].get("type") == "armor"
            }
            return find_by_name(owned_armor, query)

    def explicit_dual_slot_and_item_query(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method explicit_dual_slot_and_item_query")

    def equipment_choices_text(self, candidates):
            names = []
            seen = set()
            for _score, _item_id, item in candidates:
                name = item.get("name", "")
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
            return ", ".join(names)

    def equipped_jewelry(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equipped_jewelry")

    def socketed_gem_rows_for_item(self, slot, item_id):
            return list(
                self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                    item_id,
                )
            )

    def jewelry_socket_text(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method jewelry_socket_text")

    async def return_socketed_gems(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method return_socketed_gems")

    async def show_geodes(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_geodes")

    def _find_owned_geode(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method _find_owned_geode")

    async def open_geode(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method open_geode")

    async def show_gems(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_gems")

    async def cut_gem(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method cut_gem")

    async def socket_gem(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method socket_gem")

    async def show_socketed_gems(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_socketed_gems")

    def automatic_dual_slot_v03020(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method automatic_dual_slot_v03020")

    async def equip_shortcut_dual_v03020(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equip_shortcut_dual_v03020")

    async def equip_shortcut_slot_v03016(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equip_shortcut_slot_v03016")

    async def equip_item(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method equip_item")

    async def unequip_item(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unequip_item")

    def consumable_resource_restore_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method consumable_resource_restore_v11196")

    def find_consumable_for_use(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method find_consumable_for_use")

    def restore_missing_eren_map_v0714(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method restore_missing_eren_map_v0714")

    async def use_item(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_item")

# v4.20.0: exact historical implementations rebound onto original class.
SessionInventoryEquipmentMixin.parse_player_currency_transfer = _sb420_bind(_sb420_src_01.parse_player_currency_transfer, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.give_player = _sb420_bind(_sb420_src_01.give_player, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.inventory = _sb420_bind(_sb420_src_01.inventory, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.inspect_equipped_v1225 = _sb420_bind(_sb420_src_01.inspect_equipped_v1225, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equipment = _sb420_bind(_sb420_src_01.equipment, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.show_class_sets = _sb420_bind(_sb420_src_01.show_class_sets, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equipment_item_score = _sb420_bind(_sb420_src_01.equipment_item_score, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.auto_equipment_stat_weight_v11196 = _sb420_bind(_sb420_src_01.auto_equipment_stat_weight_v11196, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.auto_equipment_property_weight_v11196 = _sb420_bind(_sb420_src_02.auto_equipment_property_weight_v11196, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.auto_equipment_score_v03040 = _sb420_bind(_sb420_src_02.auto_equipment_score_v03040, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.auto_equip_best_v03040 = _sb420_bind(_sb420_src_02.auto_equip_best_v03040, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.owned_armor_for_slot = _sb420_bind(_sb420_src_02.owned_armor_for_slot, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.explicit_dual_slot_and_item_query = _sb420_bind(_sb420_src_02.explicit_dual_slot_and_item_query, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equipped_jewelry = _sb420_bind(_sb420_src_02.equipped_jewelry, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.jewelry_socket_text = _sb420_bind(_sb420_src_02.jewelry_socket_text, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.return_socketed_gems = _sb420_bind(_sb420_src_02.return_socketed_gems, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.show_geodes = _sb420_bind(_sb420_src_02.show_geodes, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin._find_owned_geode = _sb420_bind(_sb420_src_02._find_owned_geode, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.open_geode = _sb420_bind(_sb420_src_02.open_geode, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.show_gems = _sb420_bind(_sb420_src_02.show_gems, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.cut_gem = _sb420_bind(_sb420_src_03.cut_gem, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.socket_gem = _sb420_bind(_sb420_src_03.socket_gem, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.show_socketed_gems = _sb420_bind(_sb420_src_03.show_socketed_gems, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.automatic_dual_slot_v03020 = _sb420_bind(_sb420_src_03.automatic_dual_slot_v03020, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equip_shortcut_dual_v03020 = _sb420_bind(_sb420_src_03.equip_shortcut_dual_v03020, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equip_shortcut_slot_v03016 = _sb420_bind(_sb420_src_03.equip_shortcut_slot_v03016, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.equip_item = _sb420_bind(_sb420_src_04.equip_item, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.unequip_item = _sb420_bind(_sb420_src_04.unequip_item, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.consumable_resource_restore_v11196 = _sb420_bind(_sb420_src_04.consumable_resource_restore_v11196, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.find_consumable_for_use = _sb420_bind(_sb420_src_04.find_consumable_for_use, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.restore_missing_eren_map_v0714 = _sb420_bind(_sb420_src_04.restore_missing_eren_map_v0714, globals(), "SessionInventoryEquipmentMixin")
SessionInventoryEquipmentMixin.use_item = _sb420_bind(_sb420_src_05.use_item, globals(), "SessionInventoryEquipmentMixin")

