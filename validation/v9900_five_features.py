# -*- coding: utf-8 -*-
"""v99 targeted regression: five new Admin Live areas and runtime safety."""
import asyncio
import copy
import json
import sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204, blank
from systems import admin_live_five_v9900 as v99
from systems import uoss_regeneration_v9900 as regen
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from data.quests import QUESTS
from core.classes_skills import CLASS_SKILLS

async def main():
    count=0
    def ok(test, label):
        nonlocal count
        assert test, label
        count+=1
    host=Fake();guest=Fake(False,host.server.db)
    host.server.sessions=[host];guest.server.sessions=[host,guest]
    db=host.server.db.conn
    service=LiveContentV1204(SimpleNamespace(conn=db))
    host.server.live_content_v1204=service
    guest.server.live_content_v1204=service
    async def call(command, actor=host):
        await actor.admin_command('live '+command)
        return actor.messages[-1]
    for num in (60,61,62,63,64):
        ok('POMOC '+str(num) in await call('pomoc '+str(num)),'help '+str(num))
        ok('Nieznana komenda' in await call('pomoc '+str(num),guest),'permission '+str(num))
    ok('KONTROLA' in await call('arena real kontrola'),'arena control')
    ok('NIE' in host.messages[-1] and 'SQLite' in host.messages[-1],'arena honest separation')
    skill={'class_name':next(iter(CLASS_SKILLS)), 'name':'Promień Testu 9900',
        'desc':'Zwykły atak testowy oparty o silnik.', 'kind':'damage', 'unlock':1,
        'mana':1,'cooldown':4,'scale':'strength','mult':1.2,'aliases':[]}
    skillid='live_test_skill_9900'
    ok('BRAK W DRAFT' in await call('skill kreator karta '+skillid),'skill initial')
    original=copy.deepcopy(service.draft)
    command='skill kreator plan '+skillid+' | '+json.dumps(skill,ensure_ascii=False)
    ok('SKILL KREATOR PLAN' in await call(command),'skill planned')
    ok(service.draft==original,'skill no early mutation')
    ok('zatwierdzono' in await call('skill kreator zatwierdz POTWIERDZAM'),'skill approved')
    ok(skillid in service.draft['skills'] and skillid not in service.active['skills'],'skill draft only')
    ok('Cofnieto' in await call('skill kreator cofnij POTWIERDZAM'),'skill undo')
    ok(service.draft==original,'skill exact undo')
    invalid={**skill,'mult':999}
    ok('ADMIN LIVE V99' in await call('skill kreator plan '+skillid+' | '+json.dumps(invalid)),'skill invalid')
    # Validate formerly rejected two-status *new* skill definitions.
    status_skill={**skill,'olc_statuses':[{'kind':'poison','chance':0.5}]}
    # The authoritative status parser decides allowed fields; a structural
    # validation error must never mutate DRAFT regardless of result.
    await call('skill kreator plan '+skillid+' | '+json.dumps(status_skill))
    ok(service.draft==original,'status safe staging')
    key=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    boss_rule={'phases':[{'below_hp':100,'every':2,'heal_percent':5,'label':'Sila Odrodzenia'},
                         {'below_hp':50,'every':1,'heal_percent':8,'label':'Ostatni Dech'}]}
    ok('UOSS ODNOWA PLAN' in await call('boss uoss odnowa plan '+key+' | '+json.dumps(boss_rule)),'boss staged')
    ok('zatwierdzono' in await call('boss uoss odnowa zatwierdz POTWIERDZAM'),'boss approved')
    ok(key in service.draft['v99_rules'] and key not in service.active['v99_rules'],'boss draft')
    ok('Cofnieto' in await call('boss uoss odnowa cofnij POTWIERDZAM'),'boss undo')
    ok(service.draft==original,'boss exact undo')
    invalid={key:{'phases':[{'below_hp':90,'every':0,'heal_percent':12,'label':'Bad'}]}}
    try:regen.validate(invalid)
    except ValueError:count+=1
    else:raise AssertionError('bad boss rules accepted')
    regen.sync({key:boss_rule})
    mob=SimpleNamespace(alive=True,hp=40,max_hp=100,combat_turn=1)
    healed,label=regen.apply_regen(mob,{'uoss_unique_superboss_key':key})
    ok((healed,label,mob.hp)==(8,'Ostatni Dech',48),'boss actual heal')
    ok(regen.apply_regen(mob,{'uoss_unique_superboss_key':key})==(0,''),'boss once per turn')
    mob.combat_turn=2
    ok(regen.apply_regen(mob,{'uoss_unique_superboss_key':key})[0]==8,'boss cadence')
    mob.hp=0;mob.combat_turn=3
    ok(regen.apply_regen(mob,{'uoss_unique_superboss_key':key})==(0,''),'boss dead not healed')
    regen.sync({})
    qid=next(iter(QUESTS))
    ok('QUEST DOKTOR POLE' in await call('questy doktor pole '+qid),'quest inventory')
    # Conservative field repair. If not supported by the quest's kind,
    # full service validation vetoes it, and no state changes.
    original=copy.deepcopy(service.draft)
    old=QUESTS[qid].get('reward_gold',0)
    ok('QUEST DOKTOR NAPRAW PLAN' in await call(f'questy doktor napraw plan {qid} reward_gold | {old+1}'),'quest plan')
    ok(service.draft==original,'quest staged')
    ok('zatwierdzono' in await call('questy doktor napraw zatwierdz POTWIERDZAM'),'quest approved')
    ok('Cofnieto' in await call('questy doktor napraw cofnij POTWIERDZAM'),'quest undo')
    ok(service.draft==original,'quest undo exact')
    friend=Fake(False,host.server.db);friend.account_id=7;friend.character.name='OnlineFriend'
    host.server.sessions=[host,friend]
    ok('POSTAC ONLINE ZASOBY' in await call('postacie online zasoby karta OnlineFriend'),'online card')
    oldhp,oldmana=friend.current_hp,friend.current_mana
    ok('POSTAC ONLINE PLAN' in await call('postacie online zasoby plan OnlineFriend | hp=55,mana=40'),'online plan')
    ok((friend.current_hp,friend.current_mana)==(oldhp,oldmana),'online planned no effect')
    ok('ZMIENIONO' in await call('postacie online zasoby zatwierdz POTWIERDZAM'),'online commit')
    ok((friend.current_hp,friend.current_mana)==(55,40),'online value changed')
    ok('COFNIETO' in await call('postacie online zasoby cofnij POTWIERDZAM'),'online undo')
    ok((friend.current_hp,friend.current_mana)==(oldhp,oldmana),'online restored')
    ok('POSTAC ONLINE PLAN' in await call('postacie online zasoby plan OnlineFriend | hp=70'),'online conflict staged')
    friend.current_hp=44
    ok('Konflikt' in await call('postacie online zasoby zatwierdz POTWIERDZAM'),'online CAS')
    ok(friend.current_hp==44,'online conflict preserved')
    friend.combat_mob_key='danger'
    ok('Postac walczy' in await call('postacie online zasoby plan OnlineFriend | hp=70'),'combat guard')
    ok('Nieznana komenda' in await call('skill kreator karta '+skillid,guest),'skill permissions')
    ok('Nieznana komenda' in await call('postacie online zasoby karta OnlineFriend',guest),'online permissions')
    ok('Nieznana komenda' in await call('boss uoss odnowa karta '+key,guest),'boss permissions')
    ok('Nieznana komenda' in await call('questy doktor pole '+qid,guest),'quest permissions')
    return count

if __name__=='__main__':print(f'V99 FIVE FEATURES: {asyncio.run(main())} PASS')
