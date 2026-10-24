# -*- coding: utf-8 -*-
"""Regression for real custom race creation, passive runtime and SQLite restart."""
import asyncio
import copy
import tempfile
from pathlib import Path
from validation.v3600_admin_guardian2 import Fake
from systems import admin_live_races_v7600 as races
from systems import admin_live_heritage_v7100 as heritage
from core.classes_skills import RACES,CLASSES,starting_hp_mana_for,RACE_CLASS_RECOMMENDATIONS
from core.character_resources import AUTHORED_RACE_PASSIVE_PROFILES,race_passive_profile
from storage.database import Database

async def main():
    checks=0
    def ck(test,label):
        nonlocal checks
        if not test:raise AssertionError(label)
        checks+=1
    originals=(copy.deepcopy(RACES),copy.deepcopy(AUTHORED_RACE_PASSIVE_PROFILES),copy.deepcopy(RACE_CLASS_RECOMMENDATIONS))
    state=(races.CONFIG_PATH,races._SETTINGS,races._ORIGINAL_RACES,races._ORIGINAL_PASSIVES,races._ORIGINAL_RECOMMENDATIONS)
    h_state=(heritage.CONFIG_PATH,heritage._SETTINGS,heritage._BASE_REGISTRY)
    owner=Fake();guest=Fake(False,owner.server.db)
    async def cmd(query,who=owner):
        await who.admin_command('live '+query)
        return who.messages[-1]
    try:
        with tempfile.TemporaryDirectory() as folder:
            races.CONFIG_PATH=Path(folder)/'custom_races_v7600.json'
            heritage.CONFIG_PATH=Path(folder)/'heritage_v7100.json'
            heritage._SETTINGS=None;heritage._BASE_REGISTRY=None
            heritage.restore()
            races._SETTINGS=None;races._ORIGINAL_RACES=None;races._ORIGINAL_PASSIVES=None;races._ORIGINAL_RECOMMENDATIONS=None
            db=Database(str(Path(folder)/'disposable.db'))
            owner.server.db=db
            ck('POMOC 36' in await cmd('pomoc 36'),'help')
            for command in ('pomoc 36','rodowod nowa rasa lista','rodowod nowa rasa plan Nimfa | Elf | 8 14 8 12 8','rodowod nowa rasa zatwierdz POTWIERDZAM'):
                ck('Nieznana komenda' in await cmd(command,guest),f'permissions {command}')
            ck('BRAK' in await cmd('rodowod nowa rasa lista'),'empty')
            for command in ('rodowod nowa rasa plan Elf | Elf | 8 14 8 12 8',
                            'rodowod nowa rasa plan Test | Elf | 10 10 10 10 11',
                            'rodowod nowa rasa plan Nimfa | Unknown | 8 14 8 12 8',
                            'rodowod nowa rasa plan Nimfa | Elf | 31 10 3 3 3',
                            'rodowod nowa rasa plan Nimfa | Elf | 8 14 8 12 8;bad'):
                ck('ADMIN LIVE NOWE RASY' in await cmd(command),f'reject {command}')
            ck(len(RACES)==len(originals[0]),'no race mutation without commit')
            ck('PLAN Nimfa' in await cmd('rodowod nowa rasa plan Nimfa | Elf | 8 14 8 12 8'),'valid plan')
            ck(not races.CONFIG_PATH.exists(),'plan did not touch file')
            ck('ZAPISANA Nimfa' in await cmd('rodowod nowa rasa zatwierdz POTWIERDZAM'),'commit')
            ck(len(RACES)==len(originals[0])+1,'creator sees extra race')
            row=next(row for row in RACES if row[0]=='Nimfa')
            ck(sum(row[2:])==50,'starting stats')
            ck(race_passive_profile('Nimfa')==race_passive_profile('Elf'),'real runtime passive')
            ck('Nimfa' in RACE_CLASS_RECOMMENDATIONS,'character creator recommendations')
            ck('RODOWOD PLAN' in await cmd('rodowod rasa plan Elf | 9 14 8 11 8'),'existing race editable after addition')
            ck('RODOWOD ZAPISANO' in await cmd('rodowod zatwierdz POTWIERDZAM'),'existing race edit commit')
            ck('Nimfa' in [r[0] for r in RACES],'new race survives heritage update')
            ck('RODOWOD: cofnieto' in await cmd('rodowod cofnij POTWIERDZAM'),'existing edit undo')
            ck('Nimfa' in [r[0] for r in RACES],'new race survives heritage undo')
            ck(starting_hp_mana_for(row,CLASSES[0])[0]>0,'real character resources')
            ck('Nimfa' in await cmd('rodowod nowa rasa lista'),'list')
            ck('PLAN Lunaria' in await cmd('rodowod nowa rasa plan Lunaria | Ogr | 10 10 10 10 10'),'second race plan')
            ck('ZAPISANA Lunaria' in await cmd('rodowod nowa rasa zatwierdz POTWIERDZAM'),'second race commit')
            ck('COFNIETA Lunaria' in await cmd('rodowod nowa rasa cofnij POTWIERDZAM'),'safe undo when unused')
            ck(all(row[0]!='Lunaria' for row in RACES),'unused race gone')
            from validation.race_balance_v1177 import audit_race_balance_v1177
            ck(audit_race_balance_v1177(runtime=True)['error_count']==0,'all runtime race passive formulas incl custom')
            ck('pasyw' in (await cmd('rodowod nowa rasa karta Nimfa')).lower(),'card')
            ck('ADMIN LIVE NOWE RASY' in await cmd('rodowod nowa rasa plan Nimfa | Ork | 10 10 10 10 10'),'no mutation after create')
            # Restart in the same Python process: restore all runtime indexes from JSON.
            races._SETTINGS=None
            races.restore()
            ck(len(RACES)==len(originals[0])+1 and race_passive_profile('Nimfa')==race_passive_profile('Elf'),'reload persisted race')
            account=db.create_account('TestNimfy76','Secure_Password_Test_76!')
            names={case:'Nimfa' for case in ('nom','gen','dat','acc','ins','loc','voc')}
            cid,slot=db.create_character_for_master(account,'NimfaTester76',row,CLASSES[0],names,gender='kobieta')
            record=db.character_for_account(cid)
            ck(record['race']=='Nimfa' and record['class_name']=='Wojownik','real SQLite saved race')
            ck('ADMIN LIVE NOWE RASY' in await cmd('rodowod nowa rasa cofnij POTWIERDZAM'),'cannot orphan saved character')
            db.conn.close()
            # Simulate actual server boot order: DB migration first, then creator restore.
            RACES[:]=originals[0]
            AUTHORED_RACE_PASSIVE_PROFILES.clear();AUTHORED_RACE_PASSIVE_PROFILES.update(originals[1])
            RACE_CLASS_RECOMMENDATIONS.clear();RACE_CLASS_RECOMMENDATIONS.update(originals[2])
            races._SETTINGS=None
            db2=Database(str(Path(folder)/'disposable.db'))
            races.restore()
            ck('Nimfa' in [r[0] for r in RACES],'boot order restored race after opening saved SQLite')
            ck(db2.character_for_account(cid)['race']=='Nimfa','SQLite restart persisted')
            ck(db2.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','DB integrity')
            db2.conn.close()
            ck('Nimfa' in races.current(),'configured race preserved')
            # Non-using race is reversible in a separate isolated DB run.
            # Do not delete Nimfa: the fixture has a saved Nimfa character.
            ck('ADMIN LIVE NOWE RASY' in await cmd('rodowod nowa rasa plan Nimfa | Elf | 8 14 8 12 8'),'duplicates rejected')
    finally:
        RACES[:]=originals[0]
        AUTHORED_RACE_PASSIVE_PROFILES.clear();AUTHORED_RACE_PASSIVE_PROFILES.update(originals[1])
        RACE_CLASS_RECOMMENDATIONS.clear();RACE_CLASS_RECOMMENDATIONS.update(originals[2])
        (races.CONFIG_PATH,races._SETTINGS,races._ORIGINAL_RACES,races._ORIGINAL_PASSIVES,races._ORIGINAL_RECOMMENDATIONS)=state
        (heritage.CONFIG_PATH,heritage._SETTINGS,heritage._BASE_REGISTRY)=h_state
        owner.server.db.conn.close()
    return checks

if __name__=='__main__':
    print('V76.00.0 PLAYABLE RACES:',asyncio.run(main()),'PASS')
