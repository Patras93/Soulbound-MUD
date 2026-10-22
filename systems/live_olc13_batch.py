# -*- coding: utf-8 -*-
"""v16.00.0 OLC: atomic, bounded edits for EXISTING catalogue entries.

No game code is executed from player input. No side effects on preview or failed
validation. Publication still uses the original live-content SQLite revision.
"""
import copy
import json
from data.quests import QUESTS
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from data.crafting_recipes import CRAFT_RECIPES
from core.classes_skills import CLASS_SKILLS
from systems.live_quest_olc_v1209 import (QUEST_XP_ALIASES, QUEST_AUTO_FIELDS,
                                            parse_quest_edit)
from systems.live_olc6_skill_editor import stage_existing_skill
from systems.live_content_v1204 import _integer

MAX_BATCH = 100
CATEGORIES = {
    'quest': 'quest_edits', 'zadanie': 'quest_edits',
    'surowiec': 'resource_edits', 'resource': 'resource_edits',
    'skill': 'skill_edits', 'umiejetnosc': 'skill_edits',
    'mob': 'mob_edits', 'potwor': 'mob_edits',
    'receptura': 'recipe_edits', 'recipe': 'recipe_edits',
    'przedmiot': 'item_edits', 'item': 'item_edits',
}
QUEST_FIELDS = frozenset(('reward_xp', 'xp_postaci', 'xp_bieglosci', 'xp_duszy',
                          'xp_statystyk', 'reward_class_xp', 'reward_soul_xp',
                          'reward_stat_xp', 'reward_profession_xp', 'reward_tool_xp',
                          'xp_profesji', 'xp_narzedzia', 'reward_silver', 'reward_gold',
                          'reward_mithril', 'repeat_cooldown'))
RESOURCE_FIELDS = frozenset(('prof_fixed','tool_fixed','prof_scale','tool_scale',
                             'prof_mode','tool_mode'))
SKILL_FIELDS = frozenset(('mana','cooldown','mult','unlock'))
MOB_FIELDS = frozenset(('respawn_seconds','class_xp_reward','soul_reward',
                        'stat_reward','silver','gold','mithril'))
RECIPE_FIELDS = frozenset(('min_profession_level', 'quantity', 'min_tool_level', 'tool_xp'))
ITEM_FIELDS = frozenset(('price', 'required_level', 'heal', 'defense',
                         'attack', 'magic_attack', 'magic_defense', 'weapon_power'))
FIELDS = {'quest_edits':QUEST_FIELDS, 'resource_edits':RESOURCE_FIELDS,
          'skill_edits':SKILL_FIELDS, 'mob_edits':MOB_FIELDS,
          'recipe_edits':RECIPE_FIELDS, 'item_edits':ITEM_FIELDS}
RESOURCE_TYPES = frozenset(('resource','material','craft_material',
                            'gem_raw','archaeology_find'))


def _catalogue(section):
    if section == 'quest_edits': return QUESTS
    if section == 'mob_edits': return MOB_TEMPLATES
    if section == 'recipe_edits': return CRAFT_RECIPES
    if section == 'item_edits': return ITEMS
    if section == 'skill_edits':
        return {str(row['id']): row for rows in CLASS_SKILLS.values() for row in rows}
    return {key: row for key,row in ITEMS.items()
            if isinstance(row,dict) and row.get('type') in RESOURCE_TYPES}


def _selection(category, prefix, field):
    section = CATEGORIES.get(str(category).lower())
    if not section:
        raise ValueError('Grupa: quest, surowiec, skill, mob, receptura albo przedmiot.')
    if field not in FIELDS[section]:
        raise ValueError(f'{category}: niedozwolone pole grupowe. Dozwolone: '
                         + ', '.join(sorted(FIELDS[section])))
    if not isinstance(prefix,str) or not 3 <= len(prefix) <= 80 or not all(
            c.isascii() and (c.isalnum() or c == '_') for c in prefix):
        raise ValueError('Prefiks ID: 3–80 znaków ASCII (litery, cyfry, _).')
    catalog = _catalogue(section)
    matches = sorted(k for k in catalog if k.startswith(prefix))
    if not matches:
        raise ValueError(f'Nie znaleziono ID rozpoczynających się od {prefix}.')
    if len(matches) > MAX_BATCH:
        raise ValueError(f'Znaleziono {len(matches)} pozycji; maks. {MAX_BATCH}. '
                         'Podaj dłuższy prefiks, by uniknąć przypadkowej edycji.')
    return section, catalog, matches


def _field(section, field):
    return QUEST_XP_ALIASES.get(field, field) if section=='quest_edits' else field


