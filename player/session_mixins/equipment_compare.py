# -*- coding: utf-8 -*-
"""Inventory equipment comparison outside shops, Soulbound v0.60.0."""

from core.mines_threat import EQUIPMENT_SLOT_NAMES, ITEMS
from network.protocol_gameplay_utils import (
    find_by_name,
    normalize_lookup_text,
    v03042_upgrade_defense_bonus,
    v03042_upgrade_primary_stat,
    v03042_upgrade_stat_bonus,
)
from systems.equipment_crafting import CLASS_SET_STAT_NAMES
from systems.items_resources import MATERIAL_PROPERTY_NAMES


class SessionEquipmentCompareV0600Mixin:
    def _comparison_valid_slots_v0600(self, item):
        logical = str(item.get("slot") or "")
        if logical == "ring":
            return {"ring", "ring1", "ring2"}
        if logical == "charm":
            return {"charm", "charm1", "charm2"}
        if logical == "earring":
            return {"earring", "earring1", "earring2"}
        return {logical}

    def _comparison_snapshot_v0600(self, item_id, item, slot=None):
        defense = int(item.get("defense", 0) or 0)
        stats = {str(k): int(v or 0) for k, v in (item.get("stats") or {}).items()}
        props = {str(k): float(v or 0) for k, v in (item.get("properties") or {}).items()}

        reforge = self.server.db.equipment_reforge(self.account_id, item_id)
        affix = str(reforge["affix"]) if reforge else str(item.get("affix") or "")
        affix_amount = int(reforge["affix_amount"]) if reforge else int(item.get("affix_amount", 0) or 0)
        if affix:
            stats[affix] = stats.get(affix, 0) + affix_amount

        upgrade_level = int(self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id) or 0)
        defense += int(v03042_upgrade_defense_bonus(item, upgrade_level))
        if upgrade_level > 0:
            upgrade_stat = v03042_upgrade_primary_stat(item, affix)
            upgrade_amount = int(v03042_upgrade_stat_bonus(upgrade_level))
            if upgrade_stat and upgrade_amount:
                stats[str(upgrade_stat)] = stats.get(str(upgrade_stat), 0) + upgrade_amount

        try:
            for row in self.server.db.equipment_runes_v0925(self.account_id, item_id):
                rune = ITEMS.get(str(row["rune_id"]), {})
                for key, value in (rune.get("rune_stats") or {}).items():
                    stats[str(key)] = stats.get(str(key), 0) + int(value or 0)
                for key, value in (rune.get("rune_properties") or {}).items():
                    props[str(key)] = props.get(str(key), 0.0) + float(value or 0)
        except Exception:
            pass

        # Gems are tied to a concrete equipped slot, so only count them for that slot.
        if slot:
            try:
                for row in self.server.db.socketed_gems(self.account_id, slot, item_id):
                    gem = ITEMS.get(str(row["gem_id"]), {})
                    gaffix = str(gem.get("affix") or "")
                    if gaffix:
                        stats[gaffix] = stats.get(gaffix, 0) + int(gem.get("affix_amount", 0) or 0)
            except Exception:
                pass

        try:
            sockets = int(self.equipment_total_socket_capacity_v03114(item_id, item, "gem"))
        except Exception:
            sockets = 0
        return {"defense": defense, "stats": stats, "properties": props, "sockets": sockets, "upgrade": upgrade_level}

    def _format_delta_v0600(self, value, percent=False):
        if abs(float(value)) < 1e-9:
            return "0%" if percent else "0"
        sign = "+" if value > 0 else ""
        if percent:
            return f"{sign}{value:g}%"
        return f"{sign}{int(value)}"

    def _comparison_delta_parts_v0600(self, new, old):
        parts = []
        ddef = int(new["defense"]) - int(old["defense"])
        if ddef:
            parts.append(f"Obrona {self._format_delta_v0600(ddef)}")
        keys = sorted(set(new["stats"]) | set(old["stats"]))
        for key in keys:
            diff = int(new["stats"].get(key, 0)) - int(old["stats"].get(key, 0))
            if diff:
                parts.append(f"{CLASS_SET_STAT_NAMES.get(key, key)} {self._format_delta_v0600(diff)}")
        pkeys = sorted(set(new["properties"]) | set(old["properties"]))
        for key in pkeys:
            diff = float(new["properties"].get(key, 0.0)) - float(old["properties"].get(key, 0.0))
            if abs(diff) > 1e-9:
                parts.append(f"{MATERIAL_PROPERTY_NAMES.get(key, key)} {self._format_delta_v0600(diff, True)}")
        dsockets = int(new["sockets"]) - int(old["sockets"])
        if dsockets:
            parts.append(f"Gniazda {self._format_delta_v0600(dsockets)}")
        return parts

    async def compare_equipment_v0600(self, query=""):
        raw = str(query or "").strip()
        if not raw:
            await self.send("Użycie: porownaj <przedmiot>, na przykład porownaj Runiczny Pierścień Harmonii.")
            return
        owned = {
            item_id: item for item_id, item in ITEMS.items()
            if item.get("type") == "armor" and int(self.server.db.item_qty(self.account_id, item_id)) > 0
        }
        found = find_by_name(owned, raw)
        if not found:
            q = normalize_lookup_text(raw)
            candidates = [item.get("name", iid) for iid, item in owned.items() if q and q in normalize_lookup_text(item.get("name", iid))]
            if candidates:
                await self.send("Nazwa jest niejednoznaczna. Pasują: " + "; ".join(candidates[:10]) + ".")
            else:
                await self.send("Nie masz takiego elementu EQ w ekwipunku.")
            return
        item_id, item = found
        if not self.auto_equipment_eligible_v03040(item):
            await self.send("Uwaga: tego przedmiotu nie możesz obecnie założyć z powodu wymagań klasy albo poziomu.")
        valid_slots = self._comparison_valid_slots_v0600(item)
        equipped_rows = [row for row in self.server.db.equipment(self.account_id) if str(row["slot"]) in valid_slots]
        await self.send(f"PORÓWNANIE EQ: {item.get('name', item_id)}. Slot: {EQUIPMENT_SLOT_NAMES.get(item.get('slot'), item.get('slot','?'))}.")
        await self.send(self.format_item_description(item_id, item))
        if not equipped_rows:
            new = self._comparison_snapshot_v0600(item_id, item, None)
            zero = {"defense": 0, "stats": {}, "properties": {}, "sockets": 0, "upgrade": 0}
            parts = self._comparison_delta_parts_v0600(new, zero)
            await self.send("W tym slocie nic nie masz założonego. Zysk po założeniu: " + (", ".join(parts) if parts else "brak liczbowych statystyk") + ".")
            return
        for row in equipped_rows:
            current_id = str(row["item_id"])
            current = ITEMS.get(current_id)
            if not current:
                continue
            slot = str(row["slot"])
            slot_name = EQUIPMENT_SLOT_NAMES.get(slot, slot)
            if current_id == item_id:
                await self.send(f"{slot_name}: ten przedmiot jest już założony.")
                continue
            new = self._comparison_snapshot_v0600(item_id, item, None)
            old = self._comparison_snapshot_v0600(current_id, current, slot)
            parts = self._comparison_delta_parts_v0600(new, old)
            summary = ", ".join(parts) if parts else "brak różnic liczbowych"
            await self.send(f"{slot_name}: zamiast {current.get('name', current_id)} otrzymasz: {summary}.")
