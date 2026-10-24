# -*- coding: utf-8 -*-
"""Focused Linux regressions; Windows PREDEPLOY remains mandatory separately."""
import asyncio
import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_shop_progression_v7003 as shop
from systems import admin_live_heritage_v7100 as heritage
from systems.admin_live_v7100 import quest_cycles, quest_kind_coverage, arena_coverage
from core.classes_skills import RACES, CLASSES
from core import live_level_caps_v5200 as caps

async def checks():
    count=0
    def check(condition,desc=''):
        nonlocal count
        assert condition,desc
        count+=1
    owner=Fake()
    db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    guest=Fake(False,db)
    guest.server.live_content_v1204=owner.server.live_content_v1204
    service=owner.server.live_content_v1204
    before=copy.deepcopy(service.draft)
    async def cmd(s,who=owner):
        await who.admin_command('live '+s)
        return who.messages[-1]
    oldstate=copy.deepcopy(caps.current());op=shop.CONFIG_PATH;oc=shop._settings
    hp=heritage.CONFIG_PATH;hc=heritage._SETTINGS
    original_races=list(RACES);original_classes=list(CLASSES)
    try:
        with tempfile.TemporaryDirectory() as temp:
            shop.CONFIG_PATH=Path(temp)/'shops.json';shop._settings=None
            heritage.CONFIG_PATH=Path(temp)/'heritage.json';heritage._SETTINGS=None
            check('POMOC 29' in await cmd('pomoc 29'))
            check('POMOC 30' in await cmd('pomoc 30'))
            check('POMOC 31' in await cmd('pomoc 31'))
            for s in ('arena uoss pokrycie','questy automaty typy', 'questy automaty cykle',
                      'skill pakiet plan warrior_power_slash cooldown | 5',
                      'boss fazy plan goblin_warchief',
                      'limity reszta','postacie karta Friend','rodowod rasa karta Elf',
                      'sklepy progresja dodaj market leather_vest 900 POTWIERDZAM'):
                check('Nieznana komenda' in await cmd(s,guest),s)
            check('NIE' in await cmd('arena uoss pokrycie'))
            check('questow' in await cmd('questy automaty typy'))
            check('CYKLE' in await cmd('questy automaty cykle'))
            check('bezlimitu' in await cmd('limity reszta') or 'LIMITY RESZTA' in owner.messages[-1])
            check(service.draft==before)
            for bad in ('skill pakiet plan nope cooldown | 5',
                        'skill pakiet plan warrior_power_slash unknown | 5',
                        'skill pakiet plan warrior_power_slash cooldown 5',
                        'boss fazy plan black_rabite'):
                check('ADMIN LIVE V71:' in await cmd(bad),bad)
                check(service.draft==before)
            check('SKILL PAKIET PLAN' in await cmd('skill pakiet plan warrior_power_slash cooldown | 5 ; warrior_power_slash mechanic_cooldown | true'))
            check(service.draft==before)
            check('SKILL PAKIET' in await cmd('skill pakiet zatwierdz POTWIERDZAM'))
            check(service.draft['skill_edits']['warrior_power_slash']['mechanic_cooldown'] is True)
            check('Cofnieto' in await cmd('skill pakiet cofnij POTWIERDZAM'))
            check(service.draft==before)
            check('BOSS FAZY:' in await cmd('boss fazy podglad goblin_warchief'))
            check('BOSS FAZY PLAN' in await cmd('boss fazy plan goblin_warchief'))
            check(service.draft==before)
            check('BOSS FAZY' in await cmd('boss fazy zatwierdz POTWIERDZAM'))
            check(len(service.draft['mob_edits']['goblin_warchief']['olc_boss_phases'])==3)
            check('Cofnieto' in await cmd('boss fazy cofnij POTWIERDZAM'))
            check(service.draft==before)
            # Version 70.00.3 remains backwards-compatible; schema 2 is opt-in.
            for k in ('eq','bieglosc'):caps._state[k]=1500
            check('SKLEP DODANO' in await cmd('sklepy progresja dodaj market leather_vest 900 POTWIERDZAM'))
            check('SKLEP DODANO' in await cmd('sklepy progresja dodaj market lucky_charm 1000 POTWIERDZAM'))
            check(len(shop.current()['market'])==2)
            check(len(shop.append_progression_offer('market',list(shop.SHOPS['market'])))==len(shop.SHOPS['market'])+2)
            raw=json.loads(shop.CONFIG_PATH.read_text('utf-8'))
            check(raw['schema']==2)
            shop._settings=None
            check(len(shop.current()['market'])==2)
            check('ADMIN LIVE SKLEPY' in await cmd('sklepy progresja dodaj market leather_vest 900 POTWIERDZAM'))
            check('SKLEP USUNIETO' in await cmd('sklepy progresja usun market leather_vest 900 POTWIERDZAM'))
            check(len(shop.current()['market'])==1)
            check('wylaczono' in await cmd('sklepy progresja wylacz market POTWIERDZAM'))
            check(shop.current()=={})
            # Race changes only newly created characters; 50-point budget.
            check('RASA Elf' in await cmd('rodowod rasa karta Elf'))
            check('ADMIN LIVE RODOWOD' in await cmd('rodowod rasa plan Elf | 10 10 10 10 11'))
            check('RODOWOD PLAN' in await cmd('rodowod rasa plan Elf | 9 14 8 11 8'))
            check('RODOWOD ZAPISANO' in await cmd('rodowod zatwierdz POTWIERDZAM'))
            check(list(next(x for x in RACES if x[0]=='Elf')[2:])==[9,14,8,11,8])
            heritage._SETTINGS=None
            check(heritage.current()['races']['Elf']==[9,14,8,11,8])
            check('RODOWOD' in await cmd('rodowod cofnij POTWIERDZAM'))
            check(RACES==original_races)
            check('KLASA Wojownik' in await cmd('rodowod klasa karta Wojownik'))
            check('RODOWOD PLAN' in await cmd('rodowod klasa plan Wojownik | Wielki Miecz Duszy'))
            check('RODOWOD ZAPISANO' in await cmd('rodowod zatwierdz POTWIERDZAM'))
            check(next(x for x in CLASSES if x[0]=='Wojownik')[2]=='Wielki Miecz Duszy')
            check('RODOWOD' in await cmd('rodowod cofnij POTWIERDZAM'))
            check(CLASSES==original_classes)
            # Test field with proper offline row; no account/economy writes.
            for f in ('strength','dexterity','constitution','intelligence','willpower','charisma'):
                db.conn.execute(f'ALTER TABLE characters ADD COLUMN {f} INT NOT NULL DEFAULT 10')
            db.conn.execute('ALTER TABLE characters ADD COLUMN deaths INT NOT NULL DEFAULT 0')
            db.conn.commit()
            check('OFFLINE Friend' in await cmd('postacie karta Friend'))
            check('POSTAC PLAN' in await cmd('postacie plan Friend strength 42'))
            check(db.conn.execute('SELECT strength FROM characters WHERE name="Friend"').fetchone()[0]==10)
            check('POSTAC ZAPISANA' in await cmd('postacie zatwierdz POTWIERDZAM'))
            check(db.conn.execute('SELECT strength FROM characters WHERE name="Friend"').fetchone()[0]==42)
            check(db.conn.execute("SELECT count(*) FROM admin_actions_v1224 WHERE action='admin_live_v7100_set'").fetchone()[0]==1)
            check('POSTAC COFNIETO' in await cmd('postacie cofnij POTWIERDZAM'))
            check(db.conn.execute('SELECT strength FROM characters WHERE name="Friend"').fetchone()[0]==10)
            check('ADMIN LIVE POSTACIE' in await cmd('postacie plan Tester strength 90'))
            check('ADMIN LIVE POSTACIE' in await cmd('postacie plan Friend character_level 99'))
            check('ADMIN LIVE POSTACIE' in await cmd('postacie plan Friend strength -1'))
            check(service.active==before and service.draft==before)
    finally:
        RACES[:]=original_races;CLASSES[:]=original_classes
        caps._state.clear();caps._state.update(oldstate)
        shop.CONFIG_PATH=op;shop._settings=oc
        heritage.CONFIG_PATH=hp;heritage._SETTINGS=hc
        db.conn.close()
    return count

if __name__=='__main__':
    print('V71.00.0 EIGHT AREAS:',asyncio.run(checks()),'PASS')
