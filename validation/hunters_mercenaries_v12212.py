# -*- coding: utf-8 -*-
"""Regression for leader-shared bounties, real kill credit and EQ-backed hires."""
import asyncio
import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from storage.db_inventory import DatabaseInventoryMixin
from systems.mercenary_taverns import mercenary_damage_cap_ratio_v12212, mercenary_owner_power_v1213


def validate_hunters_mercenaries_v12212():
    checks = 0
    def ok(value, message):
        nonlocal checks
        if not value:
            raise AssertionError('v1.22.12: ' + message)
        checks += 1

    for template, ratio in (({}, 1.0), ({'elite': True}, 1.0),
                            ({'rank': 'elite'}, 1.0), ({'world_boss': True}, 1.0),
                            ({'rank': 'world_boss'}, 1.0),
                            ({'uoss_unique_superboss_key': 'black_rabite'}, 1.0)):
        ok(mercenary_damage_cap_ratio_v12212(template) == ratio, 'uncapped damage ' + str(template))
    for physical, magic in ((40000, 1000), (1000, 40000), (40000, 40000)):
        ok(mercenary_owner_power_v1213(physical, magic) == 40000, 'cross-class EQ')

    class Db(DatabaseInventoryMixin):
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.conn.executescript('''
                CREATE TABLE hunter_contracts_v1225(account_id INTEGER, tier TEXT,
                    target_id TEXT, needed INTEGER, progress INTEGER DEFAULT 0,
                    reward_silver INTEGER, state TEXT DEFAULT 'active', ready_after INTEGER DEFAULT 0,
                    PRIMARY KEY(account_id, tier));
                CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY, silver INTEGER DEFAULT 0,
                    gold INTEGER DEFAULT 0, mithril INTEGER DEFAULT 0);
            ''')
        def master_account_for_character(self, account_id):
            return account_id
    db = Db()

    # Compile the real player command: this exercise catches wiring mistakes.
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / 'player/session_mixins/mercenary_taverns.py').read_text('utf8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SessionMercenaryTavernsMixin')
    cmd = next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'handle_hunters_v1225')
    namespace = {'time': __import__('time'), 'currency_price_text': str}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cmd], type_ignores=[])),
                 '<live hunters>', 'exec'), namespace)

    class Session:
        handle_hunters_v1225 = namespace['handle_hunters_v1225']
        def __init__(self, id, room):
            self.account_id = id
            self.character = SimpleNamespace(room_id=room)
            self.messages = []
        async def send(self, text):
            self.messages.append(str(text))

    leader = Session(1, 'soul_hunter_board_v1225')
    member = Session(2, 'soul_hunter_board_v1225')
    elsewhere = Session(3, 'another_room')
    server = SimpleNamespace(db=db, party_key_for_account=lambda id: 1 if id in (1, 2, 3) else None,
        party_sessions=lambda _id, same_room=None: [s for s in (leader, member, elsewhere)
                 if same_room is None or s.character.room_id == same_room])
    for s in (leader, member, elsewhere):
        s.server = server

    async def go():
        nonlocal checks
        for tier, mob, template, need in (
            ('boss', 'goblin_warchief', {'world_boss': True}, 1),
            ('elitarne', 'v028_region_01_elite', {'elite': True}, 4),
            ('zwykle', 'goblin', {'quest_target': 'goblin'}, 6),
        ):
            await leader.handle_hunters_v1225('przyjmij ' + tier)
            for account_id in (1, 2, 3):
                row = db.hunter_state_v1225(account_id, tier)
                ok(row is not None and row['state'] == 'active', tier + ' shared for nearby player')
            ok(db.hunter_state_v1225(3, tier) is not None, tier + ' shared with distant online member')
            wrong = db.hunter_kill_v1225(1, 'training_dummy', {'training_dummy': True})
            ok(not wrong, tier + ' must not credit training dummy')
            for _ in range(need):
                for account_id in (1, 2, 3):
                    recorded = db.hunter_kill_v1225(account_id, mob, template)
                    ok(any(t == tier for t, *_ in recorded), tier + ' credit to eligible member')
            ok(db.hunter_state_v1225(1, tier)['state'] == 'ready', tier + ' ready')
            ok(db.hunter_state_v1225(2, tier)['state'] == 'ready', tier + ' teammate ready')
            ok(db.hunter_state_v1225(3, tier)['state'] == 'ready', tier + ' remote teammate ready')
        # Test alias, award exactly once, and no accidental debit of other member.
        await leader.handle_hunters_v1225('odbierz bos')
        ok(db.hunter_state_v1225(1, 'boss')['state'] == 'cooldown', 'boss alias claims')
        ok(db.hunter_state_v1225(2, 'boss')['state'] == 'ready', 'teammate reward independent')
        ok(db.conn.execute('SELECT silver FROM bank_balances WHERE account_id=1').fetchone()[0] == 2000000,
           'boss reward full amount')
        await member.handle_hunters_v1225('odbierz boss')
        ok(db.hunter_state_v1225(2, 'boss')['state'] == 'cooldown', 'teammate boss reward')
        await leader.handle_hunters_v1225('odbierz bos')
        ok(db.conn.execute('SELECT silver FROM bank_balances WHERE account_id=1').fetchone()[0] == 2000000,
           'reward cannot be paid twice')
        await leader.handle_hunters_v1225('odbierz elitarne')
        await member.handle_hunters_v1225('odbierz elitarne')
        await leader.handle_hunters_v1225('odbierz zwykle')
        await member.handle_hunters_v1225('odbierz zwykle')
        ok(all(db.hunter_state_v1225(1, tier)['state'] == 'cooldown' for tier in ('boss','zwykle','elitarne')),
           'every category can be claimed')
    asyncio.run(go())
    # Existing accepted bounty: defeating any valid boss should count.
    db.hunter_accept_v1225(4, 'boss', 'goblin_warchief', 1, 2000000, 1)
    ok(db.hunter_kill_v1225(4, 'another_boss', {'rank': 'world_boss'}) == [('boss', 1, 1)],
       'older accepted boss bounty credits another real boss')
    db.hunter_accept_v1225(5, 'zwykle', 'goblin', 6, 15000, 1)
    ok(db.hunter_kill_v1225(5, 'goblin_archer', {'quest_target': 'goblin'}) == [('zwykle', 1, 6)],
       'goblin variants credit')
    db.close = db.conn.close
    db.close()
    return checks


if __name__ == '__main__':
    print('HUNTERS MERCENARIES v1.22.12:', validate_hunters_mercenaries_v12212(), 'checks PASS')
