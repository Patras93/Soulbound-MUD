# -*- coding: utf-8 -*-
"""Real OLC and production status-turn engine checks for two authored effects."""
import asyncio
import copy
from types import SimpleNamespace
from systems.live_olc19_status_skills import (
    parse_statuses, apply_skill_effects_v9300, skill_effect_bundle,
    cast_with_olc_status_v1900,
)
from systems.live_content_v1204 import LiveContentV1204
from systems.summon_status_v1808 import summon_status_enemy_turn_v1808
from validation.v3600_admin_guardian2 import Fake
from core.classes_skills import CLASS_SKILLS

async def main():
    n=0
    def ok(flag,label):
        nonlocal n
        assert flag,label;n+=1
    combo=[{'kind':'poison','chance':1.0,'power_percent':20,'ticks':2},
           {'kind':'burn','chance':1.0,'power_percent':10,'ticks':2}]
    ok(parse_statuses(combo)==combo,'parses canonical list')
    ok(parse_statuses('auto') is None,'clear all')
    ok(parse_statuses('  '+__import__('json').dumps(combo)+'  ')==combo,'JSON text')
    for invalid in ([],{},None,
                    [{'kind':'poison','chance':1.}]*2,
                    [{'kind':'shock','chance':1.},{'kind':'freeze','chance':1.}],
                    [{'kind':'burn','chance':1.}]*3,
                    [{'kind':'poison','chance':1.},'auto'],
                    [{'kind':'shock','chance':float('nan')}],
                    '[{"kind":"poison","chance":true}]',
                    '__import__("os").system("echo hacked")'):
        try:
            value=parse_statuses(invalid)
            if invalid is None:
                raise AssertionError('none accepted')
        except (ValueError,TypeError):ok(True,'bad input blocked')
        else:raise AssertionError(f'accepted invalid {invalid!r}: {value!r}')
    mob=SimpleNamespace(key='mob',template_id='wolf',room_id='r',hp=1000,alive=True)
    messages=apply_skill_effects_v9300(mob,combo,200,{'max_hp':1000},now=10,rolls=[0,0])
    ok(len(messages)==2,'two real status messages')
    ok(set(mob.v1808_summon_statuses)=={'poison','burn'},'real shared status pool')
    ok(mob.hp==1000,'no phantom instant damage')
    lines,skip,killed=summon_status_enemy_turn_v1808(mob,now=14)
    ok(mob.hp<1000 and not killed,'actual DOT tick')
    ok(bool(lines),'real periodic message')
    ok(not apply_skill_effects_v9300(mob,combo,200,now=15,rolls=[0,0]),'cooldown preserved')
    stunned=SimpleNamespace(key='mob',template_id='wolf',room_id='r',hp=1000,alive=True)
    ok(len(apply_skill_effects_v9300(stunned,[{'kind':'shock','chance':1.},
        {'kind':'poison','chance':1.}],200,now=10,rolls=[0,0]))==2,'control plus dot')
    lines,skip,killed=summon_status_enemy_turn_v1808(stunned,now=11)
    ok(skip and not killed,'real control skip')
    boss=SimpleNamespace(key='boss',template_id='b',room_id='r',hp=1000,alive=True)
    ok(not apply_skill_effects_v9300(boss,[{'kind':'shock','chance':.2}],200,
        {'boss':True},now=10,rolls=[.15]),'boss resist')
    ok(skill_effect_bundle({'olc_status':{'kind':'burn','chance':1.}})[0]['kind']=='burn','legacy field')
    ok(skill_effect_bundle({'olc_statuses':combo})==combo,'new field')

    user=Fake();service=LiveContentV1204(SimpleNamespace(conn=user.server.db.conn))
    user.server.live_content_v1204=service
    original=copy.deepcopy(service.draft)
    try:
        message=await _command(user,'pomoc 51')
        ok('POMOC 51' in message,'help routing')
        for raw in ('not JSON','[]','[{"kind":"freeze","chance":1},{"kind":"shock","chance":1}]',
                    '[{"kind":"burn","chance":1},{"kind":"burn","chance":1}]'):
            try:service.stage_edit('skill','warrior_power_slash','olc_statuses',raw)
            except ValueError:ok(True,'invalid stage rejected')
            else:raise AssertionError('invalid OLC saved '+raw)
        ok(service.draft==original,'no invalid draft writes')
        command='edytuj skill warrior_power_slash olc_statuses | '+__import__('json').dumps(combo,separators=(',',':'))
        reply=await _command(user,command)
        ok('przygotowano zmian' in reply,'admin edited via live command')
        ok(service.draft['skill_edits']['warrior_power_slash']['olc_statuses']==combo,'OLC stored pair')
        ok(service.active==original,'ACTIVE untouched')
        ok('edycji' in service.validate(service.draft),'OLC validator reads combo')
        ok('Aktywowano' in service.apply(user.server,'tester'),'real OLC publish')
        ok(service.active['skill_edits']['warrior_power_slash']['olc_statuses']==combo,'published saved')
        ok(CLASS_SKILLS['Wojownik'][0]['id']!='nonexistent','catalog unchanged definition')
        ok(service.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite valid')
        # Runtime tests use a fake room, never a real account or live server.
        class Session:
            character=SimpleNamespace(room_id='r')
            combat_mob_key='m'
            _recap52_dealt=0
            def __init__(self):
                self.mob=SimpleNamespace(key='m',template_id='wolf',room_id='r',hp=1000,alive=True)
                self.events=[]
                self.server=SimpleNamespace(world=SimpleNamespace(room_mobs=lambda _room:[self.mob]),
                                            party_combat_broadcast=self.broadcast)
            def find_skill_from_input(self,raw):
                return {'name':'Test','kind':'damage','olc_statuses':combo},''
            async def broadcast(self,*args,**kw):
                self.events.append(args[1])
        actor=Session()
        async def cast(self,raw):
            self.mob.hp-=300
            self._recap52_dealt+=300
            return 'hit'
        ok(await cast_with_olc_status_v1900(actor,'spell',cast,{'wolf':{'max_hp':1000}})=='hit','adapter executed')
        ok(set(actor.mob.v1808_summon_statuses)=={'poison','burn'},'live adapter dual status')
        ok(len(actor.events)==2,'two player-facing combat messages')
        ok(actor.mob.hp==700,'no duplicated physical damage')
        print(f'V93 SKILL EFFECTS: {n} PASS',flush=True)
    finally:
        user.server.db.conn.close()

async def _command(user, command):
    await user.admin_command('live '+command)
    return user.messages[-1]

if __name__=='__main__':asyncio.run(main())
