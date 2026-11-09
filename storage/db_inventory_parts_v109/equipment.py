# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: equipment; AST bez zmian."""
from .dependencies import *

class EquipmentV109Mixin:
    def equipment(self, account_id):
        return self.conn.execute(
            "SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot",
            (account_id,),
        ).fetchall()

    def equipped_item(self, account_id, slot):
        row = self.conn.execute(
            "SELECT item_id FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        ).fetchone()
        return row["item_id"] if row else None

    def unequip(self, account_id, slot):
        if getattr(self, '_v106_shadow_slots_disposable_copy', False):
            from systems.v10700_eq_runtime_gate import is_enabled
            if not is_enabled(self):
                raise PermissionError('v107 EQ: aktywacja fizycznych slotów niezatwierdzona')
            from systems.equipment_shadow_slots_v10600 import detach
            from systems.v10700_equipment_write_barrier import approved_instance_operation
            with approved_instance_operation(self.conn):
                return detach(self.conn, account_id, slot, self._v106_shadow_item_catalog,
                              confirm_disposable_copy=True)
        self.conn.execute(
            "DELETE FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()
