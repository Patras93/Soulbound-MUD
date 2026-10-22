# -*- coding: utf-8 -*-
"""v22: controlled expansion of eight existing OLC domains.

Native ancient bosses (v500) and their UOSS equivalents are NOT the same
thing. Never modify UOSS, real player stats, progression caps or saved XP.
"""
import json
from systems.summon_ai_v1200 import CLASS_AI
from systems.world_events_v12812 import EVENTS

ANCIENT_FIELD = 'olc_ancient_phases'
ANCIENT_ELEMENTS = frozenset(('fire','ice','lightning','dark','holy','earth',
                              'water','wind','arcane','poison','shadow','physical'))
SUMMON_FIELDS = frozenset(('ability', 'role', 'bonus_percent',
    'guard_threshold_percent', 'execute_threshold_percent', 'tactic_interval'))
SUMMON_ROLES = frozenset(('heal','guard','mark','curse','slow','execute'))
WORLD_FIELDS = frozenset(('combat_xp_bonus_percent','event_cycle_minutes','event_order',
    'event_offset_minutes','multi_cap_bonus_percent','multi_cap_category_bonus',
    'multi_cap_all_owned_classes'))
CAP_CATEGORIES = frozenset(('postać','dusza','soul tier','broń duszy','statystyki',
                            'klasy','profesje','narzędzia','skille','wzniesienia'))


def validate_ancient(value):
    """Three authored-ancient phases, in HP order. Explicit, bounded inputs."""
    if type(value) is not list or len(value) != 3:
        raise ValueError('Pradawny: JSON musi zawierać dokładnie 3 fazy.')
    previous = 101
    for i, row in enumerate(value, 1):
        if type(row) is not dict or set(row) != {'hp_percent', 'name', 'attack_percent', 'element', 'duration_seconds'}:
            raise ValueError(f'Pradawny: niepoprawne pola fazy {i}.')
        pct = row['hp_percent']
        if type(pct) is not int or not 1 <= pct < previous:
            raise ValueError('Pradawny: progi HP całkowite 1–99, ściśle malejące.')
        previous = pct
        name = row['name']
        if type(name) is not str or not 1 <= len(name.strip()) <= 70 or any(ord(c) < 32 for c in name):
            raise ValueError('Pradawny: nazwa fazy 1–70 znaków.')
        if type(row['attack_percent']) is not int or not 100 <= row['attack_percent'] <= 400:
            raise ValueError('Pradawny: procent ataku 100–400 (bez osłabiania bossa).')
        if type(row['element']) is not str or row['element'] not in ANCIENT_ELEMENTS:
            raise ValueError('Pradawny: nieznany żywioł.')
        if type(row['duration_seconds']) is not int or not 1 <= row['duration_seconds'] <= 180:
            raise ValueError('Pradawny: czas 1–180 sekund.')
    return True


def validate_summons(value):
    if type(value) is not dict or len(value) > len(CLASS_AI):
        raise ValueError('Przywołania: wymagany słownik klas.')
    for cls, edits in value.items():
        if cls not in CLASS_AI or type(edits) is not dict or not edits or not set(edits) <= SUMMON_FIELDS:
            raise ValueError(f'Przywołania: nieznana klasa lub pole {cls}.')
        if 'ability' in edits:
            name = edits['ability']
            if type(name) is not str or not 1 <= len(name.strip()) <= 70 or any(ord(c) < 32 for c in name):
                raise ValueError('Nazwa umiejętności przywołania: 1–70 znaków.')
        if 'role' in edits and (type(edits['role']) is not str or edits['role'] not in SUMMON_ROLES):
            raise ValueError('Rola: heal/guard/mark/curse/slow/execute.')
        if 'bonus_percent' in edits and (type(edits['bonus_percent']) is not int or not 100 <= edits['bonus_percent'] <= 300):
            raise ValueError('Bonus przywołania: procent 100–300; nigdy poniżej oryginału.')
        for field, low, high in (('guard_threshold_percent',5,100),
                                 ('execute_threshold_percent',1,95),
                                 ('tactic_interval',1,12)):
            if field in edits and (type(edits[field]) is not int or not low <= edits[field] <= high):
                raise ValueError(f'Przywołanie {cls}.{field}: zakres {low}–{high}.')
    return True


def validate_world(value):
    if type(value) is not dict or not set(value) <= WORLD_FIELDS:
        raise ValueError('Reguły świata: nieznane pole.')
    for key, low, high in (('combat_xp_bonus_percent',100,300),
                           ('event_cycle_minutes',30,720),
                           ('event_offset_minutes',0,719),
                           ('multi_cap_bonus_percent',100,1000)):
        if key in value and (type(value[key]) is not int or not low <= value[key] <= high):
            raise ValueError(f'{key}: liczba całkowita {low}–{high}.')
    if 'multi_cap_all_owned_classes' in value and type(value['multi_cap_all_owned_classes']) is not bool:
        raise ValueError('multi_cap_all_owned_classes: true lub false.')
    if 'multi_cap_category_bonus' in value:
        factors = value['multi_cap_category_bonus']
        if type(factors) is not dict or not set(factors) <= CAP_CATEGORIES:
            raise ValueError('Multi Cap: nieznane kategorie.')
        for label, factor in factors.items():
            if type(factor) is not int or not 100 <= factor <= 1000:
                raise ValueError(f'Multi Cap {label}: liczba 100–1000 procent.')
    if 'event_order' in value:
        known = {e[0] for e in EVENTS}
        seq = value['event_order']
        if type(seq) is not list or len(seq) != len(known) or any(type(x) is not str for x in seq) or set(seq) != known:
            raise ValueError('Kolejność wydarzeń: dokładnie cztery oryginalne ID, bez duplikatów.')
    return True


