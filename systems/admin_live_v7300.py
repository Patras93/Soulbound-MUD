# -*- coding: utf-8 -*-
"""v73: atomic multi-quest prerequisite maintenance and multi-field boss phase plans.

This module never runs combat scripts, grants awards, modifies SQLite or publishes OLC.
All user values are data, checked by existing production OLC validators.
"""
from __future__ import annotations
import copy
import re

from data.mobs import MOB_TEMPLATES
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v7200 import _boss_template
from systems.live_olc17_quest_dependencies import validate_dependency_graph, quest_requirements
from systems.live_olc4_boss_phases import default_boss_phases, validate_boss_phases, eligible_boss
from systems.monster_ai import PROTECTED_FLAGS

HELP = (
    'ADMIN LIVE POMOC 33: questy zaleznosci pakiet plan Q1 | Q2,Q3 ; Q2 | BRAK (1-8 questow); '
    'questy zaleznosci pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj; '
    'boss fazy pakiet plan ID | 1.hp_percent=85; 2.attack_multiplier=1.75; 3.message=Tekst; '
    'boss fazy pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj; '
    'boss fazy raport ID; boss uoss ochrona ID. '
    'Kazdy pakiet jest walidowany W CALOSCI, dotyczy tylko DRAFT. '
    'Publikacja osobno. Skryptowane UOSS sa TYLKO do odczytu, arena NIE jest 1:1.'
)
_ID = re.compile(r'[A-Za-z0-9_-]{1,100}', flags=re.ASCII)
_INT = re.compile(r'[0-9]{1,3}', flags=re.ASCII)
_MULT = re.compile(r'[0-9]{1,2}(?:\.[0-9]{1,3})?', flags=re.ASCII)


def _check_id(text):
    if not _ID.fullmatch(text):
        raise ValueError('Niepoprawny ID; uzyj liter ASCII, cyfr, _ lub - (1-100 znakow).')
    return text


def quest_bulk_plan(session, service, raw):
    session.adminlive7300_quest_plan = None
    if not 1 <= len(raw) <= 1600:
        raise ValueError('Plan: 1..1600 znakow.')
    operations = [part.strip() for part in raw.split(';')]
    if not 1 <= len(operations) <= 8 or any(not item for item in operations):
        raise ValueError('Wymagane 1-8 niepustych zmian oddzielonych srednikiem.')
    catalog = _effective(service)
    edits = {}
    for item in operations:
        if item.count('|') != 1:
            raise ValueError('Wpisz QUEST_ID | ID1,ID2 lub BRAK; kolejne po sredniku.')
        qid, raw_deps = (value.strip() for value in item.split('|', 1))
        _check_id(qid)
        if qid not in catalog or qid in edits:
            raise ValueError('Nieznany lub powtorzony QUEST_ID: ' + qid[:100])
        if not raw_deps:
            raise ValueError('Pusta lista nie jest dozwolona; uzyj BRAK.')
        deps = [] if raw_deps.casefold() == 'brak' else [x.strip() for x in raw_deps.split(',')]
        if len(deps) > 8 or len(deps) != len(set(deps)):
            raise ValueError('Maksymalnie 8 roznych zaleznosci na quest.')
        for dep in deps:
            _check_id(dep)
            if dep not in catalog or dep == qid:
                raise ValueError('Nieznana lub wlasna zaleznosc: ' + dep)
        edits[qid] = deps
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    updated = candidate.setdefault('quest_edits', {})
    for qid, deps in edits.items():
        updated.setdefault(qid, {})['requires_quests'] = deps
        catalog[qid] = dict(catalog[qid], requires_quests=deps)
    # Important: validate the *final* graph, not intermediate partially edited states.
    validate_dependency_graph(catalog)
    service.validate(candidate)
    if before == candidate:
        raise ValueError('Nie ma zmian do zapisania.')
    _plan(session, 'adminlive7300_quest_plan', before, service.active, candidate,
          'QUEST ZALEZNOSCI PAKIET')
    lines = [f'{qid}: '+(','.join(deps) if deps else 'BRAK') for qid, deps in edits.items()]
    return ('QUEST ZALEZNOSCI PAKIET PLAN: ' + '; '.join(lines) +
            '. Uwaga: stare requires_quest bez zmian. Caly graf poprawny. '
            'Bez zapisu; questy zaleznosci pakiet zatwierdz POTWIERDZAM.')


