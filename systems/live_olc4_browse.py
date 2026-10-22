# -*- coding: utf-8 -*-
"""NVDA-friendly read-only catalog discovery. No database changes."""
from systems.live_olc_preview_v12010 import SECTIONS, FIELDS
from systems.live_content_v1204 import CLASS_SKILLS


def fields_for(service, category, ident):
    category = str(category).casefold()
    if category not in SECTIONS:
        raise ValueError('Nieznana kategoria OLC.')
    section, catalog = SECTIONS[category]
    if section == 'skill_edits':
        item = next((skill for rows in CLASS_SKILLS.values() for skill in rows if skill.get('id') == ident), None)
        if item is None: item = service.draft['skills'].get(ident)
    elif ident in catalog:
        item = catalog[ident]
    else:
        additions = {'quest_edits':'quests','room_edits':'rooms','mob_edits':'mobs',
                     'item_edits':'items','npc_edits':'npcs','recipe_edits':'recipes',
                     'shop_edits':'shops'}
        item = service.draft[additions[section]].get(ident) if section in additions else None
    if item is None:
        raise ValueError('Nieznany identyfikator. Najpierw wpisz admin live katalog KATEGORIA.')
    available = ({'name','desc','unlock','mana','mult','scale','effect','olc_status'}
                 if section == 'skill_edits' and ident in service.draft['skills']
                 else FIELDS[section])
    existing = sorted(set(item).intersection(available)) if isinstance(item, dict) else []
    if section == 'skill_edits' and ident not in service.draft['skills']:
        available = set(item).intersection(available) | ({'olc_status'} if item.get('kind') in ('damage','aoe_damage') and not any(x in item for x in ('mec_authored','mec_special','special','active_special','aoe','target_mode','v1100_dual_elements')) else set())
    example = existing[0] if existing else sorted(available)[0]
    return (f'OLC {category} {ident}: obsługiwane pola: {", ".join(sorted(available))}. '
            f'Obecnie zapisane w definicji: {", ".join(existing) or "lista pozycji"}. '
            f'Aktualna wartość pola: admin live edytuj {category} {ident} {example}')


def find_catalog(service, category, phrase='', page=1):
    category = str(category).casefold()
    if category not in SECTIONS:
        raise ValueError('Nieznana kategoria OLC.')
    if not 1 <= page <= 99999:
        raise ValueError('Strona poza zakresem.')
    section, registry = SECTIONS[category]
    if section == 'skill_edits':
        entries = {s['id']: s for skills in CLASS_SKILLS.values() for s in skills}
        entries.update(service.draft['skills'])
    else:
        entries = dict(registry)
        # Also expose additions prepared through OLC/JSON before publication.
        addition = {'room_edits':'rooms','mob_edits':'mobs',
                    'item_edits':'items','npc_edits':'npcs',
                    'quest_edits':'quests','recipe_edits':'recipes',
                    'shop_edits':'shops'}.get(section)
        if addition:
            entries.update(service.draft[addition])
    needle = str(phrase).casefold().strip()
    def label(obj, key):
        return str(obj.get('name', key)) if isinstance(obj, dict) else key
    found = [(key, label(obj,key)) for key,obj in entries.items()
             if needle in key.casefold() or needle in label(obj,key).casefold()]
    found.sort(key=lambda x: x[0])
    per_page = 12
    total = max(1, (len(found) + per_page - 1)//per_page)
    if page > total:
        raise ValueError(f'Brak strony {page}; dostępnych: {total}.')
    return (f'OLC katalog {category}, filtr „{needle or "wszystkie"}”: {len(found)} wyników, '
            f'strona {page}/{total}. ' +
            ('; '.join(f'{key} ({value[:55]})' for key,value in found[(page-1)*per_page:page*per_page])
             if found else 'Brak wyników.'))
