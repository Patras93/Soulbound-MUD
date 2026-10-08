# -*- coding: utf-8 -*-
"""Small release test: payments, contracts and isolation from UOSS helpers."""
import sqlite3
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
    check(pick_next_contract(rows,'mag',1001)=='wojownik','round robin')
    check(db.hire_mercenary(3,'paladyn',2000000,now=1000)=='money','insufficient funds')
    check(db.mercenary_contracts(3,1001)==[],'no free contract')
    check(db.mercenary_contracts(2,4000)==[],'expire')
    check(db.hire_mercenary(2,'lucznik',300,now=4000)=='ok','hire after expiration')
    db.dismiss_mercenary(2,'lucznik')
    check(not db.mercenary_contracts(2,4001),'dismiss')
    check('Popoi' not in MERCENARIES and 'Primm' not in MERCENARIES,'UOSS independent')
    db.conn.close()
    return {'checks':checks,'errors':0}
