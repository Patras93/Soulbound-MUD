"""Deterministic, authored snapshot of legacy numeric defaults (v1.28.3).

A single, versioned catalogue replaces the destructive old on-start Generator
Core pass. No skills, items or quests are synthesized or renamed at runtime.
Existing authored values always take priority. The old mathematical helpers
remain available for unrelated dynamic systems until migrated safely.
"""
from __future__ import annotations
import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parent.parent / 'data' / 'catalogue_numeric_defaults_v1283.json'
_TABLES = ('ROOMS', 'MOB_TEMPLATES', 'ITEMS', 'QUESTS', 'CLASS_SKILLS',
           'CRAFT_RECIPES', 'COOK_RECIPES', 'ALCHEMY_RECIPES', 'JEWELCRAFT_RECIPES')


def apply_catalogue_defaults_v1283(namespace):
    if not _CATALOG_PATH.is_file():
        raise RuntimeError('Missing static catalogue data: '+str(_CATALOG_PATH))
    data = json.loads(_CATALOG_PATH.read_text(encoding='utf-8'))
    loaded = skipped = missing = 0
    missing_ids = []
    for table_name in _TABLES:
        registry = namespace.get(table_name) or {}
        defaults = data.get(table_name, {})
        if table_name == 'CLASS_SKILLS':
            registry = {str(s.get('id')): s for rows in registry.values() for s in rows}
        for identifier, fields in defaults.items():
            record = registry.get(identifier)
            if not isinstance(record, dict):
                # A region may generate a different subset of optional rooms
                # for its runtime map layout. Stage-only metadata is safe to
                # omit when such a room does not exist in this world instance.
                if table_name == 'ROOMS' and set(fields) == {'generator_level'}:
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
    # Detect a shifted catalogue or wrong dependency order during deploy.
    if missing > 0:
        raise RuntimeError(f'Static catalogue mismatch: {missing} missing record IDs: {missing_ids[:30]}')
    return {'loaded_numeric_defaults':loaded, 'authored_fields_preserved':skipped,
            'unknown_record_ids':missing, 'mutating_generator_disabled':True}
