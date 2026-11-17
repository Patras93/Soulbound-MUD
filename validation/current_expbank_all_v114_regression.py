# -*- coding: utf-8 -*-
"""Real manual EXP-bank full-claim transaction, on disposable SQLite only."""
import asyncio
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))

from storage.database import _DeferredCommitConnection
from systems.manual_exp_bank_v11325 import redeem_exp_bank
from player.session_mixins.character_profile import SessionCharacterProfileMixin

class ClaimDB:
    def __init__(self):
        self.conn=_DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT INTO accounts VALUES(1),(2)')
        self.conn.execute('CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,PRIMARY KEY(account_id,kind,source_key))')
        self.conn.execute('CREATE TABLE learned_skills(account_id INTEGER, skill_id TEXT)')
        self.conn.commit()
        self.saves=0
    def save_character(self,c,commit=False):
        self.saves+=1
        # Real SQLite writes under the same SAVEPOINT.
        self.conn.execute('CREATE TABLE IF NOT EXISTS v114_test_progress(account_id INTEGER PRIMARY KEY, xp TEXT)')
        self.conn.execute('INSERT INTO v114_test_progress VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET xp=excluded.xp',(c.account_id,str(c.character_xp)))
    def experience_bank_rows_v2011(self,account):
        return [(k,key,int(b)) for k,key,b in self.conn.execute('SELECT kind,source_key,balance FROM experience_bank_v2011 WHERE account_id=? ORDER BY kind,source_key',(account,))]
    def put(self,account,kind,source,balance):
        self.conn.execute('INSERT OR REPLACE INTO experience_bank_v2011 VALUES(?,?,?,?)',(account,kind,source,str(balance)))
        self.conn.commit()
    def balance(self,account,kind,source=''):
        row=self.conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=? AND kind=? AND source_key=?',(account,kind,source)).fetchone()
        return int(row[0]) if row else 0

class Char:
    account_id=1
    def __init__(self):
        self.character_level=10
        self.character_xp=0
        self.soul_level=10
        self.soul_xp=0
    def add_character_xp(self,amount):
        self.character_xp+=amount
    def add_soul_xp(self,amount):
        self.soul_xp+=amount

class TestSession(SessionCharacterProfileMixin):
    def __init__(self,db):
        self.server=SimpleNamespace(db=db)
        self.account_id=1
        self.character=Char()
        self.messages=[]
    async def send(self,text):
        self.messages.append(str(text))