def _parse_boss_field(field, raw):
    if field in ('hp_percent', 'duration_seconds'):
        if not _INT.fullmatch(raw):
            raise ValueError(field+': podaj liczbe calkowita.')
        return int(raw)
    if field == 'attack_multiplier':
        if not _MULT.fullmatch(raw):
            raise ValueError('attack_multiplier: liczba z kropka.')
        return float(raw)
    if field == 'message':
        if not raw.strip() or len(raw) > 140 or any(ord(c) < 32 or ord(c) == 127 for c in raw):
            raise ValueError('message: 1-140 znakow bez znakow sterujacych.')
        return raw
    raise ValueError('Pole: hp_percent, duration_seconds, attack_multiplier albo message.')


def boss_bulk_plan(session, service, raw):
    # Reuse the existing slot and its established commit/undo commands.
    session.adminlive7100_boss_plan = None
    if not 1 <= len(raw) <= 1500 or raw.count('|') != 1:
        raise ValueError('Format: BOSS_ID | 1.hp_percent=85; 2.message=Tekst.')
    ident, settings = (v.strip() for v in raw.split('|', 1))
    _check_id(ident)
    meta = _boss_template(service, ident)
    phases = copy.deepcopy(meta.get('olc_boss_phases') or default_boss_phases(meta))
    ops = [op.strip() for op in settings.split(';')]
    if not 1 <= len(ops) <= 12 or any(not op for op in ops):
        raise ValueError('Wymagane 1-12 pelnych zmian.')
    seen = set()
    descriptions = []
    for op in ops:
        if '=' not in op:
            raise ValueError('Format: NR.POLE=WARTOSC.')
        lhs, val = (v.strip() for v in op.split('=', 1))
        parts = lhs.split('.')
        if len(parts) != 2 or not _INT.fullmatch(parts[0]):
            raise ValueError('Format: NR.POLE=WARTOSC.')
        idx = int(parts[0]) - 1
        field = parts[1]
        if idx < 0 or idx >= len(phases) or (idx, field) in seen:
            raise ValueError('Numer fazy poza zakresem lub powtorzone pole.')
        seen.add((idx, field))
        value = _parse_boss_field(field, val)
        phases[idx][field] = value
        descriptions.append(f'{idx+1}.{field}={str(value)[:60]}')
    validate_boss_phases(meta, phases)
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    candidate.setdefault('mob_edits', {}).setdefault(ident, {})['olc_boss_phases'] = phases
    service.validate(candidate)
    if before == candidate:
        raise ValueError('Brak zmiany.')
    _plan(session, 'adminlive7100_boss_plan', before, service.active, candidate,
          'BOSS FAZY PAKIET')
    return (f'BOSS FAZY PAKIET PLAN {ident}: ' + '; '.join(descriptions) +
            '. Zweryfikowano caly uklad faz; tylko DRAFT. '
            'boss fazy pakiet zatwierdz POTWIERDZAM.')


def boss_report(service, ident):
    _check_id(ident)
    meta = _boss_template(service, ident)
    phases = copy.deepcopy(meta.get('olc_boss_phases') or default_boss_phases(meta))
    validate_boss_phases(meta, phases)
    lines = [f'{idx}: HP {p["hp_percent"]}%, atak x{p["attack_multiplier"]}, '
             f'czas {p["duration_seconds"]} s, tekst {p["message"]}'
             for idx, p in enumerate(phases, 1)]
    return f'BOSS FAZY RAPORT {ident}, {len(phases)} etapow: ' + '; '.join(lines)+'. Bez zmian.'


