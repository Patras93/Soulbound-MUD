# -*- coding: utf-8 -*-
"""v24.00.1: a published OLC gold edit must change the REAL quest payout."""
import asyncio
import ast
import copy
import sqlite3
from pathlib import Path
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, QUESTS
    from systems.game_feel_rewards import quest_completion_bonus_v11324
    from core.progression_resources import v0190_quest_currency_reward
    from systems.live_olc_preview_v12010 import describe_current_edit
    from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL

    counts = 0
    def ok(condition, reason):
        nonlocal counts
        assert condition, reason
        counts += 1

    original = copy.deepcopy(QUESTS['bandit_patrol'])
    # Production boot normally sets this marker via world.runtime_progression.
    # Make it explicit here so the test catches the exact production failure.
    QUESTS['bandit_patrol'].update(
        reward_silver=1829, reward_gold=0, reward_mithril=0,
        manual_currency_reward_coins=1829, currency_reward_mode='manual')
    conn = sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER)')
    conn.execute("INSERT INTO quests VALUES(1, 'bandit_patrol', 'active', 5)")
    conn.commit()
    db = SimpleNamespace(conn=conn, account_name=lambda *_:'test-admin', record_admin_action_v1224=lambda *_:None)
    world=SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world, sessions=[], db=db)
    svc=None
    try:
        svc=LiveContentV1204(db)
        server.live_content_v1204=svc
        ok(v0190_quest_currency_reward(QUESTS['bandit_patrol'])==1829, 'production marker overrides authored payout')

        # Test the REAL admin command dispatcher with the exact user's syntax.
        source=(Path(__file__).resolve().parents[1]/'player/session_mixins/admin_tools.py').read_text('utf-8')
        tree=ast.parse(source)
        owner=next(node for node in tree.body if isinstance(node,ast.ClassDef) and
                   any(getattr(child,'name','')=='admin_live_v1204' for child in node.body))
        method=next(node for node in owner.body if getattr(node,'name','')=='admin_live_v1204')
        mini=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='GoldAdmin',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
        ns={};exec(compile(mini,'gold_admin_test','exec'),ns)
        actor=ns['GoldAdmin']()
        actor.server=server
        actor.master_account_id=1
        actor.is_admin=lambda:True
        actor.messages=[];actor.news=[]
        async def send(msg):actor.messages.append(str(msg))
        async def news(msg):actor.news.append(str(msg))
        actor.send=send;actor.news_channel_v1204=news
        asyncio.run(actor.admin_live_v1204('edytuj quest bandit_patrol reward_gold 100'))
        ok(svc.draft['quest_edits']['bandit_patrol']['reward_gold']==100, 'user syntax accepted without pipe')
        ok(v0190_quest_currency_reward(QUESTS['bandit_patrol'])==1829, 'staged change not active')
        asyncio.run(actor.admin_live_v1204('sprawdz'))
        asyncio.run(actor.admin_live_v1204('aktywuj POTWIERDZAM'))
        q=QUESTS['bandit_patrol']
        ok(svc.revision==1, 'published once')
        ok((q['reward_silver'],q['reward_gold'],q['reward_mithril'])==(11829,0,0), 'normalized denomination')
        ok(q['manual_currency_reward_coins']==11829 and q['currency_reward_mode']=='manual', 'manual marker updated')
        ok(v0190_quest_currency_reward(q)==11829, 'real quest turn-in uses new gold')
        ok(quest_completion_bonus_v11324(q,11829,0.0)==0, 'manual award never receives random envelope')
        ok(conn.execute("SELECT progress FROM quests WHERE quest_id='bandit_patrol'").fetchone()[0]==5, 'active quest progress retained')
        ok('100' in describe_current_edit(svc,'quest','bandit_patrol','reward_gold'), 'preview shows authored gold')
        ok(len(actor.news)==1, 'one post-publish NEWS')

        # Exact 100 gold: zero the already-existing 1829 silver.
        svc.stage_edit('quest','bandit_patrol','reward_silver','0')
        svc.stage_edit('quest','bandit_patrol','reward_mithril','0')
        svc.apply(server,'test-admin')
        ok(v0190_quest_currency_reward(QUESTS['bandit_patrol'])==10000,'100 gold exactly')
        ok(QUESTS['bandit_patrol']['reward_silver']==10000, 'canonical silver wallet')
        ok(conn.execute("SELECT progress FROM quests WHERE quest_id='bandit_patrol'").fetchone()[0]==5, 'quest progress intact after second revision')
        try:
            svc.stage_edit('quest','bandit_patrol','reward_mithril',str(CURRENCY_SQLITE_SAFE_TOTAL))
        except ValueError:
            counts+=1
        else: raise AssertionError('unsafe sqlite reward accepted')
        ok(v0190_quest_currency_reward(QUESTS['bandit_patrol'])==10000,'invalid draft did not publish')
        # Simulate engine restart: uninstall current snapshot, load active from SQLite.
        svc._remove(world)
        svc=LiveContentV1204(db)
        server.live_content_v1204=svc
        ok(svc.revision==2 and v0190_quest_currency_reward(QUESTS['bandit_patrol'])==10000, 'persistent after service reload')
        svc.apply(server,'test-admin',rollback=True)
        ok(v0190_quest_currency_reward(QUESTS['bandit_patrol'])==11829,'rollback to prior amount')
    finally:
        if svc is not None:
            svc._remove(world)
        QUESTS['bandit_patrol'].clear()
        QUESTS['bandit_patrol'].update(original)
        conn.close()
    return counts

if __name__ == '__main__':
    print(f'v24.00.1 QUEST GOLD OLC: PASS {run()} kontroli')
