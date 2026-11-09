# -*- coding: utf-8 -*-
"""Bank, inventory, equipment, storage, transfers and crafting persistence."""

import json

from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, normalize_currency_values
from storage.db_shared import DROP_HISTORY_LIMIT, V03042_EQ_UPGRADE_MAX, is_craft_material_storage_item


from .db_inventory_parts_v109 import (
    BankCurrencyV109Mixin,
    BankItemsV109Mixin,
    InventoryV109Mixin,
    ShopLotsV109Mixin,
    MailV109Mixin,
    EquipmentV109Mixin,
    GemsV109Mixin,
    ProfessionsV109Mixin,
    EnchantV109Mixin,
    ToolsV109Mixin,
    StorageV109Mixin,
    CraftingV109Mixin,
    ForgeV109Mixin,
    HuntersV109Mixin,
    ProtectionV109Mixin,
)

class DatabaseInventoryMixin(
    BankCurrencyV109Mixin,
    BankItemsV109Mixin,
    InventoryV109Mixin,
    ShopLotsV109Mixin,
    MailV109Mixin,
    EquipmentV109Mixin,
    GemsV109Mixin,
    ProfessionsV109Mixin,
    EnchantV109Mixin,
    ToolsV109Mixin,
    StorageV109Mixin,
    CraftingV109Mixin,
    ForgeV109Mixin,
    HuntersV109Mixin,
    ProtectionV109Mixin,
):
    """Zgodny interfejs v108; stare audyty źródłowe wymagają sześciu metod lokalnie."""

    def add_item(self, account_id, item_id, qty=1, commit=True):
        from systems.equipment_inventory_flow_v10600 import tracked, add
        if tracked(self, item_id):
            return add(self, account_id, item_id, qty, commit=commit)
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = max(1, require_sqlite_int64('inventory.increment', qty))
        # v0.9.15: materiały rzemieślnicze nigdy nie zapychają zwykłego
        # inventory. Każde źródło używające add_item automatycznie kieruje
        # je do Szkatułki Rzemieślniczej.
        if is_craft_material_storage_item(item_id):
            self.add_storage_item(account_id, "craftbox", item_id, qty, commit=commit)
            return
        current = self.conn.execute(
            'SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
            (account_id, item_id)).fetchone()
        balance = self._v104_crafting_quantity(current[0]) if current else 0
        require_sqlite_int64('inventory.quantity', balance + qty)
        self.conn.execute(
            """
            INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        if commit:
            self.conn.commit()


    def add_drop_history(self, account_id, item_id, item_name, rarity, source, zone):
        self.conn.execute(
            "INSERT INTO drop_history(account_id,item_id,item_name,rarity,source,zone) "
            "VALUES(?,?,?,?,?,?)",
            (account_id, item_id, item_name, rarity, source, zone),
        )
        self.conn.execute(
            "DELETE FROM drop_history WHERE account_id=? AND id NOT IN ("
            "SELECT id FROM drop_history WHERE account_id=? ORDER BY id DESC LIMIT ?)",
            (account_id, account_id, DROP_HISTORY_LIMIT),
        )
        self.conn.commit()
        recorder = getattr(self, "record_activity_v0560", None)
        if recorder:
            recorder(
                account_id, "drop", str(item_name),
                f"Rzadkość: {rarity}. Źródło: {source or 'nieznane'}. Strefa: {zone or 'nieznana'}."
            )


    def equip(self, account_id, slot, item_id, commit=True):
        # v106: opt-in SHADOW EQUIPMENT on an explicitly marked disposable DB.
        # On production/v105 this branch never runs; old storage stays intact.
        if getattr(self, '_v106_shadow_slots_disposable_copy', False):
            from systems.v10700_eq_runtime_gate import is_enabled
            if not is_enabled(self):
                raise PermissionError('v107 EQ: aktywacja fizycznych slotów niezatwierdzona')
            from systems.equipment_shadow_slots_v10600 import attach_by_item
            from systems.v10700_equipment_write_barrier import approved_instance_operation
            with approved_instance_operation(self.conn):
                return attach_by_item(self.conn, account_id, slot, item_id,
                     self._v106_shadow_item_catalog, commit=commit,
                     confirm_disposable_copy=True)
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        if commit:
            self.conn.commit()


    def save_profession(self, account_id, profession, level, xp, actions):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        # v104 etap 13: preflight calej operacji; bez czesciowej utraty EXP.
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import write_exact_work_xp_copy
            write_exact_work_xp_copy(self, account_id, 'profession', profession,
                                     level=level, xp=xp, counter=actions)
        elif getattr(self, '_v104_live_exact_keyed_xp', False):
            # Zachowaj historyczne tworzenie profilu przy pierwszym zapisie,
            # lecz najpierw sprawdz wszystkie pola aby zly EXP nie tworzyl wiersza.
            from core.big_numbers_v10400 import canonical_uint
            canonical_uint(xp)
            require_sqlite_int64('professions.level', level)
            require_sqlite_int64('professions.actions', actions)
            self.ensure_profession(account_id, profession)
            from storage.big_number_live_keyed_xp_v10400 import write_live_keyed_xp
            write_live_keyed_xp(self, account_id, 'profession', profession,
                                level=level, xp=xp, counter=actions)
        else:
            for field, value in (('level', level), ('xp', xp), ('actions', actions)):
                require_sqlite_int64('professions.' + field, value)
            self.conn.execute(
                "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
                (level, xp, actions, account_id, profession),
            )
        if not outer_transaction_v104:
            self.conn.commit()


    def save_tool(self, account_id, tool_type, level, xp, uses):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        # v104 etap 13: nie dopuszczaj cichego przejscia przez REAL/overflow.
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import write_exact_work_xp_copy
            write_exact_work_xp_copy(self, account_id, 'tool', tool_type,
                                     level=level, xp=xp, counter=uses)
        elif getattr(self, '_v104_live_exact_keyed_xp', False):
            from core.big_numbers_v10400 import canonical_uint
            canonical_uint(xp)
            require_sqlite_int64('tools.level', level)
            require_sqlite_int64('tools.uses', uses)
            self.ensure_tool(account_id, tool_type)
            from storage.big_number_live_keyed_xp_v10400 import write_live_keyed_xp
            write_live_keyed_xp(self, account_id, 'tool', tool_type,
                                level=level, xp=xp, counter=uses)
        else:
            for field, value in (('level', level), ('xp', xp), ('uses', uses)):
                require_sqlite_int64('tools.' + field, value)
            self.conn.execute(
                "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
                (level, xp, uses, account_id, tool_type),
            )
        if not outer_transaction_v104:
            self.conn.commit()


    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        """Lossless count across sources; never SQL SUM(INTEGER) / SUM(TEXT)."""
        ids = self._v104_crafting_ids(item_ids)
        if not ids:
            return 0
        # SQLite parameter limit is platform/version-dependent. Avoid large IN
        # clauses (and their unintended failures) by batching item IDs.
        total = 0
        for start in range(0, len(ids), 450):
            batch = ids[start:start + 450]
            ph = ','.join('?' for _ in batch)
            for row in self.conn.execute(
                    f'SELECT quantity FROM inventory WHERE account_id=? AND item_id IN ({ph})',
                    (account_id, *batch)):
                total += self._v104_crafting_quantity(row[0])
            if container:
                for row in self.conn.execute(
                        f'SELECT quantity FROM profession_storage '
                        f'WHERE account_id=? AND container=? AND item_id IN ({ph})',
                        (account_id, container, *batch)):
                    total += self._v104_crafting_quantity(row[0])
        return total

