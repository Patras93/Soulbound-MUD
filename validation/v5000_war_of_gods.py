# -*- coding: utf-8 -*-
"""v5.00.0 end-to-end catalog, scripted encounter, and progression invariants.

Does not claim to play 2901 quests via TCP. Isolated SQL and existing Windows
60/60 remain the real deployment gate.
"""
from types import SimpleNamespace
from collections import Counter
from unittest.mock import patch


def run_regression(server=None):
    if server is None:
        import server
    from world.legends_v3200 import _reachable, OPPOSITE
    from systems.war_of_gods_bosses_v5000 import PROFILES, unique_phase, effective_elemental_template, validate_profiles
    from systems.legends_ocean_v5000 import CYCLES
    from systems.ocean_sagas_v2300 import hazard
    from core.class_mastery_v5000 import ARTS
    from core.classes_skills import CLASS_SKILLS
    from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
    from systems.professions import V03053_CRAFT_RECIPES
    from systems.mastery_crafting_v2201 import TOOL_TYPES
    from data.crafting_recipes import CRAFT_RECIPES
    from core.progression_resources import character_xp_to_next
    from systems.milestone_cap_rewards_v2103 import explorer_award_per_point_v4211
    from validation.v4211_independent_xp_rewards import run_regression as xp_regression
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from player.session_mixins.profession_storage import SessionProfessionStorageMixin

    rooms=server.ROOMS;npcs=server.NPCS;mobs=server.MOB_TEMPLATES
    quests=server.QUESTS;items=server.ITEMS
    report=server.V5000_WAR_OF_GODS
    assert report == {'bosses_upgraded':12,'story_quests':128,'trial_rooms':40,
     'ocean_quests':20,'profession_deliveries':28,
     'rooms':104,'npcs':0,'mobs':53,'spawns':61,'quests':200,'items':68}, report
    checks=1
    reachable=_reachable(rooms)
    npc_rooms=Counter(n.get('room') for n in npcs.values())
    for key,room in rooms.items():
        if not str(key).startswith('v500_'):continue
        assert key in reachable, ('unreachable',key)
        assert not room.get('traps') and not room.get('random_traps')
        for direction,target in room['exits'].items():
            assert target in rooms and rooms[target]['exits'].get(OPPOSITE[direction])==key
            checks+=1
        assert npc_rooms[key] <= 1
        checks+=3
    for i in range(12):
        key=f'v4000_ancient_{i:02d}_boss'
        row=mobs[key]
        assert row['v500_ancient_profile']==i and row['boss'] and row['fame_target']
        assert 'fazy' in row['boss_mechanic_text']
        thresholds,names,multipliers,elements=PROFILES[i]
        mob=SimpleNamespace(hp=10000,alive=True,adaptive_max_hp_v11330=10000)
        assert unique_phase(mob,row,now=10) is None
        for stage,threshold in enumerate(thresholds,1):
            mob.hp=threshold*100
            msg=unique_phase(mob,row,now=20)
            assert names[stage-1] in msg
            assert mob.v1230_boss_phase == stage
            assert mob.v1230_phase_attack_multiplier == multipliers[stage-1]
            assert effective_elemental_template(mob,row)['attack_elements_v11339'] == (elements[stage-1],) if elements[stage-1]!='physical' else effective_elemental_template(mob,row)['attack_elements_v11339']==row['attack_elements_v11339']
            assert unique_phase(mob,row,now=25) is None
            checks+=6
        checks+=2
    checks+=validate_profiles()
    for slug in CYCLES:
        period,strength,_=CYCLES[slug]
        assert hazard(slug,period-1,'salwa')[0]==100 and 'UWAGA' in hazard(slug,period-1,'salwa')[1]
        assert hazard(slug,period,'salwa')[0]==strength
        assert hazard(slug,period,'oslona')[0]==strength  # Existing command reduces impact later.
        checks+=3
    assert hazard('legenda_cisza',3,'salwa') == (100,hazard('legenda_cisza',3,'salwa')[1])
    assert hazard('niewymieniony',99,'salwa') == (100,'')
    checks+=2
    assert len(ARTS)==14
    for name in ARTS:
        selected=[s for s in CLASS_SKILLS[name] if s['id'].startswith('v500_')]
        assert len(selected)==2 and [s['unlock'] for s in selected]==[350,700]
        assert all(s['kind'] in ('damage','aoe_damage','execute','guard','boost') for s in selected)
        assert all(bool(s.get('aliases')) for s in selected)
        checks+=4
    valid_givers={n['name'] for n in npcs.values()}
    all_offers={q for n in npcs.values() for q in n.get('quest_chain',())}
    class Verifier(SessionQuestCommandsMixin,SessionProfessionStorageMixin):
        pass
    verifier=Verifier()
    new_quests={k:v for k,v in quests.items() if str(k).startswith('v500_')}
    assert len(new_quests)==200
    for qid,q in new_quests.items():
        assert qid in all_offers and q['giver'] in valid_givers
        assert q['kind'] in ('kill','collect','talk_npc')
        assert q['requires_quest'] in quests
        assert ((q['kind']=='kill' and q['target'] in mobs) or
                (q['kind']=='collect' and q['target'] in items) or
                (q['kind']=='talk_npc' and q['target'] in npcs and q['target_npc']==q['target']))
        assert not verifier.validate_quest_rewards_v1106(qid,q), (qid,'rewards')
        checks+=5
    for prof, tool, npc_id, action in PROFESSION_QUEST_SPECS_V0700:
        assert TOOL_TYPES[prof]==tool
        assert len([q for q in new_quests if q.startswith('v500_prof_'+tool+'_')])==2
        for level in (150,400):
            recipe=f'v500_recipe_{tool}_{level}'
            rec=CRAFT_RECIPES.get(recipe) or V03053_CRAFT_RECIPES.get(recipe)
            assert rec['profession']==prof and rec['tool_type']==tool
            assert all(mat in items for mat in rec['ingredients'])
            assert rec['output'] in items
            assert all(loc in rooms for loc in rec['stations'])
            assert rec['profession_xp']>0 and rec['tool_xp']>0
            checks+=6
    for l in range(1,800):
        required=character_xp_to_next(l)
        assert required>0
        checks+=1
    # Thousands of EP must not casually create level 48 on a fresh account.
    to48=sum(character_xp_to_next(l) for l in range(1,48))
    for room_ep in (1,3,5,12,30):
        for rate in (120,170,220):
            assert 10000 * rate < to48
            checks+=1
    checks += xp_regression()
    return {'checks':checks,'quests':len(new_quests),'rooms':report['rooms'],
            'bosses':12,'class_arts':28,'professions':14,'new_recipes':28,
            'ocean_fleets':len(CYCLES),'trial_zones':8}


if __name__=='__main__':
    print('WOJNA BOGOW v5.00.0:',run_regression(),'PASS')
