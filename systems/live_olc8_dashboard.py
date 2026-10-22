# -*- coding: utf-8 -*-
"""v15: safe, short NVDA-friendly previews; no writes, no game events."""
import json
from data.crafting_recipes import CRAFT_RECIPES
from systems.live_olc_preview_v12010 import SECTIONS
from core.classes_skills import CLASS_SKILLS

ADDED = {'room_edits':'rooms','mob_edits':'mobs','item_edits':'items',
         'npc_edits':'npcs','quest_edits':'quests','recipe_edits':'recipes',
         'shop_edits':'shops'}


def _compact(value, length=650):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return text if len(text) <= length else text[:length - 3] + '...'


def describe_object(service, category, ident):
    category = str(category).casefold()
    if category not in SECTIONS:
        raise ValueError('Nieznana kategoria OLC; użyj admin live mozliwosci.')
    section, registry = SECTIONS[category]
    if section == 'skill_edits':
        base = next((s for rows in CLASS_SKILLS.values() for s in rows if s.get('id') == ident), None)
        base = base or service.draft['skills'].get(ident)
    else:
        base = registry.get(ident)
        base = base if base is not None else service.draft.get(ADDED.get(section, ''), {}).get(ident)
    if base is None:
        raise ValueError('Nieznany obiekt. Użyj admin live katalog KATEGORIA [FRAZA].')
    active = service.active.get(section, {}).get(ident, {})
    draft = service.draft.get(section, {}).get(ident, {})
    # Current runtime catalog already includes published patches, so do not
    # double-apply or leak long object/quest descriptions to a screen reader.
    return (f'OLC {category}/{ident}, rewizja {service.revision}. '
            f'Nazwa: {base.get("name", ident) if isinstance(base, dict) else ident}. '
            f'Aktualne pola: {_compact(base)}. '
            f'Aktywny zapis OLC: {_compact(active)}. '
            f'Przygotowane: {_compact(draft)}. '
            f'Podgląd konkretnego pola: admin live edytuj {category} {ident} POLE. '
            'Odczyt niczego nie publikuje.')


def profession_recipes(service, phrase):
    words = str(phrase).split()
    page = int(words.pop()) if words and words[-1].isdigit() else 1
    if not 1 <= page <= 9999:
        raise ValueError('Niepoprawna strona.')
    needle = ' '.join(words).casefold().strip()
    if not needle:
        raise ValueError('Użycie: admin live recepturyprof Kowalstwo [strona].')
    entries = dict(CRAFT_RECIPES)
    entries.update(service.draft['recipes'])
    found = [(ident, record) for ident, record in entries.items()
             if needle in str(record.get('profession', '')).casefold()]
    found.sort(key=lambda x:x[0])
    per_page = 12
    pages = max(1, (len(found) + per_page - 1) // per_page)
    if page > pages:
        raise ValueError(f'Nie ma strony {page}/{pages}.')
    return (f'Receptury profesji {needle}: {len(found)}; strona {page}/{pages}. ' +
            ('; '.join(f'{ident} ({row.get("name", ident)}, lvl {row.get("min_profession_level", 1)})'
                      for ident,row in found[(page-1)*per_page:page*per_page])
             if found else 'Brak dopasowanych receptur.') +
            ' Edytuj przez: admin live pola receptura ID.')
