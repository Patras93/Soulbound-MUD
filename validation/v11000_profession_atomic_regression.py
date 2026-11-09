# -*- coding: utf-8 -*-
"""v110: niezależne testy ośmiu profesji, atomowość i ochrona obcych zapisów."""
from __future__ import annotations
import os,sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from core.v11000_archetypes import PROFESSION_SPECS
from systems.v11000_profession_work import process,product_id,tool_item_id

class DB:
    def __init__(self):
        self.conn=_DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.execute('CREATE TABLE inventory (account_id INTEGER,item_id TEXT,quantity INTEGER,'
                 'PRIMARY KEY(account_id,item_id))')
        self.conn.execute('CREATE TABLE profession_storage (account_id INTEGER,container TEXT,'
                 'item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,container,item_id))')
        self.conn.execute('CREATE TABLE v110_profession_cooldowns (account_id INTEGER,tool_type TEXT,'
                 'ready_at INTEGER,PRIMARY KEY(account_id,tool_type))')
        self.conn.execute('CREATE TABLE unrelated(x INTEGER)')
        self.conn.commit()
    def item_qty(self,aid,tid):
        row=self.conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(aid,tid)).fetchone()
        return row[0] if row else 0
    def storage_qty(self,aid,container,item):
        row=self.conn.execute('SELECT quantity FROM profession_storage WHERE account_id=? AND container=? AND item_id=?',
                              (aid,container,item)).fetchone()
        return row[0] if row else 0
    def add_item(self,aid,item,amount,commit=True):
        self.conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES (?,?,?) '
                          'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                          (aid,item,amount))
        if commit:self.conn.commit()
    def increment_profession_action_quests_v0700(self,aid,name,tool,n,**kw):
        return []

def run():
    db=DB()
    count=0
    for index,(name,tool,_,ingredient) in enumerate(PROFESSION_SPECS):
        aid=index+1
        db.conn.execute('INSERT INTO inventory VALUES (?,?,?)',(aid,ingredient,2))
        db.conn.commit()
        no_tool,reason,wrong_product=process(db,aid,index,lambda *a,**kw: None,now=100)
        assert no_tool is None and wrong_product is None and 'Brak narzędzia' in reason
        assert db.item_qty(aid,ingredient)==2 and db.item_qty(aid,product_id(index))==0
        db.add_item(aid,tool_item_id(index),1)
        def grant(*args,**kwargs):
            db.conn.execute('INSERT INTO unrelated(x) VALUES (?)',(aid,))
            db.conn.commit()  # exercise the real production deferred-commit proxy
            return (['Awans '+name],1,1)
        messages,changed,item=process(db,aid,index,grant,now=100)
        assert messages==['Awans '+name] and item==product_id(index)
        assert db.item_qty(aid,ingredient)==1 and db.item_qty(aid,item)==1
        assert db.conn.execute('SELECT count(*) FROM unrelated WHERE x=?',(aid,)).fetchone()[0]==1
        messages,warning,_=process(db,aid,index,grant,now=101)
        assert messages is None and '11 sekund' in warning
        assert db.item_qty(aid,ingredient)==1 and db.item_qty(aid,item)==1
        count+=1
    # The transaction may start during other subsystem's pending work.
    aid=100
    ingredient=PROFESSION_SPECS[0][3]
    db.conn.execute('INSERT INTO inventory VALUES (?,?,?)',(aid,ingredient,2))
    db.add_item(aid,tool_item_id(0),1)
    db.conn.commit()
    db.conn.execute('INSERT INTO unrelated VALUES (999)')
    try:
        def faulty(*args,**kwargs):
            db.conn.execute('INSERT INTO unrelated VALUES (1000)')
            db.conn.commit()
            raise RuntimeError('Test zawodnej wypłaty XP')
        process(db,aid,0,faulty,now=100)
        raise AssertionError('Failure was swallowed')
    except RuntimeError as exc:assert 'wypłaty' in str(exc)
    assert db.item_qty(aid,ingredient)==2 and db.item_qty(aid,product_id(0))==0
    assert db.conn.execute('SELECT count(*) FROM unrelated WHERE x=999').fetchone()[0]==1
    assert db.conn.execute('SELECT count(*) FROM unrelated WHERE x=1000').fetchone()[0]==0
    db.conn.rollback()
    assert db.conn.execute('SELECT count(*) FROM unrelated WHERE x=999').fetchone()[0]==0
    print(f'V110 PROFESSION TRANSACTIONS PASS: {count} independent professions, '
          'tool ownership, cooldown, failure rollback and unrelated pending writes preserved',flush=True)

if __name__=='__main__':run()
