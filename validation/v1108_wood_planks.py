# -*- coding: utf-8 -*-
"""v11.00.8: real recipe ownership, command routing, shops and help for planks."""
from __future__ import annotations
import asyncio
import server
from core.bootstrap_economy_professions import VERSION
from core.command_catalog import COMMAND_CATALOG
from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command
from player.session_mixins.crafting import SessionCraftingMixin
from systems.equipment_crafting import CRAFT_RECIPES
from systems.professions import V03053_CRAFT_RECIPES

PLANK_IDS = ('oak_plank','ash_plank','yew_plank','ironwood_plank','spiritwood_plank')

class _Sim(SessionCraftingMixin):
    def __init__(self):
        self.sent=[]
        self.actions=[]
    async def send(self, s):
        self.sent.append(str(s))
    async def perform_recipe(self, query, recipes, action_name):
        pair = next(((k, v) for k, v in recipes.items() if k == query), None)
        if pair is None:
            return False
        k, recipe = pair
        self.actions.append((k, self.recipe_profession_name(recipes,recipe),
                             self.recipe_tool_info(recipes,recipe),
                             recipe['stations'],action_name))
        return True
    def max_recipe_crafts_v03114(self, recipe):
        return 2
    def normalize_description_query(self, value):
        from network.protocol_gameplay_utils import normalize_lookup_text
        return normalize_lookup_text(value)

def run_regression():
    checks=0
    def ck(ok,why):
        nonlocal checks
        checks+=1
        if not ok: raise AssertionError('DESKI DRWALSTWO v11.00.8: '+why)
    ck(VERSION == server.VERSION and VERSION in ('11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18',), 'release identity')
    ck('obrabiaj' in COMMAND_REGISTRY and COMMAND_REGISTRY['obrabiaj'][0]=='process_wood_v1108', 'command handler')
    ck(resolve_session_command('deski')=='obrabiaj', 'short alias')
    ck(not COMMAND_CATALOG.conflicts(), 'command catalog clean')
    ck('obrabiaj' in server.HELP_TOPICS and 'obrabiaj' in server.HELP_TOPIC_ALIASES.values(), 'help alias')
    for k in PLANK_IDS:
        recipe=CRAFT_RECIPES[k]
        ck(recipe['profession']=='Drwalstwo', k+' profession')
        ck(recipe['tool_type']=='woodcutting',k+' tool type')
        ck(recipe['tool_item_id']=='saw',k+' saw item')
        ck('lumberjack_camp' in recipe['stations'] and 'forge' not in recipe['stations'],k+' lumberjack room')
        ck(all(v!=k for v in ('forge',) for st in recipe['stations']),k+' not forge')
        ck(recipe['output']==k and sum(recipe['ingredients'].values())==2,k+' stable inputs/outputs')
        ck(SessionCraftingMixin.recipe_profession_name(None,CRAFT_RECIPES,recipe)=='Drwalstwo',k+' XP profession')
        ck(SessionCraftingMixin.recipe_tool_info(None,CRAFT_RECIPES,recipe)[0]=='woodcutting',k+' XP tool')
    extra=V03053_CRAFT_RECIPES['plank']
    ck(extra['profession']=='Drwalstwo', 'treated board profession')
    ck(extra['tool_type']=='woodcutting' and extra['tool_item_id']=='saw','treated saw')
    ck(extra['stations']==('lumberjack_camp',),'treated station')
    ck(extra['output']=='treated_plank' and extra['ingredients']=={'birch_log':2},'treated stable output')
    ck(any(k.startswith('carp_') for k,v in V03053_CRAFT_RECIPES.items() if v.get('profession')=='Stolarstwo'), 'finished carpenter goods retained')
    ck(all(r.get('profession')!='Drwalstwo' for k,r in CRAFT_RECIPES.items() if k.endswith('_ingot')), 'ingots remain smithing')
    for key in (*PLANK_IDS,'plank'):
        obj=_Sim()
        asyncio.run(obj.process_wood_v1108(key))
        ck(len(obj.actions)==1 and obj.actions[0][1]=='Drwalstwo', key+' routed forestry')
        ck(obj.actions[0][2][0]=='woodcutting' and obj.actions[0][2][1]=='saw',key+' routed saw')
    for name, wanted in (('deska dębowa','oak_plank'), ('obrobiona deska','plank')):
        obj=_Sim()
        asyncio.run(obj.process_wood_v1108(name))
        ck(len(obj.actions)==1 and obj.actions[0][0]==wanted, 'Polish wood name '+name)
    obj=_Sim()
    asyncio.run(obj.show_recipes('drwalnictwo'))
    ck(any('RECEPTURY DRWALNICTWA' in x for x in obj.sent), 'alternate profession label')
    obj=_Sim()
    asyncio.run(obj.process_wood_v1108('max oak_plank'))
    ck(len(obj.actions)==2 and all(x[0]=='oak_plank' for x in obj.actions), 'bulk wood')
    for text in ('','lista','nieistniejaca deska'):
        obj=_Sim()
        asyncio.run(obj.process_wood_v1108(text))
        ck(bool(obj.sent) and not obj.actions, 'help and unknown wood '+text)
    obj=_Sim()
    asyncio.run(obj.show_recipes('drwalstwo'))
    output='\n'.join(obj.sent)
    for k in PLANK_IDS:
        ck(CRAFT_RECIPES[k]['name'] in output, k+' visible in wood recipes')
    ck(extra['name'] in output, 'treated board visible in forestry')
    ck('DRWALNICTWA' in output, 'forestry header')
    obj=_Sim()
    asyncio.run(obj.show_recipes('kowalstwo'))
    smith='\n'.join(obj.sent)
    ck(not any(line.startswith(CRAFT_RECIPES[k]['name']+'.') for line in obj.sent for k in PLANK_IDS), 'no plank recipes listed under smithing')
    ck('Żelazna sztabka' in smith, 'smithing ingot kept')
    print('DESKI / DRWALSTWO v11.00.8:',checks,'checks PASS')
    return checks

if __name__=='__main__': run_regression()
