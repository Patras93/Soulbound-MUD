# -*- coding: utf-8 -*-
"""Izolowane testy rajdów v103: graf, NPC, quest chain, fazy bossów, łupy."""
from __future__ import annotations
from collections import deque
from types import SimpleNamespace


def run():
    checks=0
    def ok(condition,message):
        nonlocal checks
        assert condition,message
        checks+=1
    from world.v10300_era_bez_granic import install as era_install, ERAS
    from world.v10300_era_raids import install as raid_install
    from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
    from systems.live_olc4_boss_phases import validate_boss_phases,eligible_boss
    rooms={'v3000_eternal_6':{'exits':{}}};mobs={};spawns=[];npcs={};quests={};items={'steel_ingot': {'name': 'Sztabka stali', 'type': 'craft_material'}};recipes={};areas=[]
    era_install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    result=raid_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    for field,count in [('raids',11),('rooms',33),('bosses',33),('quests',33),('items',22),('recipes',11)]:
        ok(result[field]==count,f'count {field}')
    ok(raid_install(rooms,mobs,spawns,npcs,quests,items,recipes)['raids']==0,'idempotent reinstall')
    boss_spawns=set(spawns)
    for slug,zone,low,high,*_ in ERAS:
        prefix=f'v10300_{slug}'
        npc=npcs[f'{prefix}_npc_2']
        ok(rooms[f'{prefix}_09']['exits']['east']==f'{prefix}_raid_1','raid entry')
        ok(rooms[f'{prefix}_raid_1']['exits']['west']==f'{prefix}_09','raid return')
        for i in (1,2,3):
            rid=f'{prefix}_raid_{i}';mid=f'{prefix}_raid_boss_{i}';qid=f'{prefix}_raid_quest_{i}'
            ok((rid,mid) in boss_spawns,'raid boss spawn')
            ok(quests[qid]['target']==mid,'quest combat target')
            ok(quests[qid]['giver']==npc['name'],'NPC quest giver')
            ok(qid in npc['specialist_quests'],'NPC offers quest')
            ok(quests[qid].get('requires_quest')==(f'{prefix}_raid_quest_{i-1}' if i>1 else None), 'quest order')
            ok(rooms[rid]['generator_level']>=low,'level region')
            boss=mobs[mid]
            ok(eligible_boss(boss),'boss eligible for phase AI')
            ok(validate_boss_phases(boss,boss['olc_boss_phases']),'boss phases valid')
            ok(len(boss['olc_boss_phases'])==4,'4 phases')
            ok(boss['class_xp_reward']>=200000 and boss['stat_reward']>=200000,'XP')
            ok(boss['olc_boss_guardian_interval']>=2,'guardian interval safe')
            if i>1:
                ok(rooms[rid]['exits']['south']==f'{prefix}_raid_{i-1}','retreat')
                ok(rooms[f'{prefix}_raid_{i-1}']['exits']['north']==rid,'forward')
        relic=f'{prefix}_raid_relic';fragment=f'{prefix}_raid_fragment'
        ok(recipes[relic]['output']==relic,'relic recipe output')
        ok(fragment in recipes[relic]['ingredients'],'fragment consumption')
        ok(all(item in items for item in recipes[relic]['ingredients']),'all recipe materials exist')
    # The real combat AI must use all four custom HP thresholds.
    template=mobs['v10300_swit_raid_boss_3']
    maximum=int(template['max_hp']);mob=SimpleNamespace(alive=True,hp=maximum,
        adaptive_max_hp_v11330=0,v1230_boss_phase=0)
    for pct,phase in ((79,1),(59,2),(39,3),(19,4)):
        mob.hp=maximum*pct//100
        event=boss_tactics_phase_v1230(mob,template,now=100.0)
        ok(f'FAZA {phase}/4' in str(event), f'phase transition {phase}: {event}')
        ok(mob.v1230_boss_phase==phase,'phase state')
        ok(boss_tactics_phase_v1230(mob,template,now=100.0) is None,'phase triggered once')
    # No level lock: access is geographical and quests are the actual progress gate.
    ok('required_level' not in rooms['v10300_swit_raid_1'],'no new character level cap')
    ok(all(int(quest['generator_level'])<=5000 for qid,quest in quests.items() if '_raid_quest_' in qid),
       'authored 801-5000')
    return checks,result

if __name__=='__main__':
    count,result=run()
    print(f'ERA BEZ GRANIC RAIDS DEVELOPMENT: {count} checks PASS; '+str(result),flush=True)
