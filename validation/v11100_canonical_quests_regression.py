# -*- coding: utf-8 -*-
"""v111+: testy historycznych katalogów na aktualnym źródle world/quests.

Żadne kopie v109/v110 nie są potrzebne w pełnym ZIP-ie PREDEPLOY.
"""
from __future__ import annotations
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from validation import v10900_actual_modular_source as reader

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    *(f'data/catalogs_v109/quests_{i:02d}.py' for i in range(1, 4)),
    *(f'world/quests_v110/{name}.py' for name in
      ('__init__', 'classes', 'races', 'events', 'regional')),
)
CANONICAL = tuple(f'world/quests/base_{i:02d}.py' for i in range(1, 4))


def run() -> int:
    checks = 0
    assert not any((ROOT / rel).exists() for rel in RETIRED)
    checks += len(RETIRED)
    for rel in CANONICAL:
        path=ROOT/rel
        assert path.is_file() and not path.is_symlink()
        ast.parse(path.read_text(encoding='utf-8-sig'))
        checks+=1
    original = reader.read_actual_modular_source_v109(ROOT/'data/quests.py')
    # This is a source inspector, not a canned test fixture; actual canonical
    # code from all three fragments is included in the reconstructed view.
    for rel in CANONICAL:
        fragment=(ROOT/rel).read_text(encoding='utf-8-sig')
        assert fragment in original,rel
        checks+=1
    with TemporaryDirectory(prefix='sb111_quest_current_') as td:
        mock_root=Path(td)
        (mock_root/'VERSION').write_text('112.00.0',encoding='utf8')
        (mock_root/'data').mkdir()
        (mock_root/'world/quests').mkdir(parents=True)
        facade=mock_root/'data/quests.py'
        facade.write_text('QUESTS = {}\n',encoding='utf8')
        for i in range(1,4):
            (mock_root/f'world/quests/base_{i:02d}.py').write_text(
                f'CANONICAL_QUEST_{i:02d} = {i}\n',encoding='utf8')
        with patch.object(reader,'ROOT',mock_root):
            view=reader.read_actual_modular_source_v109(facade)
            assert all(f'CANONICAL_QUEST_{i:02d}' in view for i in range(1,4))
            checks+=1
            (mock_root/'world/quests/base_02.py').unlink()
            try:
                reader.read_actual_modular_source_v109(facade)
            except AssertionError as exc:
                assert 'canonical quest fragments' in str(exc)
                checks+=1
            else:
                raise AssertionError('Source audit silently accepted missing current quest')
    return checks

if __name__=='__main__':
    print(f'V111 CANONICAL QUEST SOURCE REGRESSION: {run()} PASS')
