# -*- coding: utf-8 -*-
"""v95: real SQLite transaction & authorable, bounded in-engine passive regression."""
from __future__ import annotations
import asyncio, sqlite3, tempfile, pathlib, copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems import admin_live_progress_v9500 as progress
from systems import admin_live_races_v7600 as races
from systems import admin_live_classes_v7700 as classes
from systems.custom_passives_v9500 import parse_profile, validate_profile
from core.classes_skills import RACES, CLASSES
from core.character_resources import AUTHORED_RACE_PASSIVE_PROFILES, AUTHORED_CLASS_PASSIVE_PROFILES


def setup_db():
    con=sqlite3.connect(':memory:')
    con.executescript('''CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE,
        character_level INTEGER,character_xp INTEGER,soul_level INTEGER,soul_xp INTEGER,
        soul_weapon_mastery_level INTEGER,soul_weapon_mastery_xp INTEGER,race TEXT,class_name TEXT);
        INSERT INTO characters VALUES(2,'Friend',34,500,3,100,2,20,'Elf','Mag');
        CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_login TEXT,action TEXT,target TEXT);
        CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT);
        INSERT INTO accounts VALUES(1,'Admin');''')
    return con


async def main():
    count=0
    def ok(test,label):
        nonlocal count
        assert test,label;count+=1
    con=setup_db()
    db=SimpleNamespace(conn=con,account_name=lambda account:'Admin')
    owner=Fake(True)
    owner.server.db=db
    guest=Fake(False);guest.server.db=db
    owner.server.sessions=[owner];guest.server.sessions=owner.server.sessions
    async def cmd(text,who=owner):
        await who.admin_command('live '+text)
        return who.messages[-1]
    try:
        ok('POMOC 53' in await cmd('pomoc 53'),'help')
        ok('Nieznana komenda' in await cmd('pomoc 53',guest),'guest help')
        ok('Nieznana komenda' in await cmd('postacie rozwoj karta Friend',guest),'guest card')
        ok('34' in await cmd('postacie rozwoj karta Friend'),'card')
        before=con.execute('SELECT character_level,character_xp,soul_level,soul_xp,soul_weapon_mastery_level,soul_weapon_mastery_xp FROM characters').fetchone()
        text='postacie rozwoj plan Friend | postac=35,750; dusza=4,15; bron=3,25'
        ok('ROZWOJ PLAN' in await cmd(text),'plan')
        ok(con.execute('SELECT character_level FROM characters').fetchone()[0]==34,'plan read only')
        ok('ZAPISANO' in await cmd('postacie rozwoj zatwierdz POTWIERDZAM'),'commit')
        after=con.execute('SELECT character_level,character_xp,soul_level,soul_xp,soul_weapon_mastery_level,soul_weapon_mastery_xp FROM characters').fetchone()
        ok(after==(35,750,4,15,3,25),'all fields atomic')
        ok(con.execute('SELECT count(*) FROM admin_actions_v1224').fetchone()[0]==1,'audit')
        ok('COFNIETO' in await cmd('postacie rozwoj cofnij POTWIERDZAM'),'undo')
        ok(con.execute('SELECT character_level,character_xp,soul_level,soul_xp,soul_weapon_mastery_level,soul_weapon_mastery_xp FROM characters').fetchone()==before,'undo exact')
        ok(con.execute('SELECT count(*) FROM admin_actions_v1224').fetchone()[0]==2,'undo audit')
        for bad in ['postac=-1,2','postac=99999999,0','postac=4,-3','postac=4,99999999999999999',
                    'dusza=0,3','bron=0,0','postac=34,500;postac=33,1','gold=10,1','postac=1,__import__("os")']:
            ok('ADMIN LIVE ROZWOJ:' in await cmd('postacie rozwoj plan Friend | '+bad),'bad rejected '+bad)
            ok(con.execute('SELECT character_level,character_xp FROM characters').fetchone()==(34,500),'bad unchanged '+bad)
        ok('ROZWOJ PLAN' in await cmd('postacie rozwoj plan Friend | dusza=5,120'),'concurrency plan')
        con.execute('UPDATE characters SET soul_level=6');con.commit()
        ok('zmienione' in await cmd('postacie rozwoj zatwierdz POTWIERDZAM'),'concurrent change blocked')
        ok(con.execute('SELECT soul_level FROM characters').fetchone()[0]==6,'concurrent value preserved')
        con.execute('UPDATE characters SET soul_level=3');con.commit()
        owner.server.sessions.append(SimpleNamespace(closed=False,character=SimpleNamespace(name='Friend')))
        ok('OFFLINE' not in await cmd('postacie rozwoj karta Friend'),'online denied')
        owner.server.sessions.pop()
        ok('ROZWOJ PLAN' in await cmd('postacie rozwoj plan Friend | postac=35,3'),'rollback plan')
        con.execute('DROP TABLE admin_actions_v1224')
        try:
            progress.commit(owner)
        except sqlite3.OperationalError:count+=1
        else:raise AssertionError('audit failure should abort commit')
        ok(con.execute('SELECT character_level FROM characters').fetchone()[0]==34,'rollback transaction')
        con.execute('CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_login TEXT,action TEXT,target TEXT)')
        ok('ZAPISANO' in await cmd('postacie rozwoj zatwierdz POTWIERDZAM'),'retry after rollback')
        ok('COFNIETO' in await cmd('postacie rozwoj cofnij POTWIERDZAM'),'undo after rollback')
        # Passive profiles use exactly the existing engine profile registry.
        ok(parse_profile('healing','8')=={'kind':'healing','value':0.08},'heal parse')
        ok(parse_profile('dodge','2.5')['value']==0.025,'dodge parse')
        for kind,value in [('healing','99'),('magic_damage','40'),('invented','5'),('healing','nan')]:
            try:parse_profile(kind,value)
            except ValueError:count+=1
            else:raise AssertionError('invalid passive '+kind)
        with tempfile.TemporaryDirectory() as tmp:
            old_rpath,old_cpath=races.CONFIG_PATH,classes.CONFIG_PATH
            old_rs,old_cs=races._SETTINGS,classes._SETTINGS
            try:
                races.CONFIG_PATH=pathlib.Path(tmp)/'races.json';classes.CONFIG_PATH=pathlib.Path(tmp)/'classes.json'
                races._SETTINGS=None;classes._SETTINGS=None
                ok('PLAN' in races._plan(owner,'Nimfa | Elf | 10 10 10 10 10 | healing | 8'),'race plan')
                ok('Nimfa' not in {r[0] for r in RACES},'race staged only')
                ok('ZAPISANA' in races._commit(owner),'race commit')
                ok(AUTHORED_RACE_PASSIVE_PROFILES['Nimfa']=={'kind':'healing','value':0.08},'race real passive')
                ok('Nimfa' in {r[0] for r in RACES},'race creator')
                races._SETTINGS=None;races.restore()
                ok(AUTHORED_RACE_PASSIVE_PROFILES['Nimfa']['value']==0.08,'race reload persistent')
                ok('COFNIETA' in races._undo(owner),'race undo')
                ok('Nimfa' not in {r[0] for r in RACES},'race undo creator')
                ok('PLAN' in classes._mixed_plan(owner,'Runomistrz | Mag | Mag | Mag | Berlo Run | healing | 8'),'class plan')
                ok('Runomistrz' not in {r[0] for r in CLASSES},'class staged')
                ok('ZAPISANA' in classes._commit(owner),'class commit')
                ok(AUTHORED_CLASS_PASSIVE_PROFILES['Runomistrz']=={'kind':'healing','value':0.08},'class real passive')
                ok('Runomistrz' in {r[0] for r in CLASSES},'class creator')
                classes._SETTINGS=None;classes.restore()
                ok(AUTHORED_CLASS_PASSIVE_PROFILES['Runomistrz']['value']==0.08,'class reload')
                ok('COFNIETA' in classes._undo(owner),'class undo')
                ok('Runomistrz' not in {r[0] for r in CLASSES},'class undo creator')
                ok('PLAN' in races._plan(owner,'Rusalka | Elf | 10 10 10 10 10'),'legacy race plan')
                ok('ZAPISANA' in races._commit(owner),'legacy race commit')
                ok('COFNIETA' in races._undo(owner),'legacy race undo')
            finally:
                races._SETTINGS=old_rs;classes._SETTINGS=old_cs
                races.CONFIG_PATH=old_rpath;classes.CONFIG_PATH=old_cpath
                races._apply(races.current());classes._apply(classes.current())
        ok(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        print(f'V95 PROGRESSION AND CUSTOM PASSIVES: {count} PASS',flush=True)
    finally:con.close()

if __name__=='__main__':asyncio.run(main())
