# -*- coding: utf-8 -*-
"""v116.00.48: preserve NPC quest-accept naming without whole-world scans."""
from __future__ import annotations
import ast
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'player/session_mixins/quest_offers.py'


def candidate_class(npcs, quests):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    mixin = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SessionQuestOffersMixin')
    original = next(node for node in mixin.body if isinstance(node, ast.FunctionDef) and node.name == 'quest_accept_npc_name_v099')
    klass = ast.ClassDef(name='Candidate', bases=[], keywords=[], body=[original], decorator_list=[], type_params=[])
    module = ast.fix_missing_locations(ast.Module(body=[klass], type_ignores=[]))
    env = {'NPCS': npcs, 'QUESTS': quests}
    exec(compile(module, str(SOURCE), 'exec'), env)
    return env['Candidate']


def baseline(s, npcs, quests, qid, preferred=None):
    if preferred in npcs:
        npc = npcs[preferred]
        if npc.get('room') == s.character.room_id and qid in s.quest_ids_for_npc(preferred, npc):
            return npc.get('name', quests.get(qid, {}).get('giver', 'NPC'))
    quest = quests.get(qid, {})
    giver_norm = s.normalize_description_query(quest.get('giver', ''))
    ordered = list(npcs.items())
    ordered.sort(key=lambda pair: pair[1].get('room') != s.character.room_id)
    for npc_id, npc in ordered:
        if qid not in s.quest_ids_for_npc(npc_id, npc):
            continue
        if giver_norm:
            npc_norm = s.normalize_description_query(npc.get('name', ''))
            if npc_norm == giver_norm:
                return npc.get('name', quest.get('giver', 'NPC'))
        if npc.get('room') == s.character.room_id:
            return npc.get('name', quest.get('giver', 'NPC'))
    return str(quest.get('giver') or 'NPC')


class FakeCharacter:
    room_id = 'room-local'


class Harness:
    def __init__(self, cls, npcs, quests):
        self.character = FakeCharacter()
        self.calls = 0
        self.npcs = npcs
        self.quests = quests
        self.method = cls.quest_accept_npc_name_v099.__get__(self)
    def normalize_description_query(self, text):
        return str(text or '').strip().casefold()
    def quest_ids_for_npc(self, npc_id, npc):
        self.calls += 1
        return tuple(npc.get('offers', ()))


def run():
    checks = 0
    quests = {'quest-target': {'giver': 'Mistrz Cienia'}}
    fixture = [
        {'far-a': {'room': 'north', 'name': 'Mistrz Cienia', 'offers': ['quest-target']}},
        {'near-a': {'room': 'room-local', 'name': 'Sasiad', 'offers': ['quest-target']},
         'far-a': {'room': 'north', 'name': 'Mistrz Cienia', 'offers': ['quest-target']}},
        {'near-a': {'room': 'room-local', 'name': 'Sasiad', 'offers': []},
         'near-b': {'room': 'room-local', 'name': 'Mistrz Cienia', 'offers': ['quest-target']}},
        {'near-a': {'room': 'room-local', 'name': 'Mistrz Cienia', 'offers': ['quest-target']},
         'near-b': {'room': 'room-local', 'name': 'Inny', 'offers': ['quest-target']}},
        {'far-a': {'room': 'west', 'name': 'Inny', 'offers': ['quest-target']}},
        {'near-a': {'room': 'room-local', 'name': 'Inny', 'offers': ['other']}},
        {},
    ]
    rng = random.Random(11648)
    for _ in range(30):
        names = ['Mistrz Cienia', 'Mistrz Cienia', 'Inny', 'Inny', 'Handlarz']
        n = {
            f'npc-{i}': {
                'room': rng.choice(['room-local', 'north', 'south']) if i % 37 == 0 else 'north',
                'name': rng.choice(names),
                'offers': ['quest-target'] if rng.randrange(7) == 0 else [],
            }
            for i in range(250)
        }
        fixture.append(n)
    for npcs in fixture:
        cls = candidate_class(npcs, quests)
        for preferred in (None, 'far-a', 'near-a', 'near-b', 'npc-0'):
            a = Harness(cls, npcs, quests)
            b = Harness(cls, npcs, quests)
            actual = a.method('quest-target', preferred)
            expected = baseline(b, npcs, quests, 'quest-target', preferred)
            assert actual == expected, (actual, expected, preferred)
            checks += 1
    # Explicit performance assertion: an irrelevant world of 10,000 NPCs
    # must NEVER cause 10,000 expensive quest-offer/SQLite checks.
    npcs = {
        f'far-{i}': {'room': 'far-world', 'name': f'NPC {i}', 'offers': []}
        for i in range(10000)
    }
    npcs['target'] = {'room': 'far-world', 'name': 'Mistrz Cienia', 'offers': ['quest-target']}
    cls = candidate_class(npcs, quests)
    s = Harness(cls, npcs, quests)
    assert s.method('quest-target') == 'Mistrz Cienia'
    assert s.calls == 1, f'expensive offer lookups: {s.calls}'
    checks += 2
    # If no global NPC matches, do not issue even one expensive query.
    npcs['target']['name'] = 'Obcy'
    s = Harness(cls, npcs, quests)
    assert s.method('quest-target') == 'Mistrz Cienia'
    assert s.calls == 0, f'expensive offer lookups: {s.calls}'
    checks += 2
    print(f'QUEST ACCEPT NPC FAST LOOKUP v116.00.48: {checks} comparisons/checks PASS', flush=True)
    return checks

if __name__ == '__main__':
    run()
