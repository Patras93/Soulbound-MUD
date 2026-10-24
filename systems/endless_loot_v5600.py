# -*- coding: utf-8 -*-
"""v56: extend authored NORMAL combat equipment drops at genuine infinite floors.

Never adds rolls, changes authored probabilities, rerolls per party member,
converts crafting resources/keys/currencies, or touches UOSS unique rewards.
"""
from __future__ import annotations
from data.items import ITEMS
from systems.infinite_equipment import (
    infinite_source_profile, infinite_equipment_variant_for_drop,
    infinite_equipment_variant_id, infinite_equipment_power_multiplier,
)
from core.equipment_growth_v5300 import infinite_equipment_requirement


def eligible_normal_equipment_drop_v5600(item_id, template):
    """Check base item identity; never turn unique/special UOSS loot into generics."""
    key = str(item_id or '')
    item = ITEMS.get(key)
    if not isinstance(item, dict) or key.startswith(('deepq_', 'uoss_')):
        return False
    if not isinstance(template, dict) or not infinite_source_profile(template):
        return False
    if item.get('uoss_unique') or item.get('uoss_superboss') or item.get('uoss_superboss_id') or item.get('fur_shop_token'):
        return False
    if item.get('type') not in ('weapon', 'armor', 'equipment') and not item.get('slot'):
        return False
    return True


def convert_normal_equipment_drop_v5600(item_id, template):
    """Called AFTER a single authored successful roll, BEFORE party distribution."""
    if not eligible_normal_equipment_drop_v5600(item_id, template):
        return str(item_id)
    return infinite_equipment_variant_for_drop(item_id, template)


def preview_normal_equipment_drop_v5600(item_id, template):
    """Read-only: doesn't register ITEMS, roll RNG, consume resources, or write SQLite."""
    profile = infinite_source_profile(template)
    if not profile:
        return 'DROP EQ: to zrodlo nie ma progresji glebinowej ponad 600. Bez zmian.'
    if not eligible_normal_equipment_drop_v5600(item_id, template):
        return 'DROP EQ: przedmiot nie jest zwyklym EQ. Materialy, klucze, unikaty i waluty bez zmian.'
    rank = int(profile['rank'])
    stage = int(profile['effective_stage'])
    req = infinite_equipment_requirement(stage)
    vid = infinite_equipment_variant_id(item_id,profile['source'],profile['grade'],rank)
    mult = infinite_equipment_power_multiplier(rank,profile['grade'])
    return (f'DROP EQ: {item_id}; zrodlo {profile["source"]}; etap {stage}; '
        f'wymagana bieglosc {req}; moc x{mult:.3f}; ID: {vid}. '
        'Szanse dropu i nagrody calej druzyny bez zmian. Tylko podglad.')


def source_template_v5600(kind, floor):
    """Explicit, read-only owner preview only. No fabricated rank or boss status."""
    keys = {
        'krypta': 'crypt_floor', 'crypt': 'crypt_floor',
        'mityczna_krypta': 'mythic_crypt_floor', 'mythiccrypt': 'mythic_crypt_floor',
        'astral': 'astral_floor', 'wieza': 'astral_floor',
        'mityczny_astral': 'mythic_astral_floor', 'mythictower': 'mythic_astral_floor',
        'magitek': 'magitek_floor',
    }
    key = keys.get(str(kind or '').lower())
    if key is None:
        raise ValueError('Zrodlo: krypta, mityczna_krypta, astral, mityczny_astral, magitek.')
    raw = str(floor or '')
    if not raw.isascii() or not raw.isdecimal() or len(raw)>10 or not 1<=int(raw)<=1_000_000:
        raise ValueError('Pietro: podaj liczbe od 1 do 1000000.')
    return {key:int(raw)}
