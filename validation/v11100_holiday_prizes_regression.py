# -*- coding: utf-8 -*-
"""Regresja wypłat v111 na syntetycznym SQLite, bez plików produkcji."""
from __future__ import annotations
import sqlite3,sys,types
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
from systems.holiday.challenges import record_kill
from systems.holiday.prizes import claim,prize_info

class Conn:
    def __init__(self):self.raw=sqlite3.connect(':memory:')
    @property
    def in_transaction(self):return self.raw.in_transaction
    def execute(self,*args):return self.raw.execute(*args)
    @contextmanager
    def deferred_commits(self):
        try:yield;self.raw.commit()
        except BaseException:self.raw.rollback();raise
class DB:
    def __init__(self):
        self.conn=Conn();self.coins={1:0,2:0}
    def master_account_for_character(self,account):return {10:1,11:1,20:2}[account]
    def shared_wallet_for_master(self,master):return (self.coins[master],0,0)
    def set_shared_wallet_for_master(self,master,s,g,m,*,commit=True):
        self.coins[master]=s
    def apply_shared_wallet_to_character(self,char):char.silver=999

class Character:
    def __init__(self):self.character_level=1;self.character_xp=0;self.silver=0;self.gold=0;self.mithril=0

def run():
    day=date(2027,10,31)
    db=DB();a=SimpleNamespace(closed=False,character=Character(),account_id=10,server=SimpleNamespace(db=db))
    b=SimpleNamespace(closed=False,character=Character(),account_id=11,server=SimpleNamespace(db=db))
    other=SimpleNamespace(closed=False,character=Character(),account_id=20,server=SimpleNamespace(db=db))
    p=prize_info(db.conn,1,day)
    assert p['daily']==0 and p['weekly']==0
    xp=types.ModuleType('systems.atomic_character_experience_v10400')
    def award(db,char,account,value):char.character_xp+=value;return value,()
    xp.award_character_xp_atomic_v10400=award
    # Only the safe constants + converter are used in this unit test.
    import core.bootstrap_economy_professions as base
    with patch.dict(sys.modules,{'systems.atomic_character_experience_v10400':xp}),\
            patch.object(base,'CURRENCY_SQLITE_SAFE_TOTAL',10**15),\
            patch.object(base,'legacy_currency_to_coins',lambda s,g,m:s):
        assert claim(a,'D',day=day) is None
        for i in range(5):record_kill(db.conn,1,'v11100_holiday_10_mob_1',f'kill{i}',day=day)
        record_kill(db.conn,1,'v11100_holiday_10_boss','boss',day=day)
        db.conn.raw.commit()
        assert claim(a,'D',day=day)['exp']==10000
        assert claim(b,'D',day=day) is None  # second character of same master
        assert claim(a,'W',day=day)['exp']==60000
        assert claim(a,'W',day=day) is None
        assert db.coins[1]==17500 and a.character.character_xp==70000
        assert claim(other,'D',day=day) is None
        # Atomic failure: prize row and progress are unchanged; in-memory char restored.
        day2=date(2027,11,1)
        for i in range(5):record_kill(db.conn,1,'v11100_holiday_11_mob_1',f'nov{i}',day=day2)
        db.conn.raw.commit()
        old=(a.character.character_xp,a.character.silver)
        with patch.object(xp,'award_character_xp_atomic_v10400',side_effect=RuntimeError('injected')):
            try:claim(a,'D',day=day2)
            except RuntimeError as exc: assert str(exc) == 'injected'
            else:raise AssertionError('Expected fail')
        assert a.character.character_xp==old[0]
        assert a.character.silver==old[1]
        assert not prize_info(db.conn,1,day2)['daily_claimed']
    print('V111 HOLIDAY PRIZES PASS: daily, weekly, once-per-master, inactive, failed atomic payout')
if __name__=='__main__':run()
