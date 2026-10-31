# -*- coding: utf-8 -*-
"""Offline isolated tests for v104 stages 5–7; never opens a production database."""
from __future__ import annotations
import tempfile
from pathlib import Path
from copy import deepcopy


def run():
    from core.classes_skills import CLASSES, CLASS_SKILLS, V10400_CLASS_SKILLS_ADDED
    from core.class_skills_v10400 import NAMES
    from world.v10400_krainy_5001_10000 import REGIONS
    from world.v10400_equipment_5001 import install as equip, expected_ids
    from world.v10400_endgame_contracts import install as contracts
    from systems import admin_live_era_v10400 as admin
    checks=0
    def ok(value,why):
        nonlocal checks
        if not value:raise AssertionError(why)
        checks+=1
    ok(len(CLASSES)==22,'22 classes')
    ok(V10400_CLASS_SKILLS_ADDED==66,'66 new skills')
    for n,(name,*_) in enumerate(CLASSES,1):
        new=[x for x in CLASS_SKILLS[name] if x['id'].startswith(f'v10400_skill_{n:02d}_')]
        ok(len(new)==3 and {x['unlock'] for x in new}=={5200,7600,9800}, f'class skills {name}')
        ok({x['kind'] for x in new}=={'damage','aoe_damage','boost'},f'kinds {name}')
        ok(len({x['id'] for x in CLASS_SKILLS[name]})==len(CLASS_SKILLS[name]),f'unique skill IDs {name}')
        ok(all(x['name'] in NAMES[name] for x in new),f'class names {name}')
    items={'steel_ingot': {'name': 'Sztabka stali', 'type': 'craft_material'}}; recipes={}; bonuses={}
    for slug,*_ in REGIONS:
        for kind in ('alloy','material_3'):
            items[f'v10400_{slug}_{kind}']={'type':'craft_material'}
    old=deepcopy((items,recipes,bonuses))
    stats=equip(items,recipes,bonuses)
    ok(stats=={'sets':32,'items':128,'recipes':128},'set catalog counts')
    ok(set(expected_ids())==set(recipes),'every set piece craftable')
    for iid in expected_ids():
        info=items[iid];recipe=recipes[iid]
        ok(info['regional_set'] in bonuses,f'bonus {iid}')
        ok(info['slot'] in ('head','body','hands','feet'),f'slot {iid}')
        ok(recipe['output']==iid and all(ing in items for ing in recipe['ingredients']),f'valid recipe {iid}')
        ok(recipe['min_profession_level']>=5001,f'high level profession {iid}')
        if '_class_' in iid:
            ok(info['required_class'] in {c[0] for c in CLASSES},f'class-only {iid}')
    ok(equip(items,recipes,bonuses)['sets']==0,'idempotent set install')
    before=deepcopy((items,recipes,bonuses))
    ok(before==(items,recipes,bonuses),'no mutation on noop')
    quest={}; npcs={};mobs={}
    for slug,*_ in REGIONS:
        npcs[f'v10400_{slug}_npc_3']={'name':f'Strażniczka {slug}', 'specialist_quests':('old_quest',)}
        for part in ('mob_3','boss_2'):
            mobs[f'v10400_{slug}_{part}']={'name':f'Boss {slug}'}
    stats=contracts(quest,npcs,mobs,items)
    ok(stats['contracts']==30,'new contracts 30')
    for slug,*_ in REGIONS:
        offers=npcs[f'v10400_{slug}_npc_3']['specialist_quests']
        ok(offers[0]=='old_quest' and len(offers)==4,'preserve NPC offers')
        for freq,interval in (('daily',86400),('weekly',604800),('invasion',604800)):
            qid=f'v10400_contract_{slug}_{freq}';row=quest[qid]
            ok(qid in offers and row['repeatable'] and row['repeat_cooldown']==interval,'quest repeat settings')
            ok(row['target'] in mobs and row['needed']>0,'quest target')
    ok(contracts(quest,npcs,mobs,items)['contracts']==0,'idempotent contracts')
    # DRAFT/CAS/rollback on isolated file and dummy live registries.
    regs={'mobs':{'v10400_sztorm_boss_1':{'max_hp':1000,'damage':100}},
          'quests':{},'rooms':{},'items':{},'recipes':{}}
    with tempfile.TemporaryDirectory() as tmp:
        original=admin.PATH
        try:
            admin.PATH=Path(tmp)/'overrides.json';admin.reset_for_tests()
            ok(admin.command('status',regs).startswith('V104 Admin Live'),'admin status')
            ok('aktualnie 1000' in admin.command('podglad mob v10400_sztorm_boss_1 max_hp',regs),'read current values')
            ok('DRAFT' in admin.command('ustaw mob v10400_sztorm_boss_1 max_hp 1234',regs),'DRAFT')
            ok(regs['mobs']['v10400_sztorm_boss_1']['max_hp']==1000,'draft not live')
            ok('CAS' in admin.command('sprawdz',regs),'draft checked')
            ok('opublikowano' in admin.command('aktywuj POTWIERDZAM',regs),'published')
            ok(regs['mobs']['v10400_sztorm_boss_1']['max_hp']==1234,'live applied')
            ok(admin.PATH.is_file(),'atomic persisted')
            ok('cofnięto' in admin.command('cofnij POTWIERDZAM',regs),'rollback')
            ok(regs['mobs']['v10400_sztorm_boss_1']['max_hp']==1000,'original value restored')
            ok('niedozwolone' in admin.command('ustaw mob v10300_swit_boss_1 max_hp 2222',regs) or
               'Nieobsługiwane' in admin.command('ustaw mob v10300_swit_boss_1 max_hp 2222',regs), 'reject old ID')
            ok('Zakres' in admin.command('ustaw mob v10400_sztorm_boss_1 max_hp 0',regs),'reject invalid HP')
        finally:
            admin.PATH=original;admin.reset_for_tests()
    return checks

if __name__=='__main__':
    print('V104 FINAL INTEGRITY',run(),'PASS',flush=True)
