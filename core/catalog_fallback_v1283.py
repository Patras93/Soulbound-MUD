"""Load authored legacy numeric defaults once, using little temporary RAM.

The compressed catalogue is consumed as independent JSON records during the
world module's initial import, not once per mob, command or combat turn.
All numeric values and authored-value precedence are identical to v1.28.3.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parent.parent / 'data' / 'catalogue_numeric_defaults_v1283.jsonl.gz'
_TABLES = ('ROOMS', 'MOB_TEMPLATES', 'ITEMS', 'QUESTS', 'CLASS_SKILLS',
           'CRAFT_RECIPES', 'COOK_RECIPES', 'ALCHEMY_RECIPES', 'JEWELCRAFT_RECIPES')


def apply_catalogue_defaults_v1283(namespace):
    """Fill missing fields, never overwrite an authored field.

    Parse one compressed JSON line at a time: no temporary 110k-record tree.
    The gzip payload contains the exact former JSON values, with each row
    encoded as [table index, record ID, field dictionary].
    """
    if not _CATALOG_PATH.is_file():
        raise RuntimeError('Missing static catalogue data: ' + str(_CATALOG_PATH))

    registries = {name: namespace.get(name) or {} for name in _TABLES}
    skills = registries['CLASS_SKILLS']
    registries['CLASS_SKILLS'] = {
        str(skill.get('id')): skill for rows in skills.values() for skill in rows
    }
    loaded = skipped = missing = 0
    missing_ids = []
    with gzip.open(_CATALOG_PATH, 'rt', encoding='utf-8') as source:
        for line_number, line in enumerate(source, 1):
            table_index, identifier, fields = json.loads(line)
            if not isinstance(table_index, int) or not 0 <= table_index < len(_TABLES):
                raise RuntimeError(f'Invalid catalogue table at record {line_number}')
            table_name = _TABLES[table_index]
            record = registries[table_name].get(identifier)
            if not isinstance(record, dict):
                # Stage-only metadata for optional procedurally placed rooms
                # is allowed to refer to a room absent in this world instance.
                if table_name == 'ROOMS' and isinstance(fields, dict) and set(fields) == {'generator_level'}:
                    continue
                missing += 1
                missing_ids.append((table_name, identifier))
                continue
            if not isinstance(fields, dict):
                continue
            for key, value in fields.items():
                if key in record:
                    skipped += 1
                else:
                    record[key] = value
                    loaded += 1
    if missing > 0:
        raise RuntimeError(f'Static catalogue mismatch: {missing} missing record IDs: {missing_ids[:30]}')
    return {'loaded_numeric_defaults': loaded, 'authored_fields_preserved': skipped,
            'unknown_record_ids': missing, 'mutating_generator_disabled': True}
