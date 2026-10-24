# -*- coding: utf-8 -*-
"""v70.00.3: explicit opt-in, up to eight ordinary EQ variants per shop.

Original shop inventory and prices are untouched. Config lives outside SQLite,
with safe atomic persistence. Generated IDs are stable and rebuild after restart.
"""
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

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'LIVE_CONTENT' / 'shop_progression_v7003.json'
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


def _save(updated):
    global _settings
    if len(updated)>120 or any(len(_entries(x))>8 for x in updated.values()):
        raise ValueError('Maksymalnie 120 sklepow i 8 wariantow na sklep.')
    parent = CONFIG_PATH.parent
    parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({'schema':2 if any(isinstance(x,list) for x in updated.values()) else 1,'rooms':updated}, ensure_ascii=False,
                         indent=2, sort_keys=True) + '\n'
    fd, tmp = tempfile.mkstemp(dir=str(parent), prefix='.shops7003_', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, CONFIG_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    _settings = dict(updated)


def describe(room=None):
    records = current()
    if room is not None:
        _token(room, 'POKOJ')
        if room not in SHOPS:
            raise ValueError('Nieznany sklep w katalogu SHOPS.')
        if room not in records:
            return f'SKLEP PROGRESJA {room}: WYLACZONA. Oryginalna oferta bez zmian.'
        descriptions=[]
        for entry in _entries(records[room]):
            d=_compute(room,entry['item'],entry['stage'])
            descriptions.append(f'{entry["item"]} etap {entry["stage"]}; '
                f'wariant {d["id"]}; cena {d["price"]} srebra; bieg {d["requirement"]}; '
                f'widoczna {"TAK" if d["active"] else "NIE: podnies limity"}')
        return (f'SKLEP PROGRESJA {room}: '+ ' | '.join(descriptions)+
                '. Oryginalne towary bez zmian.')
    return ('SKLEPY PROGRESJA: ustawionych '+str(len(records))+' sklepow; wariantow '+
            str(sum(len(_entries(v)) for v in records.values()))+'; '+
            (', '.join(sorted(records)[:12]) if records else 'brak')+
            '. Do 8 dodatkowych wariantow na sklep, domyslnie WYLACZONE.')


def preview(room, item, stage):
    d = _compute(room, item, stage)
    return (f'SKLEP PLAN: {room}, {item} etap {stage}: dodatkowe EQ {d["id"]}, '
            f'moc x{d["multiplier"]:.3f}, bieg {d["requirement"]}, cena {d["price"]} srebra; '
            f'limity pozwalaja {"TAK" if d["active"] else "NIE"}. '
            'Bez zmian; admin live sklepy progresja ustaw POKOJ ID_EQ ETAP POTWIERDZAM.')


def configure(room,item,stage):
    d=_compute(room,item,stage)
    if not d['active']:
        raise ValueError('Najpierw podnies w admin live limity eq i bieglosc przynajmniej do ETAP.')
    updated=current()
    updated[room]={'item':item,'stage':d['stage']}
    _save(updated)
    return 'SKLEP ZAPISANO: '+describe(room)


def extend(room,item,stage):
    d=_compute(room,item,stage)
    if not d['active']:
        raise ValueError('Najpierw podnies limity eq i bieglosc do ETAP.')
    updated=current()
    records=list(_entries(updated[room])) if room in updated else []
    if len(records)>=8:raise ValueError('Sklep ma juz 8 wariantow, najpierw usun jeden.')
    if any(_compute(room,x['item'],x['stage'])['id']==d['id'] for x in records):
        raise ValueError('Ten rangowy wariant juz istnieje.')
    records.append({'item':item,'stage':d['stage']})
    updated[room]=records
    _save(updated)
    return 'SKLEP DODANO: '+describe(room)


def remove(room,item,stage):
    room,item,stage=_allowed(room,item,stage)
    updated=current()
    records=list(_entries(updated[room])) if room in updated else []
    new=[x for x in records if not (x['item']==item and x['stage']==stage)]
    if len(new)==len(records):raise ValueError('Nie ma takiego wariantu.')
    if new:updated[room]=new
    else:updated.pop(room,None)
    _save(updated)
    return 'SKLEP USUNIETO: '+describe(room)


def disable(room):
    _token(room,'POKOJ')
    updated=current()
    if room not in updated:
        return describe(room)
    updated.pop(room)
    _save(updated)
    return f'SKLEP {room}: wylaczono wariant EQ; oryginalne oferty bez zmian.'


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


HELP=('ADMIN LIVE POMOC 27: sklepy progresja status [POKOJ]; '
      'sklepy progresja prognoza POKOJ ID_EQ ETAP; '
      'sklepy progresja ustaw POKOJ ID_EQ ETAP POTWIERDZAM; '
      'sklepy progresja wylacz POKOJ POTWIERDZAM; '
      'sklepy progresja dodaj POKOJ ID_EQ ETAP POTWIERDZAM; '
      'sklepy progresja usun POKOJ ID_EQ ETAP POTWIERDZAM. '
      'Domyslnie wylaczone; tylko oryginalny zwykly EQ z oferty; do 8 dodatkowych wariantow na sklep. '
      'Kupno max jedna sztuka naraz. Wymagane limity eq i bieglosc >= ETAP. '
      'Osobny atomowy plik ustawien, bez SQLite i zmian istniejacych ofert.')

async def dispatch_v7003_shop(session,group,raw):
    args = str(raw or '').strip().split()
    if not ((group=='pomoc' and args==['27']) or
            (group in ('sklep','sklepy') and args[:1]==['progresja'])):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':output=HELP
        elif args==['progresja'] or args==['progresja','status']:
            output=describe()
        elif len(args)==3 and args[1]=='status':output=describe(args[2])
        elif len(args)==5 and args[1]=='prognoza':output=preview(args[2],args[3],args[4])
        elif len(args)==6 and args[1]=='ustaw' and args[5]=='POTWIERDZAM':
            output=configure(args[2],args[3],args[4])
        elif len(args)==6 and args[1]=='dodaj' and args[5]=='POTWIERDZAM':
            output=extend(args[2],args[3],args[4])
        elif len(args)==6 and args[1]=='usun' and args[5]=='POTWIERDZAM':
            output=remove(args[2],args[3],args[4])
        elif len(args)==4 and args[1]=='wylacz' and args[3]=='POTWIERDZAM':
            output=disable(args[2])
        else:raise ValueError('sklepy progresja status/prognoza/ustaw/wylacz; zmiana wymaga POTWIERDZAM.')
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,json.JSONDecodeError) as exc:
        output='ADMIN LIVE SKLEPY V70.00.3: '+str(exc)[:260]
    await session.send(output)
    return True