def run():
    checks=0
    db=ClaimDB();sess=TestSession(db)
    db.put(1,'character','',2_000_001_200)
    db.put(1,'soul','',2400)
    db.put(1,'skill','unlearned',75)
    db.put(2,'character','',678)
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(sess.show_exp_bank_v2011('odbierz'))
    assert db.balance(1,'character')==2_000_001_100
    assert db.balance(1,'soul')==2300
    assert db.balance(1,'skill','unlearned')==75
    assert sess.character.character_xp==100
    checks+=4
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(sess.show_exp_bank_v2011('odbierz  wszystko'))
    assert sess.character.character_xp==2_000_001_200
    assert sess.character.soul_xp==2400
    assert db.balance(1,'character')==0 and db.balance(1,'soul')==0
    assert db.balance(1,'skill','unlearned')==75
    assert db.balance(2,'character')==678
    assert any('Pozostało w banku' in m for m in sess.messages)
    checks+=6
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(sess.show_exp_bank_v2011('odbierz wszystko'))
    assert sess.character.character_xp==2_000_001_200 and db.balance(1,'skill','unlearned')==75
    checks+=1
    # Full claim bypasses the former 1e9 hard chunk even with tiny Multi Cap.
    db.put(1,'character','',3_100_000_000)
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=1):
        asyncio.run(sess.show_exp_bank_v2011('wyplac wszystko'))
    assert db.balance(1,'character')==0 and sess.character.character_xp==5_100_001_200
    checks+=2
    # Numeric overflow keeps the original account balance while other axes pay.
    db.put(1,'soul','',999)
    db.put(1,'character','',77)
    def overflow(_):raise OverflowError('soul SQLite int64')
    sess.character.add_soul_xp=overflow
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(sess.show_exp_bank_v2011('wypłać wszystko'))
    assert db.balance(1,'soul')==999 and db.balance(1,'character')==0
    assert sess.character.character_xp==5_100_001_277
    assert any('limit techniczny' in m for m in sess.messages)
    checks+=3
    # Zero cap never releases saved EXP.
    db.put(1,'character','',100)
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=0):
        asyncio.run(sess.show_exp_bank_v2011('odbierz wszystko'))
    assert db.balance(1,'character')==100
    checks+=1
    # Fatal SQLite save error restores memory, bank and other account.
    db.put(1,'character','',123)
    before=sess.character.character_xp
    def fail_save(*args,**kw):raise sqlite3.OperationalError('synthetic failed write')
    with patch.object(db,'save_character',side_effect=fail_save),patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        caught=None
        try:asyncio.run(sess.show_exp_bank_v2011('odbierz wszystko'))
        except sqlite3.OperationalError as exc:caught=exc
    assert isinstance(caught,sqlite3.OperationalError)
    assert db.balance(1,'character')==123 and db.balance(2,'character')==678
    assert sess.character.character_xp==before
    checks+=3
    # Just viewing the bank must not mutate any row.
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',side_effect=AssertionError('read cannot calculate cap')):
        asyncio.run(sess.show_exp_bank_v2011())
    assert db.balance(1,'character')==123
    checks+=1
    db.conn.close()
    # All seven real credit paths, not just character/Soul, on isolated rows.
    class AxisDB(ClaimDB):
        def __init__(self):
            super().__init__()
            self.class_xp=0
            self.skill_xp=0
            self.profession_row={'level':1,'xp':0,'actions':12}
            self.tool_row={'level':1,'xp':0,'uses':8}
        def class_progress_row(self,account,key):
            return {'level':1} if account==1 and key=='Mage' else None
        def add_class_mastery_xp(self,account,key,amount):
            assert account==1 and key=='Mage'
            self.class_xp+=amount
        def add_skill_xp(self,account,key,amount):
            assert account==1 and key=='spell'
            self.skill_xp+=amount
        def profession(self,account,key):
            assert account==1 and key=='Mining'
            return self.profession_row.copy()
        def tool(self,account,key):
            assert account==1 and key=='pickaxe'
            return self.tool_row.copy()
        def save_profession(self,account,key,level,xp,actions):
            self.profession_row={'level':level,'xp':xp,'actions':actions}
        def save_tool(self,account,key,level,xp,uses):
            self.tool_row={'level':level,'xp':xp,'uses':uses}
    class AxisChar(Char):
        STAT_PROGRESS_FIELDS={'strength':('Siła','strength','strength_progress')}
        def __init__(self):
            super().__init__()
            self.strength=10
            self.strength_progress=0
        def stat_growth_threshold_for(self,_key):return 100
    class AxisSession(TestSession):
        def profession_xp_to_next(self,level,key):return 200
        def tool_xp_to_next(self,level,key):return 150
    axes=AxisDB()
    axes.conn.execute("INSERT INTO learned_skills VALUES(1,'spell')")
    all_rows=[('class','Mage',2001),('skill','spell',1234),('stat','siła',450),
              ('profession','Mining',650),('tool','pickaxe',625)]
    for kind,key,amount in all_rows:axes.put(1,kind,key,amount)
    axes_s=AxisSession(axes);axes_s.character=AxisChar()
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=1):
        asyncio.run(axes_s.show_exp_bank_v2011('odbierz wszystko'))
    assert axes.class_xp==2001 and axes.skill_xp==1234
    assert axes_s.character.strength==14 and axes_s.character.strength_progress==50
    assert axes.profession_row=={'level':4,'xp':50,'actions':12}
    assert axes.tool_row=={'level':5,'xp':25,'uses':8}
    assert all(axes.balance(1,k,key)==0 for k,key,_ in all_rows)
    checks+=6
    axes.conn.close()
    print(f'EXP BANK ALL v114: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
