# -*- coding: utf-8 -*-
"""v74: safe legacy quest-parent repair and read-only UOSS/source reports.

Owner only via the existing `admin live` dispatcher.  All quest changes are
validated on an isolated OLC snapshot and require a second explicit command.
No player DB writes, quest completions, RNG, combat execution, or rewards.
"""
from __future__ import annotations

import copy
import re
from collections import deque

from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.live_olc17_quest_dependencies import quest_requirements, validate_dependency_graph
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

_ID = re.compile(r'[A-Za-z0-9_-]{1,100}\Z', re.ASCII)
_PAGE = re.compile(r'[0-9]{1,4}\Z', re.ASCII)
HELP = (
    'ADMIN LIVE POMOC 34: questy zaleznosci stare karta QUEST_ID; '
    'questy zaleznosci stare plan QUEST_ID | NOWY_ID; '
    'questy zaleznosci stare zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj; '
    'questy zaleznosci wplyw QUEST_ID [STRONA] - questy wymagajace wskazanego zadania, bezposrednio i posrednio; '
    'questy zaleznosci sciezka QUEST_ID [STRONA] - poprzednicy i brakujace ID; '
    'boss uoss lista [STRONA], boss uoss karta ID - oryginalny katalog spotkan. '
    'Usuwanie: questy zaleznosci stare usun plan ID; zatwierdz POTWIERDZAM. '
    'Zatwierdzenie dotyczy TYLKO DRAFT; publikacja osobno. UOSS tylko odczyt, nie walka 1:1.'
)


