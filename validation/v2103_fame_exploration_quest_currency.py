# -*- coding: utf-8 -*-
"""Soulbound v2.10.3: real reward gateways and full assembled quest catalog.

Test deliberately uses temporary in-memory SQLite and fake progression sinks:
no player's database or production character is used.
"""
from __future__ import annotations
import asyncio
from types import SimpleNamespace
import sqlite3
import time
from core.bootstrap_economy_professions import legacy_currency_to_coins
from core.progression_resources import v0190_quest_currency_reward
from systems.experience_cap_v2009 import experience_cap_v2009
from systems.milestone_cap_rewards_v2103 import (
    exploration_point_xp_v2103, fame_cap_awards_v2103,
    explorer_award_per_point_v4211, _fame_award_for_level_v4211,
)
from systems.fame_v1702 import ensure_schema, pay_due_fame


class _MockDB:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.saved = 0
    def multi_cap_v23215(self, account_id):
        assert account_id == 32
        return 248500
    def save_character(self, char):
        self.saved += 1


class _MockSession:
    account_id = 32
    closed = False
    def __init__(self):
        self.server = SimpleNamespace(db=_MockDB())
        self.character = SimpleNamespace(character_level=55, soul_level=31,
                                         STAT_PROGRESS_FIELDS=('str','dex','con','int','wis','cha'))
        self.received = []
        self.messages = []
    def active_class_names(self):
        return ('Mag','Wojownik')
    def class_mastery_level(self, name):
        return 70 if name == 'Mag' else 24
    async def grant_combat_soul_xp_v11350(self, xp, **kw):
        self.received.append(('soul', xp, kw))
    async def grant_class_xp(self, xp, **kw):
        self.received.append(('class', xp, kw))
    async def grant_stat_xp_v11342(self, xp, **kw):
        self.received.append(('stat', xp, kw))
    def add_character_xp_with_event(self, xp, **kw):
        self.received.append(('character', xp, kw))
        return []
    async def send(self, line):
        self.messages.append(line)


def run_regression():
    from systems.content_registry import QUESTS
    checks = 0
    for lv in (1, 10, 55, 100, 300, 799, 800):
        c = SimpleNamespace(character_level=lv)
        assert exploration_point_xp_v2103(c) == explorer_award_per_point_v4211(1)['character']
        checks += 1
    s = _MockSession()
    caps = fame_cap_awards_v2103(s)
    assert all(caps[k] == 248500 for k in ('character','soul','stat','class_total'))
    checks += 4
    ensure_schema(s.server.db.conn)
    s.server.db.conn.execute('''INSERT INTO fame_pending_v1703
        (account_id,region,boss_id,boss_name,reward_xp,due_at)
        VALUES(?,?,?,?,?,?)''', (32, 'Test', 'test_boss', 'Boss testowy', 100, time.time()-10))
    s.server.db.conn.commit()
    assert asyncio.run(pay_due_fame(s)) == 1
    assert {n:x for n,x,_ in s.received} == {
        'character':caps['character'], 'soul':caps['soul'],
        'stat':caps['stat'], 'class':caps['class_total']}
    checks += 2
    assert asyncio.run(pay_due_fame(s)) == 0
    assert len(s.received) == 4
    assert s.server.db.conn.execute('SELECT delivered FROM fame_pending_v1703 WHERE account_id=32').fetchone()[0] == 1
    checks += 3
    # Explicit manual/item-only quests must not be rewritten into money quests.
    cases = [
        ({'generator_level':8, 'reward_gold':7}, 700),
        ({'generator_level':8, 'reward_mithril':1}, 100_000_000),
        ({'generator_level':8, 'reward_silver':0}, 100),
        ({'generator_level':8, 'manual_currency_reward_coins':0}, 0),
        ({'generator_level':8, 'currency_reward_mode':'manual', 'reward_silver':20}, 20),
        ({'generator_level':8, 'reward_silver':11,'reward_gold':1}, 111),
    ]
    for quest, expected in cases:
        assert v0190_quest_currency_reward(quest) == expected, (quest, expected)
        checks += 1
    auto = manual = zero = 0
    for qid,quest in QUESTS.items():
        assert isinstance(quest,dict), qid
        currency = v0190_quest_currency_reward(quest)
        assert isinstance(currency, int) and currency >= 0, (qid,currency)
        manual_quest = ('manual_currency_reward_coins' in quest or
                        quest.get('currency_reward_mode') == 'manual')
        if manual_quest:
            manual += 1
            if quest.get('manual_currency_reward_coins') is not None:
                assert currency == max(0,int(quest['manual_currency_reward_coins'])), qid
        else:
            assert currency >= 100, (qid,currency)
            # Static authored reward/preview must likewise be in normal silver.
            if quest.get('generator_level') is not None:
                declared = legacy_currency_to_coins(quest.get('reward_silver',0),
                            quest.get('reward_gold',0),quest.get('reward_mithril',0))
                assert currency >= declared, qid
                if declared == 0:
                    zero += 1
            auto += 1
        checks += 1
    return {'checks': checks, 'quests':len(QUESTS), 'auto_quests':auto,
            'manual_quests':manual, 'zero_static_but_auto_pays':zero}


if __name__ == '__main__':
    import os, tempfile
    with tempfile.TemporaryDirectory(prefix='sb2103-') as tmp:
        os.environ['SOULBOUND_DB'] = tmp + '/test.sqlite'
        os.environ['SOULBOUND_HOST'] = '127.0.0.1'
        import server
    print('FAME EP QUEST GOLD v2.10.3:', run_regression(), 'PASS')
