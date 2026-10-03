# -*- coding: utf-8 -*-
"""Friends commands kept separate from the main social mixin."""
from player.session_mixins.skill_learning import normalize_lookup_text

class SessionFriendsMixin:
    async def handle_friends_v0928(self, args=''):
        raw = str(args or '').strip()
        parts = raw.split(maxsplit=1)
        action = normalize_lookup_text(parts[0]) if parts else 'list'
        conn = self.server.db.conn
        if action in ('', 'list', 'lista'):
            rows = conn.execute("SELECT friend_account_id FROM player_friends_v0928 WHERE account_id=? ORDER BY created_at, friend_account_id", (self.account_id,)).fetchall()
            await self.send(f"ZNAJOMI: {len(rows)}.")
            if not rows:
                await self.send("Lista znajomych jest pusta.")
                return
            for row in rows:
                aid = int(row['friend_account_id'])
                name = self._social_name_v03051(aid)
                session = self.server.find_character_session(name)
                await self.send(f"{name}: {'online' if session and not session.closed and session.character else 'offline'}.")
            return
        if action in ('requests', 'zaproszenia'):
            rows = conn.execute("SELECT sender_account_id FROM player_friend_requests_v0928 WHERE target_account_id=? ORDER BY created_at", (self.account_id,)).fetchall()
            await self.send(f"ZAPROSZENIA DO ZNAJOMYCH: {len(rows)}.")
            for row in rows:
                await self.send(self._social_name_v03051(row['sender_account_id']))
            if not rows:
                await self.send("Brak oczekujących zaproszeń.")
            return
        if len(parts) < 2:
            await self.send("Znajomi: friend; friend dodaj <gracz>; friend akceptuj <gracz>; friend usuń <gracz>; friend zaproszenia.")
            return
        aid = self._social_target_id_v03051(parts[1])
        if aid is None:
            await self.send("Nie ma takiej postaci.")
            return
        aid = int(aid)
        name = self._social_name_v03051(aid)
        if action in ('add', 'dodaj', 'invite', 'zaproś', 'zapros'):
            if aid == int(self.account_id):
                await self.send("Nie możesz dodać samego siebie do znajomych.")
                return
            if self.server.db.are_friends_v0928(self.account_id, aid):
                await self.send(f"{name} jest już na liście znajomych.")
                return
            reverse = conn.execute("SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (aid, self.account_id)).fetchone()
            if reverse:
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (aid, self.account_id))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id, aid))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (aid, self.account_id))
                conn.commit()
                await self.send(f"Znajomość z {name} została zaakceptowana.")
                return
            conn.execute("INSERT OR IGNORE INTO player_friend_requests_v0928(sender_account_id,target_account_id) VALUES(?,?)", (self.account_id, aid))
            conn.commit()
            await self.send(f"Wysłano zaproszenie do znajomych: {name}.")
            return
        if action in ('accept', 'akceptuj', 'zaakceptuj'):
            req = conn.execute("SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (aid, self.account_id)).fetchone()
            if not req:
                await self.send("Nie masz zaproszenia od tej osoby.")
                return
            conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (aid, self.account_id))
            conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id, aid))
            conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (aid, self.account_id))
            conn.commit()
            await self.send(f"Dodano do znajomych: {name}.")
            return
        if action in ('remove', 'usun', 'usuń', 'delete'):
            conn.execute("DELETE FROM player_friends_v0928 WHERE (account_id=? AND friend_account_id=?) OR (account_id=? AND friend_account_id=?)", (self.account_id, aid, aid, self.account_id))
            conn.commit()
            await self.send(f"Usunięto ze znajomych: {name}.")
            return
        await self.send("Znajomi: friend; friend dodaj <gracz>; friend akceptuj <gracz>; friend usuń <gracz>; friend zaproszenia.")
