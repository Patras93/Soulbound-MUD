# -*- coding: utf-8 -*-
"""v102.00.10: runtime regression of slow quest acceptance telemetry without real player DB."""
import ast
import asyncio
from contextlib import redirect_stdout
import io
from pathlib import Path
from types import SimpleNamespace


def run():
    root = Path(__file__).resolve().parents[1]
    path = root / 'player/session_mixins/quest_offers.py'
    src = path.read_text(encoding='utf-8')
    module = ast.parse(src, filename=str(path))
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'SessionQuestOffersMixin')
    accept = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'accept_quest_id')
    offer = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'quest_offer_state')
    checks = 0

    def ck(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1

    assignments = {n.targets[0].id: n.lineno for n in ast.walk(accept) if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    for name in ('_accept_start_v102009', '_accept_db_v102009', '_accept_requirements_v102009', '_accept_persisted_v102009'):
        ck(name in assignments, f'{name} assigned in accept_quest_id')
    ck(assignments['_accept_start_v102009'] < assignments['_accept_db_v102009']
       < assignments['_accept_requirements_v102009'] < assignments['_accept_persisted_v102009'],
       'measurements ordered in the correct function')
    offer_names = {n.id for n in ast.walk(offer) if isinstance(n, ast.Name)}
    ck('_accept_db_v102009' not in offer_names and '_accept_requirements_v102009' not in offer_names,
       'no mislocated profiling variables in offer-state')
    ck('self.server.db.start_quest(self.account_id, quest_id)' in src,
       'normal persistence still exists')
    ck('self.server.db.restart_quest(self.account_id, quest_id)' in src,
       'repeat persistence still exists')

    # Compile actual production accept_quest_id, not a rewritten copy, using fake SQLite/session.
    subset = ast.ClassDef(name='ExtractedQuestAccept', bases=[], keywords=[],
                          body=[accept], decorator_list=[])
    isolated = ast.fix_missing_locations(ast.Module(body=[subset], type_ignores=[]))

    class Clock:
        def __init__(self, step):
            self.value = 0.0
            self.step = step
        def perf_counter(self):
            current = self.value
            self.value += self.step
            return current

    quest = {'name': 'Testowy quest', 'needed': 1, 'description': 'Znajdz przedmiot.',
             'repeatable': True, 'accept_items': {}}
    globals_ = {'time': Clock(0.1), 'QUESTS': {'example': quest},
                'QUEST_REPEAT_COOLDOWN_SECONDS': 60, 'ITEMS': {}}
    exec(compile(isolated, str(path), 'exec'), globals_)
    Mixin = globals_['ExtractedQuestAccept']

    class Db:
        def __init__(self, initial=None):
            self.row = initial
            self.actions = []
        def quest(self, account_id, quest_id):
            return self.row
        def start_quest(self, account_id, quest_id):
            self.actions.append('start')
            self.row = {'status': 'active'}
        def restart_quest(self, account_id, quest_id):
            self.actions.append('restart')
            self.row = {'status': 'active'}
        def repeat_quest_seconds_remaining(self, *args):
            return 0

    class Player(Mixin):
        def __init__(self, initial=None):
            self.db = Db(initial)
            self.server = SimpleNamespace(db=self.db, party_key_for_account=lambda *_: None)
            self.account_id = 1
            self.character = SimpleNamespace(name='Test', room_id='test-room')
            self.combat_mob_key = None
            self.messages = []
            self.locked = False
        async def send(self, message):
            self.messages.append(message)
        def quest_lock_reasons(self, quest_id):
            return ['prerequisite'] if self.locked else []
        def quest_accept_npc_name_v099(self, quest_id, npc_id):
            return 'Questgiver'
        def quest_accept_reaction_v099(self, quest, npc, repeated=False):
            return 'Oto twoje zadanie.'
        async def announce_active_quest_progress(self, quest_id):
            self.messages.append('Postep')
        def quest_progress_for_turnin(self, quest_id):
            return 0, False

    async def exercise(initial, step, in_combat=False, locked=False, name='example'):
        player = Player(initial)
        player.combat_mob_key = 'mob' if in_combat else None
        player.locked = locked
        globals_['time'] = Clock(step)
        stream = io.StringIO()
        with redirect_stdout(stream):
            result = await player.accept_quest_id(name, npc_id='npc')
        return player, result, stream.getvalue()

    p, result, output = asyncio.run(exercise(None, 0.1))
    ck(result is True, 'slow quest acceptance returns successfully')
    ck(p.db.actions == ['start'], 'slow acceptance persisted exactly once')
    ck('[PERF QUESTACCEPT]' in output, 'slow branch executed logging')
    ck('precheck_ms=100' in output and 'requirements_ms=100' in output and 'write_reply_ms=100' in output,
       'three distinct stage durations calculated')
    ck(any('Quest przyjęty' in x for x in p.messages), 'success message delivered')
    p, result, output = asyncio.run(exercise(None, 0.01))
    ck(result is True and p.db.actions == ['start'], 'fast acceptance unchanged')
    ck('PERF QUESTACCEPT' not in output, 'fast branch does not log')
    p, result, output = asyncio.run(exercise({'status': 'completed'}, 0.1))
    ck(result is True and p.db.actions == ['restart'], 'slow repeat acceptance persisted')
    ck('PERF QUESTACCEPT' in output, 'repeat slow path safely logged')
    p, result, output = asyncio.run(exercise({'status': 'active'}, 0.1))
    ck(result is False and not p.db.actions, 'already active quest not restarted')
    p, result, output = asyncio.run(exercise(None, 0.1, locked=True))
    ck(result is False and not p.db.actions, 'locked quest not accepted')
    p, result, output = asyncio.run(exercise(None, 0.1, in_combat=True))
    ck(result is False and not p.db.actions, 'in-combat quest not accepted')
    p, result, output = asyncio.run(exercise(None, 0.1, name='missing'))
    ck(result is False and not p.db.actions, 'unknown quest not accepted')
    return checks


if __name__ == '__main__':
    print(f'QUEST ACCEPT HOTFIX v102.00.10: {run()} checks PASS', flush=True)
