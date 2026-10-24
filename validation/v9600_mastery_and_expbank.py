# -*- coding: utf-8 -*-
"""v96 end-to-end administrative class and learned skill repairs."""
import asyncio
import sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems import admin_live_mastery_v9600 as m

async def main():
    n=0
    def ok(yes,msg):
        nonlocal n
        assert yes,msg
        n+=1
    c=sqlite3.connect(':memory:')
    c.executescript('''CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE,
      character_level INTEGER,character_xp INTEGER,soul_level INTEGER,soul_xp INTEGER,
      soul_weapon_mastery_level INTEGER,soul_weapon_mastery_xp INTEGER);
      INSERT INTO characters VALUES (2,'Friend',34,5,2,3,4,7);
      CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER,xp INTEGER,active_slot INTEGER,
       PRIMARY KEY(account_id,class_name));
      INSERT INTO class_progress VALUES(2,'Wojownik',5,30,1),(2,'Mag',2,50,NULL);
      CREATE TABLE learned_skills(account_id INTEGER,skill_id TEXT,PRIMARY KEY(account_id,skill_id));
      INSERT INTO learned_skills VALUES(2,'warrior_power_slash');
      CREATE TABLE skill_progress(account_id INTEGER,skill_id TEXT,level INTEGER,xp INTEGER,uses INTEGER,
       PRIMARY KEY(account_id,skill_id));
      INSERT INTO skill_progress VALUES(2,'warrior_power_slash',4,12,30);
      INSERT INTO skill_progress VALUES(2,'warrior_war_cry',6,4,8);
      CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,
       PRIMARY KEY(account_id,kind,source_key));
      INSERT INTO experience_bank_v2011 VALUES(2,'character','','3456789999999999999999999999999999'),(2,'skill','warrior_power_slash','-4');
      CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_login TEXT,action TEXT,target TEXT);''')
    owner=Fake(True); guest=Fake(False)
    db=SimpleNamespace(conn=c,account_name=lambda a:'Admin')
    owner.server.db=db;guest.server.db=db
    owner.server.sessions=[owner];guest.server.sessions=[owner]
    async def cmd(raw,actor=owner):
        await actor.admin_command('live '+raw)
        return actor.messages[-1]
    try:
        ok('POMOC 54' in await cmd('pomoc 54'),'help')
        ok('Nieznana komenda' in await cmd('pomoc 54',guest),'guest help')
        ok('Nieznana komenda' in await cmd('postacie bieglosci karta Friend',guest),'guest cannot read progress')
        ok('Nieznana komenda' in await cmd('postacie expbank karta Friend',guest),'guest cannot read bank')
        ok('BIEGLOSCI OFFLINE' in await cmd('postacie bieglosci karta Friend'),'card')
        ok('klasa:Wojownik' in owner.messages[-1],'class card')
        ok('BANK EXP ODCZYT' in await cmd('postacie expbank karta Friend'),'bank view')
        ok('3456789999999999999999999999999999' in owner.messages[-1],'huge bank')
        ok('ujemne' in owner.messages[-1],'bank negative warning')
        before=c.execute('SELECT level,xp,active_slot FROM class_progress WHERE class_name="Wojownik"').fetchone()
        before_skill=c.execute('SELECT level,xp,uses FROM skill_progress WHERE skill_id="warrior_power_slash"').fetchone()
        raw='postacie bieglosci plan Friend | klasa:Wojownik=6,70; skill:warrior_power_slash=5,15'
        ok('BIEGLOSCI PLAN' in await cmd(raw),'plan')
        ok(c.execute('SELECT level FROM class_progress WHERE class_name="Wojownik"').fetchone()[0]==5,'plan read only')
        ok('BIEGLOSCI ZAPISANO' in await cmd('postacie bieglosci zatwierdz POTWIERDZAM'),'commit')
        ok(c.execute('SELECT level,xp,active_slot FROM class_progress WHERE class_name="Wojownik"').fetchone()==(6,70,1),'class persisted slot')
        ok(c.execute('SELECT level,xp,uses FROM skill_progress WHERE skill_id="warrior_power_slash"').fetchone()==(5,15,30),'skill persisted uses')
        ok(c.execute('SELECT balance FROM experience_bank_v2011 WHERE kind="character"').fetchone()[0]=='3456789999999999999999999999999999','bank preserved')
        ok(c.execute('SELECT COUNT(*) FROM admin_actions_v1224').fetchone()[0]==1,'audit persisted')
        ok('COFNIETO' in await cmd('postacie bieglosci cofnij POTWIERDZAM'),'undo')
        ok(c.execute('SELECT level,xp,active_slot FROM class_progress WHERE class_name="Wojownik"').fetchone()==before,'class undone')
        ok(c.execute('SELECT level,xp,uses FROM skill_progress WHERE skill_id="warrior_power_slash"').fetchone()==before_skill,'skill undone')
        for raw in ['klasa:Wojownik=0,2','klasa:Wojownik=99999999,0','klasa:Wojownik=5,9999999999999999',
                    'klasa:Wojownik=5,275940','skill:warrior_power_slash=5,296000',
                    'skill:warrior_war_cry=4,2','klasa:Nic=2,0','skill:fake_skill=3,1',
                    'klasa:Wojownik=6,1; klasa:Wojownik=7,1', 'klasa:Wojownik=7,-1']:
            ok('ADMIN LIVE BIEGLOSCI:' in await cmd('postacie bieglosci plan Friend | '+raw),'invalid rejected '+raw)
            ok(c.execute('SELECT level FROM class_progress WHERE class_name="Wojownik"').fetchone()[0]==5,'no corrupted writes '+raw)
        ok('BIEGLOSCI PLAN' in await cmd('postacie bieglosci plan Friend | klasa:Wojownik=6,70; skill:warrior_power_slash=5,15'),'concurrent plan')
        c.execute('UPDATE skill_progress SET xp=16 WHERE skill_id="warrior_power_slash"')
        ok('obca zmiane' in await cmd('postacie bieglosci zatwierdz POTWIERDZAM'),'CAS failure')
        ok(c.execute('SELECT level FROM class_progress WHERE class_name="Wojownik"').fetchone()[0]==5,'atomic rollback')
        c.execute('UPDATE skill_progress SET xp=12 WHERE skill_id="warrior_power_slash"')
        ok('BIEGLOSCI ZAPISANO' in await cmd('postacie bieglosci zatwierdz POTWIERDZAM'),'retry')
        ok('COFNIETO' in await cmd('postacie bieglosci cofnij POTWIERDZAM'),'undo retry')
        ok('BIEGLOSCI PLAN' in await cmd('postacie bieglosci plan Friend | klasa:Wojownik=6,70'),'audit plan')
        c.execute('DROP TABLE admin_actions_v1224')
        try:m.commit(owner)
        except sqlite3.OperationalError:n+=1
        else:raise AssertionError('audit failure must rollback')
        ok(c.execute('SELECT level FROM class_progress WHERE class_name="Wojownik"').fetchone()[0]==5,'audit failure rollback')
        c.execute('CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_login TEXT,action TEXT,target TEXT)')
        ok('BIEGLOSCI ZAPISANO' in await cmd('postacie bieglosci zatwierdz POTWIERDZAM'),'recover after audit fail')
        ok('COFNIETO' in await cmd('postacie bieglosci cofnij POTWIERDZAM'),'undo audit recovery')
        owner.server.sessions.append(SimpleNamespace(closed=False,character=SimpleNamespace(name='Friend')))
        ok('ADMIN LIVE BIEGLOSCI:' in await cmd('postacie bieglosci karta Friend'),'offline refusal')
        ok('ADMIN LIVE BIEGLOSCI:' in await cmd('postacie expbank karta Friend'),'bank offline refusal')
        owner.server.sessions.pop()
        ok('BIEGLOSCI OFFLINE' in await cmd('postacie bieglosci karta Friend 1'),'page 1')
        ok('Niepoprawna strona' in await cmd('postacie bieglosci karta Friend 999'),'page reject')
        ok('ok'==c.execute('PRAGMA integrity_check').fetchone()[0],'integrity')
        print(f'V96 OFFLINE CLASS/SKILL PROGRESSION + BANK AUDIT: {n} PASS',flush=True)
    finally:c.close()
if __name__=='__main__':asyncio.run(main())
