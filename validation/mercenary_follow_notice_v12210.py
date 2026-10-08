# -*- coding: utf-8 -*-
"""Small real-code regression test for readable follower notifications."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_taverns import MERCENARIES, mercenary_follow_notice_v12210


def validate_mercenary_follow_notice_v12210():
    checks = 0
    def check(result):
        nonlocal checks
        assert result
        checks += 1

    check(mercenary_follow_notice_v12210([]) == "")
    check(mercenary_follow_notice_v12210(["Seren"]) == "Seren podąża za tobą.")
    check(mercenary_follow_notice_v12210(["Seren", "Vael"]) == "Najemnicy podążają za tobą: Seren i Vael.")
    check(mercenary_follow_notice_v12210(["Seren", "Vael", "Gareth"]) == "Najemnicy podążają za tobą: Seren, Vael i Gareth.")
    root = Path(__file__).resolve().parents[1]
    perception = (root / "player/session_mixins/perception_maps.py").read_text(encoding="utf-8")
    check("mine = [spec[\"name\"] for owner, _role, spec in followers if owner is self]" in perception)
    check('if others:' in perception and 'Najemnicy innych graczy:' in perception)

    movement = (root / "player/session_mixins/movement.py").read_text(encoding="utf-8")
    tree = ast.parse(movement)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SessionMovementMixin")
    move = next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "walk_room_transition")
    guide = (root / "player/session_mixins/guide_navigation.py").read_text(encoding="utf-8")
    check("self._mercenary_guide_announced_v12210 = False" in guide)
    # Test the actual movement method against a tiny fake room, session and DB.
    class MiniAsyncio:
        create_task = staticmethod(asyncio.create_task)
        gather = staticmethod(asyncio.gather)
        @staticmethod
        async def sleep(_seconds):
            return None

    room_catalog = {
        "start": {"name": "Plac", "exits": {}},
        "middle": {"name": "Most", "exits": {}},
        "end": {"name": "Tawerna", "exits": {}},
    }
    ns = dict(asyncio=MiniAsyncio, sys=__import__('sys'),
              ROOMS=room_catalog, DIRECTION_WALK_LABELS={"north":"na północ"},
              COURIER_CITY_ROOM_TO_NAME_V0530={}, MERCENARIES=MERCENARIES,
              mercenary_follow_notice_v12210=mercenary_follow_notice_v12210)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[move], type_ignores=[])),
                 "player/session_mixins/movement.py", "exec"), ns)

    class Db:
        hires = ["paladyn", "mag", "wojownik"]
        saves = 0
        conn = SimpleNamespace(commit=lambda: None)
        def mercenary_contracts(self, account_id):
            assert account_id == 1
            return [{"role": role} for role in self.hires]
        def save_character(self, char, commit=True):
            self.saves += 1

    db = Db()
    class World:
        def ensure_runtime_room(self, room):
            assert room in room_catalog
    async def broadcast(*_args, **_kwargs):
        return None
    server = SimpleNamespace(db=db, world=World(), broadcast_room=broadcast)
    class Session:
        walk_room_transition = ns["walk_room_transition"]
        def __init__(self):
            self.server = server
            self.account_id = 1
            self.character = SimpleNamespace(name="Gracz", room_id="start")
            self.closed = False
            self.moving = False
            self._party_follow_batch_save_v11123 = False
            self.messages = []
        def party_key(self):
            return None
        async def send(self, text):
            self.messages.append(text)
        async def register_uoss_deep_dungeon_visit_v11331(self, target):
            return None
        def movement_delay(self, *args, **kwargs):
            return 0
        async def look(self):
            names = [MERCENARIES[row["role"]]["name"] for row in db.mercenary_contracts(self.account_id)]
            text = mercenary_follow_notice_v12210(names)
            if text:
                await self.send(text)

    async def simulate():
        session = Session()
        notice = "Najemnicy podążają za tobą: Seren, Vael i Gareth."
        check(await session.walk_room_transition("north", "middle", show_room=True))
        check(session.messages.count(notice) == 1)
        check(db.saves == 1 and session.character.room_id == "middle")
        check(await session.walk_room_transition("north", "end", show_room=True))
        check(session.messages.count(notice) == 2)
        check(await session.walk_room_transition("north", "end", show_room=True))
        check(session.messages.count(notice) == 2)  # No move, no announcement.
        session.character.room_id = "start"
        session.messages.clear()
        session._mercenary_guide_announced_v12210 = False
        check(await session.walk_room_transition("north", "middle", guided=True, show_room=False))
        check(await session.walk_room_transition("north", "end", guided=True, show_room=False))
        check(session.messages.count(notice) == 1)  # NVDA: once per route.
        session._mercenary_guide_announced_v12210 = False
        session.character.room_id = "start"
        check(await session.walk_room_transition("north", "middle", guided=True, show_room=False))
        check(session.messages.count(notice) == 2)  # New guide is a new route.
        db.hires = []
        session.messages.clear()
        session.character.room_id = "start"
        session._mercenary_guide_announced_v12210 = False
        check(await session.walk_room_transition("north", "end", guided=True, show_room=False))
        check(not any("podąża" in msg for msg in session.messages))
        session.closed = True
        check(not await session.walk_room_transition("north", "middle", guided=False))
        check(not any("podąża" in msg for msg in session.messages))
    asyncio.run(simulate())
    return checks


if __name__ == "__main__":
    print("MERCENARY FOLLOW NOTICE v1.22.10:", validate_mercenary_follow_notice_v12210(), "checks PASS")
