# -*- coding: utf-8 -*-
"""Account-wide, consent-based friend relationships; character names are aliases."""
from player.session_mixins.skill_learning import normalize_lookup_text


class SessionFriendsMixin:
    def _friend_self_v12213(self):
        return self.server.db.friend_master_v12213(
            self.master_account_id if self.master_account_id is not None else self.account_id
        )

    def _friend_target_v12213(self, name):
        char_id = self.server.db.character_account_id_by_name_v0928(str(name or '').strip())
        return self.server.db.friend_master_v12213(char_id) if char_id is not None else None

    def _friend_label_v12213(self, aid):
        names = self.server.db.friend_character_names_v12213(aid)
        return names[0] if names else 'konto znajomego'

    async def handle_friends_v0928(self, args=''):
        raw = str(args or '').strip()
        parts = raw.split(maxsplit=1)
        action = normalize_lookup_text(parts[0]) if parts else 'list'
        conn = self.server.db.conn
        own = self._friend_self_v12213()
        if action in ('', 'list', 'lista'):
            rows = conn.execute(
                'SELECT friend_account_id FROM player_friends_v0928 '
                'WHERE account_id=? ORDER BY created_at,friend_account_id', (own,)
            ).fetchall()
            await self.send(f'ZNAJOMI: {len(rows)} kont.')
            if not rows:
                await self.send('Lista znajomych jest pusta.')
                return
            for row in rows:
                aid = int(row['friend_account_id'])
                names = self.server.db.friend_character_names_v12213(aid)
                online = self.server.session_by_master_account(aid)
                active = online.character.name if online and online.character else None
                if names:
                    description = ', '.join(f'{name} ({"online" if active and name.casefold()==active.casefold() else "offline"})' for name in names)
                    await self.send('Postacie znajomego: ' + description + '.')
                else:
                    await self.send('Znajome konto bez postaci: offline.')
            return
        if action in ('requests', 'zaproszenia'):
            rows = conn.execute(
                'SELECT sender_account_id FROM player_friend_requests_v0928 '
                'WHERE target_account_id=? ORDER BY created_at', (own,)
            ).fetchall()
            await self.send(f'ZAPROSZENIA DO ZNAJOMYCH: {len(rows)}.')
            for row in rows:
                await self.send(self._friend_label_v12213(int(row['sender_account_id'])))
            if not rows:
                await self.send('Brak oczekujących zaproszeń.')
            return
        if len(parts)<2:
            await self.send('Znajomi: znajomi; znajomi dodaj <postać>; znajomi akceptuj <postać>; znajomi usun <postać>; znajomi zaproszenia.')
            return
        aid = self._friend_target_v12213(parts[1])
        if aid is None:
            await self.send('Nie ma takiej postaci.')
            return
        name = self._friend_label_v12213(aid)
        if action in ('add', 'dodaj', 'invite', 'zapros'):
            if aid == own:
                await self.send('Nie możesz dodać własnej postaci do znajomych.')
                return
            if self.server.db.are_friends_v0928(own,aid):
                await self.send('To konto jest już w twoich znajomych. Wszystkie jego postacie są widoczne na liście.')
                return
            reverse = conn.execute(
                'SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?',
                (aid, own)
            ).fetchone()
            if reverse:
                conn.execute('DELETE FROM player_friend_requests_v0928 WHERE '
                             '(sender_account_id=? AND target_account_id=?) OR '
                             '(sender_account_id=? AND target_account_id=?)',
                             (aid,own,own,aid))
                conn.execute('INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (own,aid))
                conn.execute('INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (aid,own))
                conn.commit()
                await self.send(f'Znajomość z {name} została zaakceptowana. Obejmuje wszystkie postacie obu kont.')
                return
            conn.execute('INSERT OR IGNORE INTO player_friend_requests_v0928(sender_account_id,target_account_id) VALUES(?,?)', (own,aid))
            conn.commit()
            await self.send(f'Wysłano zaproszenie do znajomych: {name}.')
            target = self.server.session_by_master_account(aid)
            if target and not target.closed:
                await target.send(f'{self.character.name} chce dodać cię do znajomych. Użyj: znajomi akceptuj {self.character.name}.')
            return
        if action in ('accept', 'akceptuj', 'zaakceptuj'):
            request = conn.execute(
                'SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?',
                (aid,own)
            ).fetchone()
            if not request:
                await self.send('Nie masz zaproszenia od tego konta.')
                return
            conn.execute('DELETE FROM player_friend_requests_v0928 WHERE '
                         '(sender_account_id=? AND target_account_id=?) OR '
                         '(sender_account_id=? AND target_account_id=?)', (aid,own,own,aid))
            conn.execute('INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (own,aid))
            conn.execute('INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (aid,own))
            conn.commit()
            await self.send(f'Dodano do znajomych: {name}. Obejmuje wszystkie postacie obu kont.')
            target = self.server.session_by_master_account(aid)
            if target and not target.closed:
                await target.send(f'{self.character.name} zaakceptował twoją prośbę o znajomość.')
            return
        if action in ('decline','odrzuc'):
            result = conn.execute(
                'DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?', (aid,own)
            )
            conn.commit()
            await self.send('Odrzucono prośbę.' if result.rowcount else 'Nie masz prośby od tego konta.')
            return
        if action in ('remove','usun','delete'):
            existed = self.server.db.are_friends_v0928(own,aid)
            conn.execute('DELETE FROM player_friends_v0928 WHERE (account_id=? AND friend_account_id=?) OR (account_id=? AND friend_account_id=?)', (own,aid,aid,own))
            conn.execute('DELETE FROM player_friend_requests_v0928 WHERE (sender_account_id=? AND target_account_id=?) OR (sender_account_id=? AND target_account_id=?)', (own,aid,aid,own))
            conn.commit()
            await self.send('Usunięto znajomego ze wszystkich postaci obu kont.' if existed else 'Ta osoba nie była na twojej liście znajomych.')
            return
        if action in ('party','druzyna'):
            if not self.server.db.are_friends_v0928(own,aid):
                await self.send('Najpierw dodaj tę osobę do znajomych.')
                return
            target = self.server.session_by_master_account(aid)
            if not target or target.closed or not target.character:
                await self.send(f'{name} nie jest teraz online.')
                return
            await self.party_invite(target.character.name)
            return
        if action in ('gildia','guild'):
            if not self.server.db.are_friends_v0928(own,aid):
                await self.send('Najpierw dodaj tę osobę do znajomych.')
                return
            target = self.server.session_by_master_account(aid)
            if not target or target.closed or not target.character:
                await self.send(f'{name} nie jest teraz online.')
                return
            await self.handle_guild_v0926(f'zaproś {target.character.name}')
            return
        await self.send('Znajomi: znajomi; znajomi dodaj/akceptuj/odrzuc/usun <postać>; znajomi party <postać>; znajomi gildia <postać>.')
