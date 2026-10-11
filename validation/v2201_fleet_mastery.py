# -*- coding: utf-8 -*-
"""Release gate 2.20.1: 14 mastery recipes, four per-ship modules, battle outcomes.

Runs against an isolated in-memory SQLite fixture, never a live user database.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import mastery_crafting_v2201 as crafting
from systems import profession_mastery_v2200 as professions
from systems import ocean5_modules_v2201 as mods
from systems import ocean4_v1350 as navy
from systems.imperial_economy_v1320 import STORAGE
from data.items import ITEMS


def run_regression():
    count=0
    def check(cond,msg):
        nonlocal count
        assert cond,msg
        count+=1
    check(len(crafting.RECIPES)==14,'14 recipes')
    check(len({v[1] for v in crafting.RECIPES.values()})==14,'distinct outputs')
    check(len(mods.MODULES)==4,'four modules')
    check(set(crafting.TOOL_TYPES)==set(professions.SPECIALTIES),'all 14 profession tools')
    for prof, (spec,item,mats,sell,name) in crafting.RECIPES.items():
        check(prof in professions.SPECIALTIES,'known profession '+prof)
        check(spec==professions.SPECIALTIES[prof][0],'first specialty '+prof)
        check(0<len(mats)<=3 and sell>=100_000,'master requirements '+prof)
        for mat,qty in mats.items():
            check(qty>0 and isinstance(mat,str),'ingredient quantity '+prof)
    for no,(slot,item,name) in mods.MODULES.items():
        check(item in crafting.OUTPUTS, 'module crafted '+no)
        check(slot in ('dzialo','kadlub','ochrona','nawigacja'),'valid slot')
    # FULL/FAST predeploy already imported server and registered outputs globally.
    # Use a clean fixture so the duplicate-install check is still meaningful.
    from systems.mastery_advancement_v2300 import recipe as advanced_recipe
    advanced_outputs = {advanced_recipe(prof, tier)[1] for prof in professions.SPECIALTIES for tier in (2,3)}
    items={key:value for key,value in ITEMS.items() if key not in crafting.OUTPUTS and key not in advanced_outputs}
    for resource in ['v2200_leviathan_heart','v2200_storm_core','v2200_whisper_coral','v2200_ancient_pearl']:
        items[resource]={'name':resource,'type':'resource'}
    check(crafting.install(items)==42,'registered items including mastery tiers 2 and 3')
    for _,(_,item,ingredients,sell,name) in crafting.RECIPES.items():
        check(item in items and items[item]['sell_silver']==sell,'sell catalog '+item)
        check(all(mat in items for mat in ingredients),'all ingredient ids '+item)
    try:crafting.install(items)
    except ValueError:count+=1
    else:raise AssertionError('duplicate install not rejected')
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY, silver INTEGER NOT NULL, gold INTEGER NOT NULL, mithril INTEGER NOT NULL)')
    conn.execute('CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER NOT NULL,PRIMARY KEY(account_id,item_id))')
    conn.execute('CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER NOT NULL,PRIMARY KEY(account_id,container,item_id))')
    conn.execute('INSERT INTO characters VALUES (1,100000,0,0)')
    conn.execute('INSERT INTO characters VALUES (2,100000,0,0)')
    professions.init(conn)
    navy.init(conn)
    mods.init(conn);mods.init(conn)
    # Genuine Ocean fleet schema and real ownership queries; no stubbed API.
    conn.execute('''CREATE TABLE shipyard_ships_v1321 (
      id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL, ship_class INTEGER NOT NULL,
      name TEXT NOT NULL, hull INTEGER, sails INTEGER, cargo INTEGER,
      navigation INTEGER, active INTEGER, built_at INTEGER)''')
    conn.execute("INSERT INTO shipyard_ships_v1321 VALUES(71,1,2,'Bryg testowy',4,4,4,4,1,1)")
    conn.execute("INSERT INTO shipyard_ships_v1321 VALUES(72,2,2,'Obcy bryg',4,4,4,4,1,1)")
    try:
        for prof,(specialty,item,requirements,price,name) in crafting.RECIPES.items():
            professions.unlock(conn,1,prof,specialty,100,now=50)
            for mat,qty in requirements.items():
                conn.execute('INSERT INTO inventory VALUES (?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                             (1,mat,qty))
            out,label,pxp,txp=crafting.craft(conn,1,prof,100)
            check(out==item and label==name and pxp>0 and txp>0,'craft result '+prof)
            check(conn.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',(item,)).fetchone()[0]==1,
                  'real output '+prof)
            for mat,qty in requirements.items():
                row=conn.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',(mat,)).fetchone()
                check(not row or row[0]==0,'consumed '+prof+' '+mat)
            before=conn.total_changes
            try:crafting.craft(conn,1,prof,100)
            except ValueError:count+=1
            else:raise AssertionError('free second craft '+prof)
            check(conn.total_changes==before,'no partial craft '+prof)
        try:crafting.craft(conn,1,'Kowalstwo',99)
        except ValueError:count+=1
        else:raise AssertionError('level bypass')
        try:crafting.craft(conn,2,'Kowalstwo',100)
        except ValueError:count+=1
        else:raise AssertionError('specialization bypass')
        try:mods.equip(conn,2,71,'1')
        except ValueError:count+=1
        else:raise AssertionError('ship ownership bypass')
        for no,(slot,item,name) in mods.MODULES.items():
            check(mods.equip(conn,1,71,no)==name,'equip '+no)
            check(mods.modules(conn,1,71)[slot]==item,'saved module '+no)
            row=conn.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',(item,)).fetchone()
            check(not row or row[0]==0,'consumed module '+no)
            try:mods.equip(conn,1,71,no)
            except ValueError:count+=1
            else:raise AssertionError('double equip '+no)
        check(mods.bonuses(conn,1,71)=={'dzialo','kadlub','ochrona','nawigacja'},'all modules')
        # With all modules installed, sea battle reads the actual stored loadout.
        name,hp,n=navy.begin(conn,1,'korsarze',now=10000)
        check(n==1 and hp>0,'real battle started')
        try:mods.remove(conn,1,71,'dzialo')
        except ValueError:count+=1
        else:raise AssertionError('remove allowed in battle')
        try:mods.equip(conn,1,71,'1')
        except ValueError:count+=1
        else:raise AssertionError('equip allowed in battle')
        result=navy.action(conn,1,'manewr',now=10001)
        check(result['turn']==1 and result['damage']>0,'real battle action')
        navy.begin(conn,2,'korsarze',now=10000)
        unmodified=navy.action(conn,2,'manewr',now=10001)
        check(result['damage']>unmodified['damage'],'cannon and navigator boost damage')
        check(result['losses'][0][1]>unmodified['losses'][0][1],'hull protects ship')
        check(result['turn']==unmodified['turn'],'same turn reference')
        navy.retreat(conn,1,now=10002)
        check(not navy.battle_state(conn,1)['active'],'battle stopped')
        # Removing returns material exactly once.
        for no,(slot,item,name) in mods.MODULES.items():
            check(mods.remove(conn,1,71,slot)==item,'remove '+no)
            check(conn.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',(item,)).fetchone()[0]==1,'returned item '+no)
            try:mods.remove(conn,1,71,slot)
            except ValueError:count+=1
            else:raise AssertionError('duplicate return '+no)
        check(mods.modules(conn,1,71)=={},'no lingering module')
        check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # Emulate saving/reopening SQLite without touching user's DB.
        checkpoint='\n'.join(conn.iterdump())
        recovered=sqlite3.connect(':memory:');recovered.row_factory=sqlite3.Row
        recovered.executescript(checkpoint)
        check(recovered.execute('SELECT count(*) FROM profession_specialties_v2200 WHERE account_id=1').fetchone()[0]==14,'specializations persist')
        check(mods.modules(recovered,1,71)=={},'module status persists')
        check(recovered.execute('SELECT count(*) FROM inventory WHERE account_id=1 AND quantity>0').fetchone()[0]>=4,'inventory persists')
        recovered.close()
    finally:
        conn.close()
    return count

if __name__=='__main__':
    print('SOULBOUND v2.20.1: ',run_regression(),'checks PASS')
