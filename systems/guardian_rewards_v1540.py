# -*- coding: utf-8 -*-
"""OLC 12.0: optional per-kill rewards for *ordinary boss* guardians.

No override means the original XP/zero-money path remains intact.
UOSS scripted summons never receive this policy or these coins.
"""

REWARD_FIELDS_V1540 = frozenset(("xp", "silver", "gold", "mithril"))
REWARD_LIMIT_V1540 = 10**12


def validate_guardian_rewards_v1540(value):
    if (not isinstance(value, dict) or set(value) != REWARD_FIELDS_V1540
            or any(type(v) is not int or not 0 <= v <= REWARD_LIMIT_V1540
                   for v in value.values())):
        raise ValueError("Nagrody pomocników: JSON z xp, silver, gold, mithril; liczby całkowite od 0 do 1000000000000.")
    return dict(value)



def default_guardian_rewards_v1540(parent_template):
    """Current historic amount per ordinary guardian (no OLC override)."""
    level = max(1, int(parent_template.get("level", 1) or 1))
    parent_xp = max(0, int(parent_template.get("source_xp", 0) or 0))
    return {"xp": max(500, level * 400, parent_xp // 8),
            "silver": 0, "gold": 0, "mithril": 0}


def guardian_reward_snapshot_v1540(template):
    """Freeze validated boss OLC policy on a newly summoned guardian."""
    if not isinstance(template, dict) or "olc_boss_guardian_rewards" not in template:
        return None
    return validate_guardian_rewards_v1540(template["olc_boss_guardian_rewards"])


def grant_guardian_currency_v1540(character, policy):
    """Add currency once per eligible participant (caller guards kill once).

    Only invoked for the ordinary-boss guardian branch with explicit OLC override.
    """
    if policy is None:
        return (0, 0, 0)
    validate_guardian_rewards_v1540(policy)
    amounts = tuple(policy[key] for key in ("silver", "gold", "mithril"))
    for key, amount in zip(("silver", "gold", "mithril"), amounts):
        setattr(character, key, getattr(character, key) + amount)
    return amounts
