# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: friends."""
from .dependencies import *

class FriendsV109Mixin:
    def friend_master_v12213(self, character_or_master_id):
        """Friendship belongs to the actual login account, not a character slot."""
        return self.master_account_for_character(int(character_or_master_id))

    def friend_character_names_v12213(self, master_id):
        """Always read current characters, including ones created after friendship."""
        names = [str(row["name"]) for row in self.characters_for_master(master_id)]
        if not names:
            name = self.character_name_by_account_v0928(master_id)
            return [name] if name else []
        return names

    def migrate_friend_accounts_v12213(self):
        """Move old per-character edges to master accounts once, atomically.

        A pending request never becomes an accepted friendship by migration.
        """
        flag = 'friends_master_accounts_v12213'
        if self.conn.execute('SELECT 1 FROM migration_flags WHERE flag=?', (flag,)).fetchone():
            return
        self.conn.execute('SAVEPOINT migrate_friends_v12213')
        try:
            accepted = self.conn.execute(
                'SELECT account_id,friend_account_id,created_at FROM player_friends_v0928'
            ).fetchall()
            requests = self.conn.execute(
                'SELECT sender_account_id,target_account_id,created_at FROM player_friend_requests_v0928'
            ).fetchall()
            approved = set()
            for row in accepted:
                a = self.friend_master_v12213(row['account_id'])
                b = self.friend_master_v12213(row['friend_account_id'])
                if a != b:
                    approved.add((min(a,b), max(a,b)))
            self.conn.execute('DELETE FROM player_friends_v0928')
            for a,b in sorted(approved):
                self.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (a,b))
                self.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (b,a))
            self.conn.execute('DELETE FROM player_friend_requests_v0928')
            for row in requests:
                a = self.friend_master_v12213(row['sender_account_id'])
                b = self.friend_master_v12213(row['target_account_id'])
                if a == b or (min(a,b),max(a,b)) in approved:
                    continue
                self.conn.execute('INSERT OR IGNORE INTO player_friend_requests_v0928 '
                                  '(sender_account_id,target_account_id,created_at) VALUES(?,?,?)',
                                  (a,b,row['created_at']))
            self.conn.execute('INSERT INTO migration_flags(flag) VALUES(?)', (flag,))
            self.conn.execute('RELEASE SAVEPOINT migrate_friends_v12213')
            self.conn.commit()
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT migrate_friends_v12213')
            self.conn.execute('RELEASE SAVEPOINT migrate_friends_v12213')
            raise

    def are_friends_v0928(self, account_id, friend_account_id):
        return self.conn.execute(
            "SELECT 1 FROM player_friends_v0928 WHERE account_id=? AND friend_account_id=?",
            (self.friend_master_v12213(account_id), self.friend_master_v12213(friend_account_id)),
        ).fetchone() is not None