def _id(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('Niepoprawny identyfikator: 1..100 znakow ASCII [A-Z a-z 0-9 _ -].')
    return value


def _pagination(records, page, limit=8):
    if not isinstance(page, str) or not _PAGE.fullmatch(page):
        raise ValueError('STRONA: podaj dodatnia liczbe (maks. 4 cyfry).')
    index = int(page)
    total = max(1, (len(records) + limit - 1) // limit)
    if index < 1 or index > total:
        raise ValueError('Dostepne strony: 1..'+str(total)+'.')
    return index, total, records[(index-1)*limit:index*limit]


def legacy_card(service, ident):
    _id(ident)
    catalog = _effective(service)
    if ident not in catalog:
        raise ValueError('Nieznany QUEST_ID. Uzyj admin live questy szukaj.')
    row = catalog[ident]
    parent = row.get('requires_quest') or 'BRAK'
    extras = row.get('requires_quests') or []
    if not isinstance(extras, (list, tuple)):
        raise ValueError('Niepoprawne requires_quests: najpierw napraw strukture questa.')
    missing = [ref for ref in quest_requirements(row) if ref not in catalog]
    return (f'QUEST STARE KARTA {ident}: requires_quest={parent}; '
            f'requires_quests={",".join(extras) if extras else "BRAK"}; '
            f'brakujace={",".join(missing) if missing else "BRAK"}. '
            'Tylko odczyt. Usun przez: questy zaleznosci stare usun plan ID.')


def legacy_plan(session, service, raw):
    session.adminlive7400_legacy_plan = None
    if raw.count('|') != 1 or len(raw) > 230:
        raise ValueError('Format: questy zaleznosci stare plan QUEST_ID | NOWY_ID')
    ident, wanted = (piece.strip() for piece in raw.split('|', 1))
    _id(ident); _id(wanted)
    catalog = _effective(service)
    if ident not in catalog or wanted not in catalog:
        raise ValueError('QUEST_ID lub NOWY_ID nie istnieje; wybierz prawdziwe ID.')
    if ident == wanted:
        raise ValueError('Quest nie moze wymagac samego siebie.')
    row = catalog[ident]
    parent = row.get('requires_quest')
    if not isinstance(parent, str) or not parent:
        raise ValueError('Quest nie ma starego requires_quest. Uzyj pakietu requires_quests.')
    if parent == wanted:
        raise ValueError('Zaleznosc jest juz ustawiona na to ID.')
    if wanted in (row.get('requires_quests') or []):
        raise ValueError('NOWY_ID juz wystepuje w requires_quests: odrzucam powielenie.')
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    candidate.setdefault('quest_edits', {}).setdefault(ident, {})['requires_quest'] = wanted
    catalog[ident] = {**row, 'requires_quest': wanted}
    validate_dependency_graph(catalog)
    service.validate(candidate)
    if candidate == before:
        raise ValueError('Nie ma zmian.')
    _plan(session, 'adminlive7400_legacy_plan', before, service.active,
          candidate, 'QUEST STARA ZALEZNOSC')
    return (f'QUEST STARE PLAN {ident}: requires_quest {parent} -> {wanted}. '
            'Caly graf zweryfikowany. Bez zapisu, tylko plan. '
            'questy zaleznosci stare zatwierdz POTWIERDZAM.')


def legacy_remove_plan(session, service, ident):
    """Remove legacy parent through an explicit null OLC override in DRAFT."""
    session.adminlive7400_legacy_plan = None
    _id(ident)
    catalog = _effective(service)
    if ident not in catalog:
        raise ValueError('Nieznany QUEST_ID.')
    previous = catalog[ident].get('requires_quest')
    if not previous:
        raise ValueError('Ten quest nie ma legacy requires_quest do usuniecia.')
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    candidate.setdefault('quest_edits', {}).setdefault(ident, {})['requires_quest'] = None
    catalog[ident] = {**catalog[ident], 'requires_quest': None}
    validate_dependency_graph(catalog)
    service.validate(candidate)
    _plan(session, 'adminlive7400_legacy_plan', before, service.active, candidate,
          'QUEST USUNIECIE STAREJ ZALEZNOSCI')
    return (f'QUEST STARE USUN PLAN {ident}: wymagany {previous}, teraz BRAK. '
            'Graf i DRAFT zweryfikowane. Bez zapisu. '
            'questy zaleznosci stare zatwierdz POTWIERDZAM.')


def _graph(service):
    catalog = _effective(service)
    forward = {}
    reverse = {qid: set() for qid in catalog}
    for ident, quest in catalog.items():
        deps = quest_requirements(quest)
        forward[ident] = deps
        for dep in deps:
            if dep in reverse:
                reverse[dep].add(ident)
    return catalog, forward, reverse


def dependency_impact(service, ident, page='1'):
    _id(ident)
    catalog, _, reverse = _graph(service)
    if ident not in catalog:
        raise ValueError('Nieznany QUEST_ID.')
    direct = sorted(reverse[ident])
    visited = {ident}
    queue = deque(direct)
    affected = set()
    while queue:
        key = queue.popleft()
        if key in visited:
            continue
        visited.add(key); affected.add(key)
        queue.extend(sorted(reverse[key] - visited))
    rows = sorted(affected)
    index, total, window = _pagination(rows, page)
    return (f'QUEST WPLYW {ident}: bezposrednio {len(direct)}, '
            f'wszystkie zalezne {len(affected)}, strona {index}/{total}: '
            + (', '.join(window) or 'BRAK')+
            '. Raport grafu DRAFT, nie analiza zapisanych postepow graczy. Bez zmian.')


def dependency_path(service, ident, page='1'):
    _id(ident)
    catalog, forward, _ = _graph(service)
    if ident not in catalog:
        raise ValueError('Nieznany QUEST_ID.')
    seen = {ident}
    queue = deque([ident])
    missing = set()
    while queue:
        curr = queue.popleft()
        for dep in forward[curr]:
            if dep not in catalog:
                missing.add(dep)
            elif dep not in seen:
                seen.add(dep)
                queue.append(dep)
    predecessors = sorted(seen - {ident})
    rows = predecessors + ['BRAKUJACE:'+dep for dep in sorted(missing)]
    index, total, window = _pagination(rows, page)
    return (f'QUEST SCIEZKA {ident}: poprzednikow {len(predecessors)}, '
            f'brakujacych ID {len(missing)}, strona {index}/{total}: '
            + (', '.join(window) or 'BRAK') + '. Tylko odczyt DRAFT, bez zmian.')


def uoss_list(page='1'):
    rows = [f'{key} ({str(value.get("name", key))[:45]})'
            for key, value in sorted(UOSS_SUPERBOSS_ENCOUNTERS_V11134.items())]
    index, total, window = _pagination(rows, page, 6)
    return (f'BOSS UOSS LISTA: {len(rows)} spotkan, strona {index}/{total}: '
            + '; '.join(window)+'. Skryptowane spotkania, tylko odczyt.')


def uoss_card(ident):
    _id(ident)
    row = UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(ident)
    if row is None:
        raise ValueError('Nieznany superboss z katalogu spotkan. boss uoss lista.')
    def short(key, default='BRAK'):
        value = row.get(key, default)
        return str(value)[:100]
    companions = row.get('helpers') or (() if not row.get('helper') else (row['helper'],))
    if not isinstance(companions, (tuple,list)):
        companions = ()
    return (f'BOSS UOSS KARTA {ident}: {short("name")}; tryb {short("mode")}; '
            f'odblokowanie {short("unlock_level")}; zalecany {short("recommended_level")}; '
            f'obszar {short("area")}; pomocnicy {", ".join(str(h)[:30] for h in companions[:8]) or "BRAK"}; '
            f'blokada {short("lockout_hours")} h; token {short("personal_token")}; '
            f'limit pomocnikow {short("helper_choice_limit")}; '
            'Dane z katalogu spotkan. Nie sa to rzeczywiste HP, obrazenia ani wynik walki. '
            'Brak modyfikacji skryptow, EXP, przedmiotow i SQLite.')


async def dispatch_v7400(session, group, raw):
    parts = str(raw or '').strip().split()
    is_help = group == 'pomoc' and parts == ['34']
    is_quest = group in ('questy','zadania') and parts[:1] == ['zaleznosci'] and len(parts)>1 and parts[1] in ('stare','wplyw','sciezka')
    is_boss = group == 'boss' and parts[:1] == ['uoss'] and len(parts)>1 and parts[1] in ('lista','karta')
    if not (is_help or is_quest or is_boss):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service = session.server.live_content_v1204
        if is_help:
            result = HELP
        elif is_quest:
            if parts[1] == 'wplyw' and len(parts) in (3,4):
                result = dependency_impact(service, parts[2], parts[3] if len(parts)==4 else '1')
            elif parts[1] == 'sciezka' and len(parts) in (3,4):
                result = dependency_path(service, parts[2], parts[3] if len(parts)==4 else '1')
            elif parts[1] == 'stare':
                slot, undo_slot = 'adminlive7400_legacy_plan','adminlive7400_legacy_undo'
                if parts[:4] == ['zaleznosci','stare','usun','plan'] and len(parts)==5:
                    result = legacy_remove_plan(session, service, parts[4])
                elif len(parts)==4 and parts[2]=='karta':
                    result = legacy_card(service, parts[3])
                elif len(parts)>=5 and parts[2]=='plan':
                    result = legacy_plan(session, service, raw.partition('plan')[2].strip())
                elif parts==['zaleznosci','stare','zatwierdz','POTWIERDZAM']:
                    result = _commit(session,service,slot,undo_slot)
                elif parts==['zaleznosci','stare','cofnij','POTWIERDZAM']:
                    result = _undo(session,service,slot,undo_slot)
                elif parts==['zaleznosci','stare','anuluj']:
                    setattr(session,slot,None)
                    result = 'QUEST STARE: plan anulowano.'
                else:
                    raise ValueError('questy zaleznosci stare karta/plan/usun plan/zatwierdz/cofnij/anuluj. Pomoc 34.')
            else:
                raise ValueError('questy zaleznosci wplyw/sciezka ID [STRONA]. Pomoc 34.')
        elif parts[1] == 'lista' and len(parts) in (2,3):
            result = uoss_list(parts[2] if len(parts)==3 else '1')
        elif parts[1] == 'karta' and len(parts)==3:
            result = uoss_card(parts[2])
        else:
            raise ValueError('boss uoss lista [STRONA] / karta ID. Pomoc 34.')
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        result = 'ADMIN LIVE V74: '+str(exc)[:260]
    await session.send(result)
    return True
