"""Compact catalogue parity checks, independent of production SQLite."""
from __future__ import annotations

import gzip
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from core import catalog_fallback_v1283 as catalogue

_EXPECTED_COUNTS = (2333, 14731, 95074, 782, 3403, 377, 48, 42, 163)


def run_regression():
    checks = 0
    seen = [0] * len(catalogue._TABLES)
    first = [None] * len(catalogue._TABLES)
    last = [None] * len(catalogue._TABLES)
    assert catalogue._CATALOG_PATH.is_file()
    checks += 1
    assert catalogue._CATALOG_PATH.stat().st_size < 1_000_000
    checks += 1
    with gzip.open(catalogue._CATALOG_PATH, 'rt', encoding='utf-8') as stream:
        for line in stream:
            table_index, identifier, fields = json.loads(line)
            assert isinstance(table_index, int) and 0 <= table_index < len(seen)
            assert isinstance(identifier, str) and identifier
            assert isinstance(fields, dict)
            seen[table_index] += 1
            if first[table_index] is None:
                first[table_index] = identifier
            last[table_index] = identifier
    assert tuple(seen) == _EXPECTED_COUNTS, seen
    checks += 1
    assert sum(seen) == 116953
    checks += 1
    assert all(a and b for a, b in zip(first, last))
    checks += 1

    # The importer uses the original table order and never replaces hand-authored
    # fields. Include a CLASS_SKILLS registry and a missing optional room.
    rows = (
        [0, 'optional_room', {'generator_level': 8}],
        [0, 'room', {'generator_level': 4, 'xp': 3}],
        [1, 'mob', {'generator_level': 5, 'attack': 6}],
        [2, 'item', {'price': 77}],
        [4, 'mage_spell', {'mana': 10}],
    )
    with tempfile.TemporaryDirectory(prefix='soulbound-catalog-') as temp:
        sample = Path(temp) / 'sample.gz'
        with gzip.open(sample, 'wt', encoding='utf-8') as stream:
            for record in rows:
                stream.write(json.dumps(record, separators=(',', ':')) + '\n')
        ns = {
            'ROOMS': {'room': {'generator_level': 42}},
            'MOB_TEMPLATES': {'mob': {'attack': 99}},
            'ITEMS': {'item': {}},
            'CLASS_SKILLS': {'mage': [{'id': 'mage_spell', 'mana': 5}]},
        }
        with patch.object(catalogue, '_CATALOG_PATH', sample):
            result = catalogue.apply_catalogue_defaults_v1283(ns)
            assert result == {
                'loaded_numeric_defaults': 3,
                'authored_fields_preserved': 3,
                'unknown_record_ids': 0,
                'mutating_generator_disabled': True,
            }, result
            checks += 1
            assert ns['ROOMS']['room'] == {'generator_level': 42, 'xp': 3}
            checks += 1
            assert ns['MOB_TEMPLATES']['mob'] == {'attack': 99, 'generator_level': 5}
            checks += 1
            assert ns['ITEMS']['item'] == {'price': 77}
            checks += 1
            assert ns['CLASS_SKILLS']['mage'][0]['mana'] == 5
            checks += 1
            assert ns['CLASS_SKILLS']['mage'][0]['id'] == 'mage_spell'
            checks += 1
            with gzip.open(sample, 'wt', encoding='utf-8') as stream:
                stream.write(json.dumps([1, 'unknown_mob', {'hp': 1}]) + '\n')
            try:
                catalogue.apply_catalogue_defaults_v1283(ns)
            except RuntimeError as exc:
                assert 'Static catalogue mismatch: 1' in str(exc)
                checks += 1
            else:
                raise AssertionError('Missing mob should be rejected')
    return checks
