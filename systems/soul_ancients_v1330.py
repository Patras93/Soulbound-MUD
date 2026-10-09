# -*- coding: utf-8 -*-
"""Soulbound v1.33.0: deterministic Soul evolution and authored Ancient phases.

Read-only progression is derived from existing persisted Soul Level, skill level,
Soul Weapon Mastery; no new account columns or skill replacements are necessary.
The named ancients use the existing real boss/summon combat system. UOSS bosses
are deliberately excluded from this authored extension.
"""
from __future__ import annotations

EVOLUTION_THRESHOLDS = ((100, 100), (300, 300), (600, 600))
STAGE_NAMES = ('Podstawowa', 'Przebudzona', 'Wzmocniona', 'Transcendentna')
WEAPON_MILESTONES = ((150, 2.0), (350, 4.0), (600, 6.0))
ANCIENT_STYLES = {
    'v1310_anc_deep_boss': ('earth', 'fire', 'physical', 'earth'),
    'v1310_anc_sky_boss': ('lightning', 'ice', 'magic', 'lightning'),
    'v1310_anc_lost_boss': ('arcane', 'dark', 'fire', 'arcane'),
    'v1310_anc_orc_boss': ('dark', 'earth', 'lightning', 'dark'),
}

def evolution_stage(skill_level, soul_level):
    return sum(int(skill_level) >= sl and int(soul_level) >= so for sl, so in EVOLUTION_THRESHOLDS)

def evolution_power_multiplier(skill_level, soul_level):
    """Small bonus atop canonical skill-level multiplier, never a replacement."""
    return 1.0 + 0.04 * evolution_stage(skill_level, soul_level)

def weapon_resonance_percent(mastery_level):
    for level, percent in reversed(WEAPON_MILESTONES):
        if int(mastery_level) >= level:
            return percent
    return 0.0

def ancient_attack(template_id, turn, stage):
    """Pure combat profile for the four named Starożytni; None for other mobs."""
    # The live world wraps bosses in terrain/world variants.
    # Preserve the authored combat profile on those runtime templates.
    cycle = ANCIENT_STYLES.get(str(template_id).split('__', 1)[0])
    if cycle is None:
        return None
    phase = max(0, min(3, int(stage)))
    # Effects alternate even while new helpers spawn every 3 boss actions.
    element = cycle[(max(1, int(turn)) - 1 + phase) % len(cycle)]
    if turn % 5 == 0:
        return {'element': element, 'damage_type': 'magic', 'damage_multiplier': 1.20 + .12*phase,
                'defense_factor': .78, 'drain_pct': .12, 'special': 'Rozdarcie Starożytnych'}
    if turn % 3 == 0:
        return {'element': element, 'damage_type': 'magic' if element != 'physical' else 'physical',
                'damage_multiplier': 1.15 + .08*phase,
                'defense_factor': .88, 'drain_pct': 0.0, 'special': 'Echo Pradawnych'}
    return {'element': element, 'damage_type': 'physical' if element == 'physical' else 'magic',
            'damage_multiplier': 1.0, 'defense_factor': 1.0, 'drain_pct': 0.0, 'special': ''}

def audit():
    assert [evolution_stage(k,k) for k in (1,100,300,600,800)] == [0,1,2,3,3]
    assert evolution_stage(600,90)==0
    assert [weapon_resonance_percent(x) for x in (1,150,350,600,800)] == [0,2,4,6,6]
    assert ancient_attack('goblin',5,2) is None
    assert ancient_attack('v1310_anc_sky_boss__terrain_v0362_750', 5, 2) is not None
    for ident in ANCIENT_STYLES:
        phases={ancient_attack(ident,t,p)['element'] for p in range(4) for t in range(1,9)}
        assert len(phases)>=3
        assert ancient_attack(ident,5,3)['drain_pct']>0
    return {'skills':3,'weapon_tiers':3,'ancients':len(ANCIENT_STYLES)}
