# -*- coding: utf-8 -*-
"""Explicit duplicate legacy evolution allocation; SQLite copies only."""
from __future__ import annotations
import os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_instances_v10600 import (
    snapshot,apply_to_explicit_test_copy,cutover_readiness,_manual_verified)
from systems.equipment_manual_reconcile_v10600 import reconcile_on_disposable_copy
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy,_check_account

CAT={'helm':{'type':'armor'},'ring':{'type':'armor'},'ore':{'type':'material'}}


def make_db():
    c=sqlite3.connect(':memory:')
    c.executescript('''
    CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
       PRIMARY KEY(account_id,item_id));
    CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
       PRIMARY KEY(account_id,slot));
    CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
       PRIMARY KEY(account_id,record_key));
    CREATE TABLE equipment_reforges(account_id INTEGER,item_id TEXT,affix TEXT,
       PRIMARY KEY(account_id,item_id));
    INSERT INTO inventory VALUES(1,'helm',2),(2,'helm',3),(3,'ring',2),
        (4,'ring',2),(5,'ring',2),
        (6,'ring',2),(7,'ring',2),(8,'ring',2);
    INSERT INTO equipment VALUES(1,'head','helm'),(2,'head','helm'),
        (2,'body','helm');
    INSERT INTO player_records_v03051 VALUES
        (1,'eq_evolution_v10500:helm',7),
        (2,'eq_evolution_v10500:helm',8),
        (3,'eq_evolution_v10500:ring',6),
        (4,'eq_evolution_v10500:ring',5),
        (5,'eq_evolution_v10500:ring',3),
        (6,'eq_evolution_v10500:ring',2),
        (7,'eq_evolution_v10500:ring',2),
        (8,'eq_evolution_v10500:ring',2);
    INSERT INTO equipment_reforges VALUES(4,'ring','haste');
    CREATE TABLE bank_items(account_id INTEGER,item_id TEXT,quantity INTEGER);
    INSERT INTO bank_items VALUES(6,'ring',1);
    CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER);
    INSERT INTO profession_storage VALUES(7,'stash','ring',1);
    CREATE TABLE player_mail_v03051(sender_account_id INTEGER,recipient_account_id INTEGER,
        attachment_kind TEXT,attachment_item_id TEXT,attachment_claimed INTEGER);
    INSERT INTO player_mail_v03051 VALUES(8,9,'item','ring',0);
    ''')
    return c


