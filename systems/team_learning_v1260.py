# -*- coding: utf-8 -*-
"""Battle-local enemy reactions to a powerful and fast attacking team."""
def enemy_team_pressure_v1260(mob, template):
    if not mob or any(template.get(x) for x in
            ('training_dummy','uoss_superboss','world_boss','boss','v1190_secret_guard')):
        return 1.0
    hits = max(0,int(getattr(mob,'player_hits',0) or 0))
    turns = max(0,int(getattr(mob,'combat_turn',0) or 0))
    # Learn over the encounter only: clear on next encounter, do not penalize
    # the beginner or allow 1-hit retaliations.
    if hits < 8 or turns < 3:
        return 1.0
    return 1.0 + min(.20, (hits-7) * .003)
