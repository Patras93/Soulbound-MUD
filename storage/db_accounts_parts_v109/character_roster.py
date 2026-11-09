# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: character_roster."""
from .dependencies import *

class CharacterRosterV109Mixin:
    def character_for_account(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()
        if row is None:
            return None
        if (getattr(self, '_v104_live_exact_character', False)
                and not getattr(self, '_v104_big_number_copy_rehearsal', False)):
            from storage.big_number_live_character_v10400 import read_live_character_axes
            from storage.big_number_copy_runtime_v10400 import _ExactProgressRow
            return _ExactProgressRow(row, read_live_character_axes(self, account_id, row))
        if not getattr(self, '_v104_big_number_copy_rehearsal', False):
            return row
        from storage.big_number_copy_runtime_v10400 import (
            CHARACTER_COPY_AXES, _require_copy_path, read_exact_progression_copy,
        )
        _require_copy_path(self)
        # Named AND positional reads must expose the same exact BigNumber.
        # A positional sqlite3.Row read previously returned the saturated
        # INTEGER mirror and silently lost precision despite named reads being
        # correct. Reuse the tested row facade shared with class progression.
        from storage.big_number_copy_runtime_v10400 import _ExactProgressRow
        return _ExactProgressRow(row, {
            axis: read_exact_progression_copy(self, account_id, axis)
            for axis in CHARACTER_COPY_AXES
        })

    def characters_for_master(self, master_account_id):
        rows = self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.*
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot
            """,
            (master_account_id,),
        ).fetchall()
        if (getattr(self, '_v104_live_exact_character', False)
                and not getattr(self, '_v104_big_number_copy_rehearsal', False)):
            from storage.big_number_live_character_v10400 import read_live_character_axes
            from storage.big_number_copy_runtime_v10400 import _ExactProgressRow
            return [_ExactProgressRow(row, read_live_character_axes(
                self, row['character_account_id'], row)) for row in rows]
        if not getattr(self, '_v104_big_number_copy_rehearsal', False):
            return rows
        # Character selection screens must not show truncated levels/XP in
        # the isolated BigNumber rehearsal while details show exact values.
        from storage.big_number_copy_runtime_v10400 import (
            CHARACTER_COPY_AXES, _ExactProgressRow, _require_copy_path, read_exact_progression_copy,
        )
        _require_copy_path(self)
        return [
            _ExactProgressRow(row, {
                axis: read_exact_progression_copy(self, row['character_account_id'], axis)
                for axis in CHARACTER_COPY_AXES
            })
            for row in rows
        ]

    def character_count_for_master(self, master_account_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM account_characters "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
