# -*- coding: utf-8 -*-
"""Static and actual World() spawn checks for all forty v105 bosses.

This verifies presence, quest linkage, and positive runtime combat numbers.
It does NOT claim to validate time-to-kill or five-player balance.
"""
from __future__ import annotations


def run():
    import server
    from world.v10500_region_index import REGIONS
    from world.dynamic_content import MOB_TEMPLATES, MOB_SPAWNS, QUESTS, quest_kill_targets_v0389
    world=server.World()
    checks=0
    hp=[];damage=[];stages=[]
    for slug, name, low, high, *_ in REGIONS:
        for number, room_idx, quest_no in ((1,10,9),(2,14,10)):
            rid=f'v10500_{slug}_{room_idx:02d}'
            mid=f'v10500_{slug}_boss_{number}'
            qid=f'v10500_{slug}_hunt_{quest_no:02d}'
            assert (rid,mid) in MOB_SPAWNS,(rid,mid);checks+=1
            template=MOB_TEMPLATES[mid]
            assert template.get('boss') and template.get('world_boss') and template.get('quest_target')==mid,mid;checks+=1
            quest=QUESTS[qid]
            assert quest['kind']=='kill' and quest['target']==mid and int(quest['needed'])==1,qid;checks+=1
            assert (sum(max(0,int(quest.get(k,0) or 0)) for k in ('reward_gold','reward_silver','reward_mithril'))>0 and int(quest.get('olc_reward_xp',0))>0),qid;checks+=1
            candidates=[mob for mob in world.mobs.values() if mob.room_id==rid and mid in quest_kill_targets_v0389(mob.template_id)]
            assert len(candidates)==1,(mid,len(candidates));checks+=1
            spawned=candidates[0]
            authored=MOB_TEMPLATES[spawned.template_id]
            assert int(spawned.hp)>0 and int(authored['max_hp'])>0 and int(authored['damage'])>0,mid;checks+=1
            assert int(authored.get('generator_level',0))>=low,(mid,authored.get('generator_level'),low);checks+=1
            # Resolver must find a spawned variant when addressed by its visible name.
            found=world.find_mob(rid,authored['name'])
            assert found is not None and found.key==spawned.key,(mid,'lookup');checks+=1
            assert authored.get('auto_aggro') is not True,(mid,'auto aggro');checks+=1
            hp.append(int(spawned.hp));damage.append(int(authored['damage']));stages.append(int(authored['generator_level']))
    assert len(hp)==40 and min(hp)>0 and min(damage)>0;checks+=1
    # The same level metadata must survive the real runtime respawn path.
    for slug in (REGIONS[0][0], REGIONS[-1][0]):
        room=f'v10500_{slug}_10'
        boss=f'v10500_{slug}_boss_1'
        mob=next(m for m in world.mobs.values() if m.room_id==room
                 and boss in quest_kill_targets_v0389(m.template_id))
        mob.alive=False
        mob.respawn_at=0.0
        world.refresh(force=True)
        assert mob.alive,(boss,'respawn');checks+=1
        assert int(MOB_TEMPLATES[mob.template_id]['generator_level'])>=int(server.ROOMS[room]['generator_level']),(boss,'stage after respawn');checks+=1
    report={'checks':checks,'bosses':len(hp),'min_spawn_hp':min(hp),'max_spawn_hp':max(hp),
            'min_damage':min(damage),'max_damage':max(damage),'min_stage':min(stages),'max_stage':max(stages),'qualifier':'runtime values not normal player balance'}
    return report

if __name__=='__main__':
    x=run();print('V105 REAL WORLD BOSS SPAWNS: '+str(x)+' PASS',flush=True)