def scripted_protection(service, ident):
    _check_id(ident)
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    encounter = UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(ident)
    if encounter is not None:
        # UOSS uses a separate scripted encounter catalog, not MOB_TEMPLATES.
        label = str(encounter.get('name', ident))[:100]
        helpers = encounter.get('helpers') or ()
        if isinstance(helpers, (tuple, list)):
            helper_text = ', '.join(str(h)[:30] for h in helpers[:6]) or 'BRAK'
        else:
            helper_text = 'BRAK'
        return (f'BOSS UOSS OCHRONA {ident}: {label}; zwykle fazy edytowalne NIE; '
                f'tryb {str(encounter.get("mode", "nieznany"))[:35]}; '
                f'pomocnicy {helper_text}; skryptowany katalog spotkan UOSS. '
                'Odczyt definicji; brak uruchamiania AI, zmian swiata i nagrod.')
    template = MOB_TEMPLATES.get(ident) or service.draft.get('mobs', {}).get(ident)
    if not isinstance(template, dict):
        raise ValueError('Nieznany ID moba ani superbossa UOSS.')
    combined = dict(template)
    combined.update(service.draft.get('mob_edits', {}).get(ident, {}))
    flags = sorted(flag for flag in PROTECTED_FLAGS if combined.get(flag))
    reason = 'specjalny profil starozytny' if combined.get('v500_ancient_profile') is not None else ''
    ordinary = eligible_boss(combined)
    return (f'BOSS UOSS OCHRONA {ident}: zwykle fazy edytowalne '
            f'{"TAK" if ordinary else "NIE"}; chronione flagi '+(', '.join(flags) or 'BRAK')+
            (f'; {reason}' if reason else '')+
            '. Analiza definicji, nie uruchamia AI ani produkcyjnej walki. Bez zmian.')


async def dispatch_v7300(session, group, raw):
    parts = str(raw or '').strip().split()
    help_match = group == 'pomoc' and parts == ['33']
    quest_match = group in ('questy', 'zadania') and parts[:2] == ['zaleznosci', 'pakiet']
    boss_match = group == 'boss' and (parts[:2] == ['fazy', 'pakiet'] or
                                     parts[:2] == ['fazy', 'raport'] or
                                     parts[:2] == ['uoss', 'ochrona'])
    if not (help_match or quest_match or boss_match):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    service = session.server.live_content_v1204
    try:
        if help_match:
            result = HELP
        elif quest_match:
            slot, undo_slot = 'adminlive7300_quest_plan', 'adminlive7300_quest_undo'
            if len(parts) >= 4 and parts[2] == 'plan':
                result = quest_bulk_plan(session, service, raw.partition('plan')[2].strip())
            elif parts == ['zaleznosci','pakiet','zatwierdz','POTWIERDZAM']:
                result = _commit(session, service, slot, undo_slot)
            elif parts == ['zaleznosci','pakiet','cofnij','POTWIERDZAM']:
                result = _undo(session, service, slot, undo_slot)
            elif parts == ['zaleznosci','pakiet','anuluj']:
                setattr(session, slot, None)
                result = 'QUEST ZALEZNOSCI PAKIET: plan anulowano.'
            else:
                raise ValueError('questy zaleznosci pakiet plan/zatwierdz/cofnij/anuluj. Pomoc 33.')
        elif parts[:2] == ['uoss','ochrona']:
            if len(parts) != 3:
                raise ValueError('boss uoss ochrona ID')
            result = scripted_protection(service, parts[2])
        elif parts[:2] == ['fazy','raport']:
            if len(parts) != 3:
                raise ValueError('boss fazy raport ID')
            result = boss_report(service, parts[2])
        else:
            slot, undo_slot = 'adminlive7100_boss_plan', 'adminlive7100_boss_undo'
            if len(parts) >= 4 and parts[2] == 'plan':
                result = boss_bulk_plan(session, service, raw.partition('plan')[2].strip())
            elif parts == ['fazy','pakiet','zatwierdz','POTWIERDZAM']:
                result = _commit(session, service, slot, undo_slot)
            elif parts == ['fazy','pakiet','cofnij','POTWIERDZAM']:
                result = _undo(session, service, slot, undo_slot)
            elif parts == ['fazy','pakiet','anuluj']:
                setattr(session, slot, None)
                result = 'BOSS FAZY PAKIET: plan anulowano.'
            else:
                raise ValueError('boss fazy pakiet plan/zatwierdz/cofnij/anuluj. Pomoc 33.')
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        result = 'ADMIN LIVE V73: '+str(exc)[:260]
    await session.send(result)
    return True