def run():
    before=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    c=make_db();checks=0
    def ck(value, msg):
        nonlocal checks
        assert value,msg
        checks+=1
    def fail(fn,kind):
        nonlocal checks
        try:fn()
        except kind:checks+=1
        else:raise AssertionError('Niebezpieczną operację zaakceptowano')
    def action(account=1,item='helm',qty=2,stage=7,ordinal=2,
               note='decyzja-eksperta-001',slot='head',confirm=True):
        return reconcile_on_disposable_copy(c,CAT,account_id=account,item_id=item,
            expected_quantity=qty,expected_legacy_stage=stage,
            chosen_ordinal=ordinal,reviewer_reference=note,
            selected_worn_slot=slot,confirm_disposable_copy=confirm)
    try:
        ck(snapshot(c,CAT)[0]['status']=='requires_manual_reconciliation',
            'Nieprzypisane stare EQ pozostaje nierozstrzygnięte')
        inv=list(c.execute('SELECT * FROM inventory ORDER BY account_id,item_id'))
        legacy=list(c.execute('SELECT * FROM player_records_v03051 ORDER BY account_id,record_key'))
        fail(lambda:action(confirm=False),PermissionError)
        os.environ.pop('SOULBOUND_V106_STAGING')
        fail(lambda:action(),PermissionError)
        os.environ['SOULBOUND_V106_STAGING']='1'
        fail(lambda:action(qty=3),RuntimeError)
        fail(lambda:action(stage=6),RuntimeError)
        fail(lambda:action(ordinal=3),ValueError)
        fail(lambda:action(note='x'),ValueError)
        fail(lambda:action(slot=None),RuntimeError)
        fail(lambda:action(slot='body'),RuntimeError)
        done=action()
        ck(done['new_instances']==2 and not done['already_confirmed'],
            'Po ręcznej decyzji powstają dwie fizyczne sztuki')
        ck(_manual_verified(c,1,'helm',2,7),'Zarejestrowana decyzja ma komplet ID')
        ck(c.execute('SELECT COUNT(*),SUM(evolution_stage) FROM v106_item_instances '
            'WHERE account_id=1').fetchone()==(2,7),'Dokładnie jedna z dwóch ma etap 7')
        ck(c.execute('''SELECT i.evolution_stage FROM v106_equipped_instances s
            JOIN v106_item_instances i ON i.instance_id=s.instance_id
            WHERE s.account_id=1 AND s.slot='head' ''').fetchone()==(7,),
            'Wybrany fizyczny slot zachowuje ewolucję')
        ck(action()['already_confirmed'],'Powtórzenie tej samej decyzji jest idempotentne')
        fail(lambda:action(ordinal=1),RuntimeError)
        fail(lambda:action(note='inna-decyzja-001'),RuntimeError)
        ck(snapshot(c,CAT)[0]['status']=='verified_manual',
            'Read-only snapshot rozpoznaje ręczne uzgodnienie')
        run_again=apply_to_explicit_test_copy(c,CAT,confirm_disposable_copy=True)
        ck(run_again['new_instances']==0 and run_again['ambiguous']==7,
            'Automatyczna migracja nie nadpisuje ręcznie zatwierdzonej sztuki')
        report=cutover_readiness(c,CAT)
        ck(not any(x[0]==1 and x[1]=='helm' for x in report['blocking_issues']),
            'Zweryfikowana para nie trafia ponownie do ostrzeżeń')
        ck(not report['gameplay_ready'],'Rekonsyliacja nie włącza jeszcze produkcji')
        # Three copies and two worn slots; the reviewer chooses the one evolved slot.
        r=action(account=2,qty=3,stage=8,ordinal=3,slot='body',note='decyzja-eksperta-002')
        ck(r['new_instances']==3,'Trzy kopie z jedną historyczną ewolucją')
        worn=dict(c.execute('''SELECT s.slot,i.evolution_stage FROM v106_equipped_instances s
            JOIN v106_item_instances i ON i.instance_id=s.instance_id
            WHERE s.account_id=2''').fetchall())
        ck(worn=={'head':0,'body':8},'Ewolucja tylko na jawnie wybranym slocie')
        ck(_manual_verified(c,2,'helm',3,8),'Trzy kopie poprawne')
        ck(action(account=2,qty=3,stage=8,ordinal=3,
            slot='body',note='decyzja-eksperta-002')['already_confirmed'],
            'Trzy kopie: brak powielenia podczas rerun')
        fail(lambda:action(account=4,item='ring',qty=2,stage=5,ordinal=1,
            slot=None,note='decyzja-eksperta-004'),RuntimeError)
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=4')
            .fetchone()[0]==0,'Ulepszenia v105 nie mogą zostać arbitralnie przypisane')
        for aid,description in ((6,'bank'),(7,'magazyn'),(8,'poczta')):
            fail(lambda a=aid:action(account=a,item='ring',qty=2,stage=2,ordinal=1,
                slot=None,note=f'decyzja-eksperta-00{a}'),RuntimeError)
            ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=?',
                (aid,)).fetchone()[0]==0,
                'Nie wolno wybrać kopii tylko z plecaka, gdy istnieje też '+description)
        # No worn slots, explicit human choice allowed, both units tracked.
        r=action(account=3,item='ring',qty=2,stage=6,ordinal=1,
            note='decyzja-eksperta-003',slot=None)
        ck(r['new_instances']==2,'Ręczna decyzja dla EQ w plecaku')
        ck(c.execute('SELECT COUNT(*) FROM v106_equipped_instances WHERE account_id=3')
            .fetchone()[0]==0,'Nie inventujemy miejsca założenia')
        ck(list(c.execute('SELECT * FROM inventory ORDER BY account_id,item_id'))==inv,
            'Rekonsyliacja nie zmienia inventory')
        ck(list(c.execute('SELECT * FROM player_records_v03051 ORDER BY account_id,record_key'))==legacy,
            'Oryginalne etapy v105 są nietknięte')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Integralność SQLite')
        # Inconsistency after approval is detected by BOTH migration and readiness.
        c.execute("UPDATE player_records_v03051 SET value=9 WHERE account_id=1")
        ck(not _manual_verified(c,1,'helm',2,9),'Zmiana etapu unieważnia decyzję')
        fail(lambda:apply_to_explicit_test_copy(c,CAT,confirm_disposable_copy=True),RuntimeError)
        ck(any(x[0]==1 for x in cutover_readiness(c,CAT)['blocking_issues']),
           'Zmiana po audycie musi blokować cutover')
        c.execute("UPDATE player_records_v03051 SET value=7 WHERE account_id=1")
        ck(_manual_verified(c,1,'helm',2,7),'Po przywróceniu decyzja jest ważna')
        # SQLite trigger forces a mid-batch failure. No partial instance or decision remains.
        c.execute('''CREATE TRIGGER v106_force_reconcile_abort BEFORE INSERT
            ON v106_item_instances WHEN NEW.account_id=5 AND NEW.evolution_stage=3
            BEGIN SELECT RAISE(ABORT,'forced manual failure'); END''')
        fail(lambda:action(account=5,item='ring',qty=2,stage=3,ordinal=2,
            note='decyzja-eksperta-005',slot=None),sqlite3.IntegrityError)
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=5')
           .fetchone()[0]==0,'SQL failure cofa wszystkie ID')
        ck(c.execute('SELECT COUNT(*) FROM v106_manual_evolution_allocations WHERE account_id=5')
           .fetchone()[0]==0,'SQL failure cofa także decyzję')
        c.execute('DROP TRIGGER v106_force_reconcile_abort')
        # A parent-owned SAVEPOINT keeps authority to roll back the manual decision.
        c.execute('SAVEPOINT user_parent')
        ck(action(account=5,item='ring',qty=2,stage=3,ordinal=2,
            note='decyzja-eksperta-005',slot=None)['new_instances']==2,
            'Ręczna decyzja w transakcji nadrzędnej')
        c.execute('ROLLBACK TO SAVEPOINT user_parent')
        c.execute('RELEASE SAVEPOINT user_parent')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=5')
           .fetchone()[0]==0,'ROLLBACK rodzica cofa ID')
        ck(c.execute('SELECT COUNT(*) FROM v106_manual_evolution_allocations WHERE account_id=5')
           .fetchone()[0]==0,'ROLLBACK rodzica cofa audyt')
        # Preparation may coexist with unresolved *unequipped* inventory,
        # but it must never reassign either reviewed worn physical instance.
        ids_before=c.execute('SELECT slot,instance_id FROM v106_equipped_instances '
            'WHERE account_id=2 ORDER BY slot').fetchall()
        prepared=prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        ck(prepared['new_slot_bindings']==0,
            'Przygotowanie slotów nie nadpisuje ręcznej decyzji')
        ck(c.execute('SELECT slot,instance_id FROM v106_equipped_instances '
            'WHERE account_id=2 ORDER BY slot').fetchall()==ids_before,
            'Wariant noszony po uzgodnieniu pozostaje ten sam')
        _check_account(c,1,CAT);_check_account(c,2,CAT)
        ck(True,'Po ręcznej migracji wyposażenie pozostaje spójne')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Końcowa integralność')
        return checks
    finally:
        c.close()
        if before is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=before

if __name__=='__main__':print('V106 MANUAL EVOLUTION RECONCILIATION:',run(),'PASS',flush=True)
