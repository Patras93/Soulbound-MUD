# -*- coding: utf-8 -*-
"""Static plus real World() high-tier balance invariants (not player TTK)."""
from __future__ import annotations

def run():
    import server
    from world.dynamic_content import MOB_TEMPLATES, MOB_SPAWNS,QUESTS
    from world.v10500_region_index import REGIONS
    world=server.World()
    checks=0
    ordinary=[];bosses=[]
    for slug,name,low,high,*_ in REGIONS:
        prev_lvl=0
        for j in range(1,9):
            mid=f'v10500_{slug}_mob_{j}'
            authored=MOB_TEMPLATES[mid]
            level=int(authored['generator_level'])
            assert low <= level <= high and level>prev_lvl,(mid,level,prev_lvl);checks+=1
            prev_lvl=level
            assert int(authored['max_hp'])>0 and int(authored['damage'])>0,mid;checks+=1
            candidates=[m for m in world.mobs.values() if m.alive
                and str(MOB_TEMPLATES[m.template_id].get('base_template') or m.template_id)==mid]
            assert candidates,(mid,'not spawned');checks+=1
            for mob in candidates:
                tpl=MOB_TEMPLATES[mob.template_id]
                if tpl.get('elite_affix'):
                    continue  # Historical special affix remains separately scaled.
                assert int(tpl.get('generator_level',0))>=low,(mid,'stage');checks+=1
                expected_hp=int(authored['max_hp'])
                expected_damage=int(authored['damage'])
                assert int(tpl['max_hp'])==expected_hp,(mid,'hp',tpl['max_hp'],expected_hp);checks+=1
                assert int(tpl['damage'])==expected_damage,(mid,'damage',tpl['damage'],expected_damage);checks+=1
                assert int(mob.hp)==expected_hp,(mid,'mob hp');checks+=1
            ordinary.append((low,int(authored['max_hp']),int(authored['damage'])))
        for j in (1,2):
            mid=f'v10500_{slug}_boss_{j}'
            t=MOB_TEMPLATES[mid]
            assert int(t['max_hp'])>int(authored['max_hp']) and int(t['damage'])>int(authored['damage']),(mid,'boss');checks+=1
            bosses.append((low,int(t['max_hp']),int(t['damage'])))
    assert len(ordinary)==160 and len(bosses)==40;checks+=1
    assert min(x[1] for x in ordinary)>0 and min(x[2] for x in ordinary)>0;checks+=1
    assert max(x[1] for x in ordinary)>min(x[1] for x in ordinary);checks+=1
    assert max(x[2] for x in ordinary)>min(x[2] for x in ordinary);checks+=1
    first=[p for p in ordinary if p[0]==REGIONS[0][2]]
    last=[p for p in ordinary if p[0]==REGIONS[-1][2]]
    assert min(x[1] for x in last)>max(x[1] for x in first);checks+=1
    assert min(x[2] for x in last)>max(x[2] for x in first);checks+=1
    return {'checks':checks, 'ordinary':len(ordinary),'bosses':len(bosses),
            'min_normal_hp':min(x[1] for x in ordinary),'max_normal_hp':max(x[1] for x in ordinary),
            'min_normal_damage':min(x[2] for x in ordinary),'max_normal_damage':max(x[2] for x in ordinary),
            'qualified':'numeric growth only; NOT real player time-to-kill'}

if __name__=='__main__':print('V105 HIGH LEVEL NUMERIC BALANCE: '+repr(run())+' PASS',flush=True)
