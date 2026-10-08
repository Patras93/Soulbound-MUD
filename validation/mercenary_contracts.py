# -*- coding: utf-8 -*-
"""Regression: payments, permanent contracts, migration and UOSS isolation."""
import sqlite3
import time
from storage.db_mercenaries import DatabaseMercenariesMixin
from systems.mercenary_taverns import MERCENARIES, mercenary_role, pick_next_contract
from core.classes_skills import CLASSES


def mercenary_contract_audit_v1170():
    checks=0
    class FakeDB(DatabaseMercenariesMixin):
        def __init__(self):
            self.conn=sqlite3.connect(":memory:")
            self.conn.row_factory=sqlite3.Row
            self.conn.execute("CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,silver INTEGER)")
            self.conn.execute("INSERT INTO account_wallet VALUES(1,1000000)")
            self.create_mercenary_schema()
        def master_account_for_character(self, ident):
            return 1
        def shared_wallet_for_master(self, master):
            return (self.conn.execute("SELECT silver FROM account_wallet WHERE master_account_id=?",(master,)).fetchone()[0],0,0)
        def set_shared_wallet_for_master(self, master, silver, gold, mithril, *, commit=True):
            self.conn.execute("UPDATE account_wallet SET silver=? WHERE master_account_id=?",(silver,master))
            if commit:
                self.conn.commit()
    db=FakeDB()
    def check(value, label):
        nonlocal checks
        if not value:
            raise AssertionError(label)
        checks+=1
    check(mercenary_role('Elira')=='kaplan', 'hiring by name')
    check(mercenary_role('Kapłanka')=='kaplan', 'hiring by class')
    check(len(CLASSES)==14, 'canonical class count')
    check(len(MERCENARIES)==len(CLASSES)+1, 'one mercenary for every class plus Paladin')
    check({s['class'] for s in MERCENARIES.values() if s['class']}=={c[0] for c in CLASSES}, 'exact class coverage')
    check(sum(s['class'] is None for s in MERCENARIES.values())==1 and MERCENARIES['paladyn']['role']=='Paladyn', 'extra Paladin preserved')
    check(len({s['name'].casefold() for s in MERCENARIES.values()})==len(MERCENARIES), 'unique hire names')
    check(mercenary_role('Łowca')=='lucznik' and mercenary_role('Łucznik')=='lucznik' and mercenary_role('Riven')=='lucznik', 'old archer contracts remain valid')
    check(mercenary_role('Cyborg') is None and mercenary_role('Mec')=='mec', 'Mec class not Cyborg race')
    for klass in CLASSES:
        role = mercenary_role(klass[0])
        check(role is not None and MERCENARIES[role]['class']==klass[0], f'can hire {klass[0]}')
    for role, spec in MERCENARIES.items():
        check(bool(spec['ability']) and spec['attack_type'] in ('physical','magic') and spec['power']>0, f'{role} combat action')
    check(db.hire_mercenary(2,'kaplan',13000,now=1000)=='ok','hire')
    check(db.shared_wallet_for_master(1)[0]==987000,'charge exact amount')
    check(db.hire_mercenary(2,'kaplan',13000,now=1000)=='duplicate','no duplicated hire')
    check(db.shared_wallet_for_master(1)[0]==987000,'no duplicated charge')
    check(db.hire_mercenary(2,'mag',13000,now=1000)=='ok','second hire')
    check(db.hire_mercenary(2,'wojownik',13000,now=1000)=='ok','third hire')
    check(db.hire_mercenary(2,'lucznik',13000,now=1000)=='full','three contract cap')
    rows=db.mercenary_contracts(2,1001)
    check(len(rows)==3, '3 active')
    check(all(row['expires_at']==0 for row in rows), 'all hires permanent')
    check(pick_next_contract(rows,'mag',1001)=='wojownik','round robin')
    check(pick_next_contract(rows,'mag',10**12)=='wojownik','permanent combat after long time')
    check(db.hire_mercenary(3,'paladyn',2000000,now=1000)=='money','insufficient funds')
    check(db.mercenary_contracts(3,1001)==[],'no free contract')
    check(len(db.mercenary_contracts(2,10**12))==3,'no expiry at any time')
    check(db.hire_mercenary(2,'lucznik',300,now=4000)=='full','no fourth hire after 45 minutes')
    check(db.dismiss_mercenary(2,'mag')==1,'dismiss one')
    check(db.hire_mercenary(2,'lucznik',300,now=4000)=='ok','hire in freed slot')
    db.dismiss_mercenary(2,'lucznik')
    check({row['role'] for row in db.mercenary_contracts(2,4001)}=={'kaplan','wojownik'},'dismiss only selected')
    check(db.dismiss_mercenary(2,'lucznik')==0,'cannot dismiss twice')
    check(db.dismiss_mercenary(2)==2,'dismiss all')
    check(db.mercenary_contracts(2,4001)==[],'all dismissed')
    check(db.mercenary_contracts(3,4001)==[],'other character unaffected')
    # Existing 45-minute contracts: keep active hires, discard expired ones,
    # and migrate without charging a second time.
    clock=time.time()
    db.conn.execute("INSERT INTO mercenary_contracts VALUES (?,?,?)",(5,'paladyn',clock+2000))
    db.conn.execute("INSERT INTO mercenary_contracts VALUES (?,?,?)",(5,'mag',clock-1))
    old_balance=db.shared_wallet_for_master(1)[0]
    db.create_mercenary_schema()
    check({row['role'] for row in db.mercenary_contracts(5)}=={'paladyn'}, 'preserve only active historical hire')
    check(db.mercenary_contracts(5)[0]['expires_at']==0,'convert historical hire to permanent')
    check(db.shared_wallet_for_master(1)[0]==old_balance,'migration does not charge wallet')
    db.create_mercenary_schema()
    check(db.mercenary_contracts(5)[0]['expires_at']==0,'restart retains permanent hire')
    check(db.mercenary_contracts(6)==[],'accounts isolated')
    check(pick_next_contract([{'role':'paladyn','expires_at':100}], None, 101) is None,'ignore obsolete timed hire')
    check('Popoi' not in MERCENARIES and 'Primm' not in MERCENARIES,'UOSS independent')
    db.conn.close()
    return {'checks':checks,'errors':0}
