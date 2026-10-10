"""v1.26.4: nonproduction mathematical and scripted-boss regressions.

Runs on dummy objects and never touches the player's save or Railway.
"""
from __future__ import annotations
import math
import ast
from pathlib import Path
from types import SimpleNamespace
from core.large_number_math import rounded_product, safe_success_ratio
from systems.mercenary_taverns import (
    mercenary_owner_real_action_power_v1231, mercenary_owner_full_power_v12213,
)
from systems.mercenary_memory_v1250 import memory_learn_v1250
from systems.adaptive_combat import adaptive_target_max_hp_v11330, adaptive_reward_multiplier_v11330
from world.uoss_superboss_runtime import (
    superboss_phase_v11137, superboss_phase_event_v11138,
    superboss_counterattack_multiplier_v11137,
    superboss_source_ability_v11162, superboss_source_summons_v11162,
    SUPERBOSS_TOKEN_ITEMS_V11135,
)


def audit_v1264():
    count = 0
    def check(cond, label):
        nonlocal count
        count += 1
        assert cond, 'v1.26.4: '+label

    # All this used to raise OverflowError when int(10**400) passed through float.
    check(rounded_product(10**400, 1.5) == 15*10**399, 'exact huge product')
    check(safe_success_ratio(10**400, 10**400) == 1.0, 'huge observed hit')
    check(safe_success_ratio(10**400, 1) == 2.0, 'clamp observed hit at 2')
    for size in (10**12, 10**30, 10**100, 10**400):
        full = mercenary_owner_full_power_v12213(size,1,1.5,1.0,1.2)
        check(full == rounded_product(rounded_product(size,1.5),1.2),'mercenary full EQ')
        check(full > size, 'owner power grows without a ceiling')
    class Owner:
        character=SimpleNamespace(soul_weapon_mastery_level=1,soul_tier=1,class_name='Wojownik')
        def __init__(self, hit): self.hit=hit
        def consider_player_expected_hit(self): return self.hit
        def basic_attack_hit_count_v11196(self): return 6
        def player_action_interval_v11154(self): return 1.0
    for size in (10**12,10**100,10**400):
        check(mercenary_owner_real_action_power_v1231(Owner(size), size) >= 30*size,
              'hire inherits full five-second action even at huge power')
    obj = SimpleNamespace(_mercenary_memory_v1250={('mag','boss'):
               {'attempts':[0,0,0], 'success':[0.,0.,0.]}},
               server=SimpleNamespace(db=None),account_id=1)
    memory_learn_v1250(obj, ('mag','boss'),0,10**400,10**400,10**400)
    check(obj._mercenary_memory_v1250[('mag','boss')]['success'][0]==1.0,
          'mercenary learning survives giant damage')

    src = ast.parse((Path(__file__).resolve().parents[1]/'player/session_mixins/combat_damage.py').read_text(encoding='utf8'))
    klass = next(x for x in src.body if isinstance(x, ast.ClassDef) and x.name=='SessionCombatDamageMixin')
    ns = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[klass],type_ignores=[])),
                 'combat_damage.py','exec'),ns)
    SessionCombatDamageMixin = ns['SessionCombatDamageMixin']
    class Db:
        def mercenary_contracts(self, aid):
            return [{'role':'wojownik','expires_at':0},
                    {'role':'mag','expires_at':0},
                    {'role':'paladyn','expires_at':0}]
        def mercenary_progress_v1220(self, aid, role):
            return {'specialization':'automatyczna'}
    class Player(SessionCombatDamageMixin):
        def __init__(self, hit):
            self.hit=hit; self.account_id=42
            self.server=SimpleNamespace(db=Db())
            self.character=SimpleNamespace(character_level=600,
                soul_weapon_mastery_level=1,soul_tier=1,class_name='Wojownik')
        def consider_player_expected_hit(self): return self.hit
        def basic_attack_hit_count_v11196(self): return 6
        def player_action_interval_v11154(self): return 1.0
        def physical_power(self): return self.hit
        def spell_power(self): return self.hit//2
    owner=Player(10**400)
    player_dps=owner.adaptive_member_dps_v11330(owner)
    merc_dps=owner.adaptive_member_mercenary_dps_v1261(owner)
    check(isinstance(player_dps,int) and player_dps>10**400,'unbounded player contribution')
    check(isinstance(merc_dps,int) and merc_dps>10**400,'unbounded three-merc contribution')
    check(owner.adaptive_party_dps_v1261([owner])==player_dps,'party scaling excludes three mercenaries')
    check(adaptive_target_max_hp_v11330(10**6,player_dps,{'rank':'boss'}) > 10**400,
          'boss HP tracks real player without hires')
    check(adaptive_reward_multiplier_v11330(10**6,10**400)>5.0,
          'very difficult encounters pay increasing multiplier')

    # Five named superbosses: phase thresholds, transition events and cooldown.
    for key in ('black_rabite','serpentarius','yiazmat','ruby_weapon','emerald_weapon'):
        template={'uoss_unique_superboss_key':key}
        max_hp=10**400
        boss=SimpleNamespace(alive=True,hp=max_hp, adaptive_max_hp_v11330=max_hp,
                             phase_stage=0,combat_turn=1,template_id='superboss')
        check(key in SUPERBOSS_TOKEN_ITEMS_V11135,key+' personal reward token exists')
        for fraction,stage in ((100,0),(74,1),(39,2),(14,3)):
            boss.hp=max_hp*fraction//100
            check(superboss_phase_v11137(template,boss)==stage,key+' exact phase')
            multiplier,_=superboss_counterattack_multiplier_v11137(template,boss)
            check(math.isfinite(multiplier) and multiplier>=1,key+' counterattack multiplier')
            event=superboss_phase_event_v11138(None,template,boss)
            if stage>0:
                check(event is not None and event[0]==stage,key+' phase event once')
                check(superboss_phase_event_v11138(None,template,boss) is None,key+' no duplicate event')
        boss.alive=False
        check(superboss_phase_v11137(template,boss) is None,key+' dead phase stopped')
    for key,turn,ability in (('black_rabite',2,'Summon Greater Demon'),
                             ('serpentarius',12,'Gravija'),('yiazmat',15,'Stone Breath')):
        boss=SimpleNamespace(combat_turn=turn,template_id='superboss',uoss_summon_used_v1144=False)
        template={'uoss_unique_superboss_key':key}
        check(superboss_source_ability_v11162(template,boss)==ability,key+' original ability')
        if key=='black_rabite':
            check(len(superboss_source_summons_v11162(None,template,boss,ability))==1,
                  'Black Rabite only summons once')
            check(not superboss_source_summons_v11162(None,template,boss,ability),
                  'no duplicate summons')
    return count

if __name__=='__main__':
    print(f'SOULBOUND v1.26.4 MATH AND BOSSES: {audit_v1264()} checks PASS')
