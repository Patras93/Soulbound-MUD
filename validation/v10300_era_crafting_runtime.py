# -*- coding: utf-8 -*-
"""33 real Era 103 crafting redemptions, isolated SQLite (no production data)."""
from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace


def run():
    import server  # normal gameplay bootstrap and source registry install
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from core.classes_skills import CLASSES, RACES
    from data.crafting_recipes import CRAFT_RECIPES
    from systems.content_registry import QUESTS
    from systems.equipment_crafting import CRAFT_RECIPES as GAME_CRAFT_RECIPES
    from core.bootstrap_economy_professions import tool_tier, required_tool_tier_for_level

    async def inner():
        checks = 0
        with tempfile.TemporaryDirectory(prefix='sb-103-craft-') as tmp:
            db = Database(str(Path(tmp)/'crafter.sqlite'))
            aid = db.create_account('era103_crafter','private_testing_pass')
            db.create_character(aid, 'CrafterEra103', RACES[0],CLASSES[0],{
                'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
                'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            sess = Session.__new__(Session)
            sess.account_id=aid
            sess.character=Character.from_row(db.character_for_account(aid))
            sess.server=SimpleNamespace(db=db,sessions=set(),parties={})
            sess.combat_mob_key=None
            messages=[]
            async def send(text,*args,**kwargs):messages.append(str(text))
            sess.send=send
            sess.recipe_action_seconds=lambda *args,**kwargs:0
            candidates=[(rid,rec) for rid,rec in CRAFT_RECIPES.items() if rid.startswith('v10300_')]
            assert len(candidates)==33, len(candidates)
            assert CRAFT_RECIPES is GAME_CRAFT_RECIPES, 'craft command uses another registry'
            checks+=2
            for rid,recipe in sorted(candidates):
                assert recipe['output'] in server.ITEMS, f'{rid}: item missing in gameplay'
                profession=sess.recipe_profession_name(CRAFT_RECIPES,recipe)
                tool_type,tool_id,_=sess.recipe_tool_info(CRAFT_RECIPES,recipe)
                required=int(recipe['min_profession_level'])
                # These recipes must remain obtainable when admin unsets the hard level cap.
                db.profession(aid,profession)
                db.save_profession(aid,profession,max(required,5000),0,0)
                db.tool(aid,tool_type)
                db.save_tool(aid,tool_type,max(required,5000),0,0)
                assert tool_tier(max(required,5000))>=required_tool_tier_for_level(required),rid
                if db.item_qty(aid,tool_id)<1:db.add_item(aid,tool_id,1)
                for item,quantity in recipe['ingredients'].items():
                    db.add_item(aid,item,int(quantity)+2)
                sess.character.room_id=recipe['stations'][0]
                before={item:sess.available_recipe_item(item) for item in recipe['ingredients']}
                output_before=sum(db.item_qty(aid,row['item_id']) for row in db.inventory(aid) if row['item_id']==recipe['output'] or row['item_id'].endswith('_'+recipe['output'])) + db.storage_qty(aid,'craftbox',recipe['output'])
                messages.clear()
                succeeded=await sess.perform_recipe(recipe['name'],CRAFT_RECIPES,'rzemiosło')
                assert succeeded,(rid,messages[-15:])
                output_after=sum(db.item_qty(aid,row['item_id']) for row in db.inventory(aid) if row['item_id']==recipe['output'] or row['item_id'].endswith('_'+recipe['output'])) + db.storage_qty(aid,'craftbox',recipe['output'])
                assert output_after>output_before,(rid,'output not added',str(messages[-12:]))
                checks+=4
                for item,quantity in recipe['ingredients'].items():
                    assert before[item]-sess.available_recipe_item(item)==quantity,(rid,item,'ingredients not consumed',before[item],sess.available_recipe_item(item))
                    checks+=1
            assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            checks+=1
            db.conn.close()
        return checks
    return asyncio.run(inner())

if __name__=='__main__':
    print(f'ERA 103 CRAFT REAL SQLITE: {run()} checks PASS',flush=True)
