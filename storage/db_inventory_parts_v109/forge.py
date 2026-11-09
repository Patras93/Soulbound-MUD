# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: forge; AST bez zmian."""
from .dependencies import *

class ForgeV109Mixin:
    def equipment_reforge(self, account_id, item_id):
        return self.conn.execute(
            "SELECT affix,affix_amount,rerolls FROM equipment_reforges WHERE account_id=? AND item_id=?",
            (account_id,item_id),
        ).fetchone()

    def save_equipment_reforge(self, account_id, item_id, affix, amount):
        self.conn.execute(
            "INSERT INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,1) "
            "ON CONFLICT(account_id,item_id) DO UPDATE SET affix=excluded.affix,affix_amount=excluded.affix_amount,rerolls=equipment_reforges.rerolls+1",
            (account_id,item_id,affix,int(amount)),
        )
        self.conn.commit()

    def equipment_runes_v0925(self, account_id, item_id):
        return self.conn.execute(
            "SELECT socket_index,rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? ORDER BY socket_index",
            (account_id,item_id),
        ).fetchall()

    def add_equipment_rune_v0925(self, account_id, item_id, socket_index, rune_id):
        self.conn.execute(
            "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
            (account_id,item_id,int(socket_index),rune_id),
        )
        self.conn.commit()

    def remove_equipment_rune_v0925(self, account_id, item_id, socket_index):
        row=self.conn.execute(
            "SELECT rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        ).fetchone()
        if not row: return None
        self.conn.execute(
            "DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        )
        self.conn.commit()
        return str(row["rune_id"])

    def equipment_upgrade_level_v03042(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT upgrade_level FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return max(0, int(row["upgrade_level"])) if row else 0

    def set_equipment_upgrade_level_v03042(self, account_id, item_id, level):
        existing=self.equipment_upgrade_level_v03042(account_id,item_id)
        # Existing +levels are not rolled back when an admin lowers the cap.
        level = max(0, min(max(V03042_EQ_UPGRADE_MAX, existing), int(level)))
        if level <= 0:
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "INSERT INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?) "
                "ON CONFLICT(account_id,item_id) DO UPDATE SET upgrade_level=excluded.upgrade_level",
                (account_id, item_id, level),
            )
        self.conn.commit()

    def clear_equipment_crafting_v0925(self, account_id, item_id):
        self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.commit()

    def transfer_equipment_crafting_v0925(self, from_account_id, to_account_id, item_id):
        from systems.equipment_evolution_v10500 import is_evolved
        if is_evolved(self.conn, from_account_id, item_id):
            raise ValueError('Ewoluowany przedmiot jest przypisany do postaci; najpierw wyzeruj ewolucję u Haldora.')
        ref=self.equipment_reforge(from_account_id,item_id)
        runes=list(self.equipment_runes_v0925(from_account_id,item_id))
        upgrade=self.equipment_upgrade_level_v03042(from_account_id,item_id)
        if ref:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,?)",
                (to_account_id,item_id,ref["affix"],int(ref["affix_amount"]),int(ref["rerolls"])),
            )
            self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        for rr in runes:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
                (to_account_id,item_id,int(rr["socket_index"]),rr["rune_id"]),
            )
        if runes:
            self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        if upgrade > 0:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?)",
                (to_account_id,item_id,int(upgrade)),
            )
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (from_account_id,item_id),
            )
        self.conn.commit()

    def crafting_mastery_v03054(self, account_id, profession, category):
        profession=str(profession); category=str(category)
        self.conn.execute(
            "INSERT OR IGNORE INTO crafting_mastery_v03054(account_id,profession,category) VALUES(?,?,?)",
            (int(account_id),profession,category),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT * FROM crafting_mastery_v03054 WHERE account_id=? AND profession=? AND category=?",
            (int(account_id),profession,category),
        ).fetchone()

    def add_crafting_mastery_action_v03054(self, account_id, profession, category, critical=False, legendary=False):
        self.crafting_mastery_v03054(account_id,profession,category)
        self.conn.execute(
            "UPDATE crafting_mastery_v03054 SET actions=actions+1, criticals=criticals+?, legendary_count=legendary_count+? "
            "WHERE account_id=? AND profession=? AND category=?",
            (1 if critical else 0,1 if legendary else 0,int(account_id),str(profession),str(category)),
        )
        self.conn.commit()
        return self.crafting_mastery_v03054(account_id,profession,category)

    def crafting_masteries_v03054(self, account_id):
        return self.conn.execute(
            "SELECT * FROM crafting_mastery_v03054 WHERE account_id=? ORDER BY profession,category",
            (int(account_id),),
        ).fetchall()
