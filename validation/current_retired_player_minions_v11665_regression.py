# -*- coding: utf-8 -*-
"""v116.65: players and UOSS NPC helpers only; archives untouched."""
import asyncio
import sqlite3
import unittest
from types import SimpleNamespace

from player.session_mixins.minions_party_monitor_v11665 import SessionMinionsPartyMonitorV11665Mixin
from systems.visible_companions_v1801 import nearby_companions_v1801

class Legacy:
    def __init__(self):
        self.server=SimpleNamespace(db=SimpleNamespace(_retired_player_minions_v11665=True))
        self.sent=[]
        self.character=SimpleNamespace(name='Lider',room_id='temple')
        self.account_id=1
        self.current_hp=100
        self.current_mana=60
        self.combat_mob_key=None
    async def send(self,msg):self.sent.append(str(msg))
    def party_key(self):return 1
    def normalize_description_query(self,x):return str(x).lower()
    def max_hp(self):return 100
    def max_mana(self):return 100
    def is_downed_v0371(self):return False
    def v11664_can_use_summon(self,*args):return True
    async def cast_minion_spell_v11664(self,*args):raise AssertionError('live cast invoked')
    async def summons_v1700(self,*args):raise AssertionError('live summon invoked')
    async def mage_elementals_v1702(self,*args):raise AssertionError('live elementals invoked')
    async def druid_call_v1708(self,*args):raise AssertionError('live druid call invoked')
    async def druid_order_v1708(self,*args):raise AssertionError('live druid order invoked')
    async def necro_v1700(self,*args):return 'non_summon_necro'
    async def summon_combat_turn_v1700(self,*args):raise AssertionError('live summon combat')
    async def summon_take_enemy_hit_v1702(self,*args,**kw):raise AssertionError('live summon intercept')
    def _v1806_summon_rest_regen(self):raise AssertionError('live summon regen')
    def _v1711_companions_for_healing(self,*args,**kw):raise AssertionError('live summon heal')
    def _v1702_prepare_summon_lives(self,*args):raise AssertionError('live summon migration')
    def _v1710_refresh_summon_health(self,*args):raise AssertionError('live summon refresh')
    def _v1703_dismiss_summons_on_login(self):raise AssertionError('live summon mutation')
    def _v1702_upgrade_summon_life(self,*args):raise AssertionError('live summon upgrade')
    async def handle_party(self,arg):return 'legacy party'
    def active_class_names(self):return ('Mag',)
    def _v1700_conn(self):return self.server.db.conn

class Actor(SessionMinionsPartyMonitorV11665Mixin,Legacy):pass

def run():
    checks=0
    actor=Actor()
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE summons_v1700(account_id INTEGER, summon_type TEXT, active INTEGER,hp INTEGER)')
    conn.execute("INSERT INTO summons_v1700 VALUES(1,'mag',1,900)")
    conn.commit()
    actor.server.db.conn=conn
    orig=conn.total_changes
    assert not actor.v11664_can_use_summon('mag','Nekromanta');checks+=1
    for action in (actor.cast_minion_spell_v11664('skeletal mage'),actor.summons_v1700('przywolaj mag'),
                   actor.mage_elementals_v1702('przywolaj ogien'),actor.druid_call_v1708('wolf'),
                   actor.druid_order_v1708('attack'),actor.necro_v1700('przywolaj mag'),
                   actor.minions_v11665('przywolaj wilk')):
        asyncio.run(action)
    assert len(actor.sent)==7 and all('wycofane' in s for s in actor.sent);checks+=1
    assert actor.current_mana==60 and conn.total_changes==orig;checks+=1
    assert asyncio.run(actor.summon_combat_turn_v1700(SimpleNamespace(alive=True))) is None;checks+=1
    assert asyncio.run(actor.summon_take_enemy_hit_v1702(SimpleNamespace(alive=True))) is False;checks+=1
    assert actor._v1806_summon_rest_regen()==0 and actor._v1711_companions_for_healing()==[];checks+=1
    assert actor._v1702_prepare_summon_lives(conn) is None and actor._v1710_refresh_summon_health(conn) is None;checks+=1
    assert actor._v1703_dismiss_summons_on_login()==0 and actor._v1702_upgrade_summon_life(conn,'mag',3) is None;checks+=1
    assert conn.execute('SELECT active,hp FROM summons_v1700').fetchone()==(1,900) and conn.total_changes==orig;checks+=1
    assert nearby_companions_v1801(SimpleNamespace(db=actor.server.db,sessions={actor}),'temple')==[];checks+=1
    assert asyncio.run(actor.necro_v1700('wyrwij dusze'))=='non_summon_necro';checks+=1
    assert asyncio.run(actor.handle_party('lista'))=='legacy party';checks+=1
    # Verify the NPC helper path has not been touched by the retirement MRO.
    assert 'apply_uoss_helper_turn_v1146' not in SessionMinionsPartyMonitorV11665Mixin.__dict__;checks+=1
    assert 'try_hire_uoss_helper_v11160' not in SessionMinionsPartyMonitorV11665Mixin.__dict__;checks+=1
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    combat=(root/'player/session_mixins/combat_damage.py').read_text(encoding='utf8')
    assert '_retired_player_minions_v11665' in combat and 'for member in (() if _no_helpers_v11665 else members)' in combat;checks+=1
    server=(root/'server/mud_server.py').read_text(encoding='utf8')
    assert server.count('self.db._retired_player_minions_v11665 = True')>=2;checks+=1
    loop=(root/'player/session_mixins/command_loop.py').read_text(encoding='utf8')
    assert 'self.server.db._retired_player_minions_v11665 = True' in loop;checks+=1
    conn.close()
    print(f'LIVE RETIRED PLAYER SUMMONS v116.65: {checks}/{checks} PASS')
    return checks

if __name__=='__main__':run()
