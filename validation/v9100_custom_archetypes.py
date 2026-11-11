# -*- coding: utf-8 -*-
"""v91: all authored archetypes and independent skill/passive mixing; no production DB."""
import asyncio
import copy
import json
import tempfile
from pathlib import Path
from core.classes_skills import CLASSES,CLASS_SKILLS,CLASS_DESCRIPTIONS,CLASS_STARTING_STAT_BONUSES
from core.character_resources import AUTHORED_CLASS_PASSIVE_PROFILES, class_passive_profile
from systems import admin_live_classes_v7700 as addon
from validation.v3600_admin_guardian2 import Fake
from storage.database import Database

async def run():
    n=0
    def check(condition,why):
        nonlocal n
        assert condition,why
        n+=1
    before=(copy.deepcopy(CLASSES),copy.deepcopy(CLASS_SKILLS),copy.deepcopy(CLASS_DESCRIPTIONS),
            copy.deepcopy(CLASS_STARTING_STAT_BONUSES),copy.deepcopy(AUTHORED_CLASS_PASSIVE_PROFILES))
    old=(addon.CONFIG_PATH,addon._SETTINGS,addon._ORIGINAL)
    owner=Fake();guest=Fake(False,owner.server.db)
    async def cmd(arg,user=owner):
        await user.admin_command('live '+arg)
        return user.messages[-1]
    try:
        with tempfile.TemporaryDirectory() as d:
            addon.CONFIG_PATH=Path(d)/'custom_classes_v7700.json'
            addon._SETTINGS=None;addon._ORIGINAL=None
            addon.restore()
            check(len(addon.PARENTS)==22,'22 base classes')
            check('POMOC 49' in await cmd('pomoc 49'),'help 49')
            check('Nieznana komenda' in await cmd('pomoc 49',guest),'admin access')
            for p in addon.PARENTS:
                check(p in CLASS_SKILLS and p in AUTHORED_CLASS_PASSIVE_PROFILES,'author baseline '+p)
                check(p in CLASS_STARTING_STAT_BONUSES,'stats base '+p)
                check(p in {x[0] for x in CLASSES},'class baseline '+p)
            for s in (
                'rodowod nowa klasa mieszana plan Runiarz | Wojewoda | Mag | Druid | Mlot',
                'rodowod nowa klasa mieszana plan Runiarz | Mag | Niewiadoma | Druid | Mlot',
                'rodowod nowa klasa mieszana plan Runiarz | Mag | Druid | Niewiadoma | Mlot',
                'rodowod nowa klasa mieszana plan Runiarz | Mag | Druid | Mag',
                'rodowod nowa klasa mieszana plan Runiarz | Mag | Druid | Mag | ',
            ):
                check('ADMIN LIVE NOWE KLASY' in await cmd(s),'bad plan blocked '+s)
            check(not addon.CONFIG_PATH.exists(),'bad plans did not write')
            check('Nieznana komenda' in await cmd('rodowod nowa klasa mieszana plan Runiarz | Mag | Paladyn | Druid | Runy',guest),'guest blocked')
            check('MIESZANA PLAN' in await cmd('rodowod nowa klasa mieszana plan Runiarz | Mag | Paladyn | Druid | Runy'),'mixed plan valid')
            check(not addon.CONFIG_PATH.exists(),'plan no file')
            check('ZAPISANA' in await cmd('rodowod nowa klasa zatwierdz POTWIERDZAM'),'commit')
            check(addon.current()['Runiarz']['skill_parent']=='Paladyn','source skills config')
            check(addon.current()['Runiarz']['passive_parent']=='Druid','source passive config')
            check(len(CLASS_SKILLS['Runiarz'])==len(CLASS_SKILLS['Paladyn']),'skills cloned')
            check(class_passive_profile('Runiarz')==class_passive_profile('Druid'),'passive cloned')
            check(CLASS_STARTING_STAT_BONUSES['Runiarz']==CLASS_STARTING_STAT_BONUSES['Mag'],'stats from main')
            check(len([k for k in CLASSES if k[0]=='Runiarz'])==1,'appears once')
            check('skille Paladyn' in await cmd('rodowod nowa klasa karta Runiarz'),'NVDA card')
            ids=[skill['id'] for skills in CLASS_SKILLS.values() for skill in skills]
            check(len(set(ids))==len(ids),'all skill IDs unique')
            check('ADMIN LIVE NOWE KLASY' in await cmd('rodowod nowa klasa mieszana plan Runiarz | Mag | Druid | Druid | Runy'),'cannot change used class in place')
            account_db=Database(str(Path(d)/'test.db'))
            owner.server.db=account_db
            account=account_db.create_account('Archetype91User','Strong_Archetype_Test_91')
            class_row=next(row for row in CLASSES if row[0]=='Runiarz')
            from core.classes_skills import RACES
            forms={form:'Archetyp' for form in ('nom','gen','dat','acc','ins','loc','voc')}
            cid,_=account_db.create_character_for_master(account,'Mixed91Hero',RACES[0],class_row,forms,gender='kobieta')
            check(account_db.character_for_account(cid)['class_name']=='Runiarz','SQLite persisted')
            check('ADMIN LIVE NOWE KLASY' in await cmd('rodowod nowa klasa cofnij POTWIERDZAM'),'cannot delete used class')
            account_db.conn.close()
            # Test fresh process-like catalog rehydration from persisted file.
            CLASSES[:]=copy.deepcopy(before[0]); CLASS_SKILLS.clear();CLASS_SKILLS.update(copy.deepcopy(before[1]))
            CLASS_DESCRIPTIONS.clear();CLASS_DESCRIPTIONS.update(copy.deepcopy(before[2]))
            CLASS_STARTING_STAT_BONUSES.clear();CLASS_STARTING_STAT_BONUSES.update(copy.deepcopy(before[3]))
            AUTHORED_CLASS_PASSIVE_PROFILES.clear();AUTHORED_CLASS_PASSIVE_PROFILES.update(copy.deepcopy(before[4]))
            addon._SETTINGS=None
            addon.restore()
            check('Runiarz' in CLASS_SKILLS,'restart class')
            check(class_passive_profile('Runiarz')==class_passive_profile('Druid'),'restart passive')
            check(len(CLASS_SKILLS['Runiarz'])==len(CLASS_SKILLS['Paladyn']),'restart skill set')
            check(json.loads(addon.CONFIG_PATH.read_text('utf-8'))['schema']==1,'backward compatible format')
            check(addon.inherited_parent('Runiarz')=='Mag','teacher retained')
            check(len(addon._validated({f'Adept {i}':{'parent':'Bard','weapon':'Lira'} for i in range(32)}))==32,'32 custom classes')
            try:addon._validated({f'Adept {i}':{'parent':'Bard','weapon':'Lira'} for i in range(33)})
            except ValueError:check(True,'limit 32 enforced')
            else:check(False,'limit 32 bypass')
            # Legacy schema 1 classes remain exactly functional.
            legacy=addon._validated({'Runolud':{'parent':'Wojownik','weapon':'Bron'}})
            check(legacy['Runolud']=={'parent':'Wojownik','weapon':'Bron'},'legacy values untouched')
            print(f'V91 CUSTOM ARCHETYPES: {n} PASS',flush=True)
    finally:
        CLASSES[:]=before[0]
        CLASS_SKILLS.clear();CLASS_SKILLS.update(before[1])
        CLASS_DESCRIPTIONS.clear();CLASS_DESCRIPTIONS.update(before[2])
        CLASS_STARTING_STAT_BONUSES.clear();CLASS_STARTING_STAT_BONUSES.update(before[3])
        AUTHORED_CLASS_PASSIVE_PROFILES.clear();AUTHORED_CLASS_PASSIVE_PROFILES.update(before[4])
        addon.CONFIG_PATH,addon._SETTINGS,addon._ORIGINAL=old

if __name__=='__main__':asyncio.run(run())
