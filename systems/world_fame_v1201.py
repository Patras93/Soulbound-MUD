# -*- coding: utf-8 -*-
"""v12.00.1: additional meaningful, one-time Fame encounters throughout the world.

Add naturally spawned region champions, not fame awards for ordinary monster
kills. IDs are deterministic and independent of runtime process/session.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha1

EXCLUDED_ROOMS = frozenset({'temple_basement', 'temple_basement_storage',
    'temple_basement_pantry', 'temple_basement_wine', 'temple_basement_drain',
    'temple_basement_moldy', 'temple_basement_cistern',
    'temple_basement_flooded', 'temple_basement_root',
    'temple_basement_hidden', 'temple_basement_nest_a'})


def install(rooms, mobs, spawns, help_topics):
    """Make up to 2 distinct non-boss champions per eligible existing region.

    Bosses and existing one-time Fame targets retain IDs and rewards. Ordinary
    mobs remain ordinary; champions are separate, genuine spawned enemies.
    Stable natural spawn locations and IDs protect SQLite from duplicate Fame.
    """
    from systems.fame_v1702 import fame_region, _is_fame_target, _eligible_natural_fame_enemy
    groups = defaultdict(dict)
    occupied = {(str(room), str(mid)) for room, mid in spawns}
    for room, mid in tuple(spawns):
        if room not in rooms or room in EXCLUDED_ROOMS:
            continue
        meta = mobs.get(mid)
        if not meta or _is_fame_target(meta) or not _eligible_natural_fame_enemy(meta):
            continue
        if meta.get('elite_base_template') or meta.get('rare_base_template') or meta.get('base_template'):
            continue  # choose authored natural species only, not procedural variants
        if meta.get('quest_boss') or meta.get('training_dummy'):
            continue
        hp, damage = int(meta.get('max_hp') or 0), int(meta.get('damage') or 0)
        if hp <= 0 or damage <= 0:
            continue
        zone = fame_region(room, rooms)
        if zone == 'Nieznana kraina':
            continue
        # Avoid NPC service rooms and the introductory temple/tutorial.
        existing = groups[zone].get(str(mid))
        score = (hp, damage, str(room))
        if existing is None or score > existing[0]:
            groups[zone][str(mid)] = score, str(room)
    made=[]
    for zone in sorted(groups):
        candidates=sorted(groups[zone].items(),key=lambda pair:pair[1][0],reverse=True)
        for base_id, (_, room) in candidates[:2]:
            stable=sha1((zone+'\0'+base_id+'\0'+room).encode('utf-8')).hexdigest()[:16]
            tid='v1201_fame_champion_'+stable
            if tid in mobs:
                raise RuntimeError('Duplicate world Fame champion ID: '+tid)
            source=mobs[base_id]
            champion=dict(source)
            champion['name']='Elitarny Strażnik: '+str(source.get('name') or base_id)
            champion['v1201_base_hp']=int(source['max_hp'])
            champion['v1201_base_damage']=int(source['damage'])
            champion['max_hp']=max(int(source['max_hp'])+1, int(source['max_hp']*2.4))
            champion['damage']=max(int(source['damage'])+1, int(source['damage']*1.65))
            for reward in ('class_xp_reward','soul_reward','stat_reward'):
                if reward in source:
                    champion[reward]=max(1,int(source[reward]*2))
            champion['rank']='elite'
            champion['fame_target']=True
            champion['v1201_world_fame_champion']=True
            # No parent/base_template field: separate authored Fame objective.
            champion.pop('elite_base_template',None)
            champion.pop('rare_base_template',None)
            champion.pop('base_template',None)
            mobs[tid]=champion
            if (room,tid) in occupied:
                raise RuntimeError('Duplicate Fame champion spawn: '+tid)
            spawns.append((room,tid))
            made.append((zone,room,tid,base_id))
    help_topics.setdefault('fame',[]).append(
        'v12.00.1: Nowe elitarne straże Fame rozsiane po regionach świata. '
        'Każda ma własny identyfikator i daje +1 Fame przy pierwszym zabiciu '
        'na konto. Zwykłe potwory nadal nie dają Fame. '
        'fame regiony; where fame; fame braki; fame cele.')
    return {'regions_with_new_fame':len({row[0] for row in made}),
            'new_unique_fame_targets':len(made),'encounters':tuple(made)}
