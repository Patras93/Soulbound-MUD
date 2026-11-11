# -*- coding: utf-8 -*-
"""Eight distinct, paid-for material professions for v107.

Real items are consumed in a single SQLite deferred-commit unit with XP,
product and native 320 quest progress. Never work for free or in a raid.
"""
from __future__ import annotations
import time
from core.archetypes.chaos import PROFESSION_SPECS
from player.session_mixins.profesje6 import _remove_all, _sum

COOLDOWN=12


def product_id(index):
    return f'v10700_prof_product_{index+1}'


def install_products(items):
    for n,(name,tool,label,ingredient) in enumerate(PROFESSION_SPECS):
        key=product_id(n)
        if key in items:
            raise RuntimeError('v107: kolizja identyfikatora wyrobu: '+key)
    for n,(name,tool,label,ingredient) in enumerate(PROFESSION_SPECS):
        items[product_id(n)] = {
            'name':f'Wyrób {name}', 'type':'craft_material', 'price':None,
            'desc':f'Wyrób profesji {name}, wytworzony z surowców krain Chaosu.',
            'v107_profession_product':True,
        }
    return 8


def process(db, account_id, index, grant_xp, *, now=None):
    """No await inside atomic section. Grant callback uses native progression.

    Caller must use a per-session command lock to prevent overlapping calls.
    Returns (messages, quest updates, item ID), or (None, explanation, None).
    """
    if not 0 <= index < len(PROFESSION_SPECS):
        return None,'Nie ma takiej profesji.',None
    name,tool,tool_name,ingredient=PROFESSION_SPECS[index]
    now=int(time.time() if now is None else now)
    if _sum(db,account_id,ingredient)<1:
        return None, f'Brakuje 1 sztuki surowca do {name}: {ingredient}.',None
    # Separate metadata table, never alters existing inventory or quest schema.
    # The schema migration is idempotent and uses the same DB connection.
    db.conn.execute('CREATE TABLE IF NOT EXISTS v107_profession_cooldowns ('
                    'account_id INTEGER NOT NULL, tool_type TEXT NOT NULL, '
                    'ready_at INTEGER NOT NULL, PRIMARY KEY (account_id, tool_type))')
    with db.conn.deferred_commits():
        row=db.conn.execute('SELECT ready_at FROM v107_profession_cooldowns '
                'WHERE account_id=? AND tool_type=?',(account_id,tool)).fetchone()
        if row and int(row[0])>now:
            return None,f'Praca {name} dostępna za {int(row[0])-now} sekund.',None
        if not _remove_all(db,account_id,ingredient,1):
            raise RuntimeError('Surowiec zniknął podczas pracy; transakcja wycofana.')
        output=product_id(index)
        db.add_item(account_id,output,1,commit=False)
        messages,_,_=grant_xp(name,180000,tool,110000,
                               content_level=60001,content_key='v107_'+tool)
        changed=db.increment_profession_action_quests_v0700(
            account_id,name,tool,1,action_code='v107_'+tool,tier=1)
        db.conn.execute('INSERT INTO v107_profession_cooldowns('
            'account_id,tool_type,ready_at) VALUES(?,?,?) '
            'ON CONFLICT(account_id,tool_type) DO UPDATE SET ready_at=excluded.ready_at',
            (account_id,tool,now+COOLDOWN))
        db.conn.commit()  # held by deferred_commits; commits one atomic unit
    return messages,changed,output
