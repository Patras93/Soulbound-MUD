# -*- coding: utf-8 -*-
"""v4.00.0 additive-content audit: actual runtime, SQLite quests, recipes, tactics."""
from __future__ import annotations
from validation.release_contracts import release_valid


def run_regression(server=None):
    if server is None:
        import server
    from core.bootstrap_economy_professions import VERSION
    from config.balance import ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310
    from world.legends_v3200 import _reachable
    from world.legends_v3100 import OPPOSITE
    from world.imperium_v4000 import SEA_ROUTES, PRADAWNI, CRAFT_STAGES, PROF_STAGES
    from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
    from systems.professions import V03053_CRAFT_RECIPES
    from data.crafting_recipes import CRAFT_RECIPES
    from systems.companion_tactics_v4000 import tactical_response, FINISHERS, BREAKERS, GUARDIANS
    from systems.mercenary_specialists_v1240 import SPECIALISTS, specialist_attack_v1240
    from player.session_mixins.crafting import SessionCraftingMixin
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from player.session_mixins.profession_storage import SessionProfessionStorageMixin
    from systems.mastery_crafting_v2201 import TOOL_TYPES
    from systems import ocean4_v1350 as navy
    from types import SimpleNamespace
    from collections import Counter

    checks=0
    def ck(condition, why):
        nonlocal checks
        if not condition:raise AssertionError('v4.00.0: '+why)
        checks+=1
    stats=server.V4000_IMPERIUM_STATS
    ck(stats=={'rooms':216,'npcs':49,'mobs':66,'spawns':103,'quests':367,'items':119,
               'common_recipes':55,'profession_recipes':15},f'content totals: {stats}')
    ck(release_valid(VERSION, '4.00.0'),'incorrect active version')
    ck(ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310==10,'lost XP10 multiplier')
    ck(len(SEA_ROUTES)==5 and len(PRADAWNI)==12,'missing systems')
    ck(len(PROF_STAGES)==8 and len(CRAFT_STAGES)==5,'missing stages')
    rooms,npcs,mobs,quests,items=server.ROOMS,server.NPCS,server.MOB_TEMPLATES,server.QUESTS,server.ITEMS
    reachable=_reachable(rooms)
    additions={rid:r for rid,r in rooms.items() if rid.startswith('v4000_')}
    ck(len(additions)==216,'new world rooms')
    for rid,room in additions.items():
        ck(rid in reachable, f'unreachable room {rid}')
        ck(not room.get('traps') and not room.get('random_traps'),f'trapped room {rid}')
        for direction,destination in room['exits'].items():
            ck(destination in rooms, f'invalid direction {rid}:{direction}')
            ck(rooms[destination]['exits'].get(OPPOSITE[direction])==rid,f'one-way direction {rid}:{direction}')
    new_npcs={key:value for key,value in npcs.items() if key.startswith('v4000_')}
    ck(len(new_npcs)==49,'NPC count')
    rooms_owned=Counter(npc['room'] for npc in npcs.values())
    for npc_id,npc in new_npcs.items():
        ck(npc['room'] in reachable, f'unreachable NPC {npc_id}')
        ck(rooms_owned[npc['room']]==1,f'NPC shares a room: {npc_id}')
        ck(bool(npc.get('quest_chain')),f'NPC without tasks: {npc_id}')
    authored_ids = {f'v4000_old_{i:02d}_guardian' for i in range(32)}
    authored_ids |= {f'v4000_sea_{slug}_{suffix}' for slug,*_ in SEA_ROUTES
                     for suffix in ('corsair','admiral')}
    authored_ids |= {f'v4000_ancient_{i:02d}_{suffix}' for i in range(12)
                     for suffix in ('sentry','boss')}
    ck(len(authored_ids)==66 and authored_ids <= set(mobs),
       'a manually authored v4 mob was removed')
    # The full audit can also create procedural variants of these authored
    # mobs, so count canonical IDs rather than all keys with this prefix.

    ck(len([m for m in mobs if m.startswith('v4000_ancient_') and m.endswith('_boss')])==12,'boss count')
    for rid,mid in server.MOB_SPAWNS:
        if str(mid).startswith('v4000_'):
            ck(rid in reachable and mid in mobs,f'mob unreachable: {mid}')
    for i in range(12):
        mob=mobs[f'v4000_ancient_{i:02d}_boss']
        ck(bool(mob['boss']) and bool(mob['world_boss']),'superboss flag')
        ck(bool(mob['v017_boss_phases']) and len(mob['attack_elements_v11339'])==2,'real phases')
        ck(bool(mob['fame_target']) and mob['quest_target']==f'v4000_ancient_{i:02d}_boss','Fame target')
    for slug,*_ in SEA_ROUTES:
        code=f'imperium_{slug}'
        ck(code in navy.ENEMIES and navy.MATERIALS[code] in items, f'missing fleet {code}')
    valid_givers={str(n.get('name') or '') for n in npcs.values()}
    all_offers={str(q) for n in npcs.values() for q in n.get('quest_chain',())}
    total=0
    class RealVerifier(SessionQuestCommandsMixin,SessionProfessionStorageMixin): pass
    verifier=RealVerifier()
    for key,quest in quests.items():
        if not key.startswith('v4000_') or key.startswith('v4000_craft_'):
            continue
        total+=1
        ck(quest.get('giver') in valid_givers,f'missing giver {key}')
        ck(key in all_offers or key.startswith('v4000_prof_') and key in all_offers,f'quest unavailable {key}')
        ck(not verifier.validate_quest_rewards_v1106(key,quest),f'bad reward {key}')
        prior=quest.get('requires_quest')
        ck(not prior or prior in quests,f'missing predecessor {key}')
        kind,target=quest['kind'],quest.get('target')
        ck(kind in ('kill','collect','talk_npc','profession_action'),f'unknown quest kind {key}')
        ck((kind=='kill' and target in mobs) or (kind=='collect' and target in items) or
           (kind=='talk_npc' and target in npcs and quest.get('target_npc')==target) or
           (kind=='profession_action' and target in TOOL_TYPES),f'bad quest target {key}')
        ck(int(quest['needed'])>0,f'zero target {key}')
        if kind=='profession_action':
            ck(quest.get('specialist_tool_type')==TOOL_TYPES[target],f'wrong action tool {key}')
    ck(total==367,f'{total} quests instead of 367')
    recipe_ids=[key for key in list(CRAFT_RECIPES)+list(V03053_CRAFT_RECIPES) if key.startswith('v4000_craft_')]
    ck(len(recipe_ids)==70,f'craft recipes {len(recipe_ids)}')
    for rid in recipe_ids:
        recipe=CRAFT_RECIPES.get(rid) or V03053_CRAFT_RECIPES.get(rid)
        ck(recipe['profession'] in TOOL_TYPES,f'bad craft profession {rid}')
        ck(recipe['tool_type']==TOOL_TYPES[recipe['profession']],f'changed existing tool type {rid}')
        ck(recipe['output'] in items and all(mat in items for mat in recipe['ingredients']),f'craft item not registered {rid}')
        ck(all(s in rooms for s in recipe['stations']),f'non-existent station {rid}')
        ck(int(recipe['profession_xp'])>0 and int(recipe['tool_xp'])>0,'craft XP')
        engine=SessionCraftingMixin()
        kind,tool_id,label=engine.recipe_tool_info(CRAFT_RECIPES if rid in CRAFT_RECIPES else V03053_CRAFT_RECIPES, recipe)
        ck(kind==recipe['tool_type'] and tool_id in items and bool(label),f'unusable existing tool {rid}')
    ck(len(PROFESSION_QUEST_SPECS_V0700)==14,'changed profession roster')
    ck(len(SPECIALISTS)==22, '22 mercenary tactical profiles required')
    ck(not (FINISHERS & BREAKERS or FINISHERS & GUARDIANS or BREAKERS & GUARDIANS),
       'tactical role families must be disjoint')
    ck(set(SPECIALISTS)==set(FINISHERS|BREAKERS|GUARDIANS), 'all 22 combat roles require tactics')
    for role in SPECIALISTS:
        for boss in (True,False):
            for fraction in (1.0,.75,.49,.24):
                multiplier,_=tactical_response(role,boss,round(10000*fraction),10000,3)
                ck(multiplier>=1.0,f'negative ally modifier {role}')
        enemy=SimpleNamespace(hp=200,max_hp=1000)
        factor,tech,combo=specialist_attack_v1240(enemy,19,role,'magic',600,12345,boss=True)
        ck(factor>=1.0 and bool(tech),f'incorrect combat role: {role}')
    from validation.v2400_real_quest_events import run_event_coverage
    actions={qid:q for qid,q in quests.items() if qid.startswith('v4000_')}
    event_report=run_event_coverage(actions)
    ck(event_report['errors']==[] and event_report['executed']==281 and
       event_report['accepted_via_handler']==367, 'real SQLite quest event regression')
    checks+=event_report['checks']
    return {'checks':checks,'rooms':216,'npcs':49,'quests':total,'bosses':12,'ocean_routes':5,'recipes':len(recipe_ids),'professions':14}

if __name__=='__main__':
    print('IMPERIUM v4.00.0:',run_regression(),'PASS')
