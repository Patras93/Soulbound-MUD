# -*- coding: utf-8 -*-
"""Cap sound events: real v113 payout gateway and manual claim; no production DB."""
import asyncio
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Standalone execution by the universal release suite starts Python with
# validation/ as sys.path[0]. Ensure that runtime packages resolve from
# the candidate root, and that validation/events.py cannot shadow events/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

from systems.experience_bank_v2011 import banked_experience_v2011
from systems.sound_events_v1208 import record_paid_exp_event_v11329, _watch_hourly_overcap_v11329
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin

class DB(DatabaseExperienceBankV2011Mixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT INTO accounts VALUES(1),(2)')
        self.conn.commit()
        self.create_experience_bank_schema_v2011()
        self._manual_bank_only_v11325 = True
        self._v108_live_event_caps = True
    def multi_cap_v23215(self, aid): return 100


def run():
    checks=0
    db=DB()
    db.allocate_experience_bank_v2011(1,1000,'character','',100)
    bank_before = db.experience_bank_rows_v2011(1)
    with patch('systems.v10800_seasonal_events.overcap_event_state',return_value={'active':False}):
        for amount,expected,name in [(10,10,None),(49,49,None),(50,50,'HALF_CAP'),(79,79,'HALF_CAP'),(100,100,'FULL_CAP'),(999,100,'FULL_CAP'),(80,80,'HALF_CAP')]:
            before=list(getattr(db,'_sound_events_v1208',{}).get(1,[]))
            assert banked_experience_v2011(db,1,amount,'character',1)==expected
            new=getattr(db,'_sound_events_v1208',{}).get(1,[])[len(before):]
            assert len(new)==int(name is not None),(amount,new)
            if name:assert new[0].startswith('SOUND_EVENT '+name+' ')
            assert not any('EXP_BANK' in text for text in new)
            checks+=3
        # One separate account; no event mixed into account one.
        before=len(db._sound_events_v1208[1])
        assert banked_experience_v2011(db,2,100,'character',1)==100
        assert len(db._sound_events_v1208[1])==before
        assert db._sound_events_v1208[2][-1].startswith('SOUND_EVENT FULL_CAP')
        checks+=3
        assert banked_experience_v2011(db,1,0,'character',1)==0
        assert db.experience_bank_rows_v2011(1)==bank_before
        checks+=2
    with patch('systems.v10800_seasonal_events.overcap_event_state',return_value={'active':True}):
        before=len(db._sound_events_v1208[1])
        assert banked_experience_v2011(db,1,1000,'character',1)==200  # v116.58 Over CAP respects 2x cap
        assert db._sound_events_v1208[1][before:]==['SOUND_EVENT FULL_CAP cap=200 kind=character']
        checks+=2
    assert db.experience_bank_rows_v2011(1)==bank_before
    checks+=1
    # Manual stored-bank payout through live v11325 redemption code.
    from systems.manual_exp_bank_v11325 import redeem_exp_bank
    from storage.database import _DeferredCommitConnection
    con=_DeferredCommitConnection(sqlite3.connect(':memory:'))
    con.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
    con.execute('INSERT INTO accounts VALUES(1),(2)')
    con.execute('CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,PRIMARY KEY(account_id,kind,source_key))')
    con.execute("INSERT INTO experience_bank_v2011 VALUES(1,'character','','60')")
    con.execute("INSERT INTO experience_bank_v2011 VALUES(2,'character','','90')")
    con.commit()
    class ClaimDB:
        conn=con
        def experience_bank_rows_v2011(self,aid):
            return [(k,key,int(b)) for k,key,b in con.execute('SELECT kind,source_key,balance FROM experience_bank_v2011 WHERE account_id=?',(aid,))]
        def save_character(self,c,commit=False): pass
    class Char:
        account_id=1
        character_level=1
        character_xp=0
        def add_character_xp(self,x):self.character_xp+=x
    claim=ClaimDB();c=Char();msgs=[]
    async def send(line):msgs.append(line)
    ss=SimpleNamespace(server=SimpleNamespace(db=claim),account_id=1,character=c,send=send)
    with patch('systems.multi_cap_v23215.multi_cap_experience_v23215',return_value=100):
        asyncio.run(redeem_exp_bank(ss))
        assert c.character_xp==60
        assert claim._sound_events_v1208[1]==['SOUND_EVENT HALF_CAP cap=100 kind=character']
        assert claim.conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=2').fetchone()[0]=='90'
        checks+=3
        asyncio.run(redeem_exp_bank(ss))
        assert len(claim._sound_events_v1208[1])==1
        checks+=1
    # A blocked old-bank path must not emit.
    assert record_paid_exp_event_v11329(db,1,0,100) is None
    assert record_paid_exp_event_v11329(db,1,100,0) is None
    checks+=2
    # Real clock sends a distinct event only once in an active window.
    async def clock_check():
        delivered=[]
        class Listener:
            character=object()
            closed=False
            async def send(self,msg,history_store=True):delivered.append(msg)
        listener=Listener()
        server=SimpleNamespace(sessions=[listener])
        times=iter([1801.0,1802.0,5401.0,5402.0])
        async def sleep(_):
            if len(delivered)==2:
                listener.closed=True
        with patch('time.time',side_effect=lambda:next(times)),patch('asyncio.sleep',side_effect=sleep):
            await _watch_hourly_overcap_v11329(server)
        assert delivered==['SOUND_EVENT OVER_CAP_START','SOUND_EVENT OVER_CAP_START'],delivered
    asyncio.run(clock_check())
    checks+=2
    # Failed live atomic reward: no payout, no leftover CAP sound marker.
    from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400
    class BadDB(DB):
        def __init__(self):
            from storage.database import _DeferredCommitConnection
            self.conn=_DeferredCommitConnection(sqlite3.connect(':memory:'))
            self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
            self.conn.execute('INSERT INTO accounts VALUES(1)')
            self.conn.commit()
            self.create_experience_bank_schema_v2011()
            self._manual_bank_only_v11325=True
            self._v108_live_event_caps=True
        def save_character(self,*args,**kwargs):
            raise sqlite3.OperationalError('failure during save')
    failed=BadDB()
    class FailedChar:
        account_id=1
        character_level=1
        character_xp=0
        def add_character_xp(self,amount,single_level_cap=False):
            self.character_xp+=amount
            return []
    ch=FailedChar()
    with patch('systems.v10800_seasonal_events.overcap_event_state',return_value={'active':False}):
        caught_error = None
        try:
            award_character_xp_atomic_v10400(failed,ch,1,100)
        except sqlite3.OperationalError as exc:
            caught_error = exc
        assert isinstance(caught_error, sqlite3.OperationalError), 'expected SQLite failure'
    assert ch.character_xp==0
    assert not getattr(failed,'_sound_events_v1208',{}).get(1)
    checks+=2
    # Actual session dispatch: informational commands cannot flush queued audio.
    from systems.sound_events_v1208 import install_sound_hooks_v1208
    class Transport:
        def __init__(self, game_db):
            self.account_id=1
            self.server=SimpleNamespace(db=game_db,sessions=[self])
            self.character=SimpleNamespace(name='Test',room_id='tmp')
            self.closed=False
            self.sent=[]
        async def send(self, text='', combat_detail=None, history_category=None, history_store=True):
            self.sent.append(str(text))
        async def dispatch_registered_command(self, command, args):
            await self.send(command+' info')
            return True
        async def send_combat(self,text,detail='essential'): return None
        async def mob_defeated(self,mob): return None
        async def enter_world(self): return True
        async def leave_current_character_for_selection(self): return True
        async def close(self): return True
    class FakeSocial:
        async def reply_private_v0928(self, message):
            return message
    import sys
    with patch.dict(sys.modules, {'player.session_mixins.social_base':
                     SimpleNamespace(SessionBaseSocialMixin=FakeSocial)}):
        install_sound_hooks_v1208(Transport)
    transport=Transport(db)
    db._sound_events_v1208[1]=['SOUND_EVENT HALF_CAP cap=100 kind=character']
    async def read_only_check():
        for read_cmd in ('score','look','expbank','status','stats','help','eventxp'):
            await transport.dispatch_registered_command(read_cmd, '')
        assert not any('SOUND_EVENT' in x for x in transport.sent)
        assert len(db._sound_events_v1208[1])==1
        await transport.dispatch_registered_command('expbank','odbierz')
        assert transport.sent[-2]=='SOUND_EVENT HALF_CAP cap=100 kind=character'
        assert transport.sent[-1]=='expbank info'
    asyncio.run(read_only_check())
    checks+=4
    failed.conn.close();con.close();db.conn.close()
    return checks

if __name__=='__main__':
    print('CURRENT V11329 SOUND CAP:',run(),'PASS')
