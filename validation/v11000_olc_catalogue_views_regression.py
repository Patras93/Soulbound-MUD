# -*- coding: utf-8 -*-
"""V110 isolated checks: OLC fast read-only views preserve legacy safety."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from systems.v11000_olc_validation_views import combined_catalog, quest_dependency_view
from systems.live_olc17_quest_dependencies import validate_dependency_graph


def run_regression():
    n = 0
    # No overlay: no useless materialization, but validation still sees all
    # original live definitions. The result is read-only by contract.
    base_items = {'ore': {'type': 'resource'}, 'log': {'type': 'resource'}}
    assert combined_catalog(base_items, {}) is base_items; n += 1
    fresh = {'item_x': {'type': 'craft_material'}}
    merged = combined_catalog(base_items, fresh)
    assert set(merged) == {'ore', 'log', 'item_x'}; n += 1
    assert merged is not base_items and merged['ore'] == base_items['ore']; n += 1
    merged.pop('ore')
    assert 'ore' in base_items; n += 1
    assert combined_catalog(base_items, {'log': {'type': 'weapon'}})['log']['type'] == 'weapon'; n += 1
    assert base_items['log']['type'] == 'resource'; n += 1
    # Keep running cycle validation even when there is no draft quest overlay.
    q = {'one': {'requires_quest': None}, 'two': {'requires_quest': 'one'}}
    graph = quest_dependency_view(q, {}, {})
    assert graph is q; n += 1
    assert validate_dependency_graph(graph) == 2; n += 1
    overridden = quest_dependency_view(q, {}, {'one': {'requires_quest': 'two'}})
    assert overridden is not q and overridden['one']['requires_quest'] == 'two'; n += 1
    assert q['one']['requires_quest'] is None; n += 1
    try:
        validate_dependency_graph(overridden)
    except ValueError as exc:
        assert 'cykl' in str(exc); n += 1
    else:
        raise AssertionError('Nie wykryto cyklu po zmianie istniejącego questa.')
    newer = quest_dependency_view(q, {'three': {'requires_quest': 'two'}}, {})
    assert validate_dependency_graph(newer) == 3; n += 1
    assert 'three' not in q; n += 1
    broken = {'one': {'requires_quests': ['missing']}}
    try:
        validate_dependency_graph(quest_dependency_view(broken, {}, {}))
    except ValueError as exc:
        assert 'nieznany' in str(exc); n += 1
    else:
        raise AssertionError('Nie wykryto brakującej zależności.')
    return n


if __name__ == '__main__':
    print('V110 OLC CATALOGUE VIEWS:', run_regression(), 'PASS')
