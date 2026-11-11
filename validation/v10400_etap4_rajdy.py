# -*- coding: utf-8 -*-
"""v104 etap 4: 14 rajdów, graph, AI, NVDA, rewards, collisions.

Uses real world bootstrap and combat AI, no production account or network.
"""
from __future__ import annotations
from collections import Counter, deque
from copy import deepcopy
from types import SimpleNamespace


def run():
    from world import dynamic_content as w
    from world.v10400_raids_12_25 import RAIDS, install
    from systems.live_olc4_boss_phases import validate_boss_phases, eligible_boss
    from systems.live_olc20_phase_tactics import boss_stage_cycle, ROLES, ELEMENTS
    from systems.live_olc21_phase_strategy import phase_setting
    from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
    from systems.boss_companions_v1281 import boss_companion_due_v1281, boss_guardian_role_v12811
    from systems.quest_reward_floor_v1020012 import quest_xp_plan
    from systems.era_npc_offers_v10300 import visible_era_quests
    from world.v10400_krainy_5001_10000 import REGIONS
    checks = 0
    def ok(value, label):
        nonlocal checks
        if not value:
            raise AssertionError(label)
        checks += 1
    counts=w.V10400_RAIDS_BUILD
    for k,v in {'raids':14,'rooms':42,'bosses':42,'quests':42,'items':42,'recipes':14}.items():
        ok(counts[k]==v,f'count {k}: {counts[k]}')
    ok(len(RAIDS)==14 and len({r[0] for r in RAIDS})==14,'unique 14 raids')
    ok(w.V10300_RAIDS_BUILD['raids']==11, 'v103 11 raids preserved')
    for slug,*_ in REGIONS:
        ok(f'v10400_{slug}_01' in w.ROOMS, 'v104 region missing')
    original_spawns=set(w.MOB_SPAWNS)
    original_boss_ids={f'v10300_{slug}_raid_boss_{s}' for slug,*_ in
                       __import__('world.v10300_era_bez_granic',fromlist=['ERAS']).ERAS for s in (1,2,3)}
    ok(original_boss_ids.issubset(w.MOB_TEMPLATES),'legacy bosses retained')
    all_new_quests=set()
    appearances=Counter()
    opposites={'north':'south','south':'north','east':'west','west':'east'}
    for n,slug,room_no,npc_no,title,mechanic,cycle in RAIDS:
        prefix=f'v10400_raid_{n:02d}'
        origin=f'v10400_{slug}_{room_no:02d}'
        npc=w.NPCS[f'v10400_{slug}_npc_{npc_no}']
        ok(w.ROOMS[origin]['exits']['east']==f'{prefix}_stage_1',f'entrance {n}')
        ok(w.ROOMS[f'{prefix}_stage_1']['exits']['west']==origin,f'free exit {n}')
        items=[f'{prefix}_{suffix}' for suffix in ('fragment','seal','relic')]
        for iid in items:ok(iid in w.ITEMS,f'item missing {iid}')
        recipe=w.CRAFT_RECIPES[f'{prefix}_relic']
        ok(recipe['output']==f'{prefix}_relic',f'relic {n}')
        ok(all(i in w.ITEMS and v>0 for i,v in recipe['ingredients'].items()),f'recipe inputs {n}')
        ok(recipe['ingredients'][f'{prefix}_fragment']==3, f'relic fragment count {n}')
        for s in (1,2,3):
            rid=f'{prefix}_stage_{s}';mid=f'{prefix}_boss_{s}';qid=f'{prefix}_raid_quest_{s}'
            all_new_quests.add(qid)
            room=w.ROOMS[rid]; boss=w.MOB_TEMPLATES[mid]; quest=w.QUESTS[qid]
            ok((rid,mid) in original_spawns,f'boss not spawned {mid}')
            ok(room['zone']==w.ROOMS[origin]['zone'],f'region mismatch {rid}')
            ok('required_level' not in room, f'room level lock {rid}')
            ok('required_level' not in quest, f'quest level lock {qid}')
            for direction, dest in room['exits'].items():
                ok(dest in w.ROOMS and w.ROOMS[dest]['exits'].get(opposites[direction])==rid,
                   f'reversible exit {rid}:{direction} -> {dest}')
            ok(quest['kind']=='kill' and quest['target']==mid and quest['needed']==1,f'quest target {qid}')
            ok(quest['giver']==npc['name'] and qid in npc['specialist_quests'],f'npc offer {qid}')
            appearances[qid]+=npc['specialist_quests'].count(qid)
            ok(quest.get('requires_quest')==(f'{prefix}_raid_quest_{s-1}' if s>1 else None),
               f'prerequisite {qid}')
            ok(eligible_boss(boss) and validate_boss_phases(boss,boss['olc_boss_phases']),
               f'validated real boss {mid}')
            ok(len(boss['olc_boss_phases'])==4,f'4 phases {mid}')
            ok(boss['max_hp']>0 and boss['damage']>0 and boss['max_hp']<(1<<63),f'64bit HP {mid}')
            ok(boss['drops'][f'{prefix}_fragment']==1.0,f'fragment boss drop {mid}')
            ok((f'{prefix}_seal' in boss['drops'])==(s==3),f'final seal {mid}')
            ok(quest['reward_items'][f'{prefix}_fragment']==1, f'fragment quest drop {qid}')
            xp=quest_xp_plan(qid,quest)
            ok(xp['character']>=200000 and xp['class_xp']>=200000 and xp['soul']>=200000,
               f'quest reward XP {qid}')
            ok(xp['profession']==0 and xp['tool']==0, f'no profession XP from fight {qid}')
            ok(all(v>=200000 for v in xp['stats'].values()),f'all stats XP {qid}')
            # Real combat phase engine, one transition at each threshold, no duplicate.
            runtime=SimpleNamespace(alive=True,hp=boss['max_hp'],adaptive_max_hp_v11330=0,
                                    v1230_boss_phase=0,engaged_by='player',combat_turn=0,
                                    boss_last_summon_turn_v1281=-1)
            for pct,phase in ((79,1),(59,2),(39,3),(19,4)):
                runtime.hp=boss['max_hp']*pct//100
                result=boss_tactics_phase_v1230(runtime,boss,now=100.0)
                ok(f'FAZA {phase}/4' in str(result),f'phase trigger {mid}:{phase} {result}')
                ok(runtime.v1230_boss_phase==phase,f'phase state {mid}:{phase}')
                ok(boss_tactics_phase_v1230(runtime,boss,now=100.0) is None,f'phase repeated {mid}:{phase}')
                ok(boss_stage_cycle(boss,phase,'olc_boss_phase_element_cycles',ELEMENTS),
                   f'element phase {mid}:{phase}')
                ok(boss_stage_cycle(boss,phase,'olc_boss_guardian_phase_roles',ROLES),
                   f'guardian role phase {mid}:{phase}')
                ok(phase_setting(boss,phase,'olc_boss_phase_tactic_intervals',None) is not None,
                   f'tactics phase {mid}:{phase}')
                role=boss_guardian_role_v12811(boss,runtime,sequence=1)
                ok(role[0] in ROLES,f'guardian actual role {mid}:{phase}')
                interval=phase_setting(boss,phase,'olc_boss_phase_guardian_intervals',0)
                runtime.combat_turn=interval
                ok(boss_companion_due_v1281(runtime,boss),f'guardian triggered {mid}:{phase}')
                runtime.combat_turn=0
            # Existing helper selects only first available raid stage for each NPC.
            visible=visible_era_quests(npc['specialist_quests'],w.QUESTS,lambda _qid:None,())
            ok(qid not in visible if s>1 else qid in visible,f'NPC visible stage 1 only {qid}')
        # Simulate completion of stages 1 and 2 for NVDA quest list.
        completed=set(f'{prefix}_raid_quest_{s}' for s in (1,2))
        class Row(dict):
            pass
        def row(qid):
            return Row(status='completed',completion_count=1) if qid in completed else None
        visible=visible_era_quests(npc['specialist_quests'],w.QUESTS,row,())
        ok(f'{prefix}_raid_quest_3' in visible,f'visible stage 3 after 2 {n}')
    ok(set(appearances)==all_new_quests and all(v==1 for v in appearances.values()),
       'every new raid quest exactly once')
    ok(len(set(room for n,*_ in RAIDS for room in [f'v10400_raid_{n:02d}_stage_1']))==14,
       'separate raid entries')
    # BFS from v103 end to all 42 rooms, no new geography gate.
    start='v10300_tron_12';visited=set(); queue=deque([start])
    while queue:
        rid=queue.popleft()
        if rid in visited or rid not in w.ROOMS:continue
        visited.add(rid)
        queue.extend(w.ROOMS[rid].get('exits',{}).values())
    ok(all(f'v10400_raid_{n:02d}_stage_{s}' in visited for n,*_ in RAIDS for s in (1,2,3)),
       'all raids reachable from v103')
    # No-op install must not duplicate spawns / offers.
    spawns_before=list(w.MOB_SPAWNS)
    offers_before={f'v10400_{slug}_npc_{npc_no}':w.NPCS[f'v10400_{slug}_npc_{npc_no}']['specialist_quests']
                   for _,slug,_,npc_no,*_ in RAIDS}
    ok(install(w.ROOMS,w.MOB_TEMPLATES,w.MOB_SPAWNS,w.NPCS,w.QUESTS,w.ITEMS,w.CRAFT_RECIPES)['raids']==0,
       'idempotent installation')
    ok(spawns_before==w.MOB_SPAWNS,'no duplicate boss spawns')
    ok(all(w.NPCS[nid]['specialist_quests']==v for nid,v in offers_before.items()),
       'no duplicate quest offers')
    # Collision must not change pre-existing catalogs.
    from world.v10400_krainy_5001_10000 import install as install_regions
    rooms={'v10300_tron_12':{'exits':{}}}; mobs={};spawns=[];npcs={};quests={};items={};recipes={}
    install_regions(rooms,mobs,spawns,npcs,quests,items,recipes,[],{},{},{},{})
    quests['v10400_raid_20_raid_quest_3']={'sentinel':True}
    original=deepcopy((rooms,mobs,spawns,npcs,quests,items,recipes))
    try:
        install(rooms,mobs,spawns,npcs,quests,items,recipes)
        raise AssertionError('accepted collision')
    except RuntimeError as e:
        ok('kolizja quests' in str(e),f'collision reason {e}')
    ok(original==(rooms,mobs,spawns,npcs,quests,items,recipes), 'prevalidation atomicity')
    return checks

if __name__=='__main__':
    print(f'V104 RAJDY 12–25: {run()} kontroli PASS',flush=True)
