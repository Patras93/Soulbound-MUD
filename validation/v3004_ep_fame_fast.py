# -*- coding: utf-8 -*-
"""Fast source contract: EP grants the same independent XP axes as Fame."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_regression_fast():
    source = (ROOT / 'player/session_mixins/exploration_progress.py').read_text('utf-8')
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and
                 n.name == 'SessionExplorationProgressMixin')
    discovery = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and
                     n.name == 'discover_room')
    calls = [n.func.attr for n in ast.walk(discovery)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    expected = ('mark_room_discovered_with_points_v2322',
                'grant_combat_soul_xp_v11350', 'grant_class_xp',
                'grant_stat_xp_v11342', 'add_character_xp_with_event',
                'save_character')
    for method in expected:
        assert method in calls, ('EP Fame source contract', method)
    assert source.index('if not is_new:') < source.index('caps = ep_awards'), 'repeat EP guard'
    assert source.count('caps = ep_awards') == 1
    assert 'for _ in range(ep_points):' in source, 'one award per EP'
    assert 'if caps["class_total"]:' in source, 'class guard'
    assert 'bez EXP profesji i narzędzi' in source, 'NVDA summary'
    return len(expected) + 5


if __name__ == '__main__':
    print(f'EP JAK FAME v3.00.4 FAST: {run_regression_fast()} checks PASS')
