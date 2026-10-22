# -*- coding: utf-8 -*-
"""v12.00.2 jewelry XP regression, no real account/DB modifications."""
from __future__ import annotations


def run_regression():
    from systems.jewelcrafting_xp_v1202 import improved_jewelry_recipe_xp
    from systems.equipment_crafting import JEWELCRAFT_RECIPES
    from core.mines_threat import ITEMS
    from systems.profession_exp_pacing_v1201 import improved_work_xp
    checks = 0
    assert len(JEWELCRAFT_RECIPES) >= 30
    checks += 1
    qualities = set()
    for rid, recipe in JEWELCRAFT_RECIPES.items():
        assert recipe['output'] in ITEMS and recipe.get('ingredients')
        assert int(recipe.get('min_profession_level', 0)) >= 1
        quality = ITEMS[recipe['output']].get('gem_quality', 'raw')
        qualities.add(str(quality))
        params = dict(recipe, gem_quality=quality)
        prof, tool = improved_jewelry_recipe_xp(100, 50, params)
        assert prof >= 250 and tool >= 100, (rid, prof, tool)
        assert prof >= 100 and tool >= 50
        assert improved_jewelry_recipe_xp(0, 0, params) == (0, 0)
        assert improved_jewelry_recipe_xp(0, 50, params)[0] == 0
        assert improved_jewelry_recipe_xp(100, 0, params)[1] == 0
        checks += 6
    # More expensive necklaces are always at least as rewarding as rings.
    ring={'ingredients':{'iron_ingot':2}}
    necklace={'ingredients':{'iron_ingot':3}}
    assert improved_jewelry_recipe_xp(100, 50, necklace)[0] > improved_jewelry_recipe_xp(100, 50, ring)[0]
    checks += 1
    gem={'gem_cut_recipe':True,'ingredients':{'raw_gem_ruby':1}}
    common=improved_jewelry_recipe_xp(100, 50, gem)
    perfect=improved_jewelry_recipe_xp(100, 50, {**gem,'gem_quality':'perfect'})
    assert perfect[0] > common[0] and perfect[1] > common[1]
    checks += 1
    # The new award is applied after existing general EXP pacing:
    # the old payout must remain a lower bound on many levels and tiers.
    for level in (1, 20, 50, 100, 200, 400, 600, 799):
        for tier in (1, 20, 100, 400, 600):
            oldp=improved_work_xp(70, 10_000_000, level, tier)
            oldt=improved_work_xp(25, 10_000_000, level, tier,tool=True)
            newp,newt=improved_jewelry_recipe_xp(oldp, oldt, gem)
            assert newp >= oldp and newt >= oldt
            # Trivial first-tier work never gets top-tier EXP floor.
            if level>=200 and tier==1:
                hardp=improved_work_xp(70,10_000_000,level,level)
                hardt=improved_work_xp(25,10_000_000,level,level,tool=True)
                np,nt=improved_jewelry_recipe_xp(hardp,hardt,gem)
                assert np > newp and nt > newt
            checks += 2
    # Execute real recipes against a disposable SQLite DB, both with and
    # without the jewelry-only supplement. No writes to any player DB.
    checks += real_craft_regression()

    # Only recipe calls can trigger new award, never merely opening a menu.
    assert improved_jewelry_recipe_xp(100,50,None) == (100,50)
    checks += 1
    return checks


def real_craft_regression():
    import asyncio
    import os
    import random
    import re
    import tempfile
    from unittest.mock import patch
    from types import SimpleNamespace
    import server
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from core.classes_skills import RACES, CLASSES
    from systems.equipment_crafting import JEWELCRAFT_RECIPES

    async def craft(db, player_name, rid, baseline=False):
        account=db.create_account(player_name,'testing_pass')
        db.create_character(account,player_name,RACES[0],CLASSES[0],{
            'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
            'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
        sess=Session.__new__(Session)
        sess.account_id=account
        sess.character=Character.from_row(db.character_for_account(account))
        sess.server=SimpleNamespace(db=db,sessions=set(),parties={})
        sess.combat_mob_key=None
        log=[]
        async def send(message,*args,**kwargs):log.append(str(message))
        sess.send=send
        sess.recipe_action_seconds=lambda *args,**kwargs:0
        rec=JEWELCRAFT_RECIPES[rid]
        sess.character.room_id=rec['stations'][0]
        db.add_item(account,'jeweler_pliers',1)
        for item,quantity in rec['ingredients'].items():db.add_item(account,item,quantity)
        before={i:sess.available_recipe_item(i) for i in rec['ingredients']}
        random.seed(8123)
        if baseline:
            with patch('systems.jewelcrafting_xp_v1202.improved_jewelry_recipe_xp',
                       side_effect=lambda p,t,recipe:(p,t)):
                ok=await sess.perform_recipe(rec['name'],JEWELCRAFT_RECIPES,'jubilerstwo')
        else:
            ok=await sess.perform_recipe(rec['name'],JEWELCRAFT_RECIPES,'jubilerstwo')
        assert ok,(rid,player_name,log[-8:])
        for item,amount in rec['ingredients'].items():
            assert before[item]-sess.available_recipe_item(item)==int(amount),(rid,item)
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        p=next(int(re.search(r'Jubilerstwo: \+(\d+) XP',m).group(1))
               for m in log if re.search(r'Jubilerstwo: \+(\d+) XP',m))
        t=next(int(re.search(r'Szczypce Jubilerskie: \+(\d+) XP',m).group(1))
               for m in log if re.search(r'Szczypce Jubilerskie: \+(\d+) XP',m))
        return p,t

    async def run():
        checks=0
        with tempfile.TemporaryDirectory(prefix='sb-jewel-xp-') as tmp:
            db=Database(os.path.join(tmp,'jewel.db'))
            for rid,i in (('jewel_iron_ring',0),('cut_ruby',1)):
                regular=await craft(db,f'GemNew{i}',rid)
                historical=await craft(db,f'GemOld{i}',rid,baseline=True)
                assert regular[0]>historical[0] and regular[1]>historical[1],(rid,regular,historical)
                checks+=6
            db.conn.close()
        return checks
    return asyncio.run(run())

if __name__ == '__main__':
    print('JUBILERSTWO v12.00.2: ', run_regression(),'checks PASS')
