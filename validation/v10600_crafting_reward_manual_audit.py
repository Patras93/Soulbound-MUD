# -*- coding: utf-8 -*-
"""v106: audit and manual closure are fail-closed, reversible, NO reward replay."""
import os
import sqlite3
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from validation.v10600_full_recipe_atomic_flow import make_db
from systems.equipment_craft_reward_journal_v10600 import (
    begin_in_savepoint, checkpoint, pending, assert_ready,
)
from validation.v10600_craft_reward_audit_report import inspect_copy
from systems.equipment_craft_reward_audit_v10600 import (
    inspect, close_after_verified_manual_audit, CONFIRMATION, REVIEW_DOMAINS,
)


def run():
    old=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    checks=0
    opened=[]
    def ck(value, message):
        nonlocal checks
        if not value:raise AssertionError(message)
        checks+=1
    def reject(call, errors, message):
        nonlocal checks
        try: call()
        except errors: checks+=1
        else: raise AssertionError(message)
    def create(db, raw, run_id='a'*32, account=1):
        begin_in_savepoint(db,account,run_id,'recipe_1','helm','helm_quality',2)
        raw.commit()
        checkpoint(db,account,run_id,'collections')
    def reviews():
        return {k:{'status':'zgodne','evidence':'Oddzielny audyt SQLite w dziedzinie '+k}
                for k in REVIEW_DOMAINS}
    def close(db, snapshot, **kwargs):
        arguments=dict(fingerprint=snapshot['fingerprint'],operator='AdminTest',
                       reviews=reviews(),confirmation=CONFIRMATION)
        arguments.update(kwargs)
        return close_after_verified_manual_audit(db,snapshot['account_id'],snapshot['run_id'],**arguments)
    try:
        db, raw=make_db();opened.append(raw)
        db._v106_craft_audit_disposable_copy=True
        reject(lambda:inspect(db,0,'a'*32),(ValueError,), 'invalid account accepted')
        reject(lambda:inspect(db,1,'z'*32),(ValueError,), 'invalid token accepted')
        reject(lambda:inspect(db,1,'a'*32),(LookupError,), 'missing receipt accepted')
        ck(raw.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='v106_craft_reward_journal'").fetchone()[0]==0,
           'reporting empty database must not create tables')
        create(db,raw)
        snapshot=inspect(db,1,'a'*32)
        ck(snapshot['stage']=='collections','correct pending stage')
        ck(snapshot['output_qty']==2 and snapshot['output_id']=='helm_quality','real output metadata')
        ck(snapshot['automatic_grants'] is False,'inspection promises no grants')
        ck(len(snapshot['fingerprint'])==64,'snapshot digest exists')
        ck(inspect(db,1,'a'*32)['fingerprint']==snapshot['fingerprint'], 'stable snapshot fingerprint')
        ck(pending(db,1)[0]=='a'*32,'account blocked before audit')
        with TemporaryDirectory() as folder:
            offline=Path(folder)/'kopia_dziennika.sqlite'
            backup=sqlite3.connect(offline); raw.backup(backup);backup.close()
            # Regression: Windows needs explicit uri=True for file:///C:/... SQLite URIs.
            # Linux may silently accept this syntax without it, masking the bug.
            real_connect=sqlite3.connect
            with patch('validation.v10600_craft_reward_audit_report.sqlite3.connect',
                       wraps=real_connect) as open_readonly:
                lines=inspect_copy(offline)
            ck(open_readonly.call_count==1 and
               open_readonly.call_args.kwargs.get('uri') is True and
               open_readonly.call_args.args[0]==offline.resolve().as_uri()+'?mode=ro',
               'offline SQLite must use explicit read-only URI on Windows')
            ck(len(lines)==3 and 'Konto 1' in lines[1],'offline report enumerates pending receipt')
            ck('collections' in lines[1] and 'a'*32 in lines[1],
               'offline report contains exact stage and run ID')
            ck('TYLKO ODCZYT' in lines[0], 'report is clearly labelled read-only')
        reject(lambda: close(db,snapshot,confirmation='POTWIERDZAM'), (PermissionError,), 'short confirmation')
        reject(lambda: close(db,snapshot,operator='a'), (ValueError,), 'short operator')
        reject(lambda: close(db,snapshot,operator='Nie\nAdmin'), (ValueError,), 'control characters')
        reject(lambda: close(db,snapshot,fingerprint='0'*64), (RuntimeError,), 'wrong snapshot')
        reject(lambda: close(db,snapshot,fingerprint='x'), (ValueError,), 'invalid digest')
        reject(lambda: close(db,snapshot,reviews={}), (ValueError,), 'missing domains')
        for domain in REVIEW_DOMAINS:
            bad=reviews();del bad[domain]
            reject(lambda r=bad:close(db,snapshot,reviews=r),(ValueError,), 'domain omitted '+domain)
            bad=reviews();bad[domain]['status']='nie_sprawdzono'
            reject(lambda r=bad:close(db,snapshot,reviews=r),(ValueError,), 'unchecked '+domain)
            bad=reviews();bad[domain]['evidence']='ok'
            reject(lambda r=bad:close(db,snapshot,reviews=r),(ValueError,), 'short evidence '+domain)
        duplicate=reviews();duplicate['quest']['evidence']=duplicate['xp']['evidence']
        reject(lambda:close(db,snapshot,reviews=duplicate),(ValueError,), 'duplicate proof accepted')
        db._v106_craft_audit_disposable_copy=False
        reject(lambda:close(db,snapshot),(PermissionError,), 'closure without second disposable flag')
        db._v106_craft_audit_disposable_copy=True
        ck(pending(db,1)[2]=='collections','denied closures did not unblock account')
        ck(raw.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='v106_craft_reward_manual_audit'").fetchone()[0]==0,
           'denied closures did not create audit table')
        # A newer checkpoint makes an older snapshot invalid; do not accept stale evidence.
        checkpoint(db,1,'a'*32,'quest')
        reject(lambda:close(db,snapshot),(RuntimeError,), 'stale stage ticket accepted')
        updated=inspect(db,1,'a'*32)
        ck(updated['fingerprint']!=snapshot['fingerprint'], 'stage transition changes digest')
        # Verify manual closure does not touch inventory, XP or quest tables.
        tables=tuple(row[0] for row in raw.execute("SELECT name FROM sqlite_master WHERE type='table' "))
        before={name:raw.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0]
                for name in tables if name in ('inventory','v106_item_instances','quest_progress')}
        result=close(db,updated)
        ck(result['old_stage']=='quest' and result['new_stage']=='complete','audit finalizes exactly pending run')
        ck(result['automatic_grants'] is False, 'no replay by closure')
        ck(pending(db,1) is None,'account unlocked after full manual verification')
        assert_ready(db,1);checks+=1
        after={name:raw.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0] for name in before}
        ck(before==after,'audit created no equipment, rewards or quests')
        entry=raw.execute('''SELECT run_id,account_id,previous_stage,operator,decision,reviews_json
                             FROM v106_craft_reward_manual_audit''').fetchone()
        ck(entry[:4]==('a'*32,1,'quest','AdminTest'), 'operator and original stage kept')
        ck(entry[4]=='manual_verified_no_replay', 'permanent no-auto-replay decision')
        ck(all(k in entry[5] for k in REVIEW_DOMAINS),'all independently reviewed domains stored')
        reject(lambda:close(db,updated),(RuntimeError,), 'repeat decision accepted')
        reject(lambda:inspect(db,2,'a'*32),(LookupError,), 'wrong account inspected another account')
        reject(lambda:close_after_verified_manual_audit(db,2,'a'*32,
            fingerprint=updated['fingerprint'], operator='AdminTest', reviews=reviews(),
            confirmation=CONFIRMATION),(RuntimeError,), 'wrong account closed another run')
        ck(raw.execute('SELECT COUNT(*) FROM v106_craft_reward_manual_audit').fetchone()[0]==1,
           'one irreversible audit receipt')
        # A deliberately broken SQL trigger cannot half-close a craft run.
        db2, raw2=make_db();opened.append(raw2)
        db2._v106_craft_audit_disposable_copy=True
        create(db2,raw2,'b'*32)
        report=inspect(db2,1,'b'*32)
        raw2.execute('''CREATE TRIGGER abort_manual_closure BEFORE UPDATE ON v106_craft_reward_journal
            WHEN NEW.stage='complete' BEGIN SELECT RAISE(ABORT,'fault'); END''')
        raw2.commit()
        reject(lambda:close(db2,report),(sqlite3.DatabaseError,), 'failed SQL update passed')
        ck(pending(db2,1)[2]=='collections', 'SQL failure left pending stage')
        ck(raw2.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='v106_craft_reward_manual_audit'").fetchone()[0]==0 or raw2.execute('SELECT COUNT(*) FROM v106_craft_reward_manual_audit').fetchone()[0]==0,
           'SQL failure rolled back audit receipt')
        raw2.execute('DROP TRIGGER abort_manual_closure');raw2.commit()
        ck(close(db2,report)['new_stage']=='complete', 'corrected SQL operation closes once')
        # Caller-owned transaction: closure must not sneak a COMMIT.
        db3,raw3=make_db();opened.append(raw3)
        db3._v106_craft_audit_disposable_copy=True
        create(db3,raw3,'c'*32)
        report3=inspect(db3,1,'c'*32)
        raw3.execute('SAVEPOINT caller_owned')
        ck(close(db3,report3)['new_stage']=='complete', 'temporary resolution in outer tx')
        ck(pending(db3,1) is None, 'complete visible inside owner tx')
        raw3.execute('ROLLBACK TO SAVEPOINT caller_owned')
        raw3.execute('RELEASE SAVEPOINT caller_owned')
        ck(pending(db3,1)[2]=='collections','caller rollback restores pending state')
        ck(raw3.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name="v106_craft_reward_manual_audit"').fetchone()[0]==0,
           'caller rollback also removes audit schema when newly created')
        ck(close(db3,report3)['new_stage']=='complete','re-review after owner rollback')
        # Deliberately broken data always fails closed.
        db4,raw4=make_db();opened.append(raw4)
        db4._v106_craft_audit_disposable_copy=True
        create(db4,raw4,'d'*32)
        raw4.execute("UPDATE v106_craft_reward_journal SET stage='tampered' WHERE run_id=?",('d'*32,))
        raw4.commit()
        reject(lambda:inspect(db4,1,'d'*32),(RuntimeError,), 'tampered journal inspected as valid')
        # Re-open SQLite from a file to prove the audit receipt is truly persistent.
        with TemporaryDirectory() as folder:
            file=Path(folder)/'testowa_kopia.sqlite'
            on_disk=sqlite3.connect(file)
            raw.backup(on_disk)
            on_disk.close()
            reloaded=sqlite3.connect(file)
            reopened=reloaded.execute('SELECT decision FROM v106_craft_reward_manual_audit').fetchone()
            ck(reopened[0]=='manual_verified_no_replay','audit survives real file reopen')
            ck(reloaded.execute("SELECT stage FROM v106_craft_reward_journal WHERE run_id=?",('a'*32,)).fetchone()[0]=='complete',
               'closed journal survives real file reopen')
            ck('nie ma przerwanych' in inspect_copy(file)[0],
               'NVDA read-only report recognizes completed journal')
            ck(reloaded.execute('PRAGMA user_version').fetchone()[0]==0,
               'read-only reporter did not alter SQLite metadata')
            reloaded.close()
        # Without explicit SOULBOUND_V106_STAGING, even a marked DB is denied.
        os.environ['SOULBOUND_V106_STAGING']=''
        reject(lambda:inspect(db3,1,'c'*32),(PermissionError,), 'audit leaks outside staging')
        reject(lambda:close(db3,report3),(PermissionError,), 'manual closure leaks outside staging')
        return checks
    finally:
        for conn in opened: conn.close()
        if old is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=old

if __name__=='__main__':
    print('V106 CRAFT REWARD MANUAL AUDIT:',run(),'PASS',flush=True)
