# -*- coding: utf-8 -*-
"""Read-only NVDA-oriented comparison of staged OLC revisions."""
import json
from systems.live_content_v1204 import blank


def _brief(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return text if len(text) <= 150 else text[:147] + '...'


def describe_diff(active, draft, limit=15):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('Podgląd zmian: limit 1–50.')
    changes = []
    for section in blank():
        old, new = active[section], draft[section]
        if old == new:
            continue
        if isinstance(old, dict) and isinstance(new, dict):
            for key in sorted(set(old) | set(new)):
                before, after = old.get(key), new.get(key)
                if before == after:
                    continue
                if isinstance(before, dict) and isinstance(after, dict):
                    for field in sorted(set(before) | set(after)):
                        if before.get(field) != after.get(field):
                            changes.append((f'{section}/{key}/{field}', before.get(field), after.get(field)))
                else:
                    changes.append((f'{section}/{key}', before, after))
        else:
            changes.append((section, old, new))
    if not changes:
        return 'OLC: brak przygotowanych zmian. Niczego nie zapisano.'
    lines = [f'OLC: przygotowano {len(changes)} zmian. Wyświetlam pierwsze {min(limit, len(changes))}. Niczego nie zapisano.']
    for key, before, after in changes[:limit]:
        lines.append(f'{key}: było {_brief(before)}; będzie {_brief(after)}.')
    if len(changes) > limit:
        lines.append(f'Pozostało {len(changes)-limit} zmian; użyj porownaj 50 lub eksport JSON.')
    return '\n'.join(lines)
