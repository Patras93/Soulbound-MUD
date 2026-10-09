"""Regression for v1.26.3: high-tier mob HP and reward scaling."""
from __future__ import annotations
import ast
import math
from pathlib import Path
from types import SimpleNamespace

from systems.adaptive_combat import (
    adaptive_target_max_hp_v11330,
    adaptive_reward_multiplier_v11330,
    adaptive_combat_rank_v11330,
)

ROOT = Path(__file__).resolve().parents[1]


def audit_v1263():
    checks = 0
    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError("v1.26.3: " + label)

    # Preserve ordinary level-10 targets and known boss timings.
    for rank, seconds in (("normal", 8), ("elite", 10), ("rare", 12),
                          ("mini", 18), ("boss", 28), ("world_boss", 45)):
        hp = adaptive_target_max_hp_v11330(1000, 1500, {"rank": rank})
        check(hp == 1500 * seconds, f"rank {rank} baseline target")
    check(adaptive_target_max_hp_v11330(1000, 500, {"rank": "normal", "elite_hp_multiplier_v11338": 1.2}) == 4800,
          "elite multiplier preserved")

    # This boundary used to stop scaling at 9,000,000,000,000,000.
    previous = 0
    for dps in (10**8, 10**12, 10**15, 10**16, 10**18, 10**20, 10**100, 10**400):
        hp = adaptive_target_max_hp_v11330(1000, dps, {"rank": "normal"})
        check(hp == 8 * dps, f"uncapped HP for DPS={str(dps)[:20]}")
        check(hp > previous, "strict HP growth")
        check(adaptive_reward_multiplier_v11330(1000, hp) > 1, "reward for difficulty")
        previous = hp
    check(adaptive_target_max_hp_v11330(40000, 1, {"rank": "normal"}) == 40000,
          "low-DPS players do not lose authored HP")
    check(adaptive_reward_multiplier_v11330(1000, 1000) == 1.0,
          "no bonus for baseline HP")
    check(adaptive_reward_multiplier_v11330(1000, 10**400) > adaptive_reward_multiplier_v11330(1000, 10**100),
          "reward growth beyond float range")
    check(adaptive_reward_multiplier_v11330(10**400, 10**402) > 1,
          "reward with huge base HP")

    # Test the real SessionCombatDamageMixin method in isolation as in v1.26.1.
    source = ast.parse((ROOT / "player/session_mixins/combat_damage.py").read_text(encoding="utf8"))
    node = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == "SessionCombatDamageMixin")
    namespace = {"math": math, "MOB_TEMPLATES": {"test": {"max_hp": 1000, "rank": "normal"}},
                 "adaptive_target_max_hp_v11330": adaptive_target_max_hp_v11330,
                 "adaptive_reward_multiplier_v11330": adaptive_reward_multiplier_v11330,
                 "adaptive_combat_rank_v11330": adaptive_combat_rank_v11330,
                 "sys": __import__("sys")}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "combat_damage", "exec"), namespace)
    Combat = namespace["SessionCombatDamageMixin"]

    class Session(Combat):
        def __init__(self, dps):
            self.dps = dps
            self.character = SimpleNamespace(room_id="room")
            self.closed = False
            self.current_hp = 1000
            self.combat_mob_key = None
            self.server = SimpleNamespace(sessions=[], party_sessions=lambda *a, **kw: [self])
            self.account_id = 1
        def adaptive_party_dps_v1261(self, members):
            return self.dps

    fighter = Session(10**25)
    enemy = SimpleNamespace(key="monster", template_id="test", room_id="room", hp=1000, alive=True)
    high = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(high["max_hp"] == 8 * 10**25, "real mob HP > old ceiling")
    check(enemy.hp == high["max_hp"], "full health when first upscaled")
    check(high["reward_multiplier"] > 1, "real mob gets larger reward factor")
    fighter.dps = 10**3
    enemy.hp = high["max_hp"] // 4
    low = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(low["max_hp"] == 8000, "handoff adapts down after battle")
    check(enemy.hp == 2000, "handoff retains exactly 25% health")
    fighter.dps = 10**25
    fighter.combat_mob_key = enemy.key
    fighter.server.sessions = [fighter]
    extended = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(extended["max_hp"] == 8 * 10**25, "active encounter expands")
    fighter.dps = 10**3
    ongoing = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(ongoing["max_hp"] == extended["max_hp"], "active encounter cannot shrink")

    # Arithmetic with huge ints must not overflow in the display ratio or HP handoff.
    fighter.server.sessions = []
    fighter.combat_mob_key = None
    fighter.dps = 10**400
    giant = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(giant["max_hp"] == 8 * 10**400, "real method accepts huge integer DPS")
    check(math.isfinite(enemy.adaptive_hp_multiplier_v11330), "diagnostic multiplier finite")
    check(math.isfinite(enemy.adaptive_party_dps_v11330), "diagnostic DPS finite")
    enemy.hp = giant["max_hp"] // 2
    fighter.dps = 1000
    smaller = fighter.apply_adaptive_mob_scale_v11330(enemy)
    check(smaller["max_hp"] == 8000 and enemy.hp == 4000,
          "exact halving without float overflow")
    # Large HP must not crash common monster healing or superboss phases.
    from systems.monster_ecology_v1250 import ecology_turn_v1250
    from systems.monster_ai import monster_ai_execute_v1160
    from world.uoss_superboss_runtime import superboss_phase_v11137
    skeleton = SimpleNamespace(template_id="skeleton", alive=True, engaged_by=1,
        hp=10**400 // 3, room_id="crypt", combat_turn=4,
        v1250_recovered=False, v1250_ecology_next=0)
    world = SimpleNamespace(mobs={"skel": skeleton},
        mob_templates_for_ai_v1160=lambda mob: {"name": "Szkielet", "max_hp": 10**400})
    skeleton.adaptive_max_hp_v11330 = 10**400
    text = ecology_turn_v1250(world, skeleton, {"name": "Szkielet"}, now=100.0)
    check("odzyskuje" in text, "undead heals at huge HP without float overflow")
    check(skeleton.hp > 10**400 // 3, "undead recovery raises current HP")
    skeleton.monster_ai_next_action_v1160 = 0
    before = skeleton.hp
    result = monster_ai_execute_v1160(world, skeleton, {"name":"Szkielet"},
                                       {"kind": "heal", "target": skeleton}, now=120.0)
    check("odzyskuje" in result, "monster healer handles huge HP")
    check(skeleton.hp > before, "monster healer restores HP")
    boss = SimpleNamespace(alive=True, hp=10**400 // 10,
                           adaptive_max_hp_v11330=10**400)
    stage = superboss_phase_v11137({"uoss_unique_superboss_key": "black_rabite"}, boss)
    check(stage == 3, "superboss phase computed at huge HP")
    return checks


if __name__ == "__main__":
    print(f"SOULBOUND v1.26.3 UNCAPPED HP: {audit_v1263()} checks PASS")
