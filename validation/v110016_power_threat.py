"""Regression of separate level, combat-power and danger speech."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
exp = (root/'player/session_mixins/exp_terrain.py').read_text(encoding='utf-8')
combat = (root/'player/session_mixins/combat_damage.py').read_text(encoding='utf-8')
profile = (root/'player/session_mixins/character_profile.py').read_text(encoding='utf-8')
checks = [
    'def combat_power_explanation_v110016' in exp,
    'def exp_area_safety_summary_v110016' in exp,
    'gap >= 20' in exp,
    'nie zastępuje poziomu postaci' in exp,
    'area_id == "trening"' in exp,
    'area_id == "mythic_crypt"' in exp,
    'area_id == "krypta"' in exp,
    'self.exp_area_safety_summary_v110016(area, room_id=room_id)' in exp,
    'self.exp_area_safety_summary_v110016(area, room_id=c.room_id)' in profile,
    'Ocena zagrożenia wynika z prognozy tego starcia' in combat,
]
assert all(checks), [i for i, ok in enumerate(checks) if not ok]
print(f'v11.00.16 POWER AND THREAT: {len(checks)} checks PASS')
