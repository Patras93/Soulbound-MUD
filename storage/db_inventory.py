# -*- coding: utf-8 -*-
"""Bank, inventory, equipment, storage, transfers and crafting persistence."""

import json

from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, normalize_currency_values
from storage.db_shared import DROP_HISTORY_LIMIT, V03042_EQ_UPGRADE_MAX, is_craft_material_storage_item

class DatabaseInventoryMixin:
    def ensure_bank(self, account_id):
        # v0.8.32: waluta Banku Dusz jest również wspólna dla całego konta.
        currency_account_id = self.master_account_for_character(account_id)
        self.conn.execute(
            "INSERT OR IGNORE INTO bank_balances("
            "account_id,silver,gold,mithril"
            ") VALUES(?,0,0,0)",
            (currency_account_id,),
        )
        self.conn.commit()
        return currency_account_id

    def bank_balance(self, account_id):
        currency_account_id = self.ensure_bank(account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM bank_balances "
            "WHERE account_id=?",
            (currency_account_id,),
        ).fetchone()

        silver, gold, mithril = normalize_currency_values(
            row["silver"],
            row["gold"],
            row["mithril"],
        )

        if (
            silver != int(row["silver"])
            or gold != int(row["gold"])
            or mithril != int(row["mithril"])
        ):
            self.conn.execute(
                "UPDATE bank_balances "
                "SET silver=?, gold=?, mithril=? "
                "WHERE account_id=?",
                (silver, gold, mithril, currency_account_id),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT silver,gold,mithril FROM bank_balances "
                "WHERE account_id=?",
                (currency_account_id,),
            ).fetchone()

        return row

    def change_bank_currency(self, account_id, currency, amount):
        if currency not in ("silver", "gold", "mithril"):
            raise ValueError("Nieznana waluta bankowa.")

        currency_account_id = self.master_account_for_character(account_id)
        row = self.bank_balance(account_id)
        values = {
            "silver": int(row["silver"]),
            "gold": int(row["gold"]),
            "mithril": int(row["mithril"]),
        }
        values[currency] += int(amount)

        if values[currency] < 0:
            return False

        silver, gold, mithril = normalize_currency_values(
            values["silver"],
            values["gold"],
            values["mithril"],
        )

        self.conn.execute(
            "UPDATE bank_balances "
            "SET silver=?, gold=?, mithril=? "
            "WHERE account_id=?",
            (silver, gold, mithril, currency_account_id),
        )
        self.conn.commit()
        return True

    def bank_items(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM bank_items "
            "WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def bank_item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM bank_items "
            "WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        self.conn.execute(
            """
            INSERT INTO bank_items(account_id,item_id,quantity)
            VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        current = self.bank_item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM bank_items "
                "WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE bank_items SET quantity=? "
                "WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def _persisted_dynamic_item_ids(self, prefix, log_label):
        """Find self-describing dynamic item IDs across inventory-like storage."""
        prefix=str(prefix or "")
        found=set()
        tables=self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table_row in tables:
            table=str(table_row[0])
            if not table.replace("_","").isalnum():
                continue
            try:
                cols=[str(row[1]) for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
            except Exception:
                continue
            for col in cols:
                if col not in ("item_id","jewelry_item_id","attachment_item_id"):
                    continue
                try:
                    rows=self.conn.execute(
                        f"SELECT DISTINCT {col} FROM {table} WHERE {col} LIKE ?",
                        (prefix+"%",),
                    ).fetchall()
                    found.update(str(row[0]) for row in rows if row[0])
                except Exception as exc:
                    print(f"{log_label}_SCAN_TABLE_ERROR: {type(exc).__name__}: {exc}", flush=True)
        # Housing 2.0 stores item IDs inside JSON rather than a normal item_id column.
        try:
            import json as _json
            rows=self.conn.execute("SELECT storage_json FROM player_housing_v03051").fetchall()
            for row in rows:
                try:
                    box=_json.loads(row[0] or "{}")
                except Exception:
                    continue
                if isinstance(box,dict):
                    for item_id in box:
                        item_id=str(item_id or "")
                        if item_id.startswith(prefix):
                            found.add(item_id)
        except Exception as exc:
            print(f"{log_label}_HOUSING_SCAN_ERROR: {type(exc).__name__}: {exc}", flush=True)
        return sorted(found)

    def persisted_crafting_quality_item_ids_v0332(self):
        return self._persisted_dynamic_item_ids("craftq_", "CRAFTQ")

    def persisted_infinite_equipment_item_ids_v11330(self):
        return self._persisted_dynamic_item_ids("deepq_", "DEEPQ")

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_item(self, account_id, item_id, qty=1, commit=True):
        qty = max(1, int(qty))
        # v0.9.15: materiały rzemieślnicze nigdy nie zapychają zwykłego
        # inventory. Każde źródło używające add_item automatycznie kieruje
        # je do Szkatułki Rzemieślniczej.
        if is_craft_material_storage_item(item_id):
            self.add_storage_item(account_id, "craftbox", item_id, qty, commit=commit)
            return
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

    def drop_history_rows(self, account_id, limit=20):
        return self.conn.execute(
            "SELECT item_name,rarity,source,zone,created_at FROM drop_history "
            "WHERE account_id=? ORDER BY id DESC LIMIT ?",
            (account_id, max(1, min(DROP_HISTORY_LIMIT, int(limit)))),
        ).fetchall()

    def record_shop_purchase_v1175(self, account_id, item_id, quantity, unit_paid_silver, commit=True):
        """Remember cash paid for each purchased inventory unit, including Charisma discount."""
        quantity = max(1, int(quantity))
        unit_paid_silver = max(0, int(unit_paid_silver))
        self.conn.execute(
            "INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) "
            "VALUES(?,?,?,?) ON CONFLICT(account_id,item_id,paid_silver) "
            "DO UPDATE SET quantity=quantity+excluded.quantity",
            (account_id, str(item_id), unit_paid_silver, quantity),
        )
        if commit:
            self.conn.commit()

    def shop_resale_total_v1175(self, account_id, item_id, quantity, normal_unit_silver):
        """Purchased units cannot resell above paid cash; earned loot keeps normal value."""
        remaining = max(0, int(quantity))
        normal_unit_silver = max(0, int(normal_unit_silver))
        total = 0
        for row in self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(item_id)),
        ):
            units = min(remaining, int(row['quantity']))
            total += units * min(normal_unit_silver, max(0, int(row['paid_silver'])))
            remaining -= units
            if remaining <= 0:
                break
        return total + remaining * normal_unit_silver

    def _consume_shop_purchase_lots_v1175(self, account_id, item_id, quantity, *, transfer_to=None):
        """Follow inventory removals and player-to-player transfers; caller owns transaction."""
        remaining = max(0, int(quantity))
        rows = self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(item_id)),
        ).fetchall()
        for row in rows:
            units = min(remaining, int(row['quantity']))
            if not units:
                break
            cost = int(row['paid_silver'])
            if units == int(row['quantity']):
                self.conn.execute(
                    "DELETE FROM shop_purchase_lots_v1175 "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (account_id, str(item_id), cost),
                )
            else:
                self.conn.execute(
                    "UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (units, account_id, str(item_id), cost),
                )
            if transfer_to is not None:
                self.record_shop_purchase_v1175(
                    transfer_to, item_id, units, cost, commit=False
                )
            remaining -= units
        self.conn.execute(
            "DELETE FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? AND quantity<=0",
            (account_id, str(item_id)),
        )

    def bank_purchase_lot_key_v1175(self, item_id):
        return "__bank_v1175__:" + str(item_id)

    def move_shop_purchase_basis_v1175(self, account_id, from_item_id, to_item_id, quantity):
        """Carry shop cost basis into/out of bank storage without minting cheap inventory."""
        remaining = max(0, int(quantity))
        rows = self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(from_item_id)),
        ).fetchall()
        for row in rows:
            units = min(remaining, int(row["quantity"]))
            if not units:
                break
            price = int(row["paid_silver"])
            if units == int(row['quantity']):
                self.conn.execute(
                    "DELETE FROM shop_purchase_lots_v1175 "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (account_id, str(from_item_id), price),
                )
            else:
                self.conn.execute(
                    "UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (units, account_id, str(from_item_id), price),
                )
            self.record_shop_purchase_v1175(
                account_id, to_item_id, units, price, commit=False
            )
            remaining -= units
        self.conn.execute(
            "DELETE FROM shop_purchase_lots_v1175 WHERE account_id=? "
            "AND item_id=? AND quantity<=0", (account_id, str(from_item_id)),
        )
        self.conn.commit()

    def remove_item(self, account_id, item_id, qty=1, commit=True):
        qty = max(1, int(qty))
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self._consume_shop_purchase_lots_v1175(account_id, item_id, qty)
        if commit:
            self.conn.commit()
        return True

    def transfer_inventory_item(self, from_account_id, to_account_id, item_id, qty=1):
        """Atomowo przenosi zwykły item inventory między dwiema postaciami."""
        qty = max(1, int(qty))
        if from_account_id == to_account_id:
            return False
        current = self.item_qty(from_account_id, item_id)
        if current < qty:
            return False
        try:
            self.conn.execute("BEGIN")
            new_qty = current - qty
            if new_qty <= 0:
                self.conn.execute(
                    "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                    (from_account_id, item_id),
                )
            else:
                self.conn.execute(
                    "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                    (new_qty, from_account_id, item_id),
                )
            self.conn.execute(
                """
                INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
                ON CONFLICT(account_id,item_id)
                DO UPDATE SET quantity=quantity+excluded.quantity
                """,
                (to_account_id, item_id, qty),
            )
            self._consume_shop_purchase_lots_v1175(
                from_account_id, item_id, qty, transfer_to=to_account_id
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def transfer_shared_currency(self, from_character_account_id, to_character_account_id, amount_silver):
        """Atomowy transfer wspólnego salda konta między dwoma różnymi kontami."""
        amount_silver = int(amount_silver or 0)
        if amount_silver <= 0:
            return False
        from_master = self.master_account_for_character(from_character_account_id)
        to_master = self.master_account_for_character(to_character_account_id)
        if from_master == to_master:
            return False
        from_total = int(self.shared_wallet_for_master(from_master)[0])
        to_total = int(self.shared_wallet_for_master(to_master)[0])
        if from_total < amount_silver:
            return False
        if to_total + amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
            return False
        try:
            self.conn.execute("BEGIN")
            self.set_shared_wallet_for_master(
                from_master, from_total - amount_silver, 0, 0, commit=False
            )
            self.set_shared_wallet_for_master(
                to_master, to_total + amount_silver, 0, 0, commit=False
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def send_mail_attachment_v0614(self, from_account_id, to_account_id, sender_name, *, kind, item_id="", item_name="", amount_silver=0):
        """Atomowo odkłada jeden przedmiot albo walutę w pocztowym escrow."""
        from_account_id=int(from_account_id); to_account_id=int(to_account_id)
        kind=str(kind or "")
        if from_account_id==to_account_id or kind not in ("item","currency"):
            return None

        meta={}
        current=0
        if kind=="item":
            item_id=str(item_id or "")
            row=self.conn.execute(
                "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
                (from_account_id,item_id),
            ).fetchone()
            current=int(row["quantity"] or 0) if row else 0
            if current<1:
                return None
            # Dane ulepszeń są per account+item_id. Gdy ostatnia sztuka opuszcza
            # konto, przenosimy je do escrow i odtwarzamy przy odbiorze.
            if current==1:
                ref=self.conn.execute(
                    "SELECT affix,affix_amount,rerolls FROM equipment_reforges WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                up=self.conn.execute(
                    "SELECT upgrade_level FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                runes=self.conn.execute(
                    "SELECT socket_index,rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? ORDER BY socket_index",
                    (from_account_id,item_id),
                ).fetchall()
                bonus=self.conn.execute(
                    "SELECT bonus_sockets FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                mark=self.conn.execute(
                    "SELECT mark FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                if ref: meta["reforge"]={"affix":ref["affix"],"affix_amount":int(ref["affix_amount"]),"rerolls":int(ref["rerolls"])}
                if up: meta["upgrade_level"]=int(up["upgrade_level"] or 0)
                if runes: meta["runes"]=[{"socket_index":int(r["socket_index"]),"rune_id":str(r["rune_id"])} for r in runes]
                if bonus: meta["bonus_sockets"]=int(bonus["bonus_sockets"] or 0)
                if mark: meta["tech_mark"]=int(mark["mark"] or 1)
        else:
            amount_silver=int(amount_silver or 0)
            if amount_silver<=0 or amount_silver>CURRENCY_SQLITE_SAFE_TOTAL:
                return None
            from_master=self.master_account_for_character(from_account_id)
            to_master=self.master_account_for_character(to_account_id)
            if int(from_master)==int(to_master):
                return None
            from_total=int(self.shared_wallet_for_master(from_master)[0])
            to_total=int(self.shared_wallet_for_master(to_master)[0])
            if from_total<amount_silver or to_total+amount_silver>CURRENCY_SQLITE_SAFE_TOTAL:
                return None

        try:
            self.conn.execute("BEGIN")
            if kind=="item":
                if current<=1:
                    self.conn.execute("DELETE FROM inventory WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                    for table in ("equipment_reforges","equipment_upgrades_v03042","equipment_runes_v0925","equipment_socket_bonus_v03114","tech_set_upgrades_v0320"):
                        self.conn.execute(f"DELETE FROM {table} WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                else:
                    self.conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                subject="Przedmiot od gracza"
                body=f"Załącznik: {item_name or item_id} x1."
                cur=self.conn.execute(
                    "INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body,attachment_kind,attachment_item_id,attachment_item_name,attachment_item_qty,attachment_meta_json) "
                    "VALUES(?,?,?,?,?,'item',?,?,1,?)",
                    (to_account_id,from_account_id,str(sender_name),subject,body,item_id,str(item_name or item_id),json.dumps(meta,ensure_ascii=False,separators=(',',':'))),
                )
            else:
                self.set_shared_wallet_for_master(from_master,from_total-amount_silver,0,0,commit=False)
                subject="Waluta od gracza"
                body=f"Załącznik walutowy: {amount_silver} jednostek srebra bazowego."
                cur=self.conn.execute(
                    "INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body,attachment_kind,attachment_coins) "
                    "VALUES(?,?,?,?,?,'currency',?)",
                    (to_account_id,from_account_id,str(sender_name),subject,body,amount_silver),
                )
            self.conn.commit()
            return int(cur.lastrowid)
        except Exception:
            self.conn.rollback()
            raise

    def claim_mail_attachment_v0614(self, account_id, mail_id):
        """Atomowo odbiera załącznik i oznacza go jako odebrany."""
        account_id=int(account_id); mail_id=int(mail_id)
        row=self.conn.execute(
            "SELECT * FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",
            (mail_id,account_id),
        ).fetchone()
        if not row or int(row["attachment_claimed"] or 0):
            return None
        kind=str(row["attachment_kind"] or "")
        if kind not in ("item","currency"):
            return None
        if kind=="currency":
            amount=int(row["attachment_coins"] or 0)
            master=self.master_account_for_character(account_id)
            current=int(self.shared_wallet_for_master(master)[0])
            if amount<=0 or current+amount>CURRENCY_SQLITE_SAFE_TOTAL:
                return {"ok":False,"reason":"wallet_cap","kind":kind,"amount":amount}
        try:
            self.conn.execute("BEGIN")
            if kind=="item":
                item_id=str(row["attachment_item_id"] or "")
                qty=max(1,int(row["attachment_item_qty"] or 1))
                self.conn.execute(
                    "INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?) "
                    "ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity",
                    (account_id,item_id,qty),
                )
                try: meta=json.loads(str(row["attachment_meta_json"] or "{}"))
                except Exception: meta={}
                ref=meta.get("reforge") if isinstance(meta,dict) else None
                if isinstance(ref,dict):
                    self.conn.execute(
                        "INSERT OR REPLACE INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,?)",
                        (account_id,item_id,str(ref.get("affix") or ""),int(ref.get("affix_amount") or 0),int(ref.get("rerolls") or 0)),
                    )
                level=int(meta.get("upgrade_level",0) or 0) if isinstance(meta,dict) else 0
                if level>0:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?)",(account_id,item_id,level))
                for rr in (meta.get("runes") or []) if isinstance(meta,dict) else []:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",(account_id,item_id,int(rr.get("socket_index") or 0),str(rr.get("rune_id") or "")))
                bonus=int(meta.get("bonus_sockets",0) or 0) if isinstance(meta,dict) else 0
                if bonus>0:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?)",(account_id,item_id,bonus))
                mark=int(meta.get("tech_mark",1) or 1) if isinstance(meta,dict) else 1
                if mark>1:
                    self.conn.execute("INSERT OR REPLACE INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?)",(account_id,item_id,mark))
                result={"ok":True,"kind":"item","item_id":item_id,"item_name":str(row["attachment_item_name"] or item_id),"qty":qty}
            else:
                amount=int(row["attachment_coins"] or 0)
                self.set_shared_wallet_for_master(master,current+amount,0,0,commit=False)
                result={"ok":True,"kind":"currency","amount":amount}
            self.conn.execute("UPDATE player_mail_v03051 SET attachment_claimed=1,is_read=1 WHERE id=? AND recipient_account_id=?",(mail_id,account_id))
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise

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

    def equip(self, account_id, slot, item_id, commit=True):
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        if commit:
            self.conn.commit()

    def unequip(self, account_id, slot):
        self.conn.execute(
            "DELETE FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()

    def socketed_gems(self, account_id, slot, jewelry_item_id=None):
        if jewelry_item_id is None:
            return self.conn.execute(
                "SELECT socket_index,jewelry_item_id,gem_id "
                "FROM equipment_gems "
                "WHERE account_id=? AND slot=? "
                "ORDER BY socket_index",
                (account_id, slot),
            ).fetchall()
        return self.conn.execute(
            "SELECT socket_index,jewelry_item_id,gem_id "
            "FROM equipment_gems "
            "WHERE account_id=? AND slot=? AND jewelry_item_id=? "
            "ORDER BY socket_index",
            (account_id, slot, jewelry_item_id),
        ).fetchall()

    def add_socketed_gem(
        self, account_id, slot, jewelry_item_id,
        socket_index, gem_id,
    ):
        self.conn.execute(
            """
            INSERT INTO equipment_gems(
                account_id,slot,socket_index,jewelry_item_id,gem_id
            ) VALUES(?,?,?,?,?)
            ON CONFLICT(account_id,slot,socket_index)
            DO UPDATE SET
                jewelry_item_id=excluded.jewelry_item_id,
                gem_id=excluded.gem_id
            """,
            (
                account_id, slot, int(socket_index),
                jewelry_item_id, gem_id,
            ),
        )
        self.conn.commit()

    def clear_socketed_gems(self, account_id, slot):
        rows = self.socketed_gems(account_id, slot)
        self.conn.execute(
            "DELETE FROM equipment_gems "
            "WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()
        return rows

    def ensure_profession(self, account_id, profession):
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        self.conn.commit()

    def profession(self, account_id, profession):
        self.ensure_profession(account_id, profession)
        return self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()

    def save_profession(self, account_id, profession, level, xp, actions):
        self.conn.execute(
            "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
            (level, xp, actions, account_id, profession),
        )
        self.conn.commit()

    def equipment_enchant_v03053(self, account_id, slot):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? AND slot=?",(account_id,slot)).fetchone()

    def set_equipment_enchant_v03053(self, account_id, slot, enchant_key, stat, amount):
        self.conn.execute("INSERT INTO equipment_enchants_v03053(account_id,slot,enchant_key,stat,amount) VALUES(?,?,?,?,?) ON CONFLICT(account_id,slot) DO UPDATE SET enchant_key=excluded.enchant_key,stat=excluded.stat,amount=excluded.amount,updated_at=CURRENT_TIMESTAMP",(account_id,slot,enchant_key,stat,int(amount)))
        self.conn.commit()

    def equipment_enchants_v03053(self, account_id):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? ORDER BY slot",(account_id,)).fetchall()

    def ensure_tool(self, account_id, tool_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        self.conn.commit()

    def tool(self, account_id, tool_type):
        self.ensure_tool(account_id, tool_type)
        return self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()

    def save_tool(self, account_id, tool_type, level, xp, uses):
        self.conn.execute(
            "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
            (level, xp, uses, account_id, tool_type),
        )
        self.conn.commit()

    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_storage_item(self, account_id, container, item_id, qty=1, commit=True):
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        if commit:
            self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1, commit=True):
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        if commit:
            self.conn.commit()
        return True

    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        # v0.71.8: one aggregate query per storage location instead of 1-2
        # SELECTs for every ingredient/resource id. This is hot in crafting and
        # collection checks with large candidate pools.
        ids = tuple(dict.fromkeys(str(item_id) for item_id in item_ids if item_id))
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        row = self.conn.execute(
            f"SELECT COALESCE(SUM(quantity),0) AS total FROM inventory "
            f"WHERE account_id=? AND item_id IN ({placeholders})",
            (account_id, *ids),
        ).fetchone()
        total = int(row["total"] or 0) if row else 0
        if container:
            row = self.conn.execute(
                f"SELECT COALESCE(SUM(quantity),0) AS total FROM profession_storage "
                f"WHERE account_id=? AND container=? AND item_id IN ({placeholders})",
                (account_id, container, *ids),
            ).fetchone()
            total += int(row["total"] or 0) if row else 0
        return total

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None):
        remaining = needed

        if container:
            for item_id in sorted(item_ids):
                if remaining <= 0:
                    break
                qty = self.storage_qty(account_id, container, item_id)
                take = min(qty, remaining)
                if take > 0:
                    self.remove_storage_item(account_id, container, item_id, take)
                    remaining -= take

        for item_id in sorted(item_ids):
            if remaining <= 0:
                break
            qty = self.item_qty(account_id, item_id)
            take = min(qty, remaining)
            if take > 0:
                self.remove_item(account_id, item_id, take)
                remaining -= take

        return remaining == 0

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
        level = max(0, min(V03042_EQ_UPGRADE_MAX, int(level)))
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

    def transfer_bank_v1225(self, sender_id, recipient_login, *, silver=0, item_id=None, quantity=0):
        """Transfer money between master vaults or bank items between characters.

        The SAVEPOINT covers both debit and credit; failed transfers never lose funds.
        """
        from core.bootstrap_economy_professions import legacy_currency_to_coins
        from core.mines_threat import is_character_bound_item
        from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL
        sender_master = int(self.master_account_for_character(sender_id))
        recipient = self.master_account_by_name(str(recipient_login).strip())
        if recipient is None:
            return 'recipient'
        receiver_master = int(recipient['id'])
        if sender_master == receiver_master:
            return 'self'
        is_item = item_id is not None
        amount, units = int(silver), int(quantity)
        if not is_item and (amount <= 0 or amount > CURRENCY_SQLITE_SAFE_TOTAL):
            return 'invalid'
        if is_item and (units <= 0 or units > 9999 or is_character_bound_item(str(item_id))):
            return 'invalid'
        conn = self.conn
        conn.execute('SAVEPOINT transfer_bank_v1225')
        try:
            if is_item:
                dest_row=conn.execute('SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot LIMIT 1',(receiver_master,)).fetchone()
                dest_char=int(dest_row[0]) if dest_row else receiver_master
                source_char=int(sender_id)
                item_id=str(item_id)
                source=conn.execute('SELECT quantity FROM bank_items WHERE account_id=? AND item_id=?',(source_char,item_id)).fetchone()
                dest=conn.execute('SELECT quantity FROM bank_items WHERE account_id=? AND item_id=?',(dest_char,item_id)).fetchone()
                if source is None or int(source[0])<units: result='funds'
                elif dest is not None and int(dest[0])+units>CURRENCY_SQLITE_SAFE_TOTAL: result='limit'
                else:
                    conn.execute('UPDATE bank_items SET quantity=quantity-? WHERE account_id=? AND item_id=?',(units,source_char,item_id))
                    conn.execute('DELETE FROM bank_items WHERE account_id=? AND item_id=? AND quantity=0',(source_char,item_id))
                    conn.execute('INSERT INTO bank_items(account_id,item_id,quantity) VALUES(?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',(dest_char,item_id,units))
                    # Preserve the real shop cost basis on transferred goods.
                    lot='__bank_v1175__:'+item_id
                    remaining=units
                    for paid,have in conn.execute('SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 WHERE account_id=? AND item_id=? ORDER BY paid_silver',(source_char,lot)).fetchall():
                        n=min(remaining,int(have))
                        if n<=0: break
                        conn.execute('DELETE FROM shop_purchase_lots_v1175 WHERE account_id=? AND item_id=? AND paid_silver=?',(source_char,lot,int(paid)))
                        if int(have)>n:
                            conn.execute('INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) VALUES(?,?,?,?)',(source_char,lot,int(paid),int(have)-n))
                        conn.execute('INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) VALUES(?,?,?,?) ON CONFLICT(account_id,item_id,paid_silver) DO UPDATE SET quantity=quantity+excluded.quantity',(dest_char,lot,int(paid),n))
                        remaining-=n
                    result='ok'
            else:
                for master in (sender_master,receiver_master):
                    conn.execute('INSERT OR IGNORE INTO bank_balances(account_id,silver,gold,mithril) VALUES(?,0,0,0)',(master,))
                balance1=conn.execute('SELECT silver,gold,mithril FROM bank_balances WHERE account_id=?',(sender_master,)).fetchone()
                balance2=conn.execute('SELECT silver,gold,mithril FROM bank_balances WHERE account_id=?',(receiver_master,)).fetchone()
                start=legacy_currency_to_coins(*balance1)
                finish=legacy_currency_to_coins(*balance2)
                if start<amount: result='funds'
                elif finish+amount>CURRENCY_SQLITE_SAFE_TOTAL: result='limit'
                else:
                    conn.execute('UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?',(start-amount,sender_master))
                    conn.execute('UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?',(finish+amount,receiver_master))
                    result='ok'
            if result=='ok':
                conn.execute('INSERT INTO bank_transfers_v1225(sender_id,receiver_id,kind,item_id,quantity) VALUES(?,?,?,?,?)',(sender_master,receiver_master,'item' if is_item else 'money',str(item_id) if is_item else '',units if is_item else amount))
                conn.execute('RELEASE SAVEPOINT transfer_bank_v1225')
                conn.commit()
            else:
                conn.execute('ROLLBACK TO SAVEPOINT transfer_bank_v1225')
                conn.execute('RELEASE SAVEPOINT transfer_bank_v1225')
            return result
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT transfer_bank_v1225')
            conn.execute('RELEASE SAVEPOINT transfer_bank_v1225')
            raise

    def bank_transfer_history_v1225(self, account_id, limit=10):
        master=int(self.master_account_for_character(account_id))
        return self.conn.execute("""SELECT t.*,s.username sender_name,r.username receiver_name
            FROM bank_transfers_v1225 t
            JOIN accounts s ON s.id=t.sender_id
            JOIN accounts r ON r.id=t.receiver_id
            WHERE t.sender_id=? OR t.receiver_id=? ORDER BY t.id DESC LIMIT ?""",(master,master,max(1,min(20,int(limit))))).fetchall()

    def hunter_state_v1225(self, account_id, tier):
        return self.conn.execute('SELECT * FROM hunter_contracts_v1225 WHERE account_id=? AND tier=?',(int(account_id),tier)).fetchone()

    def hunter_accept_v1225(self, account_id, tier, target_id, needed, reward_silver, now):
        account_id=int(account_id)
        self.conn.execute('SAVEPOINT hunter_accept_v1225')
        try:
            old=self.hunter_state_v1225(account_id,tier)
            if old and old['state'] in ('active','ready'):
                result='active'
            elif old and int(old['ready_after'])>int(now):
                result='cooldown'
            else:
                self.conn.execute("INSERT INTO hunter_contracts_v1225(account_id,tier,target_id,needed,progress,reward_silver,state,ready_after) VALUES(?,?,?,?,0,?,'active',0) ON CONFLICT(account_id,tier) DO UPDATE SET target_id=excluded.target_id, needed=excluded.needed,progress=0,reward_silver=excluded.reward_silver,state='active',ready_after=0",(account_id,tier,str(target_id),int(needed),int(reward_silver)))
                result='ok'
            self.conn.execute('RELEASE SAVEPOINT hunter_accept_v1225')
            self.conn.commit()
            return result
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT hunter_accept_v1225')
            self.conn.execute('RELEASE SAVEPOINT hunter_accept_v1225')
            raise

    def hunter_kill_v1225(self, account_id, mob_template_id, template=None):
        """Credit genuine kills by category, including valid world variants."""
        from data.mobs import MOB_TEMPLATES
        template = template if template is not None else MOB_TEMPLATES.get(str(mob_template_id), {})
        template = template or {}
        key = str(mob_template_id)
        rank = str(template.get('rank', '')).casefold()
        is_boss = bool(rank in ('boss', 'world_boss', 'superboss') or any(template.get(flag) for flag in (
            'world_boss', 'mini_boss', 'crypt_boss', 'mythic_crypt_boss',
            'astral_boss', 'mythic_astral_boss', 'giant_fortress_boss',
            'uoss_unique_superboss_key', 'boss_mechanic', 'v020_mythic_world_boss', 'boss')))
        is_elite = bool(template.get('elite') or rank == 'elite' or key.endswith('_elite'))
        matched = {
            'zwykle': not is_boss and not is_elite and (key.startswith('goblin_') or key == 'goblin' or template.get('quest_target') == 'goblin'),
            'elitarne': is_elite,
            'boss': is_boss,
        }
        changed=[]
        for row in self.conn.execute("SELECT tier,progress,needed FROM hunter_contracts_v1225 WHERE account_id=? AND state='active'",(int(account_id),)).fetchall():
            if not matched.get(row['tier'], False):
                continue
            count=min(int(row['needed']),int(row['progress'])+1)
            self.conn.execute("UPDATE hunter_contracts_v1225 SET progress=?,state=? WHERE account_id=? AND tier=? AND state='active'",(count,'ready' if count >= int(row['needed']) else 'active',int(account_id),row['tier']))
            changed.append((row['tier'],count,int(row['needed'])))
        if changed:self.conn.commit()
        return changed

    def hunter_claim_v1225(self, account_id, tier, now, cooldown):
        """Mark bounty complete and deposit reward in same SQLite transaction."""
        master=int(self.master_account_for_character(account_id))
        self.conn.execute('SAVEPOINT hunter_claim_v1225')
        try:
            row=self.hunter_state_v1225(account_id,tier)
            if not row or row['state']!='ready':
                result=0
            else:
                reward=int(row['reward_silver'])
                self.conn.execute('INSERT OR IGNORE INTO bank_balances(account_id,silver,gold,mithril) VALUES(?,0,0,0)',(master,))
                balance=self.conn.execute('SELECT silver,gold,mithril FROM bank_balances WHERE account_id=?',(master,)).fetchone()
                from core.bootstrap_economy_professions import legacy_currency_to_coins,CURRENCY_SQLITE_SAFE_TOTAL
                total=legacy_currency_to_coins(*balance)
                if reward<=0 or total+reward>CURRENCY_SQLITE_SAFE_TOTAL:
                    result=-1
                else:
                    self.conn.execute('UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?',(total+reward,master))
                    self.conn.execute("UPDATE hunter_contracts_v1225 SET state='cooldown',ready_after=? WHERE account_id=? AND tier=? AND state='ready'",(int(now)+int(cooldown),int(account_id),tier))
                    result=reward
            if result>0:
                self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
                self.conn.commit()
            else:
                self.conn.execute('ROLLBACK TO SAVEPOINT hunter_claim_v1225')
                self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
            return result
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT hunter_claim_v1225')
            self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
            raise

    def inventory_is_protected_v1280(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT 1 FROM protected_inventory_v1280 WHERE account_id=? AND item_id=?",
            (int(account_id), str(item_id)),
        ).fetchone()
        return bool(row)

    def inventory_set_protected_v1280(self, account_id, item_id, state):
        if state:
            self.conn.execute(
                "INSERT OR IGNORE INTO protected_inventory_v1280(account_id,item_id) VALUES (?,?)",
                (int(account_id), str(item_id)),
            )
        else:
            self.conn.execute(
                "DELETE FROM protected_inventory_v1280 WHERE account_id=? AND item_id=?",
                (int(account_id), str(item_id)),
            )
        self.conn.commit()
