# -*- coding: utf-8 -*-
"""Synthetic SQLite-only tests of pre-v107 comparisons. No player DB accessed."""
from __future__ import annotations
import sqlite3
from validation.v10800_eq107_source_diagnostic_ro import compare_snapshots, KEYS


def before():
    db = sqlite3.connect(':memory:')
    db.executescript('''
        CREATE TABLE equipment(account_id INTEGER, slot TEXT, item_id TEXT);
        CREATE TABLE inventory(account_id INTEGER, item_id TEXT, quantity INTEGER);
        INSERT INTO equipment VALUES(1, 'head', 'helm');
        INSERT INTO inventory VALUES(1,'helm',2);
    ''')
    return db


def after():
    db = before()
    db.executescript('''
        CREATE TABLE v106_item_instances(instance_id TEXT, account_id INTEGER,
            item_id TEXT, evolution_stage INTEGER);
        CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,instance_id TEXT);
        CREATE TABLE v106_stored_instances(instance_id TEXT);
        INSERT INTO v106_item_instances VALUES('u1',1,'helm',0);
        INSERT INTO v106_item_instances VALUES('u2',1,'sword',0);
        INSERT INTO v106_equipped_instances VALUES(1,'head','u2');
        INSERT INTO inventory VALUES(1,'sword',1);
        UPDATE inventory SET quantity=3 WHERE item_id='helm';
    ''')
    return db

checks = 0
old, now = before(), after()
res = compare_snapshots(now, old, {'helm','sword'})
assert set(res) == set(KEYS)
assert res['SLOTY_ROZNE_SZABLONY'] == 1
assert res['SLOTY_W_BACKUPIE_JAK_EQUIPMENT'] == 1
assert res['SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_BEZ_EWOLUCJI'] == 1
checks += 1
assert res['BRAKI_SZTUK_POKRYTE_PRZYROSTEM_OD_BACKUPU'] == 1
assert res['BRAKI_SZTUK_BEZ_POKRYCIA_W_PRZYROSCIE'] == 1
assert res['BRAKI_GRUPY_BEZ_WYSTARCZAJACEGO_PRZYROSTU'] == 1
checks += 1
now.execute("UPDATE equipment SET item_id='sword'")
now.execute("UPDATE v106_equipped_instances SET instance_id='u1'")
res = compare_snapshots(now, old, {'helm','sword'})
assert res['SLOTY_W_BACKUPIE_JAK_CIEN'] == 1
assert res['SLOTY_NIEOBECNE_W_BACKUPIE'] == 0
checks += 1
now.execute("UPDATE equipment SET item_id='helm'")
now.execute("UPDATE v106_item_instances SET evolution_stage=2 WHERE instance_id='u1'")
res = compare_snapshots(now, old, {'helm','sword'})
assert res['SLOTY_ROZNE_SZABLONY'] == 0
checks += 1
now.execute("UPDATE equipment SET item_id='sword'")
now.execute("UPDATE v106_equipped_instances SET instance_id='u1'")
now.execute("UPDATE v106_item_instances SET item_id='sword' WHERE instance_id='u2'")
res = compare_snapshots(now, old, {'helm','sword'})
assert res['SLOTY_W_BACKUPIE_JAK_CIEN'] == 1
assert res['SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_BEZ_EWOLUCJI'] == 1
checks += 1
now.execute("INSERT INTO v106_stored_instances VALUES('u2')")
res = compare_snapshots(now, old, {'helm','sword'})
assert res['SLOTY_BRAK_WOLNEJ_ZGODNEJ_KOPII'] == 1
checks += 1
now.execute("DELETE FROM v106_stored_instances")
now.execute("INSERT INTO v106_item_instances VALUES('u3',1,'sword',0)")
res = compare_snapshots(now, old, {'helm','sword'})
assert res['SLOTY_WIELE_WOLNYCH_ZGODNYCH_KOPII'] == 1
checks += 1
old.close(); now.close()
print(f'V108 EQ107 POROWNANIE Z BACKUPEM: {checks}/7 PASS')
