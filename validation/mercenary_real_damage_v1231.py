# -*- coding: utf-8 -*-
"""No artificial damage caps: hires inherit real owner combat throughput."""
import asyncio
import ast
import time
from pathlib import Path
from types import SimpleNamespace

from core.player_math import character_offensive_build_multiplier
from systems.mercenary_taverns import (
    COOLDOWN, MERCENARIES, mercenary_owner_real_action_power_v1231, mercenary_owner_full_power_v12213,
)
from systems.mercenary_growth_v1220 import (mercenary_attack_multiplier, mercenary_owner_level_v1228, mercenary_tactic)


def isolated_method(path, method_name, namespace):
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/path).read_text(encoding='utf8'))
    method=next(node for cls in tree.body if isinstance(cls,ast.ClassDef)
                for node in cls.body if isinstance(node, (ast.FunctionDef,ast.AsyncFunctionDef))
                and node.name==method_name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(path), 'exec'),namespace)
    return namespace[method_name]



def validate_mercenary_real_damage_v1231():
    checks = 0
    def ok(condition, label):
        nonlocal checks
        assert condition, "Mercenary v1.23.1: " + label
        checks += 1

    consider = isolated_method('player/session_mixins/combat_damage.py', 'consider_player_expected_hit', {
        'character_offensive_build_multiplier':character_offensive_build_multiplier,
        'party_synergy_damage_multiplier_v11338':lambda owner,kind:1.0,
    })
    combat = isolated_method('player/session_mixins/mercenary_taverns.py', 'mercenary_combat_turn_v1170', {
        'time':time,
        'COOLDOWN':COOLDOWN,
        'MERCENARIES':MERCENARIES,
        'MOB_TEMPLATES':{'goblin': {'name': 'Goblin'}},
        'mercenary_owner_full_power_v12213':mercenary_owner_full_power_v12213,
        'mercenary_owner_real_action_power_v1231':mercenary_owner_real_action_power_v1231,
        'mercenary_attack_multiplier':mercenary_attack_multiplier,
        'mercenary_owner_level_v1228':mercenary_owner_level_v1228,
        'mercenary_tactic':mercenary_tactic,
        'superboss_healing_blocked_v11179':lambda o:False,
        'v0314_adjust_damage_vs_template':lambda template,damage,kind,role:(damage,''),
    })

    class DamageOwner:
        consider_player_expected_hit = consider
        def __init__(self, soul=1000, stat=500, base=20000, hits=6, interval=1.0):
            self.character = SimpleNamespace(
                class_type="physical", class_name="Wojownik", character_level=300,
                soul_weapon_mastery_level=1, soul_tier=1, soul_power=lambda:soul,
                class_physical_damage_multiplier=lambda:1.5,
                racial_physical_damage_multiplier=lambda:1.2,
                racial_all_damage_multiplier=lambda:1.1,
            )
            self._base, self._stat, self._hits, self._interval = base, stat, hits, interval
        def basic_attack_build_v11196(self): return self._base, self._stat, "physical"
        def total_set_damage_multiplier(self): return 1.5
        def equipment_damage_multiplier(self, kind): return 2.0
        def basic_attack_inherent_multiplier_v1124(self): return 1.2
        def critical_chance(self): return .25
        def critical_multiplier(self): return 2.0
        def basic_attack_hit_count_v11196(self): return self._hits
        def player_action_interval_v11154(self): return self._interval

    hero = DamageOwner()
    expected_hit = hero.consider_player_expected_hit()
    ok(expected_hit > hero._base * character_offensive_build_multiplier(hero._stat),
       "actual class, racial, EQ, critical and Soul Weapon bonuses are present")
    damage = mercenary_owner_real_action_power_v1231(hero, 1000)
    ok(damage >= expected_hit * hero._hits * COOLDOWN / hero._interval * .999,
       "hire matches owner's full five-second output")
    ok(damage > 250_000, "late game six-hit build no longer falls back to 20k")
    ok(mercenary_owner_real_action_power_v1231(DamageOwner(soul=5000), 1000) > damage,
       "Soul Weapon upgrade actually strengthens hire")
    ok(mercenary_owner_real_action_power_v1231(DamageOwner(stat=3000), 1000) > damage,
       "uncapped trained stat multiplier strengthens hire")
    ok(mercenary_owner_real_action_power_v1231(DamageOwner(hits=12), 1000) >= 2*damage - 12,
       "Haste/double hit strings propagate to mercenary")
    ok(mercenary_owner_real_action_power_v1231(DamageOwner(interval=.5), 1000) >= 2*damage - 12,
       "faster owner actions increase hire output proportionately")
    ok(mercenary_owner_real_action_power_v1231(SimpleNamespace(), 43000) == 43000,
       "legacy runtime/test owner retains full equipment fallback")

    class CombatOwner(DamageOwner):
        mercenary_combat_turn_v1170 = combat
        def __init__(self, phys=1000, magic=50):
            super().__init__()
            self._phys,self._magic = phys,magic
            self.character.name='Gracz'
            self.character.room_id='loc'
            self.account_id=1
            self.current_hp=1_000_000
            self.skill_guard=2
            self.messages=[]
            self.kills=0
            class DB:
                def mercenary_contracts(self,account,now):
                    return [dict(role=r,expires_at=0) for r in ('wojownik','mag','berserker')]
                def mercenary_progress_v1220(self,account,role):
                    return dict(specialization='automatyczna')
            self.server=SimpleNamespace(db=DB(), party_sessions=lambda *a,**k: [self], party_combat_broadcast=self.broadcast)
        def physical_power(self): return self._phys
        def spell_power(self): return self._magic
        def max_hp(self): return 1_000_000
        async def apply_boss_defense(self,mob,raw): return raw
        async def send_combat(self,msg,detail='essential'): self.messages.append(msg)
        async def broadcast(self,*args,**kwargs): pass
        async def mob_defeated(self,mob):
            self.kills+=1
            mob.alive=False

    async def scenario(phys,magic,hp):
        owner=CombatOwner(phys,magic)
        mob=SimpleNamespace(alive=True,hp=hp,template_id='goblin',room_id='loc')
        await owner.mercenary_combat_turn_v1170(mob)
        return owner,mob

    # Integration turn uses real character method, full attack-time scaling,
    # status broadcasts and the existing kill pipeline; no DB changes.
    async def run():
        p,mob=await scenario(20000,50,10**10)
        m,mob2=await scenario(50,20000,10**10)
        ok(len(p.messages)==3 and len(m.messages)==3,
           "all three independent hires attack immediately")
        ok(mob.hp == mob2.hp,
           "cross-class hires receive equal offensive owner throughput")
        ok(10**10-mob.hp >= damage*3,
           "three hires really deal player-scale damage, not reduced STR/INT")
        fin,dead=await scenario(20000,50,1)
        ok(fin.kills==1 and not dead.alive and len(fin.messages)==1,
           "mercenary finisher gives one real kill, stops remaining hires")
        first=10**10-mob.hp
        await p.mercenary_combat_turn_v1170(mob)
        ok(first==10**10-mob.hp, "five-second cooldown unchanged")
    asyncio.run(run())
    return checks


if __name__ == '__main__':
    print(f'MERCENARY REAL DAMAGE v1.23.1: {validate_mercenary_real_damage_v1231()} checks PASS')
