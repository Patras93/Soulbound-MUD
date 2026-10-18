# -*- coding: utf-8 -*-
"""Non-destructive v11 progression stress scenarios for Fame and EP.

Models a conservative *upper bound* in which each award only advances the
character axis. Does not silently change level requirements or game economy.
The simulation is a diagnostic, not an assertion that this reflects every
actual multiplayer encounter or the full Multi Cap accumulation dynamics.
"""
from core.progression_resources import character_xp_to_next
from core.player_math import SAFE_INT

LEVELS = (1, 10, 25, 50, 100, 200, 400, 600, 799)
CAP_SAMPLES = (40_000, 80_000, 248_500, 1_000_000, 10_000_000)

def run_regression():
    checks = 0
    results = []
    last_required = 0
    for level in range(1, 800):
        req = character_xp_to_next(level)
        assert isinstance(req, int) and 1 <= req <= SAFE_INT
        assert req >= last_required, ('decreasing requirements', level)
        last_required = req
        checks += 2
    for level in LEVELS:
        req = character_xp_to_next(level)
        row = {'level': level, 'exp_to_next': req, 'examples': {}}
        for cap in CAP_SAMPLES:
            # Rewards are full cap per unique Fame or EP discovery; don't
            # substitute the 50% 'target EXP' displayed to players.
            rewards_to_level = (req + cap - 1) // cap
            assert rewards_to_level >= 1
            assert (rewards_to_level - 1) * cap < req <= rewards_to_level * cap
            row['examples'][cap] = rewards_to_level
            checks += 2
        results.append(row)
    return checks, results

if __name__ == '__main__':
    checks, results = run_regression()
    for row in results:
        print(f"Lvl {row['level']}, exp {row['exp_to_next']}, "+
              ', '.join(f'{cap}: {n} nagrod' for cap, n in row['examples'].items()))
    print(f'v11 PROGRESSION DIAGNOSTIC: {checks} checks PASS')
