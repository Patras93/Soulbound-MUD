# -*- coding: utf-8 -*-
"""Legacy source checks across verified v109 refactoring.

Read *actual* shipped source, not stored copies or strings added for tests.
The v109 release suite also verifies AST equality and module integration.
"""
from pathlib import Path
from validation.v4200_virtual_source import read_actual_refactored_source_v4200

ROOT=Path(__file__).resolve().parents[1]
SHARDS={
 'data/items.py': ('data/catalogs_v109/items_*.py',),
 'data/quests.py': ('data/catalogs_v109/quests_*.py',),
 'data/npcs.py': ('data/catalogs_v109/npcs_*.py',),
 'data/mobs.py': ('data/catalogs_v109/mobs_*.py',),
 'storage/db_inventory.py': ('storage/db_inventory_parts_v109/*.py',),
 'player/session_mixins/admin_tools.py': ('player/session_mixins/admin_tools_parts_v109/*.py',),
 'player/session_mixins/combat_survival.py': ('player/session_mixins/combat_survival_parts_v109/*.py',),
 'player/session_mixins/combat_damage.py': ('player/session_mixins/combat_damage_parts_v109/*.py',),
 'player/session_mixins/combat_rewards.py': ('player/session_mixins/combat_rewards_parts_v109/*.py',),
 'player/session_mixins/sales.py': ('player/session_mixins/sales_parts_v109/*.py',),
 'player/session_mixins/world_events_endgame.py': ('player/session_mixins/world_events_parts_v109/*.py',),
 'player/session_mixins/help.py': ('player/session_mixins/help_parts_v109/*.py',),
}

def read_actual_modular_source_v109(file):
    path=Path(file).resolve(strict=True)
    rel=path.relative_to(ROOT.resolve(strict=True)).as_posix()
    code=read_actual_refactored_source_v4200(path)
    for glob in SHARDS.get(rel, ()):
        modules=sorted(ROOT.glob(glob))
        if not modules: raise AssertionError('v109 missing source shards: '+glob)
        for part in modules:
            if part.is_symlink(): raise AssertionError('v109 symlinked source: '+str(part))
            code+='\n'+part.read_text(encoding='utf-8-sig')
    return code
