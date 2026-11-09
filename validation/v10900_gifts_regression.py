# -*- coding: utf-8 -*-
"""Isolated SQL regression: date switch, shared master, rollback, relogs."""
from __future__ import annotations
import asyncio
from contextlib import contextmanager
from datetime import date
import sqlite3
from unittest.mock import patch
from systems.v10900_gifts import gift_kind,reward_plan,claim_once,award_after_delay

class Conn(sqlite3.Connection):
    @contextmanager
    def deferred_commits(self):
        yield

class Character:
    def __init__(self,aid,level=10000):
        self.account_id=aid; self.character_level=level; self.character_xp=0
        self.silver=0;self.gold=0;self.mithril=0
    def character_xp_to_next(self):return self.character_level*1000
    def add_character_xp(self,amount,**kw):
        self.character_xp+=amount
        return ['EXP '+str(amount)]

class DB:
    def __init__(self):
        self.conn=sqlite3.connect(':memory:',factory=Conn)
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER);
        CREATE TABLE account_characters(character_account_id INTEGER PRIMARY KEY,master_account_id INTEGER NOT NULL);
        CREATE TABLE characters(account_id INTEGER PRIMARY KEY,character_xp INTEGER,silver INTEGER);
        CREATE TABLE daily_login_v03051(account_id INTEGER PRIMARY KEY,last_day TEXT,streak INTEGER,best_streak INTEGER);
        CREATE TABLE v108_advent_claims(master_account_id INTEGER,gift_date TEXT,reward_silver INTEGER,PRIMARY KEY(master_account_id,gift_date));
        INSERT INTO account_wallet VALUES(1,3000,2,1);
        INSERT INTO account_characters VALUES(11,1);INSERT INTO account_characters VALUES(12,1);
        INSERT INTO characters VALUES(11,0,3000);INSERT INTO characters VALUES(12,0,3000);
        ''')
        self.conn.commit()
        self.inject_failure=False
    def master_account_for_character(self,aid):
        return self.conn.execute('SELECT master_account_id FROM account_characters WHERE character_account_id=?',(aid,)).fetchone()[0]
    def shared_wallet_for_master(self,master):
        return tuple(self.conn.execute('SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=?',(master,)).fetchone())
    def set_shared_wallet_for_master(self,master,silver,gold,mithril,*,commit=True):
        if self.inject_failure:raise RuntimeError('simulated wallet failure')
        self.conn.execute('UPDATE account_wallet SET silver=?,gold=?,mithril=? WHERE master_account_id=?',(silver,gold,mithril,master))
        if commit:self.conn.commit()
    def apply_shared_wallet_to_character(self,char):
        char.silver, char.gold,char.mithril=self.shared_wallet_for_master(self.master_account_for_character(char.account_id))
    def save_character(self,char,*,commit=False):
        self.conn.execute('UPDATE characters SET character_xp=?,silver=? WHERE account_id=?',(char.character_xp,char.silver,char.account_id))
        if commit:self.conn.commit()

class Session:
    def __init__(self,db,aid):
        self.server=type('Server',(),{'db':db})()
        self.account_id=aid
        self.character=Character(aid)
        self.closed=False
        self.messages=[]
    async def send(self,text):self.messages.append(text)


def award_fake(db,char,account,amount,**kwargs):
    assert db.conn.in_transaction
    char.add_character_xp(amount)
    db.save_character(char,commit=False)
    return amount,['EXP '+str(amount)]


async def exercise():
    checks=0
    def ck(flag,reason):
        nonlocal checks
        assert flag,reason
        checks+=1
    db=DB()
    a,b=Session(db,11),Session(db,12)
    with patch('systems.atomic_character_experience_v10400.award_character_xp_atomic_v10400',new=award_fake):
        for d in (date(2026,11,30),date(2027,1,1),date(2027,1,2)):
            ck(gift_kind(d)=='daily','normal gift on Jan 1 and other days')
        for d in (date(2026,12,1),date(2026,12,31)):
            ck(gift_kind(d)=='advent','advent only in December')
        for day in range(1,32):
            advent=reward_plan(date(2026,12,day),1,a.character)
            for d in (date(2026,11,30),date(2027,1,1)):
                daily=reward_plan(d,1,a.character)
                ck(advent['silver']>daily['silver'] and advent['exp']>daily['exp'],'every advent better than daily')
        one=claim_once(a,day=date(2026,12,1))
        ck(one and one['kind']=='advent' and one['exp']>0,'first advent automatically paid')
        from core.bootstrap_economy_professions import legacy_currency_to_coins
        initial=legacy_currency_to_coins(3000,2,1)
        ck(legacy_currency_to_coins(*db.shared_wallet_for_master(1))==initial+one['silver'],
           'wallet higher gold/mithril preserved; no silent destruction')
        ck(a.character.character_xp==one['exp'],'EXP truly added')
        ck(db.conn.execute('SELECT silver FROM characters WHERE account_id=11').fetchone()[0]==initial+one['silver'],
           'player SQL wallet mirror updated')
        ck(claim_once(a,day=date(2026,12,1)) is None,'same character no double')
        ck(claim_once(b,day=date(2026,12,1)) is None,'same master alt no double')
        ck(db.conn.execute('SELECT COUNT(*) FROM v109_gift_claims').fetchone()[0]==1,'one SQL row')
        db.inject_failure=True
        old_wallet=db.shared_wallet_for_master(1)
        old_exp=a.character.character_xp
        try:claim_once(a,day=date(2026,12,2))
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: injected failure expected in negative test
        else:raise AssertionError('wallet failure not propagated')
        ck(db.shared_wallet_for_master(1)==old_wallet and a.character.character_xp==old_exp,
           'wallet/EXP rollback on error')
        ck(db.conn.execute('SELECT COUNT(*) FROM v109_gift_claims').fetchone()[0]==1,'no ghost claim')
        db.inject_failure=False
        # Fault *after* the wallet has changed: rollback must restore SQL and
        # in-memory EXP/wallet, including account-wide mirrors.
        prior_wallet = db.shared_wallet_for_master(1)
        prior_row = tuple(db.conn.execute(
            'SELECT character_xp,silver FROM characters WHERE account_id=11').fetchone())
        def broken_xp(dbarg, char, aid, amount):
            char.character_xp += 300
            raise OSError('injected EXP save failure')
        with patch('systems.atomic_character_experience_v10400.award_character_xp_atomic_v10400',
                   new=broken_xp):
            try:
                claim_once(a,day=date(2026,12,10))
            except OSError:  # AUDIT_INTENTIONAL_PASS: expected exception in negative regression fixture
                pass
            else:
                raise AssertionError('late EXP failure hidden')
        ck(db.shared_wallet_for_master(1) == prior_wallet,
           'late EXP failure rolls back shared wallet')
        ck(tuple(db.conn.execute(
            'SELECT character_xp,silver FROM characters WHERE account_id=11').fetchone()) == prior_row,
           'late EXP failure rolls back persisted character')
        ck(a.character.character_xp == old_exp,
           'late EXP failure restores in-memory character')
        ck(db.conn.execute('SELECT 1 FROM v109_gift_claims WHERE gift_date=?',
                           ('2026-12-10',)).fetchone() is None,
           'late EXP failure leaves no awarded receipt')
        # Overflow should reject, not saturate/silently lose any money.
        from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL
        db.conn.execute('UPDATE account_wallet SET silver=?,gold=0,mithril=0 '
                        'WHERE master_account_id=1', (CURRENCY_SQLITE_SAFE_TOTAL - 1,))
        db.conn.commit()
        try:
            claim_once(a,day=date(2026,12,11))
        except OverflowError:  # AUDIT_INTENTIONAL_PASS: expected exception in negative regression fixture
            pass
        else:
            raise AssertionError('currency overflow was accepted')
        ck(db.shared_wallet_for_master(1)[0] == CURRENCY_SQLITE_SAFE_TOTAL - 1,
           'over-limit account wallet never saturated')
        ck(db.conn.execute('SELECT 1 FROM v109_gift_claims WHERE gift_date=?',
                           ('2026-12-11',)).fetchone() is None,
           'over-limit reward leaves no phantom receipt')
        db.conn.execute('UPDATE account_wallet SET silver=?,gold=?,mithril=? '
                        'WHERE master_account_id=1', prior_wallet)
        db.conn.commit()
        two=claim_once(a,day=date(2026,12,2))
        ck(two and two['kind']=='advent','retry after failure succeeds')
        db.conn.execute('INSERT INTO v108_advent_claims VALUES(?,?,?)',(1,'2026-12-03',1000))
        db.conn.commit()
        ck(claim_once(a,day=date(2026,12,3)) is None,'old manual advent prevents duplicate')
        db.conn.execute('INSERT OR REPLACE INTO daily_login_v03051 VALUES(?,?,?,?)',
                        (12,'2026-12-04',1,1))
        db.conn.commit()
        ck(claim_once(a,day=date(2026,12,4)) is None,
           'existing v108 daily from alternate character prevents December advent double')
        db.conn.execute('INSERT INTO v108_advent_claims VALUES(?,?,?)',
                        (1,'2027-01-05',1000))
        db.conn.commit()
        ck(claim_once(a,day=date(2027,1,5)) is None,
           'historical v108 January Advent prevents new January daily double')
        january=claim_once(a,day=date(2027,1,1))
        ck(january and january['kind']=='daily','daily resumes January 1')
        ck(db.conn.execute('SELECT last_day FROM daily_login_v03051 WHERE account_id=11').fetchone()[0]
           =='2027-01-01','normal daily streak saved')
        ck(claim_once(b,day=date(2027,1,1)) is None,'alt no duplicate January')
        # v108 login already paid once, no repeat under v109.
        db.conn.execute('INSERT OR REPLACE INTO daily_login_v03051 VALUES(?,?,?,?)',
                        (11,'2027-01-02',2,2))
        db.conn.commit()
        ck(claim_once(a,day=date(2027,1,2)) is None,'old daily receipt prevents second award')
        # February asynchronous flow, no 120-second wait in tests.
        with patch('systems.v10900_gifts.claim_once',side_effect=lambda s:claim_once(s,day=date(2027,2,1))):
            async_ok=await award_after_delay(a,11,a.character,delay=0)
        ck(async_ok and len(a.messages)==1 and 'DZIENNY PREZENT' in a.messages[-1],'delayed gift NVDA')
        a.closed=True
        with patch('systems.v10900_gifts.claim_once',side_effect=AssertionError('closed was awarded')):
            ck(await award_after_delay(a,11,a.character,delay=0) is None,'disconnected does not earn')
        a.closed=False
        with patch('systems.v10900_gifts.claim_once',side_effect=AssertionError('switched character was awarded')):
            ck(await award_after_delay(a,11,Character(11),delay=0) is None,'logout to selection safe')
        ck(db.conn.execute('SELECT COUNT(*) FROM v109_gift_claims').fetchone()[0]==4,
           'SQL: Dec 1, Dec 2, Jan 1, Feb 1 only')
    db.conn.close()
    print(f'V109 GIFTS: {checks} kontroli PASS, kalendarz, portfel, EXP, rollback, alt, opóźnienie')
    return checks

def run():return asyncio.run(exercise())
if __name__=='__main__':run()
