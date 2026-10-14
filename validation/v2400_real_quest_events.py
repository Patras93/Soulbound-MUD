# -*- coding: utf-8 -*-
"""Test REAL quest-progress event methods for each applicable quest definition.

No progress is synthesized with set_quest_progress. A PASS means a genuine
DatabaseQuestMixin event method advanced a quest on an isolated in-memory DB.
NPC dialogues, combat physics, travel and reward payout are NOT exercised here.
"""
from __future__ import annotations
from collections import Counter
import asyncio
from types import SimpleNamespace
import sqlite3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storage.db_quests import DatabaseQuestMixin


class QuestEventDB(DatabaseQuestMixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE quests (
              account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
              completed_at INTEGER NOT NULL DEFAULT 0,
              completion_count INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY(account_id,quest_id));
            CREATE TABLE quest_resource_progress_v0929 (
              account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
              target_id TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY(account_id,quest_id,target_id));
        ''')
    def close(self):
        self.conn.close()


def event_for(db, aid, q):
    """Return (event outputs, expected progress, fully exercised) or None.

    Avoid fake rewards, arbitrary NPC state or changing authored quest data.
    """
    kind = str(q.get('kind', ''))
    needed = max(1, int(q.get('needed', 1) or 1))
    target = q.get('target')
    if kind == 'kill' and target is not None:
        # A real monster death event adds ONE kill, never more.
        result = db.increment_quest(aid, target)
        return result, 1, needed == 1
    if kind == 'collect' and target is not None:
        if q.get('track_craft_progress'):
            result = db.increment_craft_quest(aid, target, needed)
        else:
            result = db.increment_item_collect_quest(aid, target, needed)
        return result, needed, True
    if kind == 'collect_category' and target is not None:
        # This legacy Session mixin requires native runtime symbol injection.
        # In the independent fast contract it is not safe to load alone.
        if 'player.session_mixins.quest_progress' not in sys.modules:
            return None
        from player.session_mixins.quest_progress import SessionQuestProgressMixin
        # Real Session event handler, not a manual UPDATE against the quest row.
        class _CategorySession(SessionQuestProgressMixin):
            def __init__(self):
                self.server = SimpleNamespace(db=db)
                self.account_id = aid
                self.events = []
            async def announce_active_quest_progress(self, qid):
                self.events.append(qid)
        session = _CategorySession()
        asyncio.run(session.announce_collect_category_quest_progress(target, needed))
        return session.events, needed, True
    if kind == 'collect_resource' and target is not None and q.get('track_resource_progress'):
        result = db.increment_resource_quest(aid, target, needed)
        return result, needed, True
    if kind == 'profession_action':
        profession = q.get('target') or q.get('required_profession')
        if profession:
            result = db.increment_profession_action_quests_v0700(
                aid, profession, q.get('specialist_tool_type') or '', needed,
                action_code=q.get('required_action_code'),
                tier=int(q.get('min_action_tier') or 1))
            return result, needed, True
    if kind == 'party_contract' and target is not None:
        result = db.increment_party_contract_v11339(aid, target, needed)
        return result, needed, True
    if kind == 'craft_set':
        targets = tuple(q.get('targets') or ())
        if targets:
            result = []
            for item in targets:
                result.extend(db.increment_craft_quest(aid, item, 1))
            return result, (1 << len(targets))-1, True
    if kind == 'collect_resource_set':
        resource_targets = dict(q.get('resource_targets') or {})
        if resource_targets:
            result = []
            for item, count in resource_targets.items():
                result.extend(db.increment_resource_set_quest_v0929(aid, item, int(count)))
            return result, sum(int(n) for n in resource_targets.values()), True
    return None



def wrong_event_for(db, aid, q):
    """Ensure an unrelated event cannot complete somebody else's objective."""
    kind = str(q.get('kind', ''))
    invalid = '__soulbound_test_wrong_target__'
    if kind == 'kill' and q.get('target') != '*':
        db.increment_quest(aid, invalid)
    elif kind == 'collect':
        if q.get('track_craft_progress'):
            db.increment_craft_quest(aid, invalid, 5)
        else:
            db.increment_item_collect_quest(aid, invalid, 5)
    elif kind == 'collect_resource' and q.get('track_resource_progress'):
        db.increment_resource_quest(aid, invalid, 5)
    elif kind == 'profession_action':
        db.increment_profession_action_quests_v0700(aid, invalid, invalid, 5)
    elif kind == 'party_contract':
        db.increment_party_contract_v11339(aid, invalid, 5)
    elif kind == 'craft_set':
        db.increment_craft_quest(aid, invalid, 5)
    elif kind == 'collect_resource_set':
        db.increment_resource_set_quest_v0929(aid, invalid, 5)
    else:
        return False
    return True



def run_acceptance_handlers(definitions):
    """Drive the authentic quest-accept handler, NOT a simulated NPC journey.

    Native runtime must already have injected compatibility symbols in the
    quest_turnin module. A standalone static-contract run reports NOT TESTED.
    """
    module = sys.modules.get('player.session_mixins.quest_turnin')
    if module is None or 'QUESTS' not in vars(module):
        print('HANDLER PRZYJMOWANIA NPC: NOT TESTED (brak pelnego runtime)', flush=True)
        return 0
    mixin = module.SessionQuestTurninMixin
    db = QuestEventDB()
    errors = []
    class _Actor(mixin):
        def __init__(self):
            self.server = SimpleNamespace(db=db)
            self.account_id = 0
            self.replies = []
        async def send(self, message, **kwargs):
            self.replies.append(str(message))
        async def announce_active_quest_progress(self, qid, **kwargs):
            return None
    actor = _Actor()
    async def _replay():
        count = 0
        for index, (qid, quest) in enumerate(sorted(definitions.items())):
            actor.account_id = index + 300000
            actor.replies.clear()
            try:
                await actor.handle_quest_interaction(qid)
                row = db.quest(actor.account_id, qid)
                if row is None or row['status'] != 'active' or not actor.replies:
                    errors.append(f'{qid}: realny handler nie przyjal zadania')
                else:
                    count += 1
            except Exception as exc:
                errors.append(f'{qid}: {type(exc).__name__}: {exc}')
        return count
    try:
        count = asyncio.run(_replay())
        if db.conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            errors.append('Handler przyjmowania: integralnosc SQLite')
    finally:
        db.close()
    print(f'REALNY HANDLER PRZYJMOWANIA: {count}/{len(definitions)} '
          'wykonanych wywolan w pamieci (bez rozmowy NPC przez TCP)', flush=True)
    if errors:
        for msg in errors[:25]:
            print('QUEST ACCEPT FAIL: '+msg, flush=True)
        raise AssertionError(f'Handler przyjmowania questow: {len(errors)} bledow')
    return count


def run_event_coverage(quests=None):
    if quests is None:
        from systems.content_registry import QUESTS
        definitions = QUESTS
    else:
        definitions = quests
    if not definitions:
        raise AssertionError('Brak zarejestrowanych questow')
    checks = 0
    errors = []
    executed = Counter()
    not_tested = Counter()
    fully = Counter()
    db = QuestEventDB()
    try:
        for index, (qid, quest) in enumerate(sorted(definitions.items())):
            if index and index % 250 == 0:
                print(f'QUEST EVENTS: {index}/{len(definitions)} definicji; wykonano {sum(executed.values())}', flush=True)
            kind = str(quest.get('kind') or '?')
            a, b = index + 101, index + 100000
            db.start_quest(a, qid)
            if wrong_event_for(db, a, quest):
                if db.quest(a, qid)['progress'] != 0:
                    errors.append(f'{qid}: obce zdarzenie zwiekszylo postep')
                checks += 1
            outcome = event_for(db, a, quest)
            if outcome is None:
                not_tested[kind] += 1
                continue
            produced, expected, full = outcome
            row = db.quest(a, qid)
            if int(row['progress']) != expected or not produced:
                errors.append(f'{qid} ({kind}): zdarzenie nie zwiekszylo postepu; '
                              f'jest {row["progress"]}, oczekiwano {expected}')
                continue
            executed[kind] += 1
            checks += 1
            if full:
                fully[kind] += 1
            # One player's event must not accept/advance/finish another player's quest.
            if db.quest(b, qid) is not None:
                errors.append(f'{qid}: obcy gracz otrzymal postep')
            checks += 1
            # Another identical batch must be capped at the actual quest goal.
            event_for(db, a, quest)
            repeated = db.quest(a, qid)
            repeated_expected = min(int(quest.get('needed', 1) or 1), 2) if kind == 'kill' else expected
            if int(repeated['progress']) != repeated_expected:
                errors.append(f'{qid}: ponowne zdarzenie przekroczylo limit lub skasowalo postep')
            checks += 1
            # Events after quest completion must not change the saved progress.
            db.complete_quest(a, qid)
            event_for(db, a, quest)
            finished = db.quest(a, qid)
            if finished['status'] != 'completed' or int(finished['progress']) != repeated_expected:
                errors.append(f'{qid}: zdarzenie po oddaniu zmienilo ukończone zadanie')
            checks += 1
            db.restart_quest(a, qid)
            row = db.quest(a, qid)
            if row['status'] != 'active' or int(row['progress']) != 0:
                errors.append(f'{qid}: restart nie wyzerowal postepu')
            checks += 1
            db.abandon_quest(a, qid)
            event_for(db, a, quest)
            if db.quest(a, qid)['status'] != 'abandoned' or db.quest(a, qid)['progress'] != 0:
                errors.append(f'{qid}: zdarzenie zaliczylo porzucone zadanie')
            checks += 1
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        checks += 1
    finally:
        db.close()
    print('TESTY ZDARZEN QUESTOW — PRAWDZIWE METODY POSTEPU SQLITE', flush=True)
    print(f'Zdarzenia rzeczywiste: {sum(executed.values())}/{len(definitions)} questow; '
          f'rodzaje: {dict(sorted(executed.items()))}', flush=True)
    print(f'Pelny cel w zdarzeniach DB: {sum(fully.values())}/{len(definitions)} '
          '(NIE oznacza odbioru nagrody u NPC)', flush=True)
    print(f'NOT TESTED — brak zdarzenia tego typu w tym module: '
          f'{sum(not_tested.values())}; rodzaje: {dict(sorted(not_tested.items()))}', flush=True)
    print(f'NOT TESTED — fabularne przejscie NPC, drop fizyczny, walka TCP, nagrody '
          f'{len(definitions)}/{len(definitions)}', flush=True)
    if errors:
        for item in errors[:35]:
            print('EVENT QUEST FAIL: ' + item, flush=True)
        raise AssertionError(f'{len(errors)} bledow zdarzen questowych')
    accepted = run_acceptance_handlers(definitions)
    checks += accepted
    print(f'QUEST EVENT REAL: {checks} checks PASS; 0 event errors', flush=True)
    return {'checks': checks, 'accepted_via_handler': accepted, 'executed': sum(executed.values()),
            'full_db_goal': sum(fully.values()), 'not_tested': sum(not_tested.values()),
            'errors': errors, 'by_type': dict(executed)}


if __name__ == '__main__':
    import os
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='soulbound-event-audit-') as directory:
        os.environ['SOULBOUND_DB'] = str(Path(directory) / 'events.sqlite')
        os.environ['SOULBOUND_HOST'] = '127.0.0.1'
        import server  # install dynamic quests into the shared live registry
        run_event_coverage()
