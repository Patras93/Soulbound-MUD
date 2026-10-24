# -*- coding: utf-8 -*-
"""v57: extend REAL infinite-floor boss chest gold after the authored roll.

No rerolls, no added items, no altered chest keys / boss state / recipient list.
Only the old gold plateau for Crypt, Mythic Crypt and Magitek is extended.
"""
from __future__ import annotations
from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, SILVER_PER_GOLD
from systems.infinite_equipment import infinite_source_profile

_SOURCES = {
    'krypta': ('crypt', 'crypt_floor'), 'crypt': ('crypt', 'crypt_floor'),
    'mityczna_krypta': ('mythic_crypt', 'mythic_crypt_floor'),
    'mythic_crypt': ('mythic_crypt', 'mythic_crypt_floor'),
    'magitek': ('magitek', 'magitek_floor'),
}
_SAFE_REWARD_GOLD = CURRENCY_SQLITE_SAFE_TOTAL // SILVER_PER_GOLD // 2


def chest_extension_v5700(kind, floor):
    """Return stage, multiplier without rolling random values or modifying ITEMS."""
    base = str(kind or '').lower()
    if base not in ('crypt','mythic_crypt','magitek'):
        return None
    if isinstance(floor,bool):return None
    try:
        n=int(floor)
    except (ValueError,TypeError,OverflowError):return None
    if n<1 or n>1_000_000:return None
    key = {'crypt':'crypt_floor','mythic_crypt':'mythic_crypt_floor','magitek':'magitek_floor'}[base]
    profile = infinite_source_profile({key:n})
    if not profile or profile['effective_stage']<=800:return None
    stage=profile['effective_stage']
    # Integer arithmetic: 3% per ten stages past 800, no floating-point coin errors.
    steps=(stage-800)//10
    return {'stage':stage, 'numerator':100+3*steps,'denominator':100,'source':base}


def extend_boss_chest_reward_v5700(kind,floor,reward):
    """Apply deterministic additive gold scaling to an already completed roll.

    Original item sequence and original dict are unchanged. Above SQLite-safe
    payout, give the safe maximum, never overflow the currency normalization.
    """
    if not isinstance(reward,dict):return reward
    profile=chest_extension_v5700(kind,floor)
    if profile is None:return reward
    try:gold=int(reward.get('gold',0))
    except (TypeError,ValueError,OverflowError):return reward
    if gold<=0:return reward
    enhanced=max(gold,min(_SAFE_REWARD_GOLD,(gold*profile['numerator'])//100))
    if enhanced==gold:return reward
    result=dict(reward)
    result['gold']=enhanced
    # Keep items, recipient lists, coins and all other authored rewards untouched.
    return result


def preview_chest_extension_v5700(kind,floor,original_gold):
    alias=_SOURCES.get(str(kind or '').lower())
    if alias is None:raise ValueError('Zrodlo: krypta, mityczna_krypta, magitek.')
    raw=str(floor or ''); money=str(original_gold or '')
    if not raw.isascii() or not raw.isdecimal() or len(raw)>7 or not 1<=int(raw)<=1_000_000:
        raise ValueError('Pietro: 1..1000000.')
    if not money.isascii() or not money.isdecimal() or len(money)>15 or not 1<=int(money)<=10**12:
        raise ValueError('Zloto bazowe: 1..1000000000000.')
    value=int(money);n=int(raw)
    profile=chest_extension_v5700(alias[0],n)
    if profile is None:
        return f'SKRZYNIA BOSS: {alias[0]} pietro {n}, zloto {value}. Brak premii ponad 800. Tylko podglad.'
    new=extend_boss_chest_reward_v5700(alias[0],n,{'gold':value,'items':[]})['gold']
    return (f'SKRZYNIA BOSS: {alias[0]}, pietro {n}, etap {profile["stage"]}, '
            f'bazowe zloto {value}, po premii {new}, bonus +{new-value}. '
            'Oryginalne losowanie, klucze, przedmioty i zasady druzyny bez zmian. Tylko podglad.')
