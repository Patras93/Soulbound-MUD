# -*- coding: utf-8 -*-
"""Bank, inventory, equipment, storage, transfers and crafting persistence."""

import json

from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, normalize_currency_values
from storage.db_shared import DROP_HISTORY_LIMIT, V03042_EQ_UPGRADE_MAX, is_craft_material_storage_item

class DatabaseInventoryMixin:
    def ensure_bank(self, account_id):
        # v0.8.32: waluta Banku Dusz jest również wspólna dla całego konta.
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        currency_account_id = self.master_account_for_character(account_id)
        self.conn.execute(
            "INSERT OR IGNORE INTO bank_balances("
            "account_id,silver,gold,mithril"
            ") VALUES(?,0,0,0)",
            (currency_account_id,),
        )
        if not outer_transaction_v104:
            self.conn.commit()
        return currency_account_id

    def bank_balance(self, account_id):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import _require_copy_path
            _require_copy_path(self)  # before ensure_bank writes anything
        currency_account_id = self.ensure_bank(account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM bank_balances "
            "WHERE account_id=?",
            (currency_account_id,),
        ).fetchone()

        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import (
                _ExactProgressRow, read_exact_currency_copy,
            )
            exact = read_exact_currency_copy(self, currency_account_id, 'bank')
            return _ExactProgressRow(row, dict(zip(('silver','gold','mithril'), exact)))

        # v104 etap 13: odczyt banku nie moze zaokraglac REAL / ucinac
        # przypadkowego TEXT przez int(). Wymagaj dokladnego INTEGER.
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        raw_values = tuple(require_sqlite_int64('bank_balances.' + key, row[key])
                           for key in ('silver', 'gold', 'mithril'))
        silver, gold, mithril = normalize_currency_values(*raw_values)

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
            if not outer_transaction_v104:
                self.conn.commit()
            row = self.conn.execute(
                "SELECT silver,gold,mithril FROM bank_balances "
                "WHERE account_id=?",
                (currency_account_id,),
            ).fetchone()

        return row

    def change_bank_currency(self, account_id, currency, amount):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        if currency not in ("silver", "gold", "mithril"):
            raise ValueError("Nieznana waluta bankowa.")

        currency_account_id = self.master_account_for_character(account_id)
        row = self.bank_balance(account_id)
        values = {
            "silver": int(row["silver"]),
            "gold": int(row["gold"]),
            "mithril": int(row["mithril"]),
        }
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import (
                currency_total_copy, write_exact_currency_copy,
            )
            if type(amount) is not int:
                raise TypeError('Zmienna waluty bankowej musi byc int.')
            delta = amount
            values[currency] += delta
            if values[currency] < 0:
                return False
            total = currency_total_copy(values['silver'],values['gold'],values['mithril'])
            write_exact_currency_copy(self, currency_account_id, 'bank', total, 0, 0)
            if not outer_transaction_v104:
                self.conn.commit()
            return True
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        delta = require_sqlite_int64('bank_balances.delta', amount)
        values[currency] += delta

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
        if not outer_transaction_v104:
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

    def move_bank_equipment_v106(self, account_id, item_id, qty=1, *, withdraw=False, commit=True):
        """Staging-only atomic move, never used by legacy banking methods."""
        from systems.equipment_inventory_flow_v10600 import bank_move
        return bank_move(self, account_id, item_id, qty, withdraw=withdraw, commit=commit)

    def add_bank_item(self, account_id, item_id, qty=1):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'bank.deposit')
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = max(1, require_sqlite_int64('bank_items.increment', qty))
        current = self.conn.execute(
            'SELECT quantity FROM bank_items WHERE account_id=? AND item_id=?',
            (account_id, item_id)).fetchone()
        balance = self._v104_crafting_quantity(current[0]) if current else 0
        require_sqlite_int64('bank_items.quantity', balance + qty)
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
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'bank.withdraw')
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
        from systems.equipment_inventory_flow_v10600 import tracked, remove
        if tracked(self, item_id):
            return remove(self, account_id, item_id, qty, commit=commit)
        from systems.equipment_evolution_v10500 import is_evolved
        if is_evolved(self.conn, account_id, item_id):
            return False  # evolved EQ cannot disappear while its stage is bound
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
        from systems.equipment_inventory_flow_v10600 import tracked, transfer
        if tracked(self, item_id):
            return transfer(self, from_account_id, to_account_id, item_id, qty)
        from systems.equipment_evolution_v10500 import is_evolved
        if is_evolved(self.conn, from_account_id, item_id):
            return False  # evolved EQ is character-bound
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
            from systems.equipment_inventory_flow_v10600 import tracked
            if tracked(self, item_id):
                from systems.equipment_mail_v10600 import send
                return send(self, from_account_id, to_account_id, sender_name, item_id, item_name)

            from systems.equipment_evolution_v10500 import is_evolved
            if is_evolved(self.conn, from_account_id, item_id):
                return None  # no evolved equipment in mail escrow
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
        # A staging physical escrow must never fall through the v105 generic
        # item/currency path after its mail row was edited or corrupted.
        if (getattr(self, '_v106_shadow_slots_disposable_copy', False) and
                getattr(self, '_v106_mail_shadow_disposable_copy', False)):
            from systems.equipment_inventory_flow_v10600 import tracked as _v106_tracked_mail
            from systems.v10700_eq_runtime_gate import is_enabled as _v107_eq_is_enabled
            if _v107_eq_is_enabled(self):
                linked_table=self.conn.execute("SELECT 1 FROM sqlite_master "
                    "WHERE type='table' AND name='v106_mail_equipment_escrow'").fetchone()
                if linked_table and self.conn.execute(
                    'SELECT 1 FROM v106_mail_equipment_escrow WHERE mail_id=?',
                    (mail_id,)).fetchone():
                    from systems.equipment_mail_v10600 import claim
                    return claim(self, account_id, mail_id)
        kind=str(row["attachment_kind"] or "")
        if kind=="item":
            from systems.equipment_inventory_flow_v10600 import tracked
            if tracked(self, row["attachment_item_id"]):
                from systems.equipment_mail_v10600 import claim
                return claim(self, account_id, mail_id)
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
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        if not outer_transaction_v104:
            self.conn.commit()

    def profession(self, account_id, profession):
        copy_mode = getattr(self, '_v104_big_number_copy_rehearsal', False)
        if copy_mode:
            from storage.big_number_copy_runtime_v10400 import _require_copy_path
            _require_copy_path(self)
        self.ensure_profession(account_id, profession)
        row = self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()
        if copy_mode and row is not None:
            from storage.big_number_copy_runtime_v10400 import (
                _ExactProgressRow, read_exact_work_xp_copy,
            )
            row = _ExactProgressRow(row, {'xp': read_exact_work_xp_copy(
                self, account_id, 'profession', profession)})
        elif row is not None and getattr(self, '_v104_live_exact_keyed_xp', False):
            from storage.big_number_copy_runtime_v10400 import _ExactProgressRow
            from storage.big_number_live_keyed_xp_v10400 import read_live_keyed_xp
            row = _ExactProgressRow(row, {'xp': read_live_keyed_xp(
                self, account_id, 'profession', profession)})
        return row

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

    def equipment_enchant_v03053(self, account_id, slot):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? AND slot=?",(account_id,slot)).fetchone()

    def set_equipment_enchant_v03053(self, account_id, slot, enchant_key, stat, amount):
        self.conn.execute("INSERT INTO equipment_enchants_v03053(account_id,slot,enchant_key,stat,amount) VALUES(?,?,?,?,?) ON CONFLICT(account_id,slot) DO UPDATE SET enchant_key=excluded.enchant_key,stat=excluded.stat,amount=excluded.amount,updated_at=CURRENT_TIMESTAMP",(account_id,slot,enchant_key,stat,int(amount)))
        self.conn.commit()

    def equipment_enchants_v03053(self, account_id):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? ORDER BY slot",(account_id,)).fetchall()

    def ensure_tool(self, account_id, tool_type):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        if not outer_transaction_v104:
            self.conn.commit()

    def tool(self, account_id, tool_type):
        copy_mode = getattr(self, '_v104_big_number_copy_rehearsal', False)
        if copy_mode:
            from storage.big_number_copy_runtime_v10400 import _require_copy_path
            _require_copy_path(self)
        self.ensure_tool(account_id, tool_type)
        row = self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()
        if copy_mode and row is not None:
            from storage.big_number_copy_runtime_v10400 import (
                _ExactProgressRow, read_exact_work_xp_copy,
            )
            row = _ExactProgressRow(row, {'xp': read_exact_work_xp_copy(
                self, account_id, 'tool', tool_type)})
        elif row is not None and getattr(self, '_v104_live_exact_keyed_xp', False):
            from storage.big_number_copy_runtime_v10400 import _ExactProgressRow
            from storage.big_number_live_keyed_xp_v10400 import read_live_keyed_xp
            row = _ExactProgressRow(row, {'xp': read_live_keyed_xp(
                self, account_id, 'tool', tool_type)})
        return row

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

    def move_storage_equipment_v106(self, account_id, container, item_id, qty=1,
                                     *, withdraw=False, commit=True):
        """Opt-in physical gear move, disposable staging copy only."""
        from systems.equipment_inventory_flow_v10600 import storage_move
        return storage_move(self, account_id, container, item_id, qty,
                            withdraw=withdraw, commit=commit)

    def add_storage_item(self, account_id, container, item_id, qty=1, commit=True):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'storage.deposit')
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = max(1, require_sqlite_int64('storage.increment', qty))
        current = self.conn.execute(
            'SELECT quantity FROM profession_storage WHERE account_id=? '
            'AND container=? AND item_id=?', (account_id, container, item_id)).fetchone()
        balance = self._v104_crafting_quantity(current[0]) if current else 0
        require_sqlite_int64('storage.quantity', balance + qty)
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
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'storage.withdraw')
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

    @staticmethod
    def _v104_crafting_ids(item_ids):
        # Preserve string compatibility with the existing quest/crafting IDs,
        # but prevent aliases repeated in input from doubling available stock.
        return tuple(dict.fromkeys(str(item_id) for item_id in item_ids if item_id))

    @staticmethod
    def _v104_crafting_quantity(value):
        # SQLite SUM() overflows on otherwise valid collections of int64 rows;
        # int(REAL) / int(TEXT) would silently destroy or forge item quantities.
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = require_sqlite_int64('crafting.quantity', value)
        if qty < 0:
            raise ValueError('Ujemna liczba materialow w bazie.')
        return qty

    def craft_item_atomic_v106(self, account_id, ingredients, output_id, output_qty=1,
                               *, containers=None, extra_outputs=(), success_accounting=None,
                               reward_journal=None):
        """Experimental v106 equipment craft; real DB methods, disposable copy only.

        Staged v106 perform_recipe uses this after quality/yield selection;
        other crafting routes and live production remain out of scope.
        """
        from systems.equipment_crafting_guard_v10600 import craft_output_atomic
        return craft_output_atomic(self, account_id, ingredients, output_id,
                                   output_qty, containers=containers, extra_outputs=extra_outputs,
                                   success_accounting=success_accounting, reward_journal=reward_journal)

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

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None, *, purpose='craft'):
        """All-or-nothing consumption for collection quests and crafting orders.

        Plan the entire withdrawal BEFORE mutation. One SQLite SAVEPOINT covers
        storage, inventory and shop purchase lots, even when a later removal
        fails. Incomplete stocks return False and do not consume anything.
        """
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        required = require_sqlite_int64('crafting.needed', needed)
        if required < 0:
            raise ValueError('Nie mozna pobierac ujemnej liczby materialow.')
        if required == 0:
            return True
        ids = sorted(self._v104_crafting_ids(item_ids))
        if not ids:
            return False
        # v108: quest turn-in is not legacy crafting. The ordinary `remove_item`
        # adapter already atomically selects only unmodified, unworn physical
        # copies and rejects evolved / runic / forged / equipped gear. Keep
        # the crafting ban unchanged. No other caller may bypass it.
        if purpose not in ('craft', 'quest_turnin'):
            raise ValueError('Niedozwolony cel pobierania przedmiotu')
        from systems.equipment_crafting_guard_v10600 import guard_ingredient
        from systems.equipment_inventory_flow_v10600 import tracked
        for item_id in ids:
            if purpose == 'craft':
                guard_ingredient(self, item_id)
            elif tracked(self, item_id) and container:
                # Stored per-copy equipment needs an explicit storage adapter.
                # Prevent accidental fallback to legacy storage SQL.
                if self.storage_qty(account_id, container, item_id):
                    return False
        # Use the same connection for the preflight and writes to avoid races.
        conn = self.conn
        outer_transaction = bool(conn.in_transaction)
        with conn.deferred_commits():
            conn.execute('SAVEPOINT v104_craft_consume_atomic')
            try:
                plan = []
                remaining = required
                for source in ('storage', 'inventory'):
                    if source == 'storage' and not container:
                        continue
                    for item_id in ids:
                        if source == 'storage':
                            row = conn.execute(
                                'SELECT quantity FROM profession_storage '
                                'WHERE account_id=? AND container=? AND item_id=?',
                                (account_id, container, item_id)).fetchone()
                        else:
                            row = conn.execute(
                                'SELECT quantity FROM inventory '
                                'WHERE account_id=? AND item_id=?',
                                (account_id, item_id)).fetchone()
                        qty = self._v104_crafting_quantity(row[0]) if row else 0
                        take = min(qty, remaining)
                        if take:
                            plan.append((source, item_id, take))
                            remaining -= take
                        if remaining == 0:
                            break
                    if remaining == 0:
                        break
                if remaining:
                    conn.execute('ROLLBACK TO SAVEPOINT v104_craft_consume_atomic')
                    conn.execute('RELEASE SAVEPOINT v104_craft_consume_atomic')
                    return False
                for source, item_id, take in plan:
                    if source == 'storage':
                        ok = self.remove_storage_item(
                            account_id, container, item_id, take, commit=False)
                    else:
                        ok = self.remove_item(account_id, item_id, take, commit=False)
                    if not ok:
                        if purpose == 'quest_turnin':
                            # This is normal when the visible quantity includes
                            # equipped/modified gear but no eligible plain copy.
                            # A failed item must cancel the whole withdrawal.
                            conn.execute('ROLLBACK TO SAVEPOINT v104_craft_consume_atomic')
                            conn.execute('RELEASE SAVEPOINT v104_craft_consume_atomic')
                            return False
                        raise RuntimeError('Stan materialow zmienil sie podczas pobierania.')
                conn.execute('RELEASE SAVEPOINT v104_craft_consume_atomic')
                if not outer_transaction:
                    conn.commit()  # commit only if this function owns the transaction
                return True
            except BaseException:
                conn.execute('ROLLBACK TO SAVEPOINT v104_craft_consume_atomic')
                conn.execute('RELEASE SAVEPOINT v104_craft_consume_atomic')
                raise

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
        # A bank-to-bank transfer uses raw SQL and has no physical-instance
        # escrow. Never change legacy quantities behind an armed EQ ledger.
        if is_item:
            from systems.equipment_inventory_flow_v10600 import tracked
            if tracked(self, str(item_id)):
                return 'invalid'
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
