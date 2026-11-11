# -*- coding: utf-8 -*-
"""Real recipe execution for all 14 existing tools, isolated SQLite, no live saves."""
from __future__ import annotations


def run_regression():
    import asyncio
    import os
    import tempfile
    from types import SimpleNamespace
    import server
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from core.classes_skills import CLASSES, RACES
    from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
    from systems.professions import V03053_CRAFT_RECIPES
    from data.crafting_recipes import CRAFT_RECIPES

    async def inner():
        checks=0
        with tempfile.TemporaryDirectory(prefix='sb-v4000-craft-') as td:
            db=Database(os.path.join(td,'craft.sqlite'))
            aid=db.create_account('v4000_crafter','testing_pass')
            db.create_character(aid,'CraftTester',RACES[0],CLASSES[0],{
                'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
                'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            sess=Session.__new__(Session)
            sess.account_id=aid
            sess.character=Character.from_row(db.character_for_account(aid))
            sess.server=SimpleNamespace(db=db,sessions=set(),parties={})
            sess.combat_mob_key=None
            messages=[]
            async def send(message,*args,**kwargs):messages.append(str(message))
            sess.send=send
            sess.recipe_action_seconds=lambda *args,**kwargs:0
            db.add_item(aid,'soul_shard',100)
            for prof,tool,_,_ in PROFESSION_QUEST_SPECS_V0700:
                rid=f'v4000_craft_{tool}_1'
                recipes=V03053_CRAFT_RECIPES if rid in V03053_CRAFT_RECIPES else CRAFT_RECIPES
                recipe=recipes[rid]
                kind,tool_item,name=sess.recipe_tool_info(recipes,recipe)
                if kind!=tool or tool_item not in server.ITEMS:
                    raise AssertionError('v4 wrong tool '+prof)
                db.add_item(aid,tool_item,1)
                sess.character.room_id=recipe['stations'][0]
                messages.clear()
                if prof in ('Krawiectwo','Garbarstwo','Stolarstwo'):
                    finished=await sess.v03053_craft(prof,recipe['name'])
                else:
                    finished=await sess.perform_recipe(recipe['name'],recipes,'rzemiosło')
                if not finished:
                    raise AssertionError(f'{prof}: craft rejected: '+repr(messages[-8:]))
                if db.item_qty(aid,recipe['output'])<=0 and not any(r['item_id'].startswith(recipe['output']) for r in db.inventory(aid)):
                    raise AssertionError(f'{prof}: item not produced')
                checks+=4
            integrity=db.conn.execute('PRAGMA integrity_check').fetchone()[0]
            assert integrity=='ok',integrity
            checks+=1
            db.conn.close()
        return checks
    return asyncio.run(inner())

if __name__=='__main__':
    print('CRAFTING v4.00.0:',run_regression(),'checks PASS')
