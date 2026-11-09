# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: crafting; AST bez zmian."""
from .dependencies import *

class CraftingV109Mixin:
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
