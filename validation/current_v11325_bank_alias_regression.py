# -*- coding: utf-8 -*-
"""Focused, isolated v113.00.25 rules; no production character or listener."""
import asyncio
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from systems.player_aliases import _safe_name, process_alias_input
from systems.experience_bank_v2011 import banked_experience_v2011
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin


class DB(DatabaseExperienceBankV2011Mixin):
    def __init__(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT INTO accounts VALUES(1),(2)')
        self.conn.commit()
        self.create_experience_bank_schema_v2011()
        self._manual_bank_only_v11325=True
        self._v108_live_event_caps=True
    def multi_cap_v23215(self,account_id):return 100

class Session:
    def __init__(self,db,account):
        self.account_id=account
        self.character=object()
        self.server=SimpleNamespace(db=db)
        self.lines=[]
    async def send(self,line):self.lines.append(str(line))

async def run_aliases(db):
    s=Session(db,1)
    assert _safe_name('1') and not _safe_name('look') and not _safe_name('k')
    handled,_=await process_alias_input(s,'alias 1 use cosmic rave')
    assert handled and s.lines[-1]=='Alias zapisany: 1.'
    handled,cmd=await process_alias_input(s,'1')
    assert not handled and cmd=='use cosmic rave'
    s_other=Session(db,2)
    handled,cmd=await process_alias_input(s_other,'1')
    assert not handled and cmd=='1'
    handled,_=await process_alias_input(s,'alias usuń 1')
    assert handled
    handled,cmd=await process_alias_input(s,'1')
    assert not handled and cmd=='1'
    handled,_=await process_alias_input(s,'alias look xyz')
    assert handled and 'Nie można' in s.lines[-1]
    return 8


def run():
    db=DB()
    db.allocate_experience_bank_v2011(1,1000,'character','',100)
    before=db.experience_bank_rows_v2011(1)
    assert before==[('character','',900)]
    with patch('systems.v10800_seasonal_events.overcap_event_state',return_value={'active':False}):
        assert banked_experience_v2011(db,1,300,'character',1)==100
        assert banked_experience_v2011(db,1,300,'character',1,overcap=True)==200
        assert banked_experience_v2011(db,2,90,'character',1)==90
    assert db.experience_bank_rows_v2011(1)==before
    with patch('systems.v10800_seasonal_events.overcap_event_state',return_value={'active':True}):
        assert banked_experience_v2011(db,1,100000,'character',1)==100000
    assert db.experience_bank_rows_v2011(1)==before
    result=asyncio.run(run_aliases(db))
    db.conn.close()
    # Manual claim: exact single-account debit, XP gain, persistence and
    # idempotent second claim; use real transaction wrapper, no live TCP.
    from storage.database import _DeferredCommitConnection
    from systems.manual_exp_bank_v11325 import redeem_exp_bank
    conn=_DeferredCommitConnection(sqlite3.connect(':memory:'))
    conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
    conn.execute('INSERT INTO accounts VALUES(1),(2)')
    conn.execute('CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,PRIMARY KEY(account_id,kind,source_key))')
    conn.execute("INSERT INTO experience_bank_v2011 VALUES(1,'character','','80')")
    conn.execute("INSERT INTO experience_bank_v2011 VALUES(2,'character','','30')")
    conn.commit()
    class ClaimDB:
        def __init__(self):self.conn=conn;self.saved=0
        def experience_bank_rows_v2011(self,account):
            return [(k,source,int(balance)) for k,source,balance in conn.execute('SELECT kind,source_key,balance FROM experience_bank_v2011 WHERE account_id=?',(account,))]
        def save_character(self,character,commit=False):self.saved+=1
    class Char:
        account_id=1
        def __init__(self):self.character_level=1;self.character_xp=0
        def add_character_xp(self,amount):self.character_xp+=amount
    claim=ClaimDB();character=Char()
    sess=SimpleNamespace(server=SimpleNamespace(db=claim),account_id=1,character=character)
    lines=[]
    async def send(msg):lines.append(msg)
    sess.send=send
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(redeem_exp_bank(sess))
    assert character.character_xp==80 and claim.saved==1
    assert conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=1').fetchone()[0]=='0'
    assert conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=2').fetchone()[0]=='30'
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(redeem_exp_bank(sess))
    assert character.character_xp==80
    conn.close()
    return 11+result

if __name__=='__main__':
    print('CURRENT EXP BANK & ALIAS V11325:',run(),'PASS')
