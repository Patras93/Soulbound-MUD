# -*- coding: utf-8 -*-
"""v110 wydarzenia: 4 rotacje, idempotentne nagrody, rollback SQLite."""
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from systems.events_v110.storage import create_schema
from systems.events_v110.clock import rotation,REQUIRED_KILLS,SLOT_SECONDS
from systems.events_v110.combat import record_defeat
from systems.events_v110.rewards import reward_id

class DB:
    def __init__(self):
        self.conn=_DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,'
                          'PRIMARY KEY(account_id,item_id))')
        self.conn.execute('INSERT INTO accounts VALUES (1)')
        self.conn.execute('INSERT INTO accounts VALUES (2)')
        create_schema(self.conn)
        self.conn.commit()
        self.fail=False
    def add_item(self,aid,item,amount,commit=False):
        if self.fail:raise RuntimeError('test rollback')
        self.conn.execute('INSERT INTO inventory VALUES (?,?,?) ON CONFLICT(account_id,item_id) '
                          'DO UPDATE SET quantity=quantity+excluded.quantity',(aid,item,amount))
        if commit:self.conn.commit()

def run():
    db=DB();players=[SimpleNamespace(account_id=1),SimpleNamespace(account_id=2)]
    for slot in range(4):
        t=(slot+2340000)*SLOT_SECONDS+5
        state=rotation(t)
        mob_prefix=state['region_prefix']
        template={'name':'Cel wydarzenia'}
        for i in range(REQUIRED_KILLS):
            mob=SimpleNamespace(alive=False,room_id=mob_prefix+'_01',
                 template_id=mob_prefix+'_mob_1',key='event-'+str(slot)+'-'+str(i),respawn_at=t+20+i)
            result=record_defeat(db,mob,template,players,now=t)
            assert result==('front',state['slug'],i+1)
            assert record_defeat(db,mob,template,players,now=t) is None
        before=db.conn.execute('SELECT count(*) FROM v110_event_reward_receipts').fetchone()[0]
        boss=SimpleNamespace(alive=False,room_id=mob_prefix+'_01',
             template_id=state['boss'],key='boss-'+str(slot),respawn_at=t+100)
        db.fail=True
        try:record_defeat(db,boss,template,players,now=t)
        except RuntimeError as exc:
            assert str(exc), "Injected failure must have reason"
        else:raise AssertionError('Expected simulated item failure')
        assert db.conn.execute('SELECT count(*) FROM v110_event_reward_receipts').fetchone()[0]==before
        assert db.conn.execute('SELECT completed_at FROM v110_event_progress WHERE slot=?',
                               (state['slot'],)).fetchone()[0]==0
        db.fail=False
        result=record_defeat(db,boss,template,players,now=t)
        assert result==('final',state['slug'],REQUIRED_KILLS)
        assert record_defeat(db,boss,template,players,now=t) is None
        prize=reward_id(state['slug'])
        rows=db.conn.execute('SELECT account_id,quantity FROM inventory WHERE item_id=? ORDER BY account_id',
                            (prize,)).fetchall()
        assert rows==[(1,1),(2,1)],(slot,rows)
    print('V110 EVENT REGRESSIONS PASS: 4 rotation types, '
          '36 unique kill credits, 8 distinct prize claims, 4 injected failures rolled back',flush=True)

if __name__=='__main__':run()
