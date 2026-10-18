# -*- coding: utf-8 -*-
"""End-to-end catalog invariants for v11 dungeon, profession and fleet additions."""


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.eternal_glory_world_v1100 import REGIONS
    from systems.eternal_glory_depths_v1100 import (
        DUNGEON_ROOM_IDS,DUNGEON_EP_IDS,DUNGEON_QUEST_IDS,SIGNIFICANT_FLOOR)
    from systems.eternal_glory_crafting_v1100 import (
        NEW_CHARM_IDS,PROFESSION_QUEST_IDS,PROFESSION_NAMES)
    from systems.exploration_point_values_v2322 import room_explorer_points_v2322, is_city_ep_excluded_v1002
    from systems import ocean4_v1350 as ocean
    from world.legends_v3200 import _reachable
    from data.crafting_recipes import CRAFT_RECIPES
    checks=0
    def check(ok, description):
        nonlocal checks
        if not ok:
            raise AssertionError('v11 content: '+description)
        checks+=1
    check(len(DUNGEON_ROOM_IDS)==120,'all 120 chambers')
    check(len(DUNGEON_EP_IDS)==12,'12 final landmarks')
    check(len(DUNGEON_QUEST_IDS)==24,'24 chapter quests')
    check(len(NEW_CHARM_IDS)==12,'twelve forge talismans')
    check(len(PROFESSION_QUEST_IDS)==22,'fourteen action quests')
    check(DUNGEON_ROOM_IDS <= _reachable(runtime.ROOMS),'all dungeons reachable from square')
    check(DUNGEON_QUEST_IDS | PROFESSION_QUEST_IDS <= set(runtime.QUESTS),'all quests installed')
    check(NEW_CHARM_IDS <= set(runtime.ITEMS),'all craft results installed')
    for rid in sorted(DUNGEON_ROOM_IDS):
        room=runtime.ROOMS[rid]
        check(len(room['exits'])>0,'no sealed dungeon '+rid)
        check(room['v1100_no_traps'] is True,'dungeon has no traps '+rid)
        check(not is_city_ep_excluded_v1002(room),'dungeon incorrectly marked as city '+rid)
        check(room_explorer_points_v2322(room)==(5 if rid in DUNGEON_EP_IDS else 0),'no farming EP '+rid)
        check(room['v1000_landmark']==(rid in DUNGEON_EP_IDS),'auto landmark '+rid)
        for direction,dest in room['exits'].items():
            check(dest in runtime.ROOMS,'exit exists '+rid)
    for key,zone,level,element,guide,elite,boss,places in REGIONS:
        prefix=f'v1100_vault_{key}'
        check(runtime.MOB_TEMPLATES[prefix+'_guardian']['boss'] is True,'final boss '+prefix)
        check(runtime.MOB_TEMPLATES[prefix+'_guardian']['fame_target'] is True,'Fame target '+prefix)
        check(runtime.MOB_TEMPLATES[prefix+'_guardian']['drops'][prefix+'_seal']==1,'boss drop '+prefix)
        check(runtime.QUESTS[prefix+'_quest_1']['requires_quest']==f'v1100_eg_{key}_quest_2','story sequence '+prefix)
        check(runtime.QUESTS[prefix+'_quest_2']['requires_quest']==prefix+'_quest_1','story end '+prefix)
        check(runtime.QUESTS[prefix+'_quest_2']['target']==prefix+'_guardian','true kill quest '+prefix)
        check(sum(1 for room,mob in runtime.MOB_SPAWNS if mob==prefix+'_guardian')==1,'final boss spawned '+prefix)
        recipe=CRAFT_RECIPES[f'v1100_artifact_{key}']
        check(recipe['ingredients'][f'v1100_eg_{key}_relic']==2,'legit crafting materials '+prefix)
        check(recipe['output'] in runtime.ITEMS,'craft output exists '+prefix)
        check(recipe['profession_xp']>0 and recipe['tool_xp']>0,'material-scaled craft XP '+prefix)
    for idx,profession in enumerate(PROFESSION_NAMES):
        qid=f'v1100_craft_quest_{idx:02d}'
        quest=runtime.QUESTS[qid]
        check(quest['target']==profession,'correct profession event '+qid)
        check(quest['kind']=='profession_action','working event category '+qid)
        check(any(qid in npc.get('specialist_quests',()) for npc in runtime.NPCS.values()),'quest giver actually offers '+qid)
    for key in ('reef','maelstrom','storm','abyss'):
        eid='v1100_navy_'+key
        check(eid in ocean.ENEMIES,'navy enemy installed '+eid)
        check(ocean.MATERIALS[eid] in runtime.ITEMS,'navy reward item '+eid)
    from systems.eternal_glory_story_v1100 import CHAPTER_IDS, FINAL_ARTIFACT_ID
    check(FINAL_ARTIFACT_ID in runtime.ITEMS,'final prize created')
    for idx,qid in enumerate(CHAPTER_IDS):
        q=runtime.QUESTS[qid]
        check(q['requires_quest'] in runtime.QUESTS,'story sequence exists '+qid)
        check(q['target'] in (runtime.MOB_TEMPLATES if q['kind']=='kill' else runtime.ITEMS),'story objective exists '+qid)
        check(any(qid in npc.get('specialist_quests',()) for npc in runtime.NPCS.values()),'story NPC offers '+qid)
    check(runtime.QUESTS[CHAPTER_IDS[-1]]['reward_items']=={FINAL_ARTIFACT_ID:1},'real legendary final reward')
    from systems.eternal_glory_class_guild_v1100 import CLASS_QUEST_IDS,TEAM_CONTRACT_IDS
    from core.classes_skills import CLASSES as CLASSES_22
    check(len(CLASS_QUEST_IDS)==66 and len(TEAM_CONTRACT_IDS)==12,'78 class and team quests')
    check(CLASS_QUEST_IDS | TEAM_CONTRACT_IDS <= set(runtime.QUESTS),'all class and team quests installed')
    by_class = {row[0] for row in CLASSES_22}
    for qid in CLASS_QUEST_IDS:
        q=runtime.QUESTS[qid]
        check(q['required_class'] in by_class,'only playable classes '+qid)
        check(q['requires_quest'] in runtime.QUESTS,'real prerequisite '+qid)
        check(q['target'] in runtime.MOB_TEMPLATES,'real kill target '+qid)
        check(q['kind']=='kill' and not q['repeatable'],'no free class reward '+qid)
        check(any(qid in npc.get('specialist_quests',()) for npc in runtime.NPCS.values()),'class mentor offers '+qid)
    lyra=next(n for n in runtime.NPCS.values() if n.get('name')=='Koordynatorka Kontraktów Lyra')
    for qid in TEAM_CONTRACT_IDS:
        q=runtime.QUESTS[qid]
        check(qid in lyra.get('specialist_quests',()),'party NPC offers '+qid)
        check(q['kind']=='party_contract' and q['minimum_party_size']==2,'real party handler '+qid)
        check(q['repeat_cooldown']==12*3600,'no instant repeated reward '+qid)
    for rid,npc in runtime.NPCS.items():
        if rid.startswith('v1100_'):
            check(sum(1 for other in runtime.NPCS.values() if other.get('room')==npc.get('room'))==1,'unique npc room '+rid)
    return checks

if __name__=='__main__':
    print('V11 DUNGEONS, CRAFT, OCEAN',run_regression(),'PASS')
