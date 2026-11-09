# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: bank_currency; AST bez zmian."""
from .dependencies import *

class BankCurrencyV109Mixin:
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
