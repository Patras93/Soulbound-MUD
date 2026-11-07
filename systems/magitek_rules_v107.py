# -*- coding: utf-8 -*-
"""Exact behavioural rules and guarded Soulbound balance for Magitek.

Pure functions are testable without starting the game or mutating a player DB.
Values unknown in UOSS (damage ratios, hit chances, status duration) are
explicit Soulbound preliminary balance, never claimed as source numbers.
"""
from __future__ import annotations
from dataclasses import dataclass, field

ELEMENTS = frozenset(('fire', 'ice', 'lightning', 'poison'))
INFUSING_SKILLS = {
    'firebeam': 'fire', 'icebeam': 'ice',
    'boltbeam': 'lightning', 'bioblast': 'poison',
}
INFUSION_COOLDOWN_SECONDS = 18.0  # Soulbound tuning, UOSS calls it 'brief'

@dataclass
class MagitekState:
    infused_element: str | None = None
    last_infusion_element_times: dict[str,float] = field(default_factory=dict)
    ward: str | None = None
    ward_until: float = 0.0
    runic_until: float = 0.0
    linked_magicite: str | None = None
    magicite_unlocked: bool = False


def combat_attack_stats(strength, agility, magic_attack, *, ranged_weapon=False):
    """UOSS: weapon damage ignored; range selects AGI, otherwise STR."""
    physical = max(0, int(agility if ranged_weapon else strength))
    magic = max(0, int(magic_attack))
    return physical, magic


def attack_power(strength, agility, magic_attack, *, ranged_weapon=False):
    physical, magic = combat_attack_stats(strength, agility, magic_attack,
                                          ranged_weapon=ranged_weapon)
    # A provisional Soulbound hybrid weight, not an original UOSS coefficient.
    return max(1, (physical + magic) // 2)


def damage_defense_channel(skill_slug):
    return 'physical' if skill_slug == 'tekmissile' else 'magic'


def can_use_skill(slug, job_level, *, magicite_unlocked=False, linked_magicite=None):
    from core.magitek_v107 import skill_catalogue
    row = next((s for s in skill_catalogue() if s['v107_skill'] == slug), None)
    if row is None:
        return False, 'Nieznana umiejętność Magiteka.'
    if int(job_level) < row['unlock']:
        return False, f'Wymaga poziomu klasy {row["unlock"]}.'
    if slug == 'magicitelink' and (not magicite_unlocked or not linked_magicite):
        return False, 'Magicite Link wymaga indywidualnego odblokowania i powiązanego Magicite.'
    return True, ''


def apply_ward(state, skill_slug, now, duration):
    """Exactly one protective mode; Protect+Shell OR Protect+Reflect."""
    if skill_slug not in ('tekshield', 'tekbarrier'):
        raise ValueError('unknown ward')
    if duration <= 0:
        raise ValueError('duration must be positive')
    state.ward = skill_slug
    state.ward_until = float(now) + float(duration)
    return ('protect', 'shell') if skill_slug == 'tekshield' else ('protect', 'reflect')


def active_ward(state, now):
    if state.ward and float(now) < state.ward_until:
        return state.ward
    state.ward = None
    return None


def try_charge_missile(state, skill_slug, now, *, mastered, roll, chance=0.35):
    """Skill must land first; only Tek Mastery enables residual element charge."""
    if not mastered or skill_slug not in INFUSING_SKILLS:
        return False
    element = INFUSING_SKILLS[skill_slug]
    previous = state.last_infusion_element_times.get(element, -float('inf'))
    if float(now)-previous < INFUSION_COOLDOWN_SECONDS or not 0 <= roll <= 1:
        return False
    if roll >= chance:
        return False
    state.infused_element = element
    state.last_infusion_element_times[element] = float(now)
    return True


def consume_missile_charge(state, *, landed):
    """Never eat the charge if launch misses/aborts; single use on real hit."""
    if not landed:
        return None
    charge = state.infused_element
    state.infused_element = None
    return charge


def gravity_bomb_damage(current_hp, *, accuracy, roll):
    """UOSS: chance-based half CURRENT HP, never guaranteed."""
    if not 0 <= accuracy <= 1 or not 0 <= roll <= 1:
        raise ValueError('accuracy and roll must be probabilities')
    return int(max(0,int(current_hp)) // 2) if roll < accuracy else 0


def bio_poison_chance(willpower, skill_level):
    """Explicit preliminary Soulbound chance; source says Will raises it."""
    return min(0.85, 0.20 + min(0.40, max(0, int(willpower))/2000.0) +
               min(0.25, max(1,int(skill_level))/2400.0))


def runic_interception(*, magical_attack, roll, chance, wisdom, willpower, weapon_power):
    """Only incoming magic can be intercepted; heal MP, not HP."""
    if not magical_attack or not 0 <= chance <= 1 or not 0 <= roll <= 1 or roll >= chance:
        return False, 0
    restored_mp = max(1, (max(0,int(wisdom)) + max(0,int(willpower)) +
                          max(0,int(weapon_power))) // 12)
    return True, restored_mp
