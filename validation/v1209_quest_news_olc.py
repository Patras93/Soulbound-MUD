# -*- coding: utf-8 -*-
"""v12.00.9: independent OLC quest/news checks (no production DB writes)."""
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

from systems.live_content_v1204 import LiveContentV1204, QUESTS
from systems.live_quest_olc_v1209 import parse_quest_edit, news_summary


def run_regression():
    count = 0
    original = copy.deepcopy(QUESTS['bandit_patrol'])
    with tempfile.TemporaryDirectory() as temp:
        conn = sqlite3.connect(str(Path(temp) / 'test.db'))
        conn.row_factory = sqlite3.Row
        conn.execute('CREATE TABLE quests (account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER, PRIMARY KEY(account_id,quest_id))')
        db = SimpleNamespace(conn=conn)
        live = LiveContentV1204(db)
        world = SimpleNamespace(mobs={}, _last_refresh_at=1.)
        world._register_runtime_spawn = lambda rid, mid: None
        server = SimpleNamespace(sessions=[],world=world)
        try:
            for field, value, desired in (
                ('reward_xp', '50000', ('olc_reward_xp', 50000)),
                ('reward_class_xp', '17000', ('olc_reward_class_xp', 17000)),
                ('reward_soul_xp', '3000', ('olc_reward_soul_xp', 3000)),
                ('reward_stat_xp', '1200', ('olc_reward_stat_xp', 1200)),
                ('needed', '50', ('needed', 50)),
                ('reward_items', '{"healing_potion":2}', ('reward_items', {'healing_potion':2})),
                ('repeatable','true',('repeatable',True)),
                ('repeat_cooldown','7200',('repeat_cooldown',7200)),
            ):
                assert parse_quest_edit(field, value) == desired; count += 1
                live.stage_edit('quest','bandit_patrol',field,value);count += 1
            for invalid in (('reward_xp','-5'),('reward_xp','abc'),('reward_items','{"not_an_item":3}'),('kind','<x>')):
                try: live.stage_edit('quest','bandit_patrol', *invalid)
                except ValueError: count += 1
                else: raise AssertionError(f'Accepted invalid field {invalid}')
            assert QUESTS['bandit_patrol'] == original; count += 1
            previous = copy.deepcopy(live.active)
            outcome = live.apply(server,'tester')
            assert 'rewizję 1' in outcome;count += 1
            q = QUESTS['bandit_patrol']
            assert q['olc_reward_xp'] == 50000 and q['needed'] == 50;count += 1
            assert q['olc_reward_stat_xp'] == 1200;count += 1
            text = live.describe_news(previous)
            assert 'Patrol przeciw bandytom' in text and '50000' in text and '50' in text;count += 1
            assert 'rewizja 1' in text and len(text) <= 500;count += 1
            assert live.apply(server, 'tester') == 'Nie ma nowych zmian.';count += 1
            live._remove(world)
            live = LiveContentV1204(db)
            assert QUESTS['bandit_patrol']['olc_reward_xp'] == 50000;count += 1
            conn.execute("INSERT INTO quests(account_id,quest_id,status,progress) VALUES(1,'bandit_patrol','active',2)")
            conn.commit()
            live.stage_edit('quest', 'bandit_patrol','target','temple_rat')
            try: live.apply(server,'tester')
            except ValueError as exc:
                assert 'aktywny' in str(exc);count += 1
            else: raise AssertionError('Quest active while goal changed')
            # Change a reward while the quest is active; progress must remain.
            live.reset_draft()
            live.stage_edit('quest','bandit_patrol','reward_xp','75000')
            live.apply(server,'tester')
            assert conn.execute("SELECT progress FROM quests WHERE quest_id='bandit_patrol'").fetchone()[0] == 2;count += 1
            assert QUESTS['bandit_patrol']['olc_reward_xp']==75000;count+=1
            assert '75000' in news_summary(previous, live.active,revision=2);count+=1
        finally:
            live._remove(world)
            assert QUESTS['bandit_patrol'] == original;count += 1
            conn.close()
    return count + test_admin_news_flow()


def test_admin_news_flow():
    """Exercise the real administrator command and its one-NEWS transaction."""
    import ast
    import asyncio
    source = (Path(__file__).resolve().parents[1] /
              'player/session_mixins/admin_tools.py').read_text('utf-8')
    tree = ast.parse(source)
    owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and
                 any(getattr(child, 'name', '') == 'admin_live_v1204' for child in node.body))
    method = next(node for node in owner.body if getattr(node, 'name', '') == 'admin_live_v1204')
    module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
        name='LiveAdminMini', bases=[], keywords=[], body=[method], decorator_list=[]
    )], type_ignores=[]))
    scope = {}
    exec(compile(module, 'admin_live_olc_test', 'exec'), scope)
    Mini = scope['LiveAdminMini']
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER)')
    db = SimpleNamespace(conn=conn, account_name=lambda *_: 'admin',
                         record_admin_action_v1224=lambda *args: None)
    world = SimpleNamespace(mobs={}, _last_refresh_at=10.,
                            _register_runtime_spawn=lambda *args: None)
    server = SimpleNamespace(world=world, sessions=[], db=db)
    server.live_content_v1204 = LiveContentV1204(db)
    admin = Mini()
    admin.server = server
    admin.master_account_id = 1
    admin.is_admin = lambda: True
    admin.messages, admin.news = [], []

    async def send(message):
        admin.messages.append(message)

    async def news(message):
        admin.news.append(message)

    admin.send, admin.news_channel_v1204 = send, news

    async def check():
        await admin.admin_live_v1204('questy Wedkarstwo')
        assert 'OLC questy Wedkarstwo' in admin.messages[-1]
        await admin.admin_live_v1204('quest bandit_patrol')
        assert 'OLC QUEST bandit_patrol' in admin.messages[-1]
        await admin.admin_live_v1204('edytuj quest bandit_patrol reward_xp | 50000')
        await admin.admin_live_v1204('edytuj quest bandit_patrol needed | 50')
        assert not admin.news
        await admin.admin_live_v1204('sprawdz')
        assert not admin.news
        await admin.admin_live_v1204('aktywuj POTWIERDZAM')
        assert len(admin.news) == 1 and '50000' in admin.news[0] and '50' in admin.news[0]
        await admin.admin_live_v1204('aktywuj POTWIERDZAM')
        assert len(admin.news) == 1
        await admin.admin_live_v1204('cofnij POTWIERDZAM')
        assert len(admin.news) == 2 and 'Cofnięto' in admin.news[-1]
        return 8

    try:
        return asyncio.run(check())
    finally:
        server.live_content_v1204._remove(world)
        conn.close()


if __name__ == '__main__':
    print(f'V12.00.9 QUEST EXP / CELE / NEWS: {run_regression()} checks PASS')
