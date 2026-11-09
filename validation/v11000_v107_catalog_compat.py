# -*- coding: utf-8 -*-
"""Verify the preserved 30 v107 archetypes inside the real 38-class v110 world.

Run all the historical gameplay/SQLite checks against the full registry.
Never truncate global classes/races, mutate player data, or weaken assertions.
"""
from __future__ import annotations
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

def main():
    if os.environ.get('SOULBOUND_V110_STAGING')!='1':
        raise PermissionError('v110 catalog compatibility needs isolated predeploy mode')
    import server
    import core.classes_skills as catalog
    from core.v10700_new_archetypes import CLASS_SPECS as old_classes,RACE_SPECS as old_races
    from core.v11000_archetypes import CLASS_SPECS as new_classes,RACE_SPECS as new_races
    assert len(catalog.CLASSES)==38 and len(catalog.RACES)==38
    assert len(new_classes)==len(new_races)==8
    class_prefix=catalog.CLASSES[:30];race_prefix=catalog.RACES[:30]
    assert len(set(x[0] for x in class_prefix))==30
    assert len(set(x[0] for x in race_prefix))==30
    assert all(c[0] in {x[0] for x in class_prefix} for c in old_classes)
    assert all(r[0] in {x[0] for x in race_prefix} for r in old_races)
    assert all(c[0] not in {x[0] for x in class_prefix} for c in new_classes)
    assert all(r[0] not in {x[0] for x in race_prefix} for r in new_races)
    from validation.v10700_consolidated_content_regression import run
    checks=run()  # full 38-class catalog, all old quests/professions/SQLite isolation
    assert checks > 2000
    assert len(catalog.CLASSES)==38 and len(catalog.RACES)==38
    print(f'V110 V107 CATALOG: {checks} historical content/SQLite checks PASS, '
          '30 preserved + 8 new classes/races, no production mutation',flush=True)

if __name__=='__main__':main()
