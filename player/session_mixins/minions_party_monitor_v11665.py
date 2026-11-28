# -*- coding: utf-8 -*-
"""v116.00.65: retired player summons; leader-only group monitor.

UOSS NPC helper selection and boss-turn assistance are independent and intact.
Do not erase saved summon rows; historical isolated regressions remain supported.
"""
from __future__ import annotations

import time

from network.protocol_gameplay_utils import normalize_lookup_text


class SessionMinionsPartyMonitorV11665Mixin:
    def _v11665_player_minions_retired(self):
        return bool(getattr(getattr(getattr(self, 'server', None), 'db', None),
                            '_retired_player_minions_v11665', False))

    async def handle_party(self, args):
        parts=str(args or '').strip().split(maxsplit=1)
        if parts and self.normalize_description_query(parts[0]) in ('monitor','mon','monitoring'):
            await self.party_monitor_v11665(parts[1] if len(parts)>1 else '')
            return
        if parts:
            action = self.normalize_description_query(parts[0])
            value = parts[1] if len(parts) > 1 else ''
            if action in ('dolacz', 'join') and value:
                return await self.request_remote_party_v11679(value)
            if action in ('akceptuj', 'zaakceptuj', 'przyjmij', 'accept', 'odrzuc', 'odmow', 'decline') and value:
                return await self.answer_remote_party_v11679(value, action in ('akceptuj', 'zaakceptuj', 'przyjmij', 'accept'))
            if action in ('prosby', 'requests'):
                return await self.remote_party_pending_v11679()
            if action in ('anuluj', 'cancel'):
                row = self.remote_party_requests_v11679().pop(self.account_id, None)
                await self.send('Anulowano prośbę.' if row else 'Nie masz oczekującej prośby.')
                if row:
                    await row[1].send(f'{self.character.name} anuluje prośbę o dołączenie.')
                return
            if action in ('pomoc', 'komendy', 'help'):
                await self.send('druzyny — aktywne drużyny; druzyna dolacz <numer/lider>; druzyna prosby; '
                                'druzyna akceptuj/odrzuc <gracz>; druzyna anuluj. Bez argumentu dolacz przyjmuje zaproszenie.')
        return await super().handle_party(args)

    def remote_party_online_v11679(self, session):
        return bool(session and not session.closed and session.character
                    and session.account_id is not None
                    and not getattr(session, "_remote_party_leaving_v11679", False)
                    and self.server.session_by_account(session.account_id) is session)

    def remote_party_requests_v11679(self):
        requests = getattr(self.server, 'party_join_requests_v11679', None)
        if requests is None:
            requests = self.server.party_join_requests_v11679 = {}
        now = time.monotonic()
        for aid, (requester, leader, members, expires) in list(requests.items()):
            if (expires <= now or aid != requester.account_id or not self.remote_party_online_v11679(requester)
                    or not self.remote_party_online_v11679(leader)
                    or self.server.parties.get(leader.account_id) is not members
                    or leader.party_key() != leader.account_id or requester.party_key() is not None):
                requests.pop(aid, None)
        return requests

    def remote_party_list_v11679(self):
        leaders = []
        for key, members in self.server.parties.items():
            leader = self.server.session_by_account(key)
            if self.remote_party_online_v11679(leader) and key in members:
                leaders.append((leader, members))
        return sorted(leaders, key=lambda row: row[0].character.name.casefold())

    async def show_remote_parties_v11679(self, raw=''):
        from data.rooms import ROOMS
        self.remote_party_requests_v11679()
        rows = self.remote_party_list_v11679()
        self.remote_party_list_context_v11679 = rows
        if not rows:
            await self.send('DRUŻYNY: brak aktywnych drużyn z liderem online.')
            return
        lines = ['DRUŻYNY — aktywne drużyny:']
        for index, (leader, members) in enumerate(rows, 1):
            capacity = leader.character.party_capacity()
            room = ROOMS.get(leader.character.room_id, {}).get('name', 'inna lokacja')
            goal = self.server.party_goals.get(leader.account_id, '')
            lines.append(f'{index}. Lider: {leader.character.name}. {len(members)}/{capacity} graczy; {room}.'
                         + (' Drużyna pełna.' if len(members) >= capacity else '')
                         + (f' Cel: {goal}.' if goal else ''))
        lines.append('Dołączenie: druzyna dolacz <numer lub nazwa lidera>.')
        await self.send('\r\n'.join(lines))

    async def request_remote_party_v11679(self, value):
        requests = self.remote_party_requests_v11679()
        if self.party_key() is not None:
            await self.send('Już należysz do drużyny. Najpierw ją opuść.')
            return
        selector = str(value).strip()
        if selector.isdecimal():
            rows = getattr(self, 'remote_party_list_context_v11679', [])
            index = int(selector) - 1 if len(selector) <= 6 else -1
            row = rows[index] if 0 <= index < len(rows) else None
        else:
            normalized = self.normalize_description_query(selector)
            matches = [row for row in self.remote_party_list_v11679()
                       if self.normalize_description_query(row[0].character.name) == normalized]
            row = matches[0] if len(matches) == 1 else None
        if not row:
            await self.send('Nie ma takiej drużyny. Wpisz druzyny i wybierz numer lub nazwę lidera.')
            return
        leader, members = row
        if (not self.remote_party_online_v11679(leader)
                or self.server.parties.get(leader.account_id) is not members
                or leader.party_key() != leader.account_id):
            await self.send('Lista jest nieaktualna. Wpisz druzyny ponownie.')
            return
        if len(members) >= leader.character.party_capacity():
            await self.send('Ta drużyna jest pełna.')
            return
        if (leader.is_ignored_v03051(leader.account_id, self.account_id)
                or self.is_ignored_v03051(self.account_id, leader.account_id)):
            await self.send('Nie można wysłać prośby do tej osoby.')
            return
        if self.account_id in requests:
            await self.send('Masz już oczekującą prośbę. Wpisz druzyna anuluj lub poczekaj na odpowiedź.')
            return
        requests[self.account_id] = (self, leader, members, time.monotonic() + 180)
        await self.send(f'Wysłano prośbę do lidera {leader.character.name}. Ważna 3 minuty.')
        await leader.send(f'{self.character.name} prosi o dołączenie do drużyny i teleport do ciebie. '
                          f'Wpisz druzyna akceptuj {self.character.name} lub druzyna odrzuc {self.character.name}.')

    async def remote_party_pending_v11679(self):
        requests = self.remote_party_requests_v11679()
        incoming = [row[0].character.name for row in requests.values() if row[1] is self]
        outgoing = requests.get(self.account_id)
        await self.send('Prośby do twojej drużyny: ' + (', '.join(incoming) if incoming else 'brak') + '.'
                        + (f' Twoja prośba: {outgoing[1].character.name}.' if outgoing else ''))

    def remote_party_busy_v11679(self):
        return (self.current_hp <= 0 or self.is_downed_v0371()
                or any(getattr(self, name, False) for name in (
                    'combat_mob_key', 'moving', 'guiding', 'resting', 'rest_task',
                    'auto_fishing', 'auto_fishing_task', 'auto_mining', 'auto_mining_task',
                    'auto_woodcutting', 'auto_woodcutting_task', 'auto_herbalism', 'auto_herbalism_task'))
                or self.guide_task_active() or self.smelt_task_active_v1124())

    def remote_party_entry_error_v11679(self, target):
        """New remote travel uses personal gate records, never the leader's unlocks."""
        from data.rooms import ROOMS
        from core.mine_tunnels import mine_tunnel_identity
        from core.progression_resources import mine_floor_number
        from systems.dungeons_regions import (crypt_floor_number, astral_floor_number,
            giant_fortress_floor_number, mythic_crypt_floor_number, mythic_astral_floor_number,
            ASTRAL_MIN_FLOOR)
        from systems.current_deep_dungeon_grindfields import deep_dungeon_floor_for_navigation
        from world.generation_systems import v0200_mega_identity, v0200_mega_is_boss_index
        room = ROOMS.get(target)
        if room is None:
            return 'Lokacja lidera jest niedostępna.'
        if target == self.character.room_id:
            return ''
        if (mine_tunnel_identity(target) or room.get('v1190_secret_role')
                or room.get('v020_gauntlet') or room.get('v021_endless_gauntlet_round')
                or target.startswith(('uoss_superboss_arena_', 'uoss_deep_dungeon_floor_0', 'house_', 'housing_'))
                or room.get('requires_ship') or room.get('underwater')):
            return 'Do tej specjalnej lokacji trzeba wejść zwykłą drogą.'
        error = (self.newbie_entry_block_v03051(target) or self.mythic_entry_error(target)
                 or self.profession_dungeon_access_error(target))
        if error:
            return error
        mine = mine_floor_number(target)
        if mine is not None and mine > self.mine_progress()['max_floor_unlocked']:
            return 'Najpierw odblokuj to piętro kopalni.'
        source = self.character.room_id
        for kind, parser, first in (('crypt', crypt_floor_number, 1), ('astral', astral_floor_number, ASTRAL_MIN_FLOOR),
                                    ('mythic_crypt', mythic_crypt_floor_number, 1), ('mythic_astral', mythic_astral_floor_number, 1),
                                    ('giant', giant_fortress_floor_number, 1)):
            floor = parser(target)
            if floor is not None:
                start = parser(source) or first
                for gate in range(((start+9)//10)*10, floor, 10):
                    if not self.server.db.boss_floor_cleared(self.account_id, kind, gate):
                        return f'Najpierw zalicz własną bramę bossa na piętrze {gate}.'
        floor = deep_dungeon_floor_for_navigation(target)
        if floor is not None:
            start = deep_dungeon_floor_for_navigation(source) or 1
            for gate in range(((start+24)//25)*25, floor, 25):
                if not self.uoss_deep_dungeon_apanda_cleared_v11331(gate):
                    return f'Najpierw zalicz Apandę na piętrze {gate}.'
        mega = v0200_mega_identity(target)
        if mega:
            key, index = mega
            previous = v0200_mega_identity(source)
            start = previous[1] if previous and previous[0] == key else 1
            for gate in range(start, index):
                if v0200_mega_is_boss_index(key, gate) and not self.server.db.boss_floor_cleared(self.account_id, f'v020_mega_{key}', gate):
                    return f'Najpierw zalicz własną bramę megalochu {gate}.'
        return ''

    async def answer_remote_party_v11679(self, value, accept):
        requests = self.remote_party_requests_v11679()
        selector = self.normalize_description_query(value)
        rows = [row for row in requests.values() if row[1] is self
                and self.normalize_description_query(row[0].character.name) == selector]
        if self.party_key() != self.account_id or len(rows) != 1:
            await self.send('Brak takiej aktywnej prośby do twojej drużyny. Wpisz druzyna prosby.')
            return
        requester, leader, members, expires = rows[0]
        aid = requester.account_id
        requester_name = requester.character.name
        leader_name = self.character.name
        if not accept:
            requests.pop(aid, None)
            await requester.send(f'{leader_name} odrzuca twoją prośbę o dołączenie do drużyny.')
            await self.send(f'Odrzucono prośbę gracza {requester_name}.')
            return
        if (self.is_ignored_v03051(self.account_id, aid) or requester.is_ignored_v03051(aid, self.account_id)):
            requests.pop(aid, None)
            await self.send('Prośba nie jest już dostępna.')
            return
        if len(members) >= self.character.party_capacity():
            await self.send('Drużyna jest pełna. Prośba pozostaje aktywna do wygaśnięcia.')
            return
        if (self.remote_party_busy_v11679() or requester.remote_party_busy_v11679()
                or getattr(requester, '_remote_party_dispatching_v11679', False)):
            await self.send('Teleport wymaga, aby oboje zakończyli walkę, ruch, odpoczynek i auto-profesje oraz gracz zakończył bieżącą komendę. Prośba nadal aktywna.')
            return
        target = self.character.room_id
        error = requester.remote_party_entry_error_v11679(target)
        if error:
            await self.send(f'Nie można teleportować {requester_name}: {error}')
            await requester.send(f'Nie można dołączyć teleportem: {error}')
            return
        # No await between validation, save and membership mutation. A failed
        # save cannot leave a player in a party or at the wrong room in memory.
        old = requester.character.room_id
        previous = requester.previous_room_id
        if old != target:
            requester.character.room_id = target
            requester.previous_room_id = None  # back must not bypass travel gates
            try:
                self.server.db.save_character(requester.character)
            except Exception:
                requester.character.room_id = old
                requester.previous_room_id = previous
                raise
        members.add(aid)
        ready = self.server.party_ready_checks.get(self.account_id)
        if ready is not None:
            ready.discard(aid)
        requests.pop(aid, None)
        self.server.party_invites.pop(aid, None)
        if old != target:
            await self.server.broadcast_room(old, f'{requester_name} teleportuje się do drużyny.', exclude=requester)
            await self.server.broadcast_room(target, f'{requester_name} przybywa teleportem.', exclude=requester)
        await self.server.party_broadcast(self.account_id, f'{requester_name} dołącza do drużyny.')
        if (self.remote_party_online_v11679(requester) and requester.account_id == aid
                and requester.party_key() == self.account_id):
            await requester.send(f'Prośba zaakceptowana. Dołączasz do lidera {leader_name}.')
            if (self.remote_party_online_v11679(requester) and requester.account_id == aid
                    and requester.character.room_id == target
                    and not getattr(requester, '_remote_party_dispatching_v11679', False)
                    and not requester.remote_party_busy_v11679()):
                await requester.look()

    async def teleport_to_party_leader(self, raw=""):
        """Keep old crypt recovery; also let any member return to a named teammate."""
        requested = " ".join(str(raw or "").split())
        normalized = self.normalize_description_query(requested)
        leader_words = ("", "to leader", "leader", "do lidera", "lider", "lidera")
        if not self.remote_party_online_v11679(self):
            return False
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False
        # No guessing which room to use when the team has split. The leader
        # is free to pick any online teammate without moving anyone else.
        members = self.server.parties.get(key, set())
        candidates = []
        for aid in sorted(members):
            teammate = self.server.session_by_account(aid)
            if teammate is not self and self.remote_party_online_v11679(teammate) and teammate.party_key() == key:
                candidates.append(teammate)
        if normalized in ("druzyna", "party", "lista", "list") or (normalized in leader_words and key == self.account_id):
            from data.rooms import ROOMS
            lines = ["TELEPORT DRUŻYNY — wybierz członka: "]
            for teammate in sorted(candidates, key=lambda member: member.character.name.casefold()):
                room = ROOMS.get(teammate.character.room_id, {}).get('name', teammate.character.room_id)
                state = ' (zajęty lub powalony)' if teammate.remote_party_busy_v11679() else ''
                lines.append(f'{teammate.character.name}: {room}{state}.')
            if not candidates:
                lines.append('Brak innych członków drużyny online.')
            lines.append('Użycie: tp <imię gracza> lub tp gracz <imię>.')
            await self.send('\r\n'.join(lines))
            return False
        if normalized in leader_words:
            if self.character.room_id != 'temple':
                return await super().teleport_to_party_leader(raw)
            candidates = [m for m in candidates if m.account_id == key]
        else:
            if normalized.startswith('gracz '):
                requested = requested.split(maxsplit=1)[1]
                normalized = self.normalize_description_query(requested)
            candidates = [m for m in candidates if self.normalize_description_query(m.character.name) == normalized]
        if len(candidates) != 1:
            await self.send('Nie ma takiego innego członka drużyny online. Wpisz tp druzyna.')
            return False
        teammate = candidates[0]
        if (self.remote_party_busy_v11679() or teammate.remote_party_busy_v11679()
                or getattr(teammate, '_remote_party_dispatching_v11679', False)):
            await self.send('Teleport wymaga, aby oboje byli żywi i zakończyli walkę, ruch, odpoczynek oraz auto-profesje. Spróbuj ponownie.')
            return False
        old = self.character.room_id
        target = teammate.character.room_id
        if old == target:
            await self.send(f'Jesteś już przy {teammate.character.name}.')
            return True
        error = self.remote_party_entry_error_v11679(target)
        if error:
            await self.send(f'Teleport zablokowany: {error}')
            return False
        # A synchronous check and save: no yield between membership, gate
        # checks and assignment, no changes to any other player's position.
        if (self.party_key() != key or teammate.party_key() != key
                or not self.remote_party_online_v11679(teammate)
                or teammate.character.room_id != target):
            await self.send('Drużyna lub cel zmieniły się. Spróbuj ponownie.')
            return False
        previous = self.previous_room_id
        self.character.room_id = target
        self.previous_room_id = None
        try:
            self.server.db.save_character(self.character)
        except Exception:
            self.character.room_id = old
            self.previous_room_id = previous
            raise
        from data.rooms import ROOMS
        name = self.character.name
        target_name = teammate.character.name
        await self.server.broadcast_room(old, f'{name} teleportuje się do drużyny.', exclude=self)
        await self.server.broadcast_room(target, f'{name} wraca do drużyny teleportem.', exclude=self)
        await self.send(f'Teleport do {target_name}: {ROOMS.get(target, {}).get("name", target)}.')
        await self.look()
        return True

    async def dispatch_registered_command(self, command, args):
        # Remote acceptance is executed on the leader's connection. Do not
        # relocate a different player while their own command is in flight.
        self._remote_party_dispatching_v11679 = True
        try:
            return await super().dispatch_registered_command(command, args)
        finally:
            self._remote_party_dispatching_v11679 = False

    async def leave_party(self, announce=True):
        # Includes logout and character switching, even when not in a party.
        self._remote_party_leaving_v11679 = True
        try:
            self.remote_party_requests_v11679()
            self.remote_party_list_context_v11679 = []
            return await super().leave_party(announce=announce)
        finally:
            self._remote_party_leaving_v11679 = False

    async def disband_party(self):
        self._remote_party_leaving_v11679 = True
        try:
            self.remote_party_requests_v11679()
            return await super().disband_party()
        finally:
            self._remote_party_leaving_v11679 = False

    async def party_monitor_v11665(self, raw=''):
        if not self.character or self.account_id is None:
            return
        key=self.party_key()
        if key is None:
            await self.send('MONITOR DRUŻYNY: nie należysz do drużyny.')
            return
        if int(key)!=int(self.account_id):
            await self.send('MONITOR DRUŻYNY: tylko lider może monitorować członków drużyny.')
            return
        members=sorted((s for s in self.server.party_sessions(self.account_id)
                        if getattr(s,'character',None) and not getattr(s,'closed',False)),
                       key=lambda s:(s.account_id!=key,s.character.name.casefold()))
        selector=normalize_lookup_text(raw or '').strip().casefold()
        if selector:
            members=[s for s in members if normalize_lookup_text(s.character.name).casefold()==selector]
            if not members:
                await self.send('MONITOR DRUŻYNY: nie ma takiego członka online.')
                return
        await self.send(f'MONITOR DRUŻYNY: {len(members)} graczy online. Lider: {self.character.name}.')
        from data.rooms import ROOMS
        from data.mobs import MOB_TEMPLATES
        from world.uoss_superboss_runtime import superboss_helper_profile_v11137
        uoss_seen=set()
        for member in members:
            char=member.character
            hp=max(0,int(member.current_hp)); hpmax=max(1,int(member.max_hp()))
            mp=max(0,int(member.current_mana)); mpmax=max(1,int(member.max_mana()))
            room=('obok lidera' if char.room_id==self.character.room_id
                  else ROOMS.get(char.room_id,{}).get('name','inna lokacja'))
            down=getattr(member,'is_downed_v0371',None)
            state=('powalony' if callable(down) and down()
                   else 'w walce' if getattr(member,'combat_mob_key',None) else 'spokojny')
            await self.send(f'{char.name}{" (lider)" if member.account_id==key else ""}: '
                            f'HP {hp}/{hpmax} ({min(100,hp*100//hpmax)}%), '
                            f'MP {mp}/{mpmax} ({min(100,mp*100//mpmax)}%), {state}; {room}.')
            # UOSS allies exist only for a chosen UOSS encounter, not in summons_v1700.
            mobkey=getattr(member,'combat_mob_key',None)
            mob=self.server.world.mobs.get(mobkey) if mobkey else None
            if mob and mob.alive and mob.room_id==char.room_id:
                template=MOB_TEMPLATES.get(mob.template_id,{})
                helper=superboss_helper_profile_v11137(member,template)
                if helper and helper['name'] not in uoss_seen:
                    uoss_seen.add(helper['name'])
                    await self.send(f"Wspólnik UOSS: {helper['name']}, rola {helper['role']}, aktywny przy bossie.")
        if not uoss_seen:
            await self.send('Wspólnicy UOSS: brak aktywnych przy bossie.')

    async def _v11665_summon_disabled(self):
        await self.send('Miniony i chowańce zostały wycofane z gry. '
                        'Wyjątek: wspólnicy rekrutowani do walk z bossami UOSS.')

    async def minions_v11665(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        await self.send('Miniony: użyj chowaniec lista.')

    async def cast_minion_spell_v11664(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().cast_minion_spell_v11664(raw)

    async def summons_v1700(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().summons_v1700(raw)

    async def mage_elementals_v1702(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().mage_elementals_v1702(raw)

    async def druid_call_v1708(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().druid_call_v1708(raw)

    async def druid_order_v1708(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().druid_order_v1708(raw)

    async def tactics_v1800(self, raw=''):
        if self._v11665_player_minions_retired():
            return await self._v11665_summon_disabled()
        return await super().tactics_v1800(raw)

    async def necro_v1700(self, raw=''):
        cmd=normalize_lookup_text(raw or '').strip().casefold()
        if self._v11665_player_minions_retired() and not (cmd.startswith('wyrwij') or cmd.startswith('scal ')):
            return await self._v11665_summon_disabled()
        return await super().necro_v1700(raw)

    def v11664_can_use_summon(self, kind, required_class):
        if self._v11665_player_minions_retired():
            return False
        return super().v11664_can_use_summon(kind, required_class)

    async def summon_combat_turn_v1700(self, mob):
        if self._v11665_player_minions_retired():
            return None
        return await super().summon_combat_turn_v1700(mob)

    async def summon_take_enemy_hit_v1702(self,mob,raw_damage=None,roll=None):
        if self._v11665_player_minions_retired():
            return False
        return await super().summon_take_enemy_hit_v1702(mob,raw_damage=raw_damage,roll=roll)

    def _v1806_summon_rest_regen(self):
        if self._v11665_player_minions_retired():
            return 0
        return super()._v1806_summon_rest_regen()

    def _v1711_companions_for_healing(self,include_party=False):
        if self._v11665_player_minions_retired():
            return []
        return super()._v1711_companions_for_healing(include_party=include_party)

    def _v1702_prepare_summon_lives(self, conn):
        if self._v11665_player_minions_retired():
            return None
        return super()._v1702_prepare_summon_lives(conn)

    def _v1710_refresh_summon_health(self, conn):
        if self._v11665_player_minions_retired():
            return None
        return super()._v1710_refresh_summon_health(conn)

    def _v1703_dismiss_summons_on_login(self):
        # Never mutate historic summon records during live login.
        if self._v11665_player_minions_retired():
            return 0
        return super()._v1703_dismiss_summons_on_login()

    def _v1702_upgrade_summon_life(self, conn, kind, level):
        if self._v11665_player_minions_retired():
            return None
        return super()._v1702_upgrade_summon_life(conn,kind,level)
