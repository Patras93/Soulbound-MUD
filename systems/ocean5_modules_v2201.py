# -*- coding: utf-8 -*-
"""v2.20.1: four persistent Ocean fleet components; no changes to old ships.

One module per ship and slot; replacing requires explicit dismantling in port.
During an active battle neither equip nor remove is allowed.
"""
from __future__ import annotations
from systems.imperial_economy_v1320 import atomic, give, take
from systems import ocean4_v1350 as navy

MODULES = {
 '1':('dzialo','v2201_naval_gun','Działo Lewiatana'),
 '2':('kadlub','v2201_naval_hull','Pancerz Kadłuba Głębin'),
 '3':('ochrona','v2201_naval_ward','Bariera Okrętu Burz'),
 '4':('nawigacja','v2201_naval_chart','Nawigator Głębin'),
}

def init(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS ocean5_ship_modules_v2201 (
        account_id INTEGER NOT NULL, ship_id INTEGER NOT NULL,
        slot TEXT NOT NULL, item_id TEXT NOT NULL,
        PRIMARY KEY(ship_id,slot))''')
    conn.commit()

def modules(conn, account, ship_id):
    return {r['slot']:r['item_id'] for r in conn.execute(
        'SELECT slot,item_id FROM ocean5_ship_modules_v2201 WHERE account_id=? AND ship_id=?',
        (account,ship_id))}

def _validate(conn, account, ship_id):
    if int(ship_id) not in navy._owned(conn,account):
        raise ValueError('Nie masz okrętu o tym numerze.')
    battle=navy._active_battle(conn,account)
    if battle and battle['active']:
        raise ValueError('Nie zmieniaj modułów podczas bitwy morskiej.')

def equip(conn, account, ship_id, number):
    if str(number) not in MODULES:raise ValueError('Wybierz moduł 1, 2, 3 lub 4.')
    slot,item,name=MODULES[str(number)]
    with atomic(conn):
        _validate(conn,account,ship_id)
        if slot in modules(conn,account,ship_id):
            raise ValueError('Slot zajęty. Najpierw zdejmij stary moduł.')
        take(conn,account,item,1,'inventory')
        conn.execute('INSERT INTO ocean5_ship_modules_v2201(account_id,ship_id,slot,item_id) VALUES(?,?,?,?)',
                     (account,int(ship_id),slot,item))
    return name

def remove(conn, account, ship_id, slot):
    if slot not in {v[0] for v in MODULES.values()}:
        raise ValueError('Slot: dzialo, kadlub, ochrona, nawigacja.')
    with atomic(conn):
        _validate(conn,account,ship_id)
        record=conn.execute('SELECT item_id FROM ocean5_ship_modules_v2201 WHERE account_id=? AND ship_id=? AND slot=?',
                            (account,int(ship_id),slot)).fetchone()
        if not record:raise ValueError('Brak modułu w tym slocie.')
        conn.execute('DELETE FROM ocean5_ship_modules_v2201 WHERE account_id=? AND ship_id=? AND slot=?',
                     (account,int(ship_id),slot))
        give(conn,account,record[0],1,'inventory')
    return record[0]

def bonuses(conn, account, ship_id):
    return set(modules(conn,account,ship_id))
