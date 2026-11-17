"""Retained gameplay/validation helpers for published content; no editor API."""

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
