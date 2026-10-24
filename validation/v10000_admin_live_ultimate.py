# -*- coding: utf-8 -*-
"""Focused smoke and safety tests for Admin Live v100."""
import asyncio
import copy
import json
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_ultimate_v10000 as v100
from systems import uoss_ai_v10000 as ai
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from data.quests import QUESTS

async def main():
    count=0
    def check(condition,label):
        nonlocal count
        assert condition,label
        count+=1
    a=Fake();db=a.server.db.conn
    guest=Fake(False,a.server.db)
    guest.character.name='Friend'
    a.server.sessions=[a,guest]
    guest.server=a.server
    service=LiveContentV1204(SimpleNamespace(conn=db))
    a.server.live_content_v1204=service
    async def call(command,who=a):
        await who.admin_command('live '+command)
        return who.messages[-1]
    for n in range(65,70):
        check('POMOC '+str(n) in await call('pomoc '+str(n)),'help '+str(n))
        check('Nieznana' in await call('pomoc '+str(n),guest),'no perms '+str(n))
    check('SKILL WZORCE' in await call('skill kreator wzorce'),'template help')
    base=copy.deepcopy(service.draft)
    cmd=('skill kreator wzorzec plan live_strike_10000 warrior_power_slash | '
         +json.dumps({'name':'Ostrze Stulecia','desc':'Atak z istniejacego wzorca.'}))
    check('WZORZEC PLAN' in await call(cmd),'template plan')
    check(service.draft==base,'no early skill edits')
    check('zatwierdzono' in await call('skill kreator wzorzec zatwierdz POTWIERDZAM'),'template confirm')
    check('live_strike_10000' in service.draft['skills'] and 'live_strike_10000' not in service.active['skills'],'skill draft')
    check('Cofnieto' in await call('skill kreator wzorzec cofnij POTWIERDZAM'),'template undo')
    check(service.draft==base,'skill unchanged')
    check('v100' in (await call(cmd.replace('Ostrze Stulecia','Potężne Cięcie'))),'duplicate name detected')
    check(service.draft==base,'invalid does not modify skills')
    qid=next(iter(QUESTS))
    check('QUEST DOKTOR ANALIZA' in await call('questy doktor analiza '+qid),'quest analyse')
    check('QUEST DOKTOR AUDYT' in await call('questy doktor audyt 1'),'quest audit')
    check('v100' in await call('questy doktor analiza nieznany_quest'),'missing quest handled')
    check(service.draft==base,'quest read only')
    # In real life these fields exist on the actual Character dataclass.
    db.execute('ALTER TABLE characters ADD COLUMN strength INT DEFAULT 12')
    db.execute('ALTER TABLE characters ADD COLUMN dexterity INT DEFAULT 11')
    db.execute('ALTER TABLE characters ADD COLUMN constitution INT DEFAULT 10')
    db.execute('ALTER TABLE characters ADD COLUMN intelligence INT DEFAULT 9')
    db.execute('ALTER TABLE characters ADD COLUMN willpower INT DEFAULT 8')
    db.execute('ALTER TABLE characters ADD COLUMN charisma INT DEFAULT 7')
    db.execute('ALTER TABLE characters ADD COLUMN deaths INT DEFAULT 0')
    for key,val in (('strength',12),('dexterity',11),('constitution',10),('intelligence',9),('willpower',8),('charisma',7)):
        setattr(guest.character,key,val)
    guest.character.deaths=0
    for name,val in (('character_level',30),('character_xp',2),('soul_level',1),('soul_xp',0),
                     ('soul_weapon_mastery_level',1),('soul_weapon_mastery_xp',0)):
        setattr(guest.character,name,val)
    check('POSTAC ONLINE RAPORT' in await call('postacie online raport Friend'),'online report')
    check('STATY PLAN' in await call('postacie online staty plan Friend | strength=30,dexterity=20'),'stat plan')
    check(guest.character.strength==12 and db.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==12,'stat dry run')
    check('STATY ZAPISANO' in await call('postacie online staty zatwierdz POTWIERDZAM'),'stat confirm')
    check(guest.character.strength==30 and db.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==30,'stat committed both')
    check('STATY COFNIETO' in await call('postacie online staty cofnij POTWIERDZAM'),'stat undo')
    check(guest.character.strength==12 and db.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==12,'stat reversed both')
    check('STATY PLAN' in await call('postacie online staty plan Friend | strength=40'),'stat stage conflict')
    db.execute('UPDATE characters SET strength=19 WHERE account_id=2')
    check('Konflikt' in await call('postacie online staty zatwierdz POTWIERDZAM'),'stat CAS drift rejected')
    check(guest.character.strength==12 and db.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==19,'stat no silent overwrite')
    db.execute('UPDATE characters SET strength=12 WHERE account_id=2')
    guest.combat_mob_key='combat'
    check('walczy' in await call('postacie online staty plan Friend | strength=40'),'stat combat refusal')
    guest.combat_mob_key=None
    check('Nieznana' in await call('postacie online raport Friend',guest),'online read perms')
    key=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    profile={'phases':[{'below_hp':100,'every':2,'mode':'weakest','mana_percent':5,'label':'Uderzenie many'},
                       {'below_hp':50,'every':1,'mode':'all','mana_percent':8,'label':'Ostatnia faza'}]}
    command='boss uoss ai plan '+key+' | '+json.dumps(profile)
    check('UOSS AI PLAN' in await call(command),'AI plan')
    check('zatwierdzono' in await call('boss uoss ai zatwierdz POTWIERDZAM'),'AI staged')
    check(key in service.draft['v100_rules'] and key not in service.active['v100_rules'],'AI draft only')
    check('Cofnieto' in await call('boss uoss ai cofnij POTWIERDZAM'),'AI undo')
    check(service.draft==base,'AI undo exact')
    # The authoritative publisher changes ACTIVE only after confirmed activation.
    service.draft['v100_rules'][key]=copy.deepcopy(profile)
    check(key not in ai.ACTIVE,'draft AI not active')
    check('PRZEDPUBLIKACJA OK' in service.apply(a.server,'owner',dry_run=True),'AI dry-run publish')
    check(key not in ai.ACTIVE,'AI dry-run no mutation')
    check('Aktywowano rewizję' in service.apply(a.server,'owner'),'AI hot publication')
    check(key in ai.ACTIVE and service.revision==1,'AI sync published')
    service.draft['v100_rules'].clear()
    check('Aktywowano rewizję' in service.apply(a.server,'owner'),'AI config rollback by OLC')
    check(key not in ai.ACTIVE,'AI disabled after reset')
    ai.sync({key:profile})
    m=SimpleNamespace(hp=80,max_hp=100,alive=True,combat_turn=2)
    p1=SimpleNamespace(current_hp=100,current_mana=100,account_id=2,closed=False,max_mana=lambda:200)
    p2=SimpleNamespace(current_hp=20,current_mana=100,account_id=3,closed=False,max_mana=lambda:200)
    instr=ai.action(m,{'uoss_unique_superboss_key':key},[p1,p2])
    check(instr[1]==frozenset({3}),'AI selects weakest')
    check(ai.action(m,{'uoss_unique_superboss_key':key},[p1,p2]) is None,'AI once per turn')
    check(ai.apply(p1,instr)==0 and p1.current_mana==100,'AI ignores non-target')
    check(ai.apply(p2,instr)==10 and p2.current_mana==90,'AI actual mana drain')
    check(ai.apply(p2,instr)==0,'AI no double drain')
    m.hp=40;m.combat_turn=3
    instr=ai.action(m,{'uoss_unique_superboss_key':key},[p1,p2])
    check(instr[1]==frozenset({2,3}),'AI final phase all')
    check(ai.apply(p1,instr)==16,'AI final phase drain')
    m.alive=False;m.combat_turn=4
    check(ai.action(m,{'uoss_unique_superboss_key':key},[p1,p2]) is None,'AI dead guard')
    for corrupt in ({'phases':[{'below_hp':100,'every':0,'mode':'all','mana_percent':5,'label':'x'}]},
                    {'phases':[{'below_hp':100,'every':1,'mode':'all','mana_percent':99,'label':'x'}]}):
        try:ai.validate({key:corrupt})
        except ValueError:count+=1
        else:raise AssertionError('invalid AI accepted')
    ai.sync({})
    # Arena must not change original resources, DB, or grant XP.
    a.current_hp=70
    check('ARENA SESJA' in await call('arena sesja start '+key+' 100'),'arena clone')
    before=a.current_hp
    check('ARENA SESJA' in await call('arena sesja status'),'arena private status')
    check('ARENA SESJA LAB' in await call('arena sesja krok'),'arena cloned action')
    check(a.current_hp==before,'no real HP mutation')
    check('test zamkniety' in await call('arena sesja wyjdz'),'arena exit')
    check('Nieznana' in await call('arena sesja start '+key+' 100',guest),'arena permissions')
    return count

if __name__=='__main__':print(f'ADMIN LIVE v100: {asyncio.run(main())} checks PASS')
