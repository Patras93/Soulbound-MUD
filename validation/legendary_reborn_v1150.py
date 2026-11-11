# -*- coding: utf-8 -*-
"""Deterministic regressions for Soulbound v1.15.0 boss loot and craft perks."""
from systems.legendary_reborn import (
    SPARK, HEART, CHASE_RELICS,
    apply_legendary_craft_perk_v1150, boss_legendary_roll_v1150,
)

class _FixedRNG:
    def __init__(self, *numbers):
        self.numbers = iter(numbers)
    def random(self):
        return next(self.numbers)
    def choice(self, options):
        return tuple(options)[0]


def audit_legendary_reborn_fast_v1150():
    errors = []
    checks = 0
    cases = (
        ({"level":1}, (0.0,), None),
        ({"uoss_unique_superboss_key":"black_rabite"}, (0.0,), SPARK),
        ({"uoss_unique_superboss_key":"black_rabite"}, (0.9,0.0), HEART),
        ({"uoss_unique_superboss_key":"black_rabite"}, (0.9,0.9,0.0), tuple(CHASE_RELICS)[0]),
        ({"uoss_unique_superboss_key":"black_rabite"}, (0.9,0.9,0.9), None),
        ({"crypt_floor":600,"level":600}, (0.0,), SPARK),
    )
    for template, rolls, expected in cases:
        checks += 1
        got=boss_legendary_roll_v1150(template, _FixedRNG(*rolls))
        if got != expected:
            errors.append(f"boss {template}: got={got}, expected={expected}")
    item_one={"properties":{"physical_defense_pct":3},"desc":"Test."}
    item_two={"properties":{"physical_defense_pct":3},"desc":"Test."}
    checks += 1
    a=apply_legendary_craft_perk_v1150(item_one,'craftq_legendary_none_iron_helmet','legendary')
    b=apply_legendary_craft_perk_v1150(item_two,'craftq_legendary_none_iron_helmet','legendary')
    if not a or a!=b or item_one != item_two:
        errors.append('legendary craft perk is not stable after reconstructing item id')
    checks += 1
    ordinary={"properties":{"physical_defense_pct":3},"desc":"Test."}
    if apply_legendary_craft_perk_v1150(ordinary,'craftq_normal_none_iron_helmet','normal') is not None or len(ordinary['properties'])!=1:
        errors.append('normal craft gained a rare perk')
    checks += 1
    high={"properties":{},"desc":"Test."}
    apply_legendary_craft_perk_v1150(high,'craftq_legendary_none_iron_guard','legendary')
    if not high.get('properties') or not high.get('legendary_perk_v1150'):
        errors.append('legendary craft does not equip real active properties')
    return {"checks":checks, "error_count":len(errors),"errors":errors}