def stage_extra(service, category, key, field, raw):
    from systems.live_olc24_revolution import stage as stage_v24
    if stage_v24(service,category,key,field,raw): return True
    import copy
    categories = {'przywolanie': 'summon_edits', 'summon': 'summon_edits',
                  'swiat': 'world_overrides', 'world': 'world_overrides'}
    section = categories.get(category)
    if not section:
        return False
    staged = copy.deepcopy(service.draft)
    reset = str(raw).casefold().strip() in ('auto','automatyczny')
    if section == 'summon_edits':
        if key not in CLASS_AI or field not in SUMMON_FIELDS:
            raise ValueError('Przywołanie: podaj znaną klasę i pole ability/role/bonus_percent.')
        if reset:
            staged[section].get(key, {}).pop(field, None)
            if not staged[section].get(key): staged[section].pop(key, None)
        else:
            if field in ('bonus_percent','guard_threshold_percent','execute_threshold_percent','tactic_interval'):
                # int(string,10) rejects floats, NaN and booleans.
                try: val = int(raw,10)
                except (TypeError,ValueError): raise ValueError('Wymagany całkowity procent.')
            else: val = str(raw)
            staged[section].setdefault(key, {})[field] = val
    else:
        if key != 'global' or field not in WORLD_FIELDS:
            raise ValueError('Świat: użyj admin live edytuj swiat global POLE.')
        if reset: staged[section].pop(field, None)
        elif field in ('event_order','multi_cap_category_bonus'):
            try: staged[section][field] = json.loads(raw)
            except (ValueError, TypeError): raise ValueError('Pole wymaga poprawnego JSON.')
        elif field == 'multi_cap_all_owned_classes':
            if str(raw).lower() not in ('true','false'):
                raise ValueError('Użyj true lub false.')
            staged[section][field] = str(raw).lower() == 'true'
        else:
            try: staged[section][field] = int(raw,10)
            except (ValueError, TypeError): raise ValueError('Wymagana liczba całkowita.')
    service.validate(staged)
    service.draft = staged
    return True


def extra_preview(service, category, key, field):
    from systems.live_olc24_revolution import preview as preview_v24
    result=preview_v24(service,category,key,field)
    if result is not None: return result
    categories = {'przywolanie':'summon_edits', 'summon':'summon_edits',
                  'swiat':'world_overrides', 'world':'world_overrides'}
    section = categories.get(category)
    if not section: return None
    if section == 'summon_edits':
        if key not in CLASS_AI or field not in SUMMON_FIELDS:
            raise ValueError('Nieznane przywołanie lub pole.')
        base = CLASS_AI[key]
        natural = {'ability':base[0], 'role':base[1], 'bonus_percent':100,
                   'guard_threshold_percent':80, 'execute_threshold_percent':35,
                   'tactic_interval':3}[field]
        active = service.active[section].get(key, {}).get(field)
        draft = service.draft[section].get(key, {}).get(field)
    else:
        if key != 'global' or field not in WORLD_FIELDS:
            raise ValueError('Świat: global combat_xp_bonus_percent/event_cycle_minutes/event_order.')
        natural = {'combat_xp_bonus_percent':100, 'event_cycle_minutes':180,
                   'event_offset_minutes':0, 'multi_cap_bonus_percent':100,
                   'multi_cap_category_bonus':{}, 'multi_cap_all_owned_classes':False,
                   'event_order':[x[0] for x in EVENTS]}[field]
        active = service.active[section].get(field)
        draft = service.draft[section].get(field)
    value = draft if draft is not None else (active if active is not None else natural)
    formatted = json.dumps(value,ensure_ascii=False) if isinstance(value, (list,dict,bool)) else str(value)
    return (f'OLC23 {category}/{key}/{field}: obecnie {active if active is not None else natural} '
            f'({"ręczne" if active is not None else "auto"}); w projekcie: '
            f'{draft if draft is not None else "auto"}. Do skopiowania: '
            f'admin live edytuj {category} {key} {field} | {formatted}. '
            'Aby przywrócić: wpisz auto. Publikacja: admin live aktywuj POTWIERDZAM.')


def ordinary_reward_bonus(amount, *, exact=False):
    """Extra XP only; exact UOSS and exact fixed source rewards untouched."""
    from systems.live_olc22_state import WORLD_OVERRIDES
    base = max(0,int(amount))
    if exact or base == 0: return base
    factor = int(WORLD_OVERRIDES.get('combat_xp_bonus_percent',100))
    return (base * factor + 50)//100
