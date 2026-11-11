# -*- coding: utf-8 -*-
"""Focused safety regression: v36 Guardian commands never grant rewards in arena."""
import asyncio
import copy
import sqlite3
from types import SimpleNamespace
from player.session_mixins.admin_tools import SessionAdminToolsMixin
from systems.admin_guardian2_v3600 import (arena_start, arena_hit, arena_report,
    resolve_mob, _staged_region, _event_catalog)

class DB:
    def __init__(self):
        self.conn=sqlite3.connect(':memory:'); self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''CREATE TABLE accounts(id INTEGER PRIMARY KEY, username TEXT UNIQUE);
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY, name TEXT, room_id TEXT,character_level INT);
            CREATE TABLE quests(account_id INT,quest_id TEXT,status TEXT,progress INT,completed_at INT,completion_count INT);
            CREATE TABLE professions(account_id INT,profession TEXT,level INT);
            CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_login TEXT,action TEXT,target TEXT);
            INSERT INTO accounts VALUES(1,'owner'); INSERT INTO accounts VALUES(2,'friend');
            INSERT INTO characters VALUES(1,'Tester','temple',45);
            INSERT INTO characters VALUES(2,'Friend','temple',30);
        ''')
        self.logged=[]
    def account_name(self,ident):
        row=self.conn.execute('SELECT username FROM accounts WHERE id=?',(ident,)).fetchone();return row[0] if row else ''
    def master_account_by_name(self,nick):
        return self.conn.execute('SELECT * FROM accounts WHERE username=? COLLATE NOCASE',(nick,)).fetchone()
    def record_admin_action_v1224(self,*args): self.logged.append(args)
    def quest(self,acc,qid):return self.conn.execute('SELECT * FROM quests WHERE account_id=? AND quest_id=?',(acc,qid)).fetchone()
    def quest_rows(self,acc):return self.conn.execute('SELECT * FROM quests WHERE account_id=?',(acc,)).fetchall()

class Content:
    def __init__(self):
        self.draft={'mobs':{'live_dummy': {'name':'Testowy smok','generator_level':50,'max_hp':600,'damage':12,'class_xp_reward':99}},
                    'mob_edits':{},'balances':{},'rooms':{},'links':[]}
        self.active=copy.deepcopy(self.draft)
        self._last=[]
    def validate(self, draft):return len(draft['rooms'])
    def stage_room(self,rid,lv,name,desc,zone): self.draft['rooms'][rid]= {'name':name,'desc':desc,'zone':zone,'generator_level':lv}; return self.validate(self.draft)
    def stage_link(self,a,b,c): self.draft['links'].append([a,b,c]); return self.validate(self.draft)

class Fake(SessionAdminToolsMixin):
    def __init__(self, owner=True, db=None):
        self._owner=owner
        self.master_account_id=1 if owner else 2
        self.account_id=1 if owner else 2
        self.character=SimpleNamespace(name='Tester' if owner else 'Friend',room_id='temple',character_level=45)
        self.current_hp=20;self.current_mana=10;self.combat_mob_key=None;self.closed=False
        self.messages=[];db=db or DB()
        self.server=SimpleNamespace(db=db,live_content_v1204=Content(),sessions=[self],guardian_spawns_v3600={},
            world=SimpleNamespace(mobs={},_last_refresh_at=1.0))
        self.server.find_character_session=lambda nick: next((x for x in self.server.sessions if x.character and x.character.name.casefold()==nick.casefold()), None)
    def is_admin(self):return self._owner
    def normalize_description_query(self,q):return q.casefold()
    async def send(self,msg,**kwargs):self.messages.append(str(msg))
    def party_key(self):return None
    def max_hp(self):return 100
    def max_mana(self):return 200

async def suite():
    c=0; a=Fake();owner_db=a.server.db
    await a.admin_command('test arena mob live_dummy');assert 'ARENA TESTOWA' in a.messages[-1];c+=1
    assert a.server.world.mobs=={} and not owner_db.logged;c+=1
    await a.admin_command('test atak 250');assert a.guardian_arena_v3600['hp']==350;c+=1
    await a.admin_command('test atak 350');assert a.guardian_arena_v3600['hp']==0;c+=1
    await a.admin_command('test wynik');assert 'tur 2' in a.messages[-1];c+=1
    await a.admin_command('test wyjdz');assert a.guardian_arena_v3600 is None;c+=1
    await a.admin_command('balans mob live_dummy');assert 'DRAFT' in a.messages[-1];c+=1
    await a.admin_command('kraina nowa lasmgiel | Las Mgiel | 80 | 120');assert len(a.server.live_content_v1204.draft['rooms'])==3;c+=1
    await a.admin_command('kraina sprawdz lasmgiel');assert '3 pokoi' in a.messages[-1];c+=1
    await a.admin_command('panel Tester');assert 'poziom 45' in a.messages[-1];c+=1
    await a.admin_command('questdiag Tester temple_rats');assert 'nieprzyjety' in a.messages[-1];c+=1
    await a.admin_command('questnapraw Tester temple_rats synchronizuj POTWIERDZAM');assert 'Brak' in a.messages[-1];c+=1
    await a.admin_command('historia olc 10');assert 'brak' in a.messages[-1].lower();c+=1
    await a.admin_command('role nadaj friend moderator POTWIERDZAM');assert 'Rola zapisana' in a.messages[-1];c+=1
    b=Fake(False,owner_db);await b.admin_command('panel Tester');assert 'PANEL' in b.messages[-1];c+=1
    await b.admin_command('god on');assert 'Nieznana' in b.messages[-1];c+=1
    await b.admin_command('role nadaj owner administrator POTWIERDZAM');assert 'Brak uprawnien' in b.messages[-1];c+=1
    await a.admin_command('role podglad friend');assert 'moderator' in a.messages[-1];c+=1
    await a.admin_command('event katalog');assert 'inwazja' in a.messages[-1];c+=1
    await a.admin_command('event start inwazja temple POTWIERDZAM');assert 'swiatynia' in a.messages[-1];c+=1
    await a.admin_command('spawn podglad bandit');assert 'Bandyta' in a.messages[-1];c+=1
    await a.admin_command('spawn staw bandit temple 3 POTWIERDZAM');assert 'swiatyni' in a.messages[-1];c+=1
    await a.admin_command('wsparcie on');assert 'Dolacz' in a.messages[-1];c+=1
    await a.admin_command('moc tarcza');assert 'Najpierw' in a.messages[-1];c+=1
    await a.admin_command('ratunek Friend status');assert 'online' in a.messages[-1];c+=1
    assert len(_event_catalog())==3;c+=1
    # Exact, reversible SQLite correction for an offline character only.
    owner_db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',-3,0,0)")
    await a.admin_command('questdiag Friend temple_rats');assert 'UJEMNY' in a.messages[-1];c+=1
    await a.admin_command('questnapraw Friend temple_rats synchronizuj POTWIERDZAM')
    assert 'numer korekty' in a.messages[-1] and owner_db.quest(2,'temple_rats')['progress']==0;c+=1
    await a.admin_command('historia quest');assert 'temple_rats' in a.messages[-1];c+=1
    await a.admin_command('historia cofnij 1 POTWIERDZAM');assert 'COFNIETO' in a.messages[-1] and owner_db.quest(2,'temple_rats')['progress']==-3;c+=1
    await a.admin_command('historia cofnij 1 POTWIERDZAM');assert 'Nie ma aktywnej' in a.messages[-1];c+=1
    return c

def run():return asyncio.run(suite())
if __name__=='__main__':print(f'ADMIN GUARDIAN v36: {run()} checks PASS')
