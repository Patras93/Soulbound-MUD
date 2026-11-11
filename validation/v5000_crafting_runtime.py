# -*- coding: utf-8 -*-
"""Execute all 28 new recipes in a private real SQLite Database."""
import asyncio
import tempfile
from pathlib import Path
from types import SimpleNamespace


def run_regression():
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
        with tempfile.TemporaryDirectory(prefix='sb-v500-craft-') as td:
            db=Database(str(Path(td)/'craft.sqlite'))
            aid=db.create_account('v500_crafter','testing_pass')
            db.create_character(aid,'CraftTesterV5',RACES[0],CLASSES[0],{
                'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
                'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            sess=Session.__new__(Session)
            sess.account_id=aid
            sess.character=Character.from_row(db.character_for_account(aid))
            sess.server=SimpleNamespace(db=db,sessions=set(),parties={})
            sess.combat_mob_key=None
            messages=[]
            async def send(message,*args,**kwargs): messages.append(str(message))
            sess.send=send
            sess.recipe_action_seconds=lambda *args,**kwargs:0
            for prof,tool,_,_ in PROFESSION_QUEST_SPECS_V0700:
                db.profession(aid,prof);db.save_profession(aid,prof,720,0,0)
                db.tool(aid,tool);db.save_tool(aid,tool,720,0,0)
                for level in (150,400):
                    rid=f'v500_recipe_{tool}_{level}'
                    recipes=V03053_CRAFT_RECIPES if rid in V03053_CRAFT_RECIPES else CRAFT_RECIPES
                    recipe=recipes[rid]
                    kind,tool_item,_=sess.recipe_tool_info(recipes,recipe)
                    assert kind==tool and tool_item in server.ITEMS,(rid,tool_item)
                    if db.item_qty(aid,tool_item)==0:db.add_item(aid,tool_item,1)
                    for item,amount in recipe['ingredients'].items():
                        db.add_item(aid,item,int(amount)+2)
                    sess.character.room_id=recipe['stations'][0]
                    before={item:db.item_qty(aid,item) for item in recipe['ingredients']}
                    previous=db.item_qty(aid,recipe['output'])
                    messages.clear()
                    if prof in ('Krawiectwo','Garbarstwo','Stolarstwo'):
                        done=await sess.v03053_craft(prof,recipe['name'])
                    else:
                        done=await sess.perform_recipe(recipe['name'],recipes,'rzemiosło')
                    assert done,(rid,messages[-12:])
                    assert db.item_qty(aid,recipe['output'])>previous,(rid,'missing output')
                    for item,n in recipe['ingredients'].items():
                        after=db.item_qty(aid,item)
                        assert before[item]-after==int(n),(rid,'ingredient not consumed',item,before[item],after)
                        checks+=1
                    checks+=3
            assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            checks+=1
            db.conn.close()
        return checks
    return asyncio.run(inner())

if __name__=='__main__':
    print(f'v5.00.0 CRAFT REAL SQLITE: {run_regression()} checks PASS')
