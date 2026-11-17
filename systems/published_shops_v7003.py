"""Read-only loading of published historical content. No runtime editor."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from core import live_level_caps_v5200 as caps
from data.items import ITEMS
from data.shops import SHOPS
from systems.endless_loot_v5600 import eligible_normal_equipment_drop_v5600
from systems.infinite_equipment import (
    infinite_equipment_variant_id, register_infinite_equipment_variant,
    infinite_equipment_power_multiplier, shop_variant_price_v7003,
)
from core.equipment_growth_v5300 import infinite_equipment_requirement
CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'shop_progression_v7003.json'
_settings = None
def _token(raw, what):
    if not isinstance(raw, str) or not 1 <= len(raw) <= 100 or not all(
        ch.isascii() and (ch.isalnum() or ch in '_-') for ch in raw
    ):
        raise ValueError(f'{what}: ID z liter, cyfr, - i _, do 100 znakow.')
    return raw
def _stage(raw):
    if type(raw) is int:
        level = raw
    elif isinstance(raw, str) and raw.isascii() and raw.isdecimal() and len(raw) <= 7:
        level = int(raw)
    else:
        raise ValueError('ETAP: liczba 801..1000000.')
    if not 801 <= level <= 1000000:
        raise ValueError('ETAP: liczba 801..1000000.')
    return level
def _allowed(room, item, stage):
    room = _token(room, 'POKOJ')
    item = _token(item, 'ID_EQ')
    stage = _stage(stage)
    if room not in SHOPS or item not in SHOPS[room]:
        raise ValueError('Przedmiot musi byc w statycznej ofercie podanego sklepu.')
    original = ITEMS.get(item)
    if (not eligible_normal_equipment_drop_v5600(item, {'level':stage})
            or not isinstance(original, dict)
            or original.get('class_shop_item') or original.get('fur_shop_gold_cost') is not None
            or original.get('fur_shop_token') or original.get('uoss_unique')
            or original.get('bound_to_character')):
        raise ValueError('Dostepne tylko zwykle EQ, bez narzedzi, tokenow, unikatow i przedmiotow klasowych.')
    return room, item, stage
def _caps_allow(stage):
    return all(caps.cap(axis) is None or caps.cap(axis) >= stage for axis in ('eq','bieglosc'))
def _compute(room, item, stage):
    room, item, stage = _allowed(room, item, stage)
    rank = (stage-600 + 9)//10
    full_stage = 600+10*rank
    silver = shop_variant_price_v7003(item, rank)
    return dict(room=room, item=item, stage=stage, full_stage=full_stage,
                rank=rank, price=int(silver), requirement=infinite_equipment_requirement(full_stage),
                multiplier=infinite_equipment_power_multiplier(rank, 'r'),
                id=infinite_equipment_variant_id(item, 'shop', 'r', rank),
                active=_caps_allow(stage))
def _read():
    if not CONFIG_PATH.exists():
        return {}
    obj = json.loads(CONFIG_PATH.read_text('utf-8'))
    if (type(obj) is not dict or obj.get('schema') not in (1, 2)
            or type(obj.get('rooms')) is not dict or len(obj['rooms']) > 120):
        raise ValueError('Niepoprawny plik progresji sklepow (schema 1 lub 2).')
    result = {}
    for room, records in obj['rooms'].items():
        many = records if isinstance(records, list) else [records]
        if not 1 <= len(many) <= 8:
            raise ValueError('Sklep: maksymalnie 8 wariantow EQ.')
        seen=set()
        variants=set()
        for entry in many:
            if type(entry) is not dict or set(entry) != {'item','stage'}:
                raise ValueError('Niepoprawna konfiguracja sklepu.')
            _allowed(room, entry['item'], entry['stage'])
            pair=(entry['item'],entry['stage'])
            if pair in seen:raise ValueError('Zdublowany wariant sklepu.')
            variant=_compute(room,entry['item'],entry['stage'])['id']
            if variant in variants:raise ValueError('Powtorzony rangowy wariant EQ w sklepie.')
            variants.add(variant)
            seen.add(pair)
        result[room] = many if isinstance(records,list) else records
    return result
def _entries(value):
    return value if isinstance(value,list) else [value]
def current():
    global _settings
    if _settings is None:
        _settings = _read()
    return dict(_settings)
def append_progression_offer(room, offers):
    """Only ordinary opt-in shop variants, preserving static prices and lots."""
    entry = current().get(room)
    if entry is None:
        return offers
    expanded=list(offers)
    for cfg in _entries(entry):
        data=_compute(room,cfg['item'],cfg['stage'])
        if not data['active'] or cfg['item'] not in offers:continue
        variant=register_infinite_equipment_variant(cfg['item'],'shop','r',data['rank'])
        if variant!=data['id'] or variant not in ITEMS:continue
        record=ITEMS[variant]
        record['currency']='silver'
        record['price']=data['price']
        record['shop_tier_v7003']=True
        if variant not in expanded:expanded.append(variant)
    return expanded
