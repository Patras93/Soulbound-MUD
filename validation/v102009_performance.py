# -*- coding: utf-8 -*-
"""v102.00.9: safe OLC caching, profiler wait isolation and quest diagnostics."""
import asyncio
import copy
from pathlib import Path
from types import SimpleNamespace
import sqlite3


def run():
    checks = 0
    def check(test, label):
        nonlocal checks
        assert test, label
        checks += 1
    root = Path(__file__).resolve().parents[1]
    from systems.live_content_v1204 import LiveContentV1204
    from systems.admin_live_quest_xp_threshold_v1 import plan, _eligible, _fields
    from data.quests import QUESTS
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    service = LiveContentV1204(SimpleNamespace(conn=db))
    try:
        before = copy.deepcopy(service.draft)
        check('0 lokacji' in service.validate(service.draft), 'blank validation')
        rows, info = plan(service, 'wszystkie', '1001')
        check('EXPPROGI:' in info, 'bulk preview')
        check(len(rows) > 0, 'some positive rewards below 1001')
        check(before == service.draft, 'preview read only')
        expected=[]
        for field in _fields('wszystkie'):
            matched,_ = _eligible(service, field, 1001)
            expected.extend((qid,field,amount) for qid,amount in matched)
        check(rows == expected, 'single snapshot matches independent eligibility per axis')
        check(set(QUESTS).issuperset(qid for qid,_,_ in rows), 'only real quests')
        check(service.active == before, 'active untouched')
        check('effective_items = set(ITEMS) | set(data[\'items\'])' in
              (root / 'systems/live_content_v1204.py').read_text(encoding='utf-8'),
              'shared item IDs')
        src = (root / 'systems/live_content_v1204.py').read_text(encoding='utf-8')
        check(src.count('set(ITEMS) | set(data[\'items\'])') == 2, 'no per-quest item rebuild')
        check(src.count('set(MOB_TEMPLATES) | set(data[\'mobs\'])') == 1, 'no per-quest mob rebuild')
        check(src.count('set(QUESTS) | set(data[\'quests\'])') == 2, 'no per-quest quest rebuild')
        src = (root / 'world/expansions.py').read_text(encoding='utf-8')
        check('mob_id in spawned_template_ids_v102009' in src, 'spawn membership')
        check('any(tid == mob_id for _room,tid in MOB_SPAWNS)' not in src, 'no repeated spawn scans')
        cmd = (root / 'player/session_mixins/command_loop.py').read_text(encoding='utf-8')
        check('_perf_intentional_wait_v102009' in cmd, 'intentional wait tracker')
        check('record_slow_command_v1224(command or token, _perf_work_v102009)' in cmd,
              'records work time, not total time')
        check('raw)' not in cmd[cmd.index('if _perf_work_v102009 >= 0.25:'):cmd.index('if dispatched is COMMAND_LOOP_BREAK')],
              'no command arguments logged')
        crafting = (root / 'player/session_mixins/crafting.py').read_text(encoding='utf-8')
        check('await asyncio.sleep(action_seconds)' in crafting, 'actual crafting timer unchanged')
        check('_wait_start_v102009' in crafting, 'craft timer measured')
        quit_src = (root / 'player/session_mixins/command_special_handlers.py').read_text(encoding='utf-8')
        check('selected = await self.character_selection_flow()' in quit_src,
              'same character-selection flow')
        check('_menu_started_v102009' in quit_src, 'menu waiting measured')
        quest_src = (root / 'player/session_mixins/quest_offers.py').read_text(encoding='utf-8')
        check('PERF QUESTACCEPT' in quest_src, 'quest phase diagnostic')
        check('self.server.db.start_quest(self.account_id, quest_id)' in quest_src,
              'quest accept unchanged')
        db_src = (root / 'storage/database.py').read_text(encoding='utf-8')
        check('LIMIT 100' in db_src and 'admin_slow_commands_v1224' in db_src,
              'retention still bounded')
        check('admin komendy wolne' in (root/'README_ADMIN_LIVE_PL.txt').read_text(encoding='utf-8'),
              'diagnostic documented')
        check((root/'VERSION').read_text(encoding='utf-8').strip() == '102.00.11',
              'release matches')
        return checks
    finally:
        service._remove(None)
        db.close()


if __name__ == '__main__':
    print(f'OPTIMIZATION v102.00.9: {run()} checks PASS', flush=True)
