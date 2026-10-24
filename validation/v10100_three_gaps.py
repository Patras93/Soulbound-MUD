# -*- coding: utf-8 -*-
"""Focused integration, OLC publish, CAS, rollback and arena isolation tests."""
import asyncio
import copy
import json
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import live_mechanics_v10100 as rules
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

async def main():
    count=0
    def ok(value,label):
        nonlocal count
        assert value,label
        count+=1
    admin=Fake();guest=Fake(False,admin.server.db)
    admin.server.sessions=[admin,guest];guest.server=admin.server
    c=admin.server.db.conn
    c.executescript('''
    ALTER TABLE characters ADD COLUMN character_xp INT DEFAULT 0;
    ALTER TABLE characters ADD COLUMN soul_level INT DEFAULT 1;
    ALTER TABLE characters ADD COLUMN soul_xp INT DEFAULT 0;
    ALTER TABLE characters ADD COLUMN soul_weapon_mastery_level INT DEFAULT 1;
    ALTER TABLE characters ADD COLUMN soul_weapon_mastery_xp INT DEFAULT 0;
    CREATE TABLE class_progress(account_id INT, class_name TEXT,level INT,xp INT,active_slot INT);
    CREATE TABLE skill_progress(account_id INT,skill_id TEXT,level INT,xp INT);
    CREATE TABLE learned_skills(account_id INT,skill_id TEXT);
    CREATE TABLE tools(account_id INT,tool_type TEXT,level INT,xp INT);
    CREATE TABLE experience_bank_v2011(account_id INT,kind TEXT,source_key TEXT,balance TEXT);
    CREATE TABLE inventory(account_id INT,item_id TEXT,quantity INT);
    CREATE TABLE equipment(account_id INT,item_id TEXT);
    CREATE TABLE shop_purchase_lots_v1175(account_id INT,item_id TEXT);
    CREATE TABLE protected_inventory_v1280(account_id INT,item_id TEXT);
    ''')
    admin.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=c))
    guest.character.name='Friend'; guest.character.character_level=30
    for col,v in [('character_xp',100),('soul_level',3),('soul_xp',10),('soul_weapon_mastery_level',5),('soul_weapon_mastery_xp',0)]:
        setattr(guest.character,col,v)
        c.execute('UPDATE characters SET '+col+'=? WHERE account_id=2',(v,))
    c.execute("INSERT INTO class_progress VALUES(2,'Wojownik',3,0,1)")
    c.execute("INSERT INTO experience_bank_v2011 VALUES(2,'character','','123')")
    async def call(q,who=admin):
        await who.admin_command('live '+q)
        return who.messages[-1]
    for n in range(70,74):
        ok('POMOC '+str(n) in await call('pomoc '+str(n)),'help '+str(n))
        ok('Nieznana' in await call('pomoc '+str(n),guest),'admin-only '+str(n))
    boss=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    profile={'phases':[{'below_hp':100,'every':2,'target':'weakest','actions':[
        {'type':'drain_mana','percent':3},{'type':'heal_boss','percent':5}],
        'label':'Fala Dusz'},{'below_hp':45,'every':1,'target':'all','actions':[
        {'type':'restore_mana','percent':4}], 'label':'Przyplyw'}]}
    snapshot=copy.deepcopy(admin.server.live_content_v1204.draft)
    ok('MECHANIKI PLAN' in await call('mechaniki plan '+boss+' | '+json.dumps(profile)),'mechanics plan')
    ok(snapshot==admin.server.live_content_v1204.draft,'draft not changed until approval')
    ok('zatwierdzono' in await call('mechaniki zatwierdz POTWIERDZAM'),'approve draft')
    ok(boss in admin.server.live_content_v1204.draft['v101_rules'] and boss not in rules.ACTIVE,'not published')
    ok('Cofnieto' in await call('mechaniki cofnij POTWIERDZAM'),'undo draft')
    ok(admin.server.live_content_v1204.draft==snapshot,'reversible')
    for bad in ({'phases':[{'below_hp':99,'every':0,'target':'all','actions':[{'type':'heal_boss','percent':5}],'label':'x'}]},
                {'phases':[{'below_hp':99,'every':1,'target':'all','actions':[{'type':'os.system','percent':5}],'label':'x'}]}):
        try:rules.validate({boss:bad})
        except ValueError:count+=1
        else:raise AssertionError('bad mechanic accepted')
    service=admin.server.live_content_v1204
    service.draft['v101_rules'][boss]=copy.deepcopy(profile)
    ok('PRZEDPUBLIKACJA OK' in service.apply(admin.server,'owner',dry_run=True),'OLC dry run')
    ok(boss not in rules.ACTIVE,'not prematurely published')
    ok('Aktywowano rewizję' in service.apply(admin.server,'owner'),'OLC publish')
    ok(boss in rules.ACTIVE,'hot reload active')
    mob=SimpleNamespace(hp=70,max_hp=100,combat_turn=2,alive=True)
    t1=SimpleNamespace(current_hp=90,current_mana=70,account_id=2,closed=False,max_mana=lambda:100)
    t2=SimpleNamespace(current_hp=40,current_mana=70,account_id=3,closed=False,max_mana=lambda:100)
    event=rules.on_boss_turn(mob,{'uoss_unique_superboss_key':boss},[t1,t2])
    ok(bool(event) and mob.hp==75 and event['selected']==frozenset({3}),'boss heals and targets')
    ok(rules.on_boss_turn(mob,{'uoss_unique_superboss_key':boss},[t1,t2]) is None,'only once a turn')
    ok(rules.apply_to_target(t1,event) is None and t1.current_mana==70,'unselected unchanged')
    ok(rules.apply_to_target(t2,event)=={'drain_mana':3} and t2.current_mana==67,'target drain')
    ok(rules.apply_to_target(t2,event) is None,'no duplicate drain')
    mob.hp=35;mob.combat_turn=3
    event=rules.on_boss_turn(mob,{'uoss_unique_superboss_key':boss},[t1,t2])
    ok(event and rules.apply_to_target(t1,event)=={'restore_mana':4} and t1.current_mana==74,'phase restore')
    service.draft['v101_rules'].clear();service.apply(admin.server,'owner')
    ok(boss not in rules.ACTIVE,'hot revocation')
    ok('ROZWOJ ONLINE Friend' in await call('postacie online rozwoj karta Friend'),'online card')
    ok('ROZWOJ ONLINE PLAN' in await call('postacie online rozwoj plan Friend | postac=31,200; dusza=4,20'),'online plan')
    ok(guest.character.character_level==30,'plan no mutation')
    ok('ROZWOJ ONLINE ZAPISANO' in await call('postacie online rozwoj zatwierdz POTWIERDZAM'),'online progression commit')
    ok(guest.character.character_level==31 and c.execute('SELECT character_level FROM characters WHERE account_id=2').fetchone()[0]==31,'two-store persistence')
    ok('ROZWOJ ONLINE COFNIETO' in await call('postacie online rozwoj cofnij POTWIERDZAM'),'progress undo')
    ok(guest.character.character_level==30 and c.execute('SELECT character_level FROM characters WHERE account_id=2').fetchone()[0]==30,'progress original restored')
    ok('ROZWOJ ONLINE PLAN' in await call('postacie online rozwoj plan Friend | dusza=5,90'),'conflict plan')
    c.execute('UPDATE characters SET soul_xp=11 WHERE account_id=2')
    ok('Konflikt SQLite' in await call('postacie online rozwoj zatwierdz POTWIERDZAM'),'db conflict refusal')
    ok(guest.character.soul_xp==10 and c.execute('SELECT soul_xp FROM characters WHERE account_id=2').fetchone()[0]==11,'no bad write')
    c.execute('UPDATE characters SET soul_xp=10 WHERE account_id=2')
    guest.combat_mob_key='enemy'
    ok('walce' in await call('postacie online rozwoj plan Friend | postac=42,7'),'combat protected')
    guest.combat_mob_key=None
    ok('WPISY ONLINE PLAN' in await call('postacie online wpisy plan Friend | klasa:Wojownik=4,0; bank:character:=124'),'db entry plan')
    ok('WPISY ONLINE ZAPISANO' in await call('postacie online wpisy zatwierdz POTWIERDZAM'),'db entry write')
    ok(c.execute("SELECT level FROM class_progress WHERE account_id=2 AND class_name='Wojownik'").fetchone()[0]==4,'class corrected')
    ok(c.execute("SELECT balance FROM experience_bank_v2011 WHERE account_id=2").fetchone()[0]=='124','bank corrected')
    ok('WPISY ONLINE COFNIETO' in await call('postacie online wpisy cofnij POTWIERDZAM'),'db entries undo')
    ok(c.execute("SELECT balance FROM experience_bank_v2011 WHERE account_id=2").fetchone()[0]=='123','bank restored')
    ok('WPISY ONLINE PLAN' in await call('postacie online wpisy plan Friend | klasa:Wojownik=5,0'),'class race plan')
    c.execute("UPDATE class_progress SET level=8 WHERE account_id=2")
    ok('Konflikt CAS' in await call('postacie online wpisy zatwierdz POTWIERDZAM'),'db entries CAS refusal')
    ok(c.execute('SELECT level FROM class_progress').fetchone()[0]==8,'CAS preserves source')
    c.execute("UPDATE class_progress SET level=3 WHERE account_id=2")
    ok('WPISY ONLINE PLAN' in await call('postacie online wpisy plan Friend | klasa:Wojownik=6,0; bank:character:=555'),'multirow atomic plan')
    c.execute("UPDATE experience_bank_v2011 SET balance='999' WHERE account_id=2")
    ok('Konflikt CAS' in await call('postacie online wpisy zatwierdz POTWIERDZAM'),'multirow atomic second-row refusal')
    ok(c.execute('SELECT level FROM class_progress WHERE account_id=2').fetchone()[0]==3,'first write rolled back')
    c.execute("UPDATE experience_bank_v2011 SET balance='123' WHERE account_id=2")
    admin.current_hp=72
    ok('ARENA SESJA' in await call('arena sesja start '+boss+' 100'),'arena start')
    oldhp=admin.current_hp
    ok('ARENA SERIA LAB' in await call('arena sesja seria atak,obrona,magia:fire'),'arena series')
    ok(admin.current_hp==oldhp,'real HP never changed')
    lab_copy=copy.deepcopy(admin.guardian7_lab)
    ok('ADMIN LIVE v101' in await call('arena sesja seria atak,niewlasciwe'),'arena invalid step rejected')
    ok(admin.guardian7_lab==lab_copy,'invalid arena step did not advance')
    ok('ARENA POROWNAJ' in await call('arena sesja porownaj'),'arena audit')
    ok('test zamkniety' in await call('arena sesja wyjdz'),'arena end')
    ok('Nieznana' in await call('mechaniki karta '+boss,guest),'no mechanic permissions')
    ok('Nieznana' in await call('postacie online rozwoj karta Friend',guest),'no online permissions')
    rules.sync({})
    return count

if __name__=='__main__':
    print('ADMIN LIVE v101:',asyncio.run(main()),'checks PASS')
