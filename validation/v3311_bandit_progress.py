# -*- coding: utf-8 -*-
"""v3.31.1: real kill-family -> SQLite quest progress -> NVDA text contract.

Uses isolated in-memory SQLite, NEVER a real player's account/database.
It does not claim a whole live TCP combat was played.
"""
import asyncio
import sqlite3
from types import SimpleNamespace


def run_regression(runtime):
    from storage.db_quests import DatabaseQuestMixin
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from world.dynamic_content import quest_kill_targets_v0389

    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.row_factory = sqlite3.Row
            self.conn.executescript("""
              CREATE TABLE quests (
                  account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER,
                  completed_at INTEGER DEFAULT 0, completion_count INTEGER DEFAULT 0,
                  PRIMARY KEY(account_id, quest_id));
              CREATE TABLE quest_resource_progress_v0929 (
                  account_id INTEGER, quest_id TEXT, target_id TEXT, progress INTEGER,
                  PRIMARY KEY(account_id, quest_id, target_id));
            """)

    class Session(SessionQuestProgressMixin):
        def __init__(self, db, account_id):
            self.account_id = account_id
            self.server = SimpleNamespace(db=db)
            self.messages = []

        async def send(self, message, *, combat_detail=None, history_category=None, **_kw):
            self.messages.append((str(message), combat_detail, history_category))

    assert runtime.QUESTS['bandit_patrol']['target'] == 'bandit'
    assert runtime.QUESTS['elia_hourly_bandits']['target'] == 'bandit'
    assert runtime.QUESTS['hourly_bandits']['target'] == 'bandit'
    qids = ('bandit_patrol', 'elia_hourly_bandits', 'hourly_bandits')
    regulars = (
        'bandit', 'bandit_marauder', 'bandit_scout', 'bandit_crossbowman',
        'bandit_cutthroat', 'bandit_raider', 'bandit_alchemist',
        'bandit_enforcer', 'bandit_veteran', 'bandit_captain', 'bandit_chief',
    )
    mini = ('bandit_quartermaster', 'bandit_duelist')
    checks = 0
    for mob_id in regulars + mini:
        assert mob_id in runtime.MOB_TEMPLATES, f'unknown bandit mob: {mob_id}'
        targets = quest_kill_targets_v0389(mob_id, runtime.MOB_TEMPLATES[mob_id])
        assert 'bandit' in targets, f'{mob_id} does not credit bandit quests: {targets}'
        assert len(set(targets)) == len(targets), f'duplicate kill targets: {mob_id}'
        checks += 2

    # No false credit to another species' miniboss or to neutral mobs.
    for mob_id in ('goblin', 'goblin_bombmaster', 'cemetery_crypt_reaper'):
        assert 'bandit' not in quest_kill_targets_v0389(mob_id, runtime.MOB_TEMPLATES[mob_id]), mob_id
        checks += 1

    db = DB()
    try:
        player = Session(db, 1311)
        separate = Session(db, 1312)
        for qid in qids:
            db.start_quest(player.account_id, qid)
            db.start_quest(separate.account_id, qid)
            checks += 2

        # Reject wrong enemies and keep the other account untouched.
        for target in quest_kill_targets_v0389('goblin', runtime.MOB_TEMPLATES['goblin']):
            assert db.increment_quest(player.account_id, target) == []
            checks += 1

        async def fight():
            for i, mob_id in enumerate(regulars + mini + ('bandit', 'bandit')):
                before = {qid: int(db.quest(player.account_id, qid)['progress']) for qid in qids}
                for target in quest_kill_targets_v0389(mob_id, runtime.MOB_TEMPLATES[mob_id]):
                    for qid, _new_progress in db.increment_quest(player.account_id, target):
                        await player.announce_active_quest_progress(
                            qid, runtime.MOB_TEMPLATES[mob_id]['name'])
                for qid in qids:
                    needed = int(runtime.QUESTS[qid]['needed'])
                    new_value = int(db.quest(player.account_id, qid)['progress'])
                    assert new_value == min(needed, before[qid] + 1), (qid, mob_id, before[qid], new_value)
                    if new_value != before[qid]:
                        assert any(
                            f"Postęp questa: {runtime.QUESTS[qid]['name']}" in text
                            and f"Postęp {new_value} z {needed}" in text
                            and detail == 'essential' and category == 'quest'
                            for text, detail, category in player.messages
                        ), f'no essential quest progress message: {qid} / {mob_id}'
                    assert int(db.quest(separate.account_id, qid)['progress']) == 0
                yield i
        async def run_fight():
            async for _ in fight():
                pass
        asyncio.run(run_fight())
        checks += (len(regulars)+len(mini)+2) * (len(qids)*3)
        assert any('GOTOWE DO ODDANIA' in line[0] for line in player.messages)
        checks += 1
        old_len=len(player.messages)
        # A finished but not yet turned-in quest must not spam after further kills.
        for target in quest_kill_targets_v0389('bandit', runtime.MOB_TEMPLATES['bandit']):
            for qid,_ in db.increment_quest(player.account_id, target):
                asyncio.run(player.announce_active_quest_progress(qid,'Bandyta'))
        assert len(player.messages)==old_len
        checks += 1
    finally:
        db.conn.close()
    return checks


if __name__ == '__main__':
    import server
    print('BANDIT QUEST PROGRESS v3.31.1:', run_regression(server), 'checks PASS')
