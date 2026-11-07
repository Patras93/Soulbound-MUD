# -*- coding: utf-8 -*-
"""v106: 44 real catalogue skills for all 22 classes; opt-in STAGING only.

The original trainer, book, skill queues and learned-skill storage all consume
CLASS_SKILLS; this is not a second detached catalogue. The 44 new records are
only added under SOULBOUND_V106_STAGING=1 and never replace original IDs.
Unlocks are class mastery levels, not Soul Tier/character level.
Combat-time player balance and trainer TCP remain to be validated.
"""
from __future__ import annotations

import re

# (single-target/support name, kind; party/area name, kind)
# Every class has two distinct skills and both use existing engine kinds.
_AUTHORED = {
    'Wojownik': ('Cios Astralnego Żelaza', 'damage', 'Mur Siedmiu Bastionów', 'guard'),
    'Berserker': ('Rozdarcie Czerwonej Gwiazdy', 'damage', 'Gniew Eonów', 'aoe_damage'),
    'Łotrzyk': ('Sztylet Martwej Komety', 'damage', 'Noc Tysiąca Ostrzy', 'aoe_damage'),
    'Łowca': ('Strzała Przez Wymiary', 'damage', 'Grad Astralnych Strzał', 'aoe_damage'),
    'Mnich': ('Dotyk Wewnętrznej Galaktyki', 'damage', 'Medytacja Przebudzenia', 'boost'),
    'Strażnik': ('Uderzenie Wiecznej Cytadeli', 'damage', 'Przysięga Bastionu Gwiazd', 'guard'),
    'Mag': ('Promień Serca Wszechświata', 'damage', 'Deszcz Spadających Gwiazd', 'aoe_damage'),
    'Nekromanta': ('Uścisk Astralnego Grobu', 'damage', 'Procesja Cieni Otchłani', 'aoe_damage'),
    'Kapłan': ('Światło Odrodzonego Świtu', 'heal', 'Błogosławieństwo Siedmiu Słońc', 'group_heal'),
    'Czarownik': ('Pakt Pękniętej Gwiazdy', 'damage', 'Kataklizm Zapomnianych Paktów', 'aoe_damage'),
    'Druid': ('Tchnienie Praźródła', 'heal', 'Zew Wiecznego Lasu', 'group_heal'),
    'Psionik': ('Myśl Poza Czasem', 'damage', 'Burza Astralnych Wspomnień', 'aoe_damage'),
    'Mec': ('Impuls Rdzenia Wieczności', 'damage', 'Salwa Gwiezdnych Dział', 'aoe_damage'),
    'Inżynier': ('Przeciążenie Zegara Próżni', 'damage', 'Skoordynowany Ostrzał Dronów', 'aoe_damage'),
    'Paladyn': ('Sąd Złotej Galaktyki', 'damage', 'Tarcza Ostatniego Świtu', 'guard'),
    'Samuraj': ('Cięcie Ciszy Kosmosu', 'damage', 'Taniec Ostrzy Gwiezdnych', 'aoe_damage'),
    'Korsarz': ('Salwa Burzy Eteru', 'damage', 'Armada Płonących Gwiazd', 'aoe_damage'),
    'Gladiator': ('Uderzenie Kręgu Wieczności', 'damage', 'Okrzyk Bohaterów Astralu', 'boost'),
    'Chronomanta': ('Rozbłysk Uwięzionej Sekundy', 'damage', 'Fala Rozszczepionego Czasu', 'aoe_damage'),
    'Iluzjonista': ('Zwodniczy Cios Próżni', 'damage', 'Lustrzany Kataklizm', 'aoe_damage'),
    'Bard': ('Akord Odważnego Serca', 'boost', 'Pieśń Niebiańskich Chórów', 'group_heal'),
    'Szaman': ('Ukojenie Przodków', 'heal', 'Krąg Duchów Opiekuńczych', 'group_heal'),
}

