# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: tools; AST bez zmian."""
from .dependencies import *

class ToolsV109Mixin:
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
