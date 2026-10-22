# -*- coding: utf-8 -*-
"""v12.00.13: strictly data-only new class skills for the existing combat engine."""
import unicodedata
from core.classes_skills import CLASS_SKILLS
from systems.live_content_v1204 import ID, _integer, _text

ALLOWED_KINDS = frozenset(('damage', 'aoe_damage', 'heal', 'group_heal', 'guard', 'drain', 'regen', 'evade', 'execute', 'boost'))
ALLOWED_SCALES = frozenset(('strength', 'dexterity', 'intelligence', 'wisdom', 'willpower', 'constitution'))
FIELDS = frozenset(('class_name', 'name', 'desc', 'kind', 'unlock', 'mana',
                    'cooldown', 'scale', 'mult', 'aliases'))


def _fold(label):
    value = str(label).replace('ł','l').replace('Ł','L')
    value = unicodedata.normalize('NFKD', value)
    return ''.join(c for c in value if not unicodedata.combining(c)).casefold().strip()


def validate_new_skills(skills, active):
    if not isinstance(skills, dict) or len(skills) > 500:
        raise ValueError('OLC skille: wymagany słownik, maks. 500 nowych skilli.')
    occupied_ids = {str(row['id']) for rows in CLASS_SKILLS.values() for row in rows}
    # All original published IDs remain reserved, even when a draft changes.
    occupied_ids.difference_update(active)
    used_names = set()
    for rows in CLASS_SKILLS.values():
        for row in rows:
            if row['id'] in active:
                continue
            for label in (row.get('name', ''), *row.get('aliases', [])):
                if str(label).strip():
                    used_names.add(_fold(label))
    for sid, meta in skills.items():
        if not isinstance(sid, str) or not ID.fullmatch(sid) or sid in occupied_ids:
            raise ValueError(f'OLC skill: identyfikator musi być wolnym live_: {sid}.')
        if not isinstance(meta, dict) or not (FIELDS <= set(meta) and set(meta) <= FIELDS | {'effect', 'element', 'olc_status'}):
            raise ValueError(f'OLC skill {sid}: wymagane pola {sorted(FIELDS)}.')
        if meta['class_name'] not in CLASS_SKILLS:
            raise ValueError(f'OLC skill {sid}: nieznana klasa.')
        _text(meta['name'], 100, 'Nazwa skilla')
        _text(meta['desc'], 700, 'Opis skilla')
        if meta['kind'] not in ALLOWED_KINDS or meta['scale'] not in ALLOWED_SCALES:
            raise ValueError(f'OLC skill {sid}: rodzaj damage/aoe_damage/heal/group_heal/guard/drain/regen/evade; skala strength/dexterity/intelligence/wisdom/willpower/constitution.')
        _integer(meta['unlock'], 1, 800, 'Wymagana biegłość')
        _integer(meta['mana'], 0, 1000000, 'Mana')
        # Ordinary skills remain cooldown-free by default. Explicit OLC
        # cooldowns use the EXISTING mechanic_cooldown runtime timer.
        if type(meta['cooldown']) is not int:
            raise ValueError('Cooldown musi być liczbą całkowitą w sekundach.')
        _integer(meta['cooldown'], 0, 3600, 'Cooldown w sekundach')
        if isinstance(meta['mult'], bool) or not isinstance(meta['mult'], (float, int)) or not 0.1 <= meta['mult'] <= 30.0:
            raise ValueError('Mnożnik obrażeń 0.1–30.0.')
        # Pre-v12.10.0 attack definitions have no 'effect' field. New healing
        # and guard definitions require a value that the *existing* engine reads.
        if meta['kind'] in ('heal', 'group_heal'):
            effect = meta.get('effect')
            if type(effect) not in (int, float) or not 0.001 <= effect <= 1.0:
                raise ValueError('Leczenie wymaga effect 0.001–1.0 (ułamek bazowego HP).')
        elif meta['kind'] == 'guard':
            effect = meta.get('effect')
            if type(effect) is not int or not 1 <= effect <= 10**9:
                raise ValueError('Ochrona wymaga effect 1–1000000000 (bazowy guard).')
        elif meta['kind'] == 'drain':
            effect = meta.get('effect')
            if type(effect) not in (float, int) or not 0.01 <= effect <= 1.0:
                raise ValueError('Wysysanie wymaga effect 0.01–1.0 (ułamek obrażeń leczony przez silnik).')
        elif meta['kind'] == 'boost':
            effect = meta.get('effect')
            if type(effect) not in (float, int) or not 1.01 <= effect <= 1.90:
                raise ValueError('Pasywne wzmocnienie wymaga effect 1.01–1.90 (istniejący mnożnik boost).')
            if meta['cooldown'] != 0 or meta['mana'] != 0:
                raise ValueError('Pasywny boost nie może mieć many ani cooldownu.')
        elif meta['kind'] == 'execute':
            effect = meta.get('effect')
            if type(effect) not in (float, int) or not 1.0 <= effect <= 2.0:
                raise ValueError('Egzekucja wymaga effect 1.0–2.0 (istniejący limit silnika).')
        elif 'effect' in meta:
            raise ValueError('Ten rodzaj skilla nie korzysta z parametru effect.')
        if 'element' in meta:
            from systems.elemental_combat import V11339_ELEMENT_LABELS
            if meta['kind'] not in ('damage', 'aoe_damage') or meta['element'] not in V11339_ELEMENT_LABELS:
                raise ValueError('Żywioł: tylko atak damage/aoe_damage i element obsługiwany przez silnik.')
        if 'olc_status' in meta:
            from systems.live_olc19_status_skills import parse_status
            if meta['kind'] not in ('damage','aoe_damage'):
                raise ValueError('Status OLC tylko dla zwykłych skilli damage/aoe_damage.')
            if not isinstance(meta['olc_status'], dict):
                raise ValueError('Status w zapisanej definicji skilla musi być obiektem JSON.')
            if parse_status(meta['olc_status']) is None:
                raise ValueError('Status auto oznacza brak pola; usuń olc_status.')
        aliases = meta['aliases']
        if not isinstance(aliases, list) or len(aliases) > 5 or not all(isinstance(a, str) for a in aliases):
            raise ValueError('Aliasy: lista maksymalnie 5 tekstów.')
        new_labels = [meta['name']] + aliases
        folded = []
        for label in new_labels:
            _text(label, 100, 'Alias skilla')
            folded.append(_fold(label))
        if len(set(folded)) != len(folded) or any(label in used_names for label in folded):
            raise ValueError(f'OLC skill {sid}: nazwa lub alias już zajęty.')
        used_names.update(folded)
    return len(skills)


def new_skill_definition(sid, meta):
    result = {'id':sid, 'name':meta['name'], 'aliases':list(meta['aliases']),
              'unlock':meta['unlock'], 'kind':meta['kind'], 'cooldown':meta['cooldown'],
              'mana':meta['mana'], 'desc':meta['desc'], 'scale':meta['scale'],
              'mult':meta['mult']}
    if 'olc_status' in meta:
        result['olc_status'] = dict(meta['olc_status'])
    if meta['cooldown']:
        result['mechanic_cooldown'] = True
    if 'element' in meta:
        result['element'] = meta['element']
    if meta['kind'] in ('heal', 'group_heal'):
        result['heal_pct'] = meta['effect']
    elif meta['kind'] == 'guard':
        result['guard'] = meta['effect']
    elif meta['kind'] == 'drain':
        result['drain_pct'] = meta['effect']
    elif meta['kind'] == 'boost':
        result['boost'] = meta['effect']
    elif meta['kind'] == 'execute':
        result['execute_mult'] = meta['effect']
    elif meta['kind'] == 'evade':
        result['evade'] = True
    # regen follows the already authored combat-time tick cadence and strength.
    return result
