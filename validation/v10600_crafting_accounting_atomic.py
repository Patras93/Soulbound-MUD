# -*- coding: utf-8 -*-
"""v106 staged: mastery and three durable craft statistics share item SAVEPOINT.

Runs genuine production storage method on isolated SQLite only. Does not claim
EXP, quest progress, chronicle or achievements are yet atomic.
"""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10600_full_recipe_atomic_flow import make_db


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    checks=0
    def ck(condition,reason):
        nonlocal checks
        if not condition:raise AssertionError(reason)
        checks+=1
    try:
        db,raw=make_db()
        def accounting(critical=False,legendary=False,count=2):
            return dict(profession='Kowalstwo',category='zbroja',
                        critical=critical,legendary=legendary,crafted_items=count)
        def stat(k):
            row=raw.execute('SELECT value FROM lifetime_statistics WHERE account_id=1 AND stat_key=?',(k,)).fetchone()
            return row[0] if row else 0
        def mastery():
            return raw.execute('SELECT actions,criticals,legendary_count FROM crafting_mastery_v03054 WHERE account_id=1 AND profession=? AND category=?',('Kowalstwo','zbroja')).fetchone()
        def snap():
            return tuple((tbl,tuple(tuple(r) for r in raw.execute(f'SELECT * FROM {tbl} ORDER BY 1,2')))
                         for tbl in ('inventory','profession_storage','v106_item_instances',
                                     'crafting_mastery_v03054','lifetime_statistics'))
        ck(db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                    success_accounting=accounting(critical=True)) is True,
           'successful recipe shares item+mastery+statistics transaction')
        ck(tuple(mastery())==(1,1,0),'one mastery action and one critical')
        ck((stat('craft_actions'),stat('crafted_items'),stat('profession_actions'))==(1,2,1),
           'three durable counters reflect actual output count, not one action per item')
        ck(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='helm'").fetchone()[0]==2,
           'two physical instance identifiers')
        ck(db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                    success_accounting=accounting(legendary=True)) is True,
           'second action succeeds')
        ck(tuple(mastery())==(2,1,1),'mastery critical and legendary totals conserved')
        ck((stat('craft_actions'),stat('crafted_items'),stat('profession_actions'))==(2,4,2),
           'two separate actions counted once each')
        ck(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='helm'").fetchone()[0]==4,
           'new IDs added without reusing old physical copies')
        before=snap()
        ck(db.craft_item_atomic_v106(1,{'ore':99},'helm',2,containers={'ore':'craftbox'},
                                    success_accounting=accounting()) is False,
           'lack of ingredients rejects recipe')
        ck(snap()==before,'failed preflight does not record mastery or statistics')
        bad=[dict(accounting(),crafted_items=1),
             dict(accounting(),critical='yes'),
             dict(accounting(),profession=''),
             dict(accounting(),category=''),
             dict(accounting(),legendary=2),
             dict(accounting(),crafted_items=-1),
             dict(accounting(),unexpected='field')]
        for payload in bad:
            try:
                db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                          success_accounting=payload)
            except (ValueError,TypeError,OverflowError):
                checks+=1
            else:raise AssertionError('invalid accounting accepted')
        ck(snap()==before,'invalid accounting leaves all SQLite state unchanged')
        # Failure AFTER the main output has been inserted rolls back that output,
        # ingredient withdrawals, every physical ID and previously applied mastery.
        raw.execute('''CREATE TRIGGER fail_craft_counter BEFORE UPDATE ON lifetime_statistics
            WHEN NEW.stat_key='crafted_items'
            BEGIN SELECT RAISE(ABORT,'counter failure'); END''')
        raw.commit()
        try:
            db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                      success_accounting=accounting())
        except __import__('sqlite3').DatabaseError:
            checks+=1
        else:raise AssertionError('SQL trigger should abort atomic account accounting')
        ck(snap()==before,'late SQL failure restores inputs, gear, mastery and stats')
        raw.execute('DROP TRIGGER fail_craft_counter');raw.commit()
        # Never let SQLite turn an overflowing counter into floating point.
        raw.execute("UPDATE lifetime_statistics SET value=9223372036854775807 WHERE account_id=1 AND stat_key='crafted_items'")
        raw.commit()
        overflow_snapshot=snap()
        try:
            db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                      success_accounting=accounting())
        except OverflowError:
            checks+=1
        else:raise AssertionError('INT64 overflow accepted')
        ck(snap()==overflow_snapshot,'overflow leaves items, physical IDs and stats untouched')
        raw.execute("UPDATE lifetime_statistics SET value=4 WHERE account_id=1 AND stat_key='crafted_items'")
        raw.commit()
        ck(snap()==before,'restored counter matches pre-overflow baseline')
        # Caller transaction must remain rollback-able even after success.
        baseline=snap()
        raw.execute('SAVEPOINT owner_tx')
        ck(db.craft_item_atomic_v106(1,{'ore':1},'helm',2,containers={'ore':'craftbox'},
                                    success_accounting=accounting()) is True,
           'caller-owned transaction can provisionally craft')
        ck(snap()!=baseline and stat('craft_actions')==3,
           'provisional items and statistics visible')
        raw.execute('ROLLBACK TO SAVEPOINT owner_tx')
        raw.execute('RELEASE SAVEPOINT owner_tx')
        ck(snap()==baseline,'caller rollback restores all five sets of data')
        raw.close()
        return checks
    finally:
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':
    print('V106 CRAFT ACCOUNTING ATOMIC:',run(),'PASS',flush=True)
