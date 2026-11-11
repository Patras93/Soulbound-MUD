# -*- coding: utf-8 -*-
"""v106: autorski level i NORMALNE HP wszystkich 90 nowych bossów.

Sprawdza prawdziwe metody normalizacji i World._restore_v105_authored_stage
wyjęte AST z oryginalnego kodu. Nie zastępuje symulacji walki z graczem.
"""
from __future__ import annotations
import ast,copy,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def real_restore(rooms,mobs):
    src=ROOT/'world/world_state.py'
    tree=ast.parse(src.read_text(encoding='utf-8'))
    world=next(t for t in tree.body if isinstance(t,ast.ClassDef) and t.name=='World')
    body=next(t for t in world.body if isinstance(t,ast.FunctionDef) and t.name=='_restore_v105_authored_stage')
    body.decorator_list=[]
    module=ast.fix_missing_locations(ast.Module(body=[body],type_ignores=[]))
    namespace={'ROOMS':rooms,'MOB_TEMPLATES':mobs}
    exec(compile(module,str(src),'exec'),namespace)
    return namespace['_restore_v105_authored_stage']


def run():
    from validation.v10600_stage_catalog_audit import registries
    from world.v10600_krainy_30001_60000 import install as regions_install
    from world.v10600_raids_26_35 import install as raids_install,RAID_ROWS
    from core.progression_resources import v0190_apply_combat_template
    old=os.environ.get('SOULBOUND_V106_STAGING')
    if old!='1':raise RuntimeError('Test bossów tylko w izolowanym stagingu v106.')
    state=registries();rooms,mobs,spawns,npcs,quests,items,recipes,*_=state
    regions_install(*state);raids_install(*state[:7])
    restore=real_restore(rooms,mobs)
    checks=0
    def ck(cond,msg):
        nonlocal checks
        if not cond:raise AssertionError('V106 BOSS NORMAL HP: '+msg)
        checks+=1
    boss_spawns=[(rid,mid) for rid,mid in spawns if mid.startswith('v10600_') and '_boss_' in mid]
    ck(len(boss_spawns)==90,'60 regional bosses and 30 raid phases')
    ck(len({mid for _,mid in boss_spawns})==90,'unique boss identities')
    for rid,mid in boss_spawns:
        authored=mobs[mid]
        stage=authored['generator_level']
        hp=int(authored['max_hp']);damage=int(authored['damage'])
        ck(stage==authored['v106_authored_boss_stage'] and stage>30000,'author level '+mid)
        ck(hp>=1000000 and damage>=1000,'normal HP and damage '+mid)
        ck(hp<2**63 and damage<2**63,'SQLite-safe boss statistics '+mid)
        ck(rooms[rid]['generator_level']>30000,'high-level boss room '+mid)
        # This is the very same live combat normalization function used by World.
        v0190_apply_combat_template(authored)
        ck(authored['generator_level']==800,'historical normalizer caps stage '+mid)
        ck(int(authored['max_hp'])==hp and int(authored['damage'])==damage,
           'normalizer did not replace authored HP/damage '+mid)
        restore(rid,mid)
        ck(authored['generator_level']==stage and authored['v019_stage']==stage,
           'world spawner recovers intended stage '+mid)
        ck(int(authored['max_hp'])==hp and int(authored['damage'])==damage,
           'world spawner keeps unmodified HP/damage '+mid)
        # A second actual normalization simulates a real respawn/refresh.
        v0190_apply_combat_template(authored);restore(rid,mid)
        ck(authored['generator_level']==stage and authored['max_hp']==hp,
           'idempotent respawn stage/HP '+mid)
        if '_raid_' in mid:
            phases=authored['olc_boss_phases']
            ck([p['hp_percent'] for p in phases]==[80,60,40,20],
               'phase boundaries '+mid)
            ck(all(1 < p['attack_multiplier']<=3 for p in phases),
               'phase multipliers '+mid)
            ck('south' in rooms[rid]['exits'] or 'west' in rooms[rid]['exits'],
               'raid retreat available '+mid)
    for no,*_ in RAID_ROWS:
        prefix=f'v10600_raid_{no}'
        for stage in (1,2,3):
            qid=f'{prefix}_quest_{stage}'
            ck(quests[qid]['target']==f'{prefix}_boss_{stage}',
               f'boss kill quest {no}/{stage}')
            ck(stage==1 or quests[qid].get('requires_quest')==f'{prefix}_quest_{stage-1}',
               f'raid prerequisites {no}/{stage}')
    # No-stage mode has to preserve v105 world behaviour.
    sample_rid,sample_id=boss_spawns[0];tpl=mobs[sample_id]
    os.environ.pop('SOULBOUND_V106_STAGING',None)
    try:
        v0190_apply_combat_template(tpl)
        restore(sample_rid,sample_id)
        ck(tpl['generator_level']==800,'outside staging no special restoration')
    finally:os.environ['SOULBOUND_V106_STAGING']='1'
    # An unknown/malformed marker must never alter any template's level.
    bogus='v10600_raid_26_boss_bogus'
    mobs[bogus]={'generator_level':800,'v106_authored_boss_stage':True,'max_hp':5}
    restore('v10600_raid_26_stage_1',bogus)
    ck(mobs[bogus]['generator_level']==800,'reject boolean marker')
    mobs[bogus]['v106_authored_boss_stage']='99999'
    restore('v10600_raid_26_stage_1',bogus)
    ck(mobs[bogus]['generator_level']==800,'reject string marker')
    mobs[bogus]['v106_authored_boss_stage']=100001
    restore('v10600_raid_26_stage_1',bogus)
    ck(mobs[bogus]['generator_level']==800,'reject out-of-range marker')
    # Historical v105 reconstruction still works on its own private data.
    rooms['v10500_testbossroom']={'generator_level':9100}
    mobs['v10500_testboss']={'generator_level':800,'max_hp':990000,'damage':1000}
    restore('v10500_testbossroom','v10500_testboss')
    ck(mobs['v10500_testboss']['generator_level']==9100,'old v105 restoration preserved')
    if old is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
    return checks

if __name__=='__main__':
    print('V106 BOSS 90 NORMAL HP + REAL WORLD RESTORATION: '+str(run())+' PASS',flush=True)
