# -*- coding: utf-8 -*-
"""Test kontraktu mostu po rzeczywistym killu, bez startu serwera."""
import sqlite3
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
from systems.holiday.combat import on_confirmed_kill
from systems.holiday.challenges import progress

class Conn:
    def __init__(self):
        self.raw=sqlite3.connect(':memory:')
    @property
    def in_transaction(self):return self.raw.in_transaction
    def execute(self,*a,**kw):return self.raw.execute(*a,**kw)
    @contextmanager
    def deferred_commits(self):
        try:
            yield
            self.raw.commit()
        except BaseException:
            self.raw.rollback()
            raise

class DB:
    def __init__(self):self.conn=Conn()
    def master_account_for_character(self,aid):return {10:1,11:1,12:2}[aid]

def run():
    d=date(2027,10,31)
    db=DB()
    mob=SimpleNamespace(template_id='v11100_holiday_10_boss',respawn_at=1234.5)
    players=[SimpleNamespace(account_id=i, character=SimpleNamespace(), closed=False) for i in (10,11,12)]
    with patch('systems.holiday.combat.enabled',return_value=False):
        assert on_confirmed_kill(db,mob,players,day=d)==()
        assert not hasattr(mob,'v111_holiday_fight_id')
    calls=[]
    awarded=set()
    def fake_claim(session, kind, *, day=None):
        key=(session.account_id, kind)
        calls.append(key)
        if kind!='W' or key in awarded:return None
        awarded.add(key)
        return {'silver':15000, 'exp':60000}
    with patch('systems.holiday.combat.enabled',return_value=True), \
         patch('systems.holiday.combat.claim',side_effect=fake_claim):
        assert on_confirmed_kill(db,mob,players,day=d)==(1,2)
        assert on_confirmed_kill(db,mob,players,day=d)==()
        assert calls==[(10,'D'),(10,'W'),(12,'D'),(12,'W')]*2
        assert players[0].v111_holiday_auto_prize_messages==['SWIETA: automatyczna nagroda tygodniowa: 15000 srebra i 60000 EXP.']
        for m in (1,2):
            assert progress(db.conn,m,d)['daily']==1
            assert progress(db.conn,m,d)['weekly']==1
        assert not on_confirmed_kill(db,SimpleNamespace(template_id='legacy_rat'),players,day=d)
        db.conn.execute('BEGIN')
        try:
            on_confirmed_kill(db,SimpleNamespace(template_id='v11100_holiday_10_mob_1'),players,day=d)
        except RuntimeError as e:
            assert 'committed' in str(e)
        else:raise AssertionError('Uncommitted combat was credited')
        db.conn.raw.rollback()
        # New real encounter after respawn gets a different key.
        mob.respawn_at=2345.6
        assert on_confirmed_kill(db,mob,players,day=d)==(1,2)
        assert progress(db.conn,1,d)['daily']==2
    print('V111 HOLIDAY COMBAT PASS: guarded, verified, party masters, idempotent, respawn, rollback boundary')

if __name__=='__main__':run()
