# -*- coding: utf-8 -*-
"""Verify authored Era boss HP without accepting runaway terrain clones.

Both base templates and single application of legitimate global difficulty
are valid; repeated scaling to trillion-HP is not. No DB/network use.
"""
from __future__ import annotations


def run():
    import server  # installs World v0384 patch, same as production startup
    from world.world_state import World
    from systems.content_registry import MOB_TEMPLATES
    from world.v10300_era_bez_granic import ERAS, install as era_install
    from world.v10300_era_raids import install as legacy_raid_install
    # Verify legacy authored HP on a local pre-retirement fixture.  All
    # raid enemies MUST remain absent from the active v110 monster registry.
    rooms={'v3000_eternal_6': {'exits': {}}}; old_mobs={};spawns=[]
    npcs={};quests={};items={};recipes={};areas=[]
    era_install(rooms,old_mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    legacy_raid_install(rooms,old_mobs,spawns,npcs,quests,items,recipes)
    world=World.__new__(World)
    checks=0
    for slug,zone,low,high,*_ in ERAS:
        for stage in (1,2,3):
            room=f'v10300_{slug}_raid_{stage}'
            mob=f'v10300_{slug}_raid_boss_{stage}'
            assert world._terrain_scaled_template_v0362(room,mob)==mob,(room,mob)
            checks+=1
            assert mob not in MOB_TEMPLATES, ('retired raid boss restored',mob)
            hp=int(old_mobs[mob]['max_hp'])
            # v104: ordinary authored HP is the floor; optional global difficulty
            # may legitimately increase it. Reject any accidental repeated scaling
            # (especially the old trillion-HP terrain-clone regression).
            # Authored source: world/v10300_era_raids.py, install().
            required_level = low + round((high-low)*(stage-1)/2)
            authored_hp = (1_800_000 + required_level*14_000)*(stage+1)
            assert authored_hp <= hp <= authored_hp*10, (mob,hp,authored_hp)
            checks+=1
        mob=f'v10300_{slug}_mob_1'
        # Ordinary Era mobs also retain their explicit template instead of
        # accidentally growing by legacy terrain world threat.
        if mob in MOB_TEMPLATES:
            assert world._terrain_scaled_template_v0362(f'v10300_{slug}_01',mob)==mob
            checks+=1
    assert checks>=66,checks
    return checks

if __name__=='__main__':
    print(f'ERA v103 AUTHORED HP: {run()} checks PASS',flush=True)
