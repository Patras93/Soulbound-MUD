# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: professions; AST bez zmian."""
from .dependencies import *

class ProfessionsV109Mixin:
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
