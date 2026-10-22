# -*- coding: utf-8 -*-
"""OLC 15: real multi-objective quest contract. Only data, never scripts.

Old quest kinds and their rewards are untouched. Objective kills/talks are
recorded in the existing SQLite quest_resource_progress_v0929 table using
namespaced keys; collect is checked against actual owned stock on turn-in.
"""
import json

PREFIX = "olc18:"


def objective_key(kind, target):
    return PREFIX + kind + ":" + str(target)


def validate_objectives(payload, mobs, items, npcs):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError) as exc:
            raise ValueError('Cele: nieprawidłowy JSON.') from exc
    if not isinstance(payload, dict) or not payload or set(payload) - {'kill', 'collect', 'talk'}:
        raise ValueError('Cele: JSON kill/collect/talk, co najmniej dwa rodzaje.')
    kinds = sum(bool(value) for value in payload.values())
    if kinds < 2:
        raise ValueError('Cele: wymagane co najmniej dwa rodzaje zadań.')
    checked = {}
    for kind in ('kill', 'collect'):
        if kind not in payload:
            continue
        entries = payload[kind]
        if not isinstance(entries, dict) or not entries:
            raise ValueError(f'{kind}: wymagany niepusty słownik ID -> liczba.')
        source = mobs if kind == 'kill' else items
        clean = {}
        for target, qty in entries.items():
            if not isinstance(target, str) or target not in source or type(qty) is not int or not 1 <= qty <= 10000:
                raise ValueError(f'{kind}: nieznany cel lub ilość spoza zakresu 1–10000: {target}.')
            clean[target] = qty
        checked[kind] = clean
    if 'talk' in payload:
        entries = payload['talk']
        if not isinstance(entries, list) or not entries or len(entries) != len(set(map(str, entries))):
            raise ValueError('talk: wymagana lista unikalnych ID NPC.')
        for npc_id in entries:
            if not isinstance(npc_id, str) or npc_id not in npcs:
                raise ValueError(f'talk: nieznany NPC {npc_id}.')
        checked['talk'] = list(entries)
    count = sum(len(v) for v in checked.values())
    if not 2 <= count <= 12:
        raise ValueError('Cele: 2–12 celów łącznie.')
    total = sum(sum(group.values()) if isinstance(group, dict) else len(group)
                for group in checked.values())
    if total > 10000:
        raise ValueError('Cele: najwyżej 10000 działań łącznie.')
    return checked, total


def objective_status(db, account_id, quest_id, objectives, item_count=None):
    """Return per-objective details and summary. No writes, safe for look/score."""
    results = []
    for kind in ('kill', 'talk', 'collect'):
        group = objectives.get(kind, {} if kind != 'talk' else [])
        pairs = ((value, 1) for value in group) if kind == 'talk' else group.items()
        for target, needed in pairs:
            if kind == 'collect':
                progress = int(item_count(target)) if item_count else 0
            else:
                row = db.conn.execute(
                    'SELECT progress FROM quest_resource_progress_v0929 '
                    'WHERE account_id=? AND quest_id=? AND target_id=?',
                    (account_id, quest_id, objective_key(kind, target))
                ).fetchone()
                progress = int(row['progress']) if row else 0
            results.append((kind, target, min(int(needed), max(0, progress)), int(needed)))
    current = sum(x[2] for x in results)
    total = sum(x[3] for x in results)
    return current, total, current >= total, results


def describe_goals(service, quest_id, base_quests):
    """Read-only active/draft OLC goals, short enough for NVDA."""
    def describe(payload):
        quest = dict(base_quests.get(quest_id, {}))
        quest.update(payload.get('quests', {}).get(quest_id, {}))
        quest.update(payload.get('quest_edits', {}).get(quest_id, {}))
        if quest.get('kind') != 'multi_objective':
            return 'brak zadania wielocelowego'
        parts=[]
        objectives=quest.get('objectives') or {}
        labels={'kill':'pokonaj','collect':'przynieś','talk':'porozmawiaj'}
        for kind in ('kill','collect','talk'):
            group=objectives.get(kind, {} if kind != 'talk' else [])
            entries=group.items() if kind != 'talk' else ((name,1) for name in group)
            for name,qty in entries:
                parts.append(f'{labels[kind]} {name} x{qty}')
        return ', '.join(parts) if parts else 'brak celów'
    if (quest_id not in base_quests and quest_id not in service.active.get('quests', {})
            and quest_id not in service.draft.get('quests', {})):
        raise ValueError('Nieznany quest. Wpisz admin live katalog quest FRAZA.')
    active = describe(service.active)
    draft = describe(service.draft)
    return (f'OLC CELE {quest_id}. Aktualnie: {active}. '
            f'Po zmianie: {draft}. '
            + ('BEZ ZMIAN.' if active == draft else 'WYMAGA ZATWIERDZENIA.')
            + ' Sam podgląd nie zapisuje danych.')