def _current(service, section, catalog, key, field, staged=False):
    canonical = _field(section, field)
    overrides = service.draft if staged else service.active
    row = overrides.get(section, {}).get(key, {})
    if canonical in row:
        return row[canonical]
    if section == 'resource_edits':
        return 'auto (EXP zależy od czynności i poziomu)'
    original = catalog[key]
    if section == 'quest_edits' and canonical.startswith('olc_'):
        return 'auto (wyliczane podczas oddania questa)'
    if canonical in original:
        return original[canonical]
    return 'brak osobnego ustawienia'


def preview(service, category, prefix, field):
    """Read-only; bounded compact output suitable for NVDA."""
    section, catalog, keys = _selection(category, prefix, field)
    pieces=[]
    for key in keys[:12]:
        old=_current(service,section,catalog,key,field)
        new=_current(service,section,catalog,key,field,staged=True)
        def short(v):
            value = json.dumps(v, ensure_ascii=False, separators=(',',':'))
            return value[:100] + ('...' if len(value)>100 else '')
        if new != old:
            pieces.append(f'{key}: {short(old)} -> {short(new)}')
        else:
            pieces.append(f'{key}: {short(old)}')
    extra=(f'; pozostałe {len(keys)-12} ID' if len(keys)>12 else '')
    return (f'OLC PODGLĄD GRUPY: {category}, prefiks {prefix}, pole {field}; '
            f'dopasowania {len(keys)}, maks. {MAX_BATCH}. '
            + '; '.join(pieces)+extra+'. Niczego nie zapisano. '
            f'Zmiana: admin live grupazmien {category} {prefix} {field} | WARTOSC.')


def _resource_update(staged, key, field, value):
    side=field.split('_',1)[0]
    entry=staged['resource_edits'].setdefault(key,{})
    lowval=str(value).strip().casefold()
    if lowval in ('auto','automatyczny'):
        # Reset the selected PROF or TOOL side, not the other side.
        for suffix in ('mode','fixed','scale','xp','percent'):
            entry.pop(side+'_'+suffix,None)
    elif field.endswith('_mode'):
        if lowval not in ('auto','manual','percent'):
            raise ValueError('Tryb: auto, manual albo percent.')
        if lowval == 'auto':
            for suffix in ('mode','fixed','scale','xp','percent'):
                entry.pop(side+'_'+suffix,None)
        else:
            if (side+'_'+('fixed' if lowval=='manual' else 'scale')) not in entry:
                raise ValueError('Najpierw ustaw kwotę fixed albo procent scale.')
            entry[field]=lowval
    else:
        fixed=field.endswith('_fixed')
        entry[field]=_integer(value,0,10**12 if fixed else 1000,field)
        entry[side+'_mode']='manual' if fixed else 'percent'
    if not entry:
        staged['resource_edits'].pop(key,None)


def stage(service, category, prefix, field, raw_value):
    """Validate the whole batch once, commit draft only upon complete success."""
    section, catalog, keys = _selection(category,prefix,field)
    text=str(raw_value).strip()
    if not text:
        raise ValueError('Brak nowej wartości.')
    staged=copy.deepcopy(service.draft)
    for key in keys:
        if section=='quest_edits':
            canonical=_field(section,field)
            if canonical in QUEST_AUTO_FIELDS and text.casefold() in ('auto','automatyczny'):
                entry=staged['quest_edits'].get(key,{})
                entry.pop(canonical,None)
                if not entry: staged['quest_edits'].pop(key,None)
            else:
                name, value=parse_quest_edit(field,text)
                staged['quest_edits'].setdefault(key,{})[name]=value
        elif section=='resource_edits':
            _resource_update(staged,key,field,text)
        elif section=='skill_edits':
            # Must have this field in its own real skill definition.
            stage_existing_skill(staged,key,field,text)
        elif section in ('mob_edits', 'recipe_edits', 'item_edits'):
            if text.casefold() in ('auto','automatyczny'):
                entry=staged[section].get(key,{})
                entry.pop(field,None)
                if not entry: staged[section].pop(key,None)
            else:
                if section in ('recipe_edits', 'item_edits') and field not in catalog[key]:
                    raise ValueError(f'{key}: pole {field} nie istnieje; nie dodaję nowych mechanik.')
                minimum = 1 if field in ('min_profession_level','min_tool_level','required_level','quantity','heal','defense') else 0
                maximum = 800 if field in ('min_profession_level','min_tool_level','required_level') else 10000 if field == 'quantity' else 10**15
                amount=_integer(text,minimum,maximum,field)
                staged[section].setdefault(key,{})[field]=amount
    # Existing validators cover quest cooldown, item types, skill aliases,
    # content size, caps, and all other live-world invariants.
    outcome=service.validate(staged)
    service.draft=staged
    return (f'OLC: przygotowano {len(keys)} zmian {category}/{prefix}/{field} '
            f'do {text}. {outcome}. '
            'Nie opublikowano; użyj admin live porownaj, sprawdz, aktywuj POTWIERDZAM.')
