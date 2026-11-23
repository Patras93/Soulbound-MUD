# -*- coding: utf-8 -*-
"""v116.00.65: retired player summons; leader-only group monitor.

UOSS NPC helper selection and boss-turn assistance are independent and intact.
Do not erase saved summon rows; historical isolated regressions remain supported.
"""
from __future__ import annotations

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
        return await super().handle_party(args)

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
