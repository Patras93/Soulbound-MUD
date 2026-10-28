# -*- coding: utf-8 -*-
"""v102.00.12: permanent world pressure + boosted crypt/tower recipient EXP.

No full world boot needed for this regression, no player DB, no Adaptive Combat.
"""
import ast
from pathlib import Path
from systems.dungeon_experience_v1285 import (
    dungeon_recipient_bonus_v1020012, dungeon_recipient_xp_v1286,
    _authored_level_over_800_v1020012,
)
from systems.dungeon_xp_reference_v4211 import authored_base_dungeon_xp_v4211
from config.balance import V0503_DIFFICULTY_PRESSURE
from core import balance_math

ROOT = Path(__file__).resolve().parents[1]


def _load_world_math():
    """Load real unmodified functions/constants without importing huge world."""
    source = (ROOT/'world/global_difficulty_overdrive.py').read_text(encoding='utf8')
    tree = ast.parse(source)
    names = ('_v0386_stage','_v0386_rank','_v0386_instance_kind',
             'pressure_by_content_v1020012','global_difficulty_multipliers_v0386')
    selected = [node for node in tree.body
                if isinstance(node,ast.FunctionDef) and node.name in names]
    config_node = next(node for node in tree.body
                       if isinstance(node, ast.Assign) and
                       any(isinstance(target,ast.Name) and target.id == 'V1020012_WORLD_PRESSURE'
                           for target in node.targets))
    rank_nodes = [node for node in tree.body
                  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and
                  t.id.startswith(('_V0386_RANK_','_V0386_INSTANCE','V11323_RANK_DAMAGE_PRESSURE'))
                  for t in node.targets)]
    ns={'balance_math':balance_math,'V0503_DIFFICULTY_PRESSURE':V0503_DIFFICULTY_PRESSURE,
        'CHARACTER_MAX_LEVEL':800}
    exec(compile(ast.Module(body=rank_nodes+[config_node]+selected,type_ignores=[]),'<world-pressure>', 'exec'),ns)
    return ns


def run():
    ns=_load_world_math()
    func=ns['global_difficulty_multipliers_v0386']
    bonus=ns['pressure_by_content_v1020012']
    checks=0
    sample={
        'world': {'generator_level':250,'rank':'normal'},
        'instance':{'generator_level':250,'giant_fortress_floor':1,'rank':'normal'},
        'crypt':{'generator_level':250,'crypt_floor':1,'rank':'normal'},
        'mythic_crypt':{'generator_level':250,'mythic_crypt_floor':1,'rank':'normal'},
        'tower':{'generator_level':250,'astral_floor':100,'rank':'normal'},
        'mythic_tower':{'generator_level':250,'mythic_astral_floor':1,'rank':'normal'},
        'magitek':{'generator_level':250,'magitek_floor':1,'rank':'normal'},
    }
    expected={'world':(1.20,1.22,1.4),'instance':(1.20,1.18,1.45),
              'crypt':(1.25,1.20,1.90),'mythic_crypt':(1.32,1.25,2.20),
              'tower':(1.25,1.20,2.0),'mythic_tower':(1.32,1.25,2.3),
              'magitek':(1.24,1.20,1.5)}
    neutral={k:(1.0,1.0,1.0) for k in expected}
    for name,t in sample.items():
        assert ns['_v0386_instance_kind'](t)==name,name;checks+=1
        assert bonus(t)==expected[name],name;checks+=1
        actual=func(t)
        old=ns['V1020012_WORLD_PRESSURE']
        ns['V1020012_WORLD_PRESSURE']=neutral
        try: baseline=func(t)
        finally: ns['V1020012_WORLD_PRESSURE']=old
        for axis,factor in zip(('hp','damage','reward'),expected[name]):
            assert abs(actual[axis]/baseline[axis]-factor)<.00001,(name,axis,actual,baseline);checks+=1
        assert actual['coin']==baseline['coin'], name;checks+=1
    # No accidental player/party level or fame inputs, nor reenable Adaptive.
    adaptive=(ROOT/'systems/adaptive_switch_v102006.py').read_text(encoding='utf8')
    assert 'adaptive_combat_global_v102006.json' in adaptive;checks+=1
    assert (ROOT/'LIVE_CONTENT/adaptive_combat_global_v102006.json').exists() is False;checks+=1
    for group in ('world','crypt','mythic_crypt','tower','mythic_tower'):
        a=func(sample[group]);b=func({**sample[group], 'adaptive_party_size':100,'player_level':10000})
        assert a==b,group;checks+=1
    # Per-recipient correction happens *after* raw mob XP. A high enough raw
    # award must deliver more XP on each intended dungeon XP channel.
    base={'generator_level':175,'giant_fortress_floor':12,'rank':'normal'}
    for key,factor in [('crypt_floor',1.9),('mythic_crypt_floor',2.2),
                       ('astral_floor',2.0),('mythic_astral_floor',2.3)]:
        t={'generator_level':175, key:175, 'rank':'normal'}
        assert dungeon_recipient_bonus_v1020012(t)==factor;checks+=1
        for axis in ('character','class','soul'):
            old=dungeon_recipient_xp_v1286(base,axis,10**14,175)
            new=dungeon_recipient_xp_v1286(t,axis,10**14,175)
            assert new>old,(key,axis,old,new);checks+=1
        for lvl in (1,30,80):
            xp=dungeon_recipient_xp_v1286(t,'character',10**14,lvl,
                                          downstream_multiplier=4.0)
            # Existing low-level strict caps still bound any dungeon XP.
            old=dungeon_recipient_xp_v1286(base,'character',10**14,lvl,
                                          downstream_multiplier=4.0)
            assert xp==old,(key,lvl,old,xp);checks+=1
    assert dungeon_recipient_bonus_v1020012({'crypt_floor':15,'source_xp_exact':True})==1.0;checks+=1
    assert dungeon_recipient_xp_v1286({'astral_floor':100,'source_xp_exact':True},
                                     'character',12345,5)==12345;checks+=1
    for axis in ('character','class','soul'):
        assert _authored_level_over_800_v1020012(axis,800)==authored_base_dungeon_xp_v4211(axis,800);checks+=1
        assert _authored_level_over_800_v1020012(axis,801)>_authored_level_over_800_v1020012(axis,800);checks+=1
        assert _authored_level_over_800_v1020012(axis,900)>_authored_level_over_800_v1020012(axis,801);checks+=1
    assert dungeon_recipient_xp_v1286({'crypt_floor':900,'generator_level':900},'character',10**17,900)> \
           dungeon_recipient_xp_v1286({'crypt_floor':800,'generator_level':800},'character',10**17,800);checks+=1
    return checks


if __name__ == '__main__':
    print('WORLD/CRYPT/TOWER PRESSURE v102.00.12:',run(),'checks PASS')