UNLOCKS = (15000, 30000)
KINDS = frozenset(('damage', 'aoe_damage', 'boost', 'guard', 'heal', 'group_heal'))


def authored_skill_id(class_index, slot):
    if not (1 <= class_index <= 22 and 1 <= slot <= 2):
        raise ValueError('Nieprawidłowy indeks skilla v106')
    return f'v10600_skill_{class_index:02d}_{slot}'


def is_authored_unlock_v106(skill, class_name=None):
    """Narrow whitelist: exact ID + class + level and schema, never arbitrary IDs."""
    if not isinstance(skill, dict):
        return False
    match = re.fullmatch(r'v10600_skill_(\d{2})_([12])', str(skill.get('id', '')))
    if not match:
        return False
    index, slot = map(int, match.groups())
    if not 1 <= index <= len(_AUTHORED):
        return False
    expected_class = tuple(_AUTHORED)[index - 1]
    names = _AUTHORED[expected_class]
    return (class_name in (None, expected_class)
            and type(skill.get('unlock')) is int
            and skill['unlock'] == UNLOCKS[slot - 1]
            and str(skill.get('name', '')) == names[(slot-1)*2]
            and skill.get('kind') == names[(slot-1)*2+1])


def install(catalog, classes):
    class_names = tuple(row[0] for row in classes)
    if class_names != tuple(_AUTHORED):
        raise RuntimeError('v106: zmieniono kolejność lub zestaw 22 klas')
    all_ids = {str(s.get('id')) for rows in catalog.values() for s in rows}
    added = 0
    for index, row in enumerate(classes, 1):
        class_name, class_type = row[:2]
        titles = _AUTHORED[class_name]
        magic = class_type == 'magic'
        stat = ('intelligence' if magic else
                'dexterity' if class_name in {'Łotrzyk', 'Łowca', 'Mnich', 'Samuraj', 'Korsarz', 'Inżynier'}
                else 'strength')
        rows = catalog[class_name]
        names = {str(s.get('name','')).casefold() for s in rows}
        aliases = {str(a).casefold() for s in rows for a in s.get('aliases', ())}
        for slot in (1, 2):
            sid = authored_skill_id(index, slot)
            name, kind = titles[(slot-1)*2:(slot-1)*2+2]
            if sid in all_ids or name.casefold() in names or name.casefold() in aliases:
                raise RuntimeError(f'v106: kolizja skilla klasy {class_name}: {sid}')
            skill = {
                'id': sid, 'name': name, 'aliases': [name.casefold()],
                'kind': kind, 'unlock': UNLOCKS[slot-1],
                'cooldown': 18 if slot == 1 else 28,
                'mana': (90 if slot == 1 else 150) if magic else 0,
                'desc': (f'Astralna umiejętność klasy {class_name}; '
                         f'wymaga biegłości klasy {UNLOCKS[slot-1]}.')
            }
            if kind in {'damage', 'aoe_damage'}:
                skill.update(scale=stat, mult=3.0 if kind == 'damage' else 2.35)
            elif kind in {'heal', 'group_heal'}:
                skill.update(scale='willpower' if class_name in {'Kapłan', 'Szaman'} else 'intelligence',
                             heal_pct=0.28 if kind == 'heal' else 0.16,
                             target_mode='self_or_one_ally' if kind == 'heal' else 'local_party',
                             soulbound_enemy_heal_disabled=True)
            elif kind == 'guard':
                skill.update(guard=420, duration=14)
            elif kind == 'boost':
                skill.update(boost=1.35, duration=15)
            if not is_authored_unlock_v106(skill, class_name):
                raise RuntimeError('v106: niezgodny wzorzec umiejętności')
            rows.append(skill)
            all_ids.add(sid)
            names.add(name.casefold())
            added += 1
    if added != 44:
        raise RuntimeError('v106: niekompletny katalog nowych skilli')
    return added
