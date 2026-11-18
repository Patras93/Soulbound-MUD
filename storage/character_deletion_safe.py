# -*- coding: utf-8 -*-
"""Version-neutral, atomic physical-EQ-safe character deletion for Database.

Legacy DatabaseAccountsMixin methods stay untouched for historical AST audits.
"""
from contextlib import contextmanager

class SafeCharacterDeletionMixin:
    @contextmanager
    def _v11405_delete_character_transaction(self, character_ids):
        """One checked character-deletion transaction across legacy and physical EQ.

        A guard may be lifted only within this synchronous, verified operation.
        It does not authorize arbitrary inventory writes or production cutover.
        """
        ids=tuple(sorted({int(i) for i in character_ids}))
        conn=self.conn
        barrier=bool(getattr(conn,'_v107_eq_write_barrier_active',False))
        if getattr(self,'_v107_eq_live_active',False) and not barrier:
            raise RuntimeError('Ochrona EQ nieaktywna — usuwanie postaci zatrzymane')
        if barrier:
            catalog=getattr(self,'_v106_shadow_item_catalog',None)
            if not isinstance(catalog,dict):
                raise RuntimeError('Brak katalogu fizycznego EQ — odmowa usuwania')
            from systems.equipment_shadow_slots_v10600 import _check_account
            for aid in ids:
                _check_account(conn,aid,catalog)
        from systems.v10700_equipment_write_barrier import approved_instance_operation
        existing={str(r[0]) for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        # Never discard an unclaimed attachment belonging to another account.
        # The mail sender/recipient must resolve their physical escrow first.
        if 'v106_mail_equipment_escrow' in existing:
            for aid in ids:
                if conn.execute("""SELECT 1 FROM v106_mail_equipment_escrow
                    WHERE sender_account_id=? OR recipient_account_id=? LIMIT 1""",
                    (aid,aid)).fetchone():
                    raise RuntimeError('Przed usunięciem postaci rozlicz jej pocztę z fizycznym EQ')
        outer=bool(conn.in_transaction)
        conn.execute('SAVEPOINT sb11405_character_delete')
        try:
            with approved_instance_operation(conn):
                for aid in ids:
                    # These ledgers have no account FK cascade. Delete dependent
                    # physical references before their parent copies, precisely
                    # for the character being removed; never other accounts.
                    for table in ('v106_equipped_instances','v106_stored_instances',
                                  'v106_item_instances'):
                        if table in existing:
                            conn.execute(f'DELETE FROM "{table}" WHERE account_id=?',(aid,))
                yield
                for aid in ids:
                    for table in ('v106_equipped_instances','v106_stored_instances',
                                  'v106_item_instances'):
                        if table in existing and conn.execute(
                                f'SELECT 1 FROM "{table}" WHERE account_id=? LIMIT 1',
                                (aid,)).fetchone():
                            raise RuntimeError('Niepełne usunięcie rejestru fizycznego EQ')
            conn.execute('RELEASE SAVEPOINT sb11405_character_delete')
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT sb11405_character_delete')
            conn.execute('RELEASE SAVEPOINT sb11405_character_delete')
            raise
        if not outer:
            conn.commit()

    def shared_wallet_for_master(self, master_account_id):
        """A login without any real characters has no spendable progress.

        This also hides historical orphan wallet rows until a new first
        character is created (which atomically discards stale balances).
        Other accounts retain the exact legacy wallet behavior unchanged.
        """
        master_account_id = int(master_account_id)
        row = self.conn.execute("""
            SELECT 1 FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? LIMIT 1
        """, (master_account_id,)).fetchone()
        if row is None:
            return (0, 0, 0)
        return super().shared_wallet_for_master(master_account_id)

    def create_character_for_master(self, master_account_id, name, race, cls,
                                    name_cases, gender="nieokreślona"):
        """A genuinely first character starts with the normal starter purse.

        Historical login accounts can retain a stale shared wallet after the
        last character was deleted by older releases. Do not inherit it when
        making a new character, even if an orphaned character row still exists.
        Keep the reset AND the new character in one reversible transaction.
        """
        master_account_id = int(master_account_id)
        has_character = self.conn.execute("""
            SELECT 1 FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? LIMIT 1
        """, (master_account_id,)).fetchone()
        if has_character:
            return super().create_character_for_master(
                master_account_id, name, race, cls, name_cases, gender=gender)
        with self.conn.deferred_commits():
            self.conn.execute(
                "DELETE FROM account_wallet WHERE master_account_id=?",
                (master_account_id,),
            )
            return super().create_character_for_master(
                master_account_id, name, race, cls, name_cases, gender=gender)

    def wipe_characters_for_master(self, master_account_id):
        """Delete all character progress, preserving login and password."""
        master_account_id=int(master_account_id)
        rows=self.conn.execute("""SELECT character_account_id FROM account_characters
             WHERE master_account_id=? ORDER BY slot""",(master_account_id,)).fetchall()
        ids=[int(r['character_account_id']) for r in rows]
        with self._v11405_delete_character_transaction(ids):
            for aid in ids:
                self._delete_character_mercenary_data_v3002(aid)
            for aid in ids:
                if aid!=master_account_id:
                    self.conn.execute('DELETE FROM accounts WHERE id=?',(aid,))
            if master_account_id in ids:
                self._v11405_delete_primary_character_rows(master_account_id)
            self.conn.execute('DELETE FROM account_characters WHERE master_account_id=?',
                              (master_account_id,))
            self.conn.execute('DELETE FROM account_wallet WHERE master_account_id=?',
                              (master_account_id,))
        return len(ids)

    def _v11405_delete_primary_character_rows(self, master_account_id):
        """Keep login identity, email/password recovery and shared wallet."""
        tables=self.conn.execute("""SELECT name FROM sqlite_master
             WHERE type='table' AND name NOT LIKE 'sqlite_%' """).fetchall()
        protected={'accounts','account_characters','account_wallet',
                   'account_emails_v1223','email_password_reset_v1223',
                   'password_recovery_v1222'}
        for row in tables:
            table=str(row['name'])
            if table in protected:
                continue
            cols={str(c['name']) for c in self.conn.execute(
                f'PRAGMA table_info("{table}")').fetchall()}
            if 'account_id' in cols:
                self.conn.execute(f'DELETE FROM "{table}" WHERE account_id=?',
                                  (master_account_id,))

    def delete_character_for_master(self, master_account_id, character_account_id):
        """Delete one character; retain shared wallet iff another real character remains."""
        master_account_id=int(master_account_id)
        character_account_id=int(character_account_id)
        row=self.conn.execute("""SELECT ac.slot,ac.character_account_id,c.name
          FROM account_characters ac JOIN characters c
          ON c.account_id=ac.character_account_id
          WHERE ac.master_account_id=? AND ac.character_account_id=?""",
          (master_account_id,character_account_id)).fetchone()
        if not row:
            return None
        slot=int(row['slot']);name=str(row['name'])
        with self._v11405_delete_character_transaction((character_account_id,)):
            self._delete_character_mercenary_data_v3002(character_account_id)
            if character_account_id!=master_account_id:
                self.conn.execute('DELETE FROM accounts WHERE id=?',
                                  (character_account_id,))
            else:
                self._v11405_delete_primary_character_rows(master_account_id)
                self.conn.execute("""DELETE FROM account_characters
                    WHERE master_account_id=? AND character_account_id=?""",
                    (master_account_id,character_account_id))
            # A shared wallet is progress belonging to the remaining roster,
            # not to the login account. Never carry it into a fresh character
            # after the last real character is deleted. Keep it untouched if
            # even one real character remains; the SAVEPOINT makes it atomic.
            remaining = self.conn.execute("""
                SELECT 1 FROM account_characters ac
                JOIN characters c ON c.account_id=ac.character_account_id
                WHERE ac.master_account_id=? LIMIT 1
            """, (master_account_id,)).fetchone()
            if remaining is None:
                self.conn.execute(
                    "DELETE FROM account_wallet WHERE master_account_id=?",
                    (master_account_id,),
                )
        return {'slot':slot,'name':name}

