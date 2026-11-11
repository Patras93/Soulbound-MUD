# -*- coding: utf-8 -*-
"""Focused disposable-DB regression for creator classes, skills and trainers."""
import asyncio
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems import admin_live_classes_v7700 as addon
from systems import admin_live_heritage_v7100 as heritage
from core.classes_skills import (CLASSES,CLASS_SKILLS,CLASS_DESCRIPTIONS,
                                 CLASS_STARTING_STAT_BONUSES,RACES,starting_hp_mana_for,
                                 effective_skill_mana_cost)
from core.character_resources import (AUTHORED_CLASS_PASSIVE_PROFILES,class_passive_profile)
from storage.database import Database
from systems.content_registry import NPCS
import ast

async def main():
    check_count=0
    def ck(test,label):
        nonlocal check_count
        if not test:raise AssertionError(label)
        check_count+=1
    catalogs=(copy.deepcopy(CLASSES),copy.deepcopy(CLASS_SKILLS),copy.deepcopy(CLASS_DESCRIPTIONS),
              copy.deepcopy(CLASS_STARTING_STAT_BONUSES),copy.deepcopy(AUTHORED_CLASS_PASSIVE_PROFILES))
    old=(addon.CONFIG_PATH,addon._SETTINGS,addon._ORIGINAL)
    old_heritage=(heritage.CONFIG_PATH,heritage._SETTINGS,heritage._BASE_REGISTRY)
    owner=Fake();visitor=Fake(False,owner.server.db)
    async def cmd(value,session=owner):
        await session.admin_command('live '+value)
        return session.messages[-1]
    try:
        with tempfile.TemporaryDirectory() as directory:
            addon.CONFIG_PATH=Path(directory)/'custom_classes_v7700.json'
            addon._SETTINGS=None;addon._ORIGINAL=None
            heritage.CONFIG_PATH=Path(directory)/'heritage_v7100.json'
            heritage._SETTINGS=None;heritage._BASE_REGISTRY=None
            heritage.restore();addon.restore()
            database=Database(str(Path(directory)/'test.db'))
            owner.server.db=database
            ck('POMOC 37' in await cmd('pomoc 37'),'help')
            ck('BRAK' in await cmd('rodowod nowa klasa lista'),'empty list')
            for case in ('pomoc 37','rodowod nowa klasa lista','rodowod nowa klasa plan Runomistrz | Mag | Berlo Run',
                         'rodowod nowa klasa zatwierdz POTWIERDZAM'):
                ck('Nieznana komenda' in await cmd(case,visitor),'owner only '+case)
            for case in ('rodowod nowa klasa plan Wojownik | Mag | Berlo Run',
                         'rodowod nowa klasa plan Runomistrz | Wojewoda | Berlo Run',
                         'rodowod nowa klasa plan Runomistrz | Mag | ',
                         'rodowod nowa klasa plan Runomistrz | Mag | A\tB',
                         'rodowod nowa klasa plan Runomistrz | Mag'):
                ck('ADMIN LIVE NOWE KLASY' in await cmd(case),'reject '+case)
            ck(len(CLASSES)==len(catalogs[0]),'plan no mutation')
            ck('PLAN Runomistrz' in await cmd('rodowod nowa klasa plan Runomistrz | Mag | Berlo Run'),'valid plan')
            ck(not addon.CONFIG_PATH.exists(),'plan no file')
            ck('ZAPISANA Runomistrz' in await cmd('rodowod nowa klasa zatwierdz POTWIERDZAM'),'commit')
            ck(len(CLASSES)==len(catalogs[0])+1,'real creator class count')
            row=next(r for r in CLASSES if r[0]=='Runomistrz')
            ck(row[1]=='magic' and row[2]=='Berlo Run' and row[3]==7,'class type weapon power')
            ck(CLASS_STARTING_STAT_BONUSES['Runomistrz']==CLASS_STARTING_STAT_BONUSES['Mag'],'real initial stats')
            ck(class_passive_profile('Runomistrz')==class_passive_profile('Mag'),'real passive')
            ck(starting_hp_mana_for(RACES[0],row)[1]>0,'resources')
            ck('Runomistrz' in await cmd('rodowod nowa klasa lista'),'list')
            ck('skilli' in await cmd('rodowod nowa klasa karta Runomistrz'),'card')
            skills=CLASS_SKILLS['Runomistrz']
            ck(len(skills)==len(CLASS_SKILLS['Mag']) and len(skills)>=200,'full skill progression')
            ck(all(str(s['id']).startswith('v7700_runomistrz_') for s in skills),'separate skill identity')
            ids=[s['id'] for v in CLASS_SKILLS.values() for s in v]
            ck(len(ids)==len(set(ids)),'unique global skill IDs')
            ck(all(s['mastery_choice_group'].startswith('Runomistrz:') for s in skills if s.get('mastery_choice_group')),'independent mastery group')
            ck(effective_skill_mana_cost(skills[0],'Runomistrz')>0,'magic mana')
            ck('rodowod' in (await cmd('rodowod klasa karta Mag')).lower() or 'KLASA Mag' in owner.messages[-1],'old class card unaffected')
            # Editable existing classes stay safe, preserving new class and skills.
            ck('PLAN' in await cmd('rodowod klasa plan Mag | Nowy Kostur Magii'),'heritage plan')
            ck('ZAPISANO' in await cmd('rodowod zatwierdz POTWIERDZAM'),'heritage commit')
            ck(any(r[0]=='Runomistrz' for r in CLASSES),'class survives heritage edit')
            ck('cofnieto' in (await cmd('rodowod cofnij POTWIERDZAM')).lower(),'heritage undo')
            ck(any(r[0]=='Runomistrz' for r in CLASSES),'class survives heritage undo')
            from core.progression_resources import class_type_for_name
            ck(class_type_for_name('Runomistrz')=='magic','class gameplay type')
            # NPC teacher for derived class uses a real existing teacher room.
            mag_teacher=next(n for n in NPCS.values() if n.get('teacher_class')=='Mag')
            actor=SimpleNamespace(character=SimpleNamespace(class_name='Runomistrz',room_id=mag_teacher['room']))
            actor.active_class_names=lambda:['Runomistrz']
            source=Path(__file__).resolve().parent.parent/'player/session_mixins/class_progression.py'
            tree=ast.parse(source.read_text('utf-8'))
            method=next(n for n in next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionClassProgressionMixin').body if isinstance(n,ast.FunctionDef) and n.name=='teacher_here_for_active_class')
            namespace={'NPCS':NPCS}
            exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),namespace)
            _id,teacher=namespace['teacher_here_for_active_class'](actor)
            ck(teacher is not None and teacher['teacher_class']=='Runomistrz','shared guild teacher')
            ck('Runomistrz' in await cmd('rodowod nowa klasa karta Runomistrz'),'read back')
            # Persisted character & restart (not a fabricated memory-only avatar).
            account=database.create_account('TestCustomClass77','Secure_Password_Test_77!')
            names={case:'Mag777' for case in ('nom','gen','dat','acc','ins','loc','voc')}
            cid,_slot=database.create_character_for_master(account,'CustomMage77',RACES[0],row,names,gender='kobieta')
            ck(database.character_for_account(cid)['class_name']=='Runomistrz','SQLite class ID')
            from player.character import Character
            created=Character.from_row(database.character_for_account(cid))
            ck(created.class_name=='Runomistrz' and created.class_type=='magic','real character load')
            ck(created._generated_class_passive('Runomistrz')['kind']=='magic_damage','combat passive')
            from core.progression_600 import soul_weapon_trait_for_tier_v11193
            ck(soul_weapon_trait_for_tier_v11193(5,'Runomistrz')==soul_weapon_trait_for_tier_v11193(5,'Mag'), 'soul weapon traits inherit magic')
            ck(created.class_magic_damage_multiplier() > 1.0,'magic damage multiplier in character combat math')
            ck(database.class_progress_row(cid,'Runomistrz')['level']>=1,'separate class mastery progress')
            ck('ADMIN LIVE NOWE KLASY' in await cmd('rodowod nowa klasa cofnij POTWIERDZAM'),'cannot orphan used class')
            database.conn.close()
            # Simulated restart in current Python runtime.
            CLASSES[:]=copy.deepcopy(catalogs[0]); CLASS_SKILLS.clear();CLASS_SKILLS.update(copy.deepcopy(catalogs[1]))
            CLASS_DESCRIPTIONS.clear();CLASS_DESCRIPTIONS.update(copy.deepcopy(catalogs[2]))
            CLASS_STARTING_STAT_BONUSES.clear();CLASS_STARTING_STAT_BONUSES.update(copy.deepcopy(catalogs[3]))
            AUTHORED_CLASS_PASSIVE_PROFILES.clear();AUTHORED_CLASS_PASSIVE_PROFILES.update(copy.deepcopy(catalogs[4]))
            addon._SETTINGS=None
            second=Database(str(Path(directory)/'test.db'))
            addon.restore()
            ck('Runomistrz' in [r[0] for r in CLASSES],'restart restored class')
            ck(second.character_for_account(cid)['class_name']=='Runomistrz','restart persistent identity')
            ck('Runomistrz' in CLASS_SKILLS and class_passive_profile('Runomistrz')['kind']=='magic_damage','restart skill and passive')
            ck(second.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
            second.conn.close()
            # Physical classes pay no mana, and unused class can be reversed.
            owner.server.db=Database(str(Path(directory)/'other.db'))
            ck('PLAN RycerzRun' in await cmd('rodowod nowa klasa plan RycerzRun | Wojownik | Ostrze'),'second parent')
            ck('ZAPISANA RycerzRun' in await cmd('rodowod nowa klasa zatwierdz POTWIERDZAM'),'second commit')
            ck(effective_skill_mana_cost(CLASS_SKILLS['RycerzRun'][0],'RycerzRun')==0,'new physical mana free')
            ck('COFNIETA RycerzRun' in await cmd('rodowod nowa klasa cofnij POTWIERDZAM'),'unused class reversible')
            ck('RycerzRun' not in CLASS_SKILLS,'no orphaned new skill catalogue')
            owner.server.db.conn.close()
    finally:
        CLASSES[:]=catalogs[0]
        CLASS_SKILLS.clear();CLASS_SKILLS.update(catalogs[1])
        CLASS_DESCRIPTIONS.clear();CLASS_DESCRIPTIONS.update(catalogs[2])
        CLASS_STARTING_STAT_BONUSES.clear();CLASS_STARTING_STAT_BONUSES.update(catalogs[3])
        AUTHORED_CLASS_PASSIVE_PROFILES.clear();AUTHORED_CLASS_PASSIVE_PROFILES.update(catalogs[4])
        addon.CONFIG_PATH,addon._SETTINGS,addon._ORIGINAL=old
        heritage.CONFIG_PATH,heritage._SETTINGS,heritage._BASE_REGISTRY=old_heritage
    return check_count

if __name__=='__main__':
    print('V77.00.0 PLAYABLE CLASSES:',asyncio.run(main()),'PASS')
