# -*- coding: utf-8 -*-
"""Current-value preview is read-only; tested against real OLC catalogs."""
import asyncio
import ast
import copy
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.live_content_v1204 import LiveContentV1204
from core.progression_resources import v0270_quest_character_reward
from data.quests import QUESTS


def run_regression():
    count = 0
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE quests (account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER)')
    server = SimpleNamespace(world=SimpleNamespace(mobs={}, _last_refresh_at=1,
           _register_runtime_spawn=lambda *a: None), sessions=[])
    db = SimpleNamespace(conn=con, account_name=lambda *_: 'admin',
                         record_admin_action_v1224=lambda *a: None)
    server.db = db
    live = LiveContentV1204(db)
    server.live_content_v1204 = live
    baseline = copy.deepcopy(live.draft)
    qvalue = v0270_quest_character_reward(QUESTS['bandit_patrol'])
    original_quest = copy.deepcopy(QUESTS['bandit_patrol'])
    try:
        result = describe_current_edit(live, 'quest','bandit_patrol','reward_xp')
        assert f'reward_xp | {qvalue}' in result and 'automatycznie' in result; count+=1
        assert live.draft == baseline and live.active == baseline; count+=1
        result = describe_current_edit(live,'quest','bandit_patrol','needed')
        assert f'needed | {QUESTS["bandit_patrol"]["needed"]}' in result;count+=1
        result = describe_current_edit(live,'quest','bandit_patrol','repeatable')
        assert 'repeatable | false' in result or 'repeatable | true' in result;count+=1
        result = describe_current_edit(live,'surowiec','iron_ore','prof_scale')
        assert 'prof_scale | 100' in result;count+=1
        result = describe_current_edit(live,'surowiec','iron_ore','prof_fixed')
        assert 'brak stałej wartości' in result and 'NIE aktualnym EXP' in result;count+=1
        result = describe_current_edit(live,'surowiec','iron_ore','prof_mode')
        assert 'prof_mode | auto' in result;count+=1
        assert live.draft == baseline and live.revision == 0;count+=1
        live.stage_edit('quest','bandit_patrol','reward_xp','35000')
        result = describe_current_edit(live,'quest','bandit_patrol','reward_xp')
        assert f'reward_xp | {qvalue}' in result and 'przygotowane: 35000' in result;count+=1
        live.apply(server,'admin')
        result = describe_current_edit(live,'quest','bandit_patrol','reward_xp')
        assert 'reward_xp | 35000' in result and 'ręczna' in result;count+=1
        live.stage_edit('surowiec','iron_ore','prof_fixed','500')
        live.apply(server,'admin')
        result = describe_current_edit(live,'surowiec','iron_ore','prof_fixed')
        assert 'prof_fixed | 500' in result and 'ręczna' in result;count+=1
        # Unknown IDs and disallowed fields must be rejected rather than leak input.
        for group, ident, fld in [('quest','x'*50,'needed'),('quest','bandit_patrol','arbitrary'),
                                  ('surowiec','healing_potion','prof_fixed')]:
            try: describe_current_edit(live, group, ident, fld)
            except ValueError: count+=1
            else: raise AssertionError((group, ident, fld))

        source = (Path(__file__).resolve().parents[1]/'player/session_mixins/admin_tools.py').read_text('utf-8')
        tree = ast.parse(source)
        owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and
                     any(getattr(child, 'name', '')=='admin_live_v1204' for child in node.body))
        method = next(node for node in owner.body if getattr(node,'name','')=='admin_live_v1204')
        astmodule = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
            name='Mini',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
        scope = {}
        exec(compile(astmodule,'preview_test','exec'),scope)
        mini = scope['Mini']()
        mini.server = server
        mini.master_account_id = 1
        mini.is_admin = lambda: True
        mini.messages, mini.news = [], []
        async def send(msg): mini.messages.append(msg)
        async def news(msg): mini.news.append(msg)
        mini.send = send
        mini.news_channel_v1204 = news

        async def checks():
            await mini.admin_live_v1204('edytuj quest bandit_patrol reward_xp')
            assert 'reward_xp | 35000' in mini.messages[-1] and not mini.news
            await mini.admin_live_v1204('edytuj surowiec iron_ore prof_fixed')
            assert 'prof_fixed | 500' in mini.messages[-1] and not mini.news
            await mini.admin_live_v1204('edytuj quest bandit_patrol reward_xp | 120')
            assert live.draft['quest_edits']['bandit_patrol']['olc_reward_xp']==120
            await mini.admin_live_v1204('edytuj quest bandit_patrol reward_xp')
            assert 'przygotowane: 120' in mini.messages[-1] and not mini.news
            saved = copy.deepcopy(live.draft)
            await mini.admin_live_v1204('edytuj quest brak_takiego_questa reward_xp')
            assert live.draft == saved and 'Wersja robocza bez zmian' in mini.messages[-1]
            return 5
        count+=asyncio.run(checks())
        return count
    finally:
        live._remove(server.world)
        assert QUESTS['bandit_patrol'] == original_quest
        con.close()


if __name__=='__main__':
    print('V12.00.10 PODGLAD EDYCJI NVDA:',run_regression(),'checks PASS')
