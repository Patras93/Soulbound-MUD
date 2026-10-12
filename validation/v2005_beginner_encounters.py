# -*- coding: utf-8 -*-
"""v2.00.5: real low-level adaptive damage regression, no live SQLite."""
from types import SimpleNamespace
from pathlib import Path
import ast

from data.mobs import MOB_TEMPLATES
from systems.adaptive_combat import (
    adaptive_beginner_incoming_target_v2005,
    adaptive_target_incoming_fraction_v11330,
    adaptive_target_max_hp_v11330,
    adaptive_reward_multiplier_v11330,
    adaptive_combat_rank_v11330,
)



def _combat_damage_methods():
    # Same real methods as production, without importing the entire game world
    # before its boot has initialized legacy world-side resources.
    path = Path(__file__).resolve().parents[1] / "player/session_mixins/combat_damage.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(item for item in tree.body if isinstance(item, ast.ClassDef)
               and item.name == "SessionCombatDamageMixin")
    needed = {"adaptive_enemy_damage_multiplier_v11330", "consider_adaptive_preview_v11331"}
    methods = [item for item in cls.body if isinstance(item, ast.FunctionDef)
               and item.name in needed]
    assert len(methods) == len(needed)
    for method in methods:
        method.decorator_list = []
    out = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
        name="SessionCombatDamageMixin", bases=[], keywords=[], body=methods,
        decorator_list=[],
    )], type_ignores=[]))
    context = {
        "MOB_TEMPLATES": MOB_TEMPLATES,
        "ROOMS": {},
        "adaptive_beginner_incoming_target_v2005": adaptive_beginner_incoming_target_v2005,
        "adaptive_target_incoming_fraction_v11330": adaptive_target_incoming_fraction_v11330,
        "adaptive_target_max_hp_v11330": adaptive_target_max_hp_v11330,
        "adaptive_reward_multiplier_v11330": adaptive_reward_multiplier_v11330,
        "adaptive_combat_rank_v11330": adaptive_combat_rank_v11330,
        "elite_average_enemy_multiplier_v11338": lambda template: 1.0,
    }
    exec(compile(out, str(path), "exec"), context)
    return context["SessionCombatDamageMixin"]


SessionCombatDamageMixin = _combat_damage_methods()


class _CharacterSession(SessionCombatDamageMixin):
    def __init__(self, level, hp):
        self.character = SimpleNamespace(character_level=level, room_id="test")
        self.hp_test = hp

    def max_hp(self):
        return self.hp_test

    def consider_enemy_expected_hit(self, template):
        # The authored hit can always reach the player (no defense/dodge).
        return float(template["damage"])

    def adaptive_party_members_v11330(self, mob):
        return [self]

    def adaptive_party_dps_v1261(self, members):
        return 100.0  # mercenary DPS is not included

    def v0210_world_tier_multipliers(self):
        return {"effective_hp": 1.0}

    def consider_player_expected_hit(self):
        return 25.0

    def basic_attack_hit_count_v11196(self):
        return 1

    def v0210_enemy_damage_multiplier(self):
        return 1.0


def run_regression():
    count = 0
    normal = MOB_TEMPLATES["bandit"]
    assert normal["damage"] == 9
    count += 1
    for level in (1, 8, 15):
        player = _CharacterSession(level, 1000)
        mob = SimpleNamespace(template_id="bandit", adaptive_party_size_v11330=1)
        raw_mult = player.adaptive_enemy_damage_multiplier_v11330(mob, normal)
        # Before fix level 8, 1000 HP: 70 / 9 = 7.78x (!) per bandit.
        assert 1.0 <= raw_mult <= 1.56, (level, raw_mult)
        count += 1
        preview = player.consider_adaptive_preview_v11331(
            SimpleNamespace(template_id="bandit", hp=75), normal,
        )
        assert preview["enemy_hit"] <= 9 * 1.5 + 0.01
        count += 1
    # Raw authored damage must not be artificially weakened, even at level 1.
    player = _CharacterSession(8, 80)
    mob = SimpleNamespace(template_id="bandit", adaptive_party_size_v11330=1)
    assert player.adaptive_enemy_damage_multiplier_v11330(mob, normal) >= 1.0
    count += 1
    # Protection fades smoothly; it does not suddenly vanish at level 9.
    prev = 0.0
    for level in (8, 9, 15, 16, 20, 30, 40, 50, 64, 65, 100):
        target = adaptive_beginner_incoming_target_v2005(normal, level, 9, 300)
        assert target >= 9 and target >= prev
        if level >= 65:
            assert target == 300
        prev = target
        count += 2
    # The solo boss / miniboss / elite challenge is intentionally unchanged.
    for template_id in ("bandit_captain", "bandit_chief"):
        template = MOB_TEMPLATES[template_id]
        desired = 1000 * adaptive_target_incoming_fraction_v11330(template, 1)
        target = adaptive_beginner_incoming_target_v2005(
            template, 8, template["damage"], desired,
        )
        assert target == max(template["damage"], desired)
        count += 1
    # Other novice group members do not change the level-8 safety rule.
    for party_size in (1, 2, 4):
        mob = SimpleNamespace(template_id="bandit", adaptive_party_size_v11330=party_size)
        player = _CharacterSession(8, 1000)
        assert player.adaptive_enemy_damage_multiplier_v11330(mob, normal) <= 1.56
        count += 1
    # Experienced players' adaptive floor remains unchanged.
    player = _CharacterSession(100, 1000)
    mob = SimpleNamespace(template_id="bandit", adaptive_party_size_v11330=1)
    assert player.adaptive_enemy_damage_multiplier_v11330(mob, normal) > 7.0
    count += 1
    return count


if __name__ == "__main__":
    print(f"BEGINNER ENCOUNTERS v2.00.5: {run_regression()} checks PASS")
