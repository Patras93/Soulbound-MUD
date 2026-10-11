# -*- coding: utf-8 -*-
"""v2.30.0: obligatory test of real 42 recipe chain, local AI and ocean routes.

NEVER opens production SQLite. The smoke is entirely in-memory; real six-user
TCP coverage remains a distinct mandatory stage (v2102_tcp_six_players.py).
"""
from __future__ import annotations
from collections import deque
from pathlib import Path
from types import SimpleNamespace
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.items import ITEMS
from systems import tactical_ai_v2200 as ai
from systems import monster_ai
from systems import mastery_crafting_v2201 as craft
from systems import mastery_advancement_v2300 as nextcraft
from systems import profession_mastery_v2200 as professions
from systems import ocean_depths_v2200 as depths
from systems import ocean_sagas_v2300 as sagas
from systems import ocean4_v1350 as navy


def run_regression():
    count=0
    def check(ok,info):
        nonlocal count
        assert ok,info
        count+=1
    # World-wide local AI: protect scripted bosses and training dummies.
    for label,want in [('Szaman Orków','uzdrowiciel'),('Dowódca Korsarzy','dowodca'),
                      ('Strażnik Podziemi','obronca'),('Nekromanta Pustki','nekromanta'),
                      ('Łowca Smoków','lowca')]:
        check(ai.role({'name':label})==want,'role '+label)
    check(ai.role({'name':'Zwykły wilk'})=='','ordinary wildlife remains ordinary')
    check(ai.role({'name':'Mag leśny','damage_type':'magic'})=='mag','magic role')
    check(ai.role({'name':'Strażnik','boss':True})=='','no boss role injection')
    mob=lambda name,hp:SimpleNamespace(key=name,template_id='test',room_id='p1',engaged_by='hero',hp=hp,
                                       alive=True,combat_turn=3)
    healer=mob('shaman',90); ally=mob('ally',20)
    base={'name':'Szaman Orków','max_hp':100,'damage_type':'magic'}
    check(monster_ai.monster_ai_eligible_v1160(healer,base),'old-world healer enabled')
    plan=monster_ai.monster_ai_plan_v1160(healer,base,[ally],now=200)
    check(plan['kind']=='heal' and plan['target'] is ally,'heals injured nearby ally')
    ally.room_id='another'
    check(ai.select_support(healer,base,[ally],200,lambda _:100) is None,'cannot heal other room')
    boss={'name':'Szaman','boss':True,'world_boss':True}
    check(not monster_ai.monster_ai_eligible_v1160(healer,boss),'boss protection')
    # Build genuine craft catalog, 14 * 3 without duplicate/missing ingredients.
    items=dict(ITEMS)
    for k in ('v2200_leviathan_heart','v2200_ancient_pearl','v2200_whisper_coral','v2200_storm_core'):
        items[k]={'name':k,'type':'resource'}
    # Some runtime imports may already register crafting outputs; clean fixture deliberately.
    for v in craft.RECIPES.values():items.pop(v[1],None)
    for name in professions.SPECIALTIES:
        for tier in (2,3):items.pop(nextcraft.recipe(name,tier)[1],None)
    check(craft.install(items)==42,'42 distinct craft outputs')
    check(len({nextcraft.recipe(p,t)[1] for p in professions.SPECIALTIES for t in (2,3)})==28,'28 next-stage IDs')
    for p in professions.SPECIALTIES:
        for tier in (2,3):
            spec,item,ingredients,price,name=nextcraft.recipe(p,tier)
            check(item in items and all(ing in items for ing in ingredients),'catalog for '+name)
            check(price>0 and len(ingredients)==2,'valuable multi-stage craft '+name)
    try:craft.install(items)
    except ValueError:count+=1
    else:raise AssertionError('duplicate craft did not fail')
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER)')
    conn.execute('CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER NOT NULL,PRIMARY KEY(account_id,item_id))')
    conn.execute('CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,container,item_id))')
    for a in range(1,15):conn.execute('INSERT INTO characters VALUES (?,0,0,0)',(a,))
    professions.init(conn)
    for account,profession in enumerate(professions.SPECIALTIES,1):
        for i,spec in enumerate(professions.SPECIALTIES[profession]):
            professions.unlock(conn,account,profession,spec,(100,250,450)[i],now=10000)
        first=craft.RECIPES[profession]
        for raw,amount in first[2].items():
            conn.execute('INSERT INTO inventory VALUES (?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                         (account,raw,amount))
        out,*_=craft.craft(conn,account,profession,450,1)
        check(out==first[1],'tier 1 '+profession)
        for tier in (2,3):
            spec,item,ingredients,_,name=nextcraft.recipe(profession,tier)
            extra=next(raw for raw in ingredients if raw!=out)
            conn.execute('INSERT INTO inventory VALUES (?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                         (account,extra,ingredients[extra]))
            out,name,xp,toolxp=craft.craft(conn,account,profession,450,tier)
            check(out==item and xp>0 and toolxp>0,'tier '+str(tier)+' '+profession)
            check(conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(account,out)).fetchone()[0]==1,
                  'persisted output '+profession)
            try:craft.craft(conn,account,profession,450,tier)
            except ValueError:count+=1
            else:raise AssertionError('free duplicated item '+profession)
    check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    old=conn.execute('SELECT COUNT(*) FROM profession_specialties_v2200').fetchone()[0]
    check(old==42,'old specialties persisted')
    conn.close()
    # Expand existing ocean route without displacing old rooms or IDs.
    room={'v2000_ocean_hub':{'exits':{'down':'nexus'}}}
    npcs={};shops={};mobs={};spawns=[];quests={};items={};sellers={}
    fleet=SimpleNamespace(ENEMIES={},MATERIALS={})
    depths.install(room,npcs,shops,mobs,spawns,quests,items,sellers,fleet)
    before=set(room)
    outcome=sagas.install(room,npcs,mobs,spawns,quests,fleet)
    check(outcome=={'rooms':8,'mobs':8,'quests':2,'fleet_targets':2},'ocean saga counts')
    check(before.issubset(room),'all old rooms preserved')
    check(len(quests)==6 and len(spawns)==24,'new and old quests/spawns')
    back={'north':'south','south':'north','east':'west','west':'east','northeast':'southwest','southwest':'northeast'}
    for slug,*_ in sagas.ROUTES:
        check(f'v2300_{slug}_boss' in mobs,'saga boss '+slug)
        check(f'v2300_{slug}_quest' in quests,'saga quest '+slug)
        check(f'legenda_{slug}' in fleet.ENEMIES,'saga naval challenge '+slug)
    for rid,data in room.items():
        if rid=='v2000_ocean_hub':continue
        for direction,target in data['exits'].items():
            check(target in room and room[target]['exits'].get(back[direction])==rid,
                  f'reciprocal exit {rid}.{direction} -> {target}')
    reached={'v2000_ocean_hub'};q=deque(reached)
    while q:
        for target in room[q.popleft()].get('exits',{}).values():
            if target in room and target not in reached:
                reached.add(target);q.append(target)
    check(reached==set(room),'all new rooms reachable')
    for kind in ('legenda_cisza','legenda_nawa'):
        check(sagas.hazard(kind,3 if kind.endswith('cisza') else 4,'salwa')[1].startswith('UWAGA'),
              'accessible pre-warning '+kind)
        check(sagas.hazard(kind,4 if kind.endswith('cisza') else 5,'salwa')[0]==135,
              'strong wave '+kind)
    check(sagas.hazard('korsarze',4,'salwa')==(100,''),'no old fleet balance change')
    try:sagas.install(room,npcs,mobs,spawns,quests,fleet)
    except RuntimeError:count+=1
    else:raise AssertionError('second installation overwrote old route')
    return count

if __name__=='__main__':
    print('SOULBOUND v2.30.0 TAKTYKA / PROFESJE / OCEAN:',run_regression(),'checks PASS')
