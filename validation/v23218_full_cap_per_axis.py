# -*- coding: utf-8 -*-
"""Real grant_class_xp + XP bank per-track regression; no production database."""
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace
from systems.multi_cap_v23215 import multi_cap_experience_v23215
from systems.experience_bank_v2011 import banked_experience_v2011
from systems.milestone_cap_rewards_v2103 import fame_cap_awards_v2103
from systems.experience_cap_v2009 import experience_cap_v2009
from validation.v23215_multi_cap import TestDB


def run_regression():
    checks = 0
    db = TestDB()
    classes = ['K'+str(i) for i in range(14)]
    db.ensure_primary_class(1, classes[0])
    for name in classes[1:]:
        assert not db.activate_secondary_class(1, classes[0], name)[0]
        checks += 1
    multi_cap = multi_cap_experience_v23215(db.conn, 1)
    assert multi_cap == 5500  # four core + six stats + ONE primary class
    checks += 1

    issued = []
    db.add_class_mastery_xp = lambda _account, name, amount, **kwargs: (
        issued.append((name,amount)) or
        {'level': 1, 'level_ups': 0, 'gain': amount, 'xp': amount,
         'next_xp': 50000, 'overflow_xp': 0})

    # Extract and run the actual coroutine without importing live world content.
    source = Path(__file__).resolve().parents[1]/'player/session_mixins/class_progression.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'SessionClassProgressionMixin')
    method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == 'grant_class_xp')
    scope = {'CLASS_MASTERY_MAX_LEVEL': 600}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 str(source), 'exec'), scope)

    class Fake:
        grant_class_xp = scope['grant_class_xp']
        account_id = 1
        def __init__(self):
            self.server = SimpleNamespace(db=db)
            self.messages = []
            self.events = []
            self.character = SimpleNamespace(character_level=1, soul_level=1, class_name=classes[0])
        def active_class_names(self): return list(classes[:1])
        def class_mastery_level(self, name): return 1
        def scale_progression_xp_v11342(self, amount, level, **kwargs): return amount
        def apply_double_xp(self, amount): return amount
        def guild_bonus_percent_v0926(self): return 0
        def mentor_bonus_percent_v03050(self): return 0
        def session_summary_add(self, kind, amount): self.events.append((kind,amount))
        async def send(self, msg): self.messages.append(msg)

    session = Fake()
    # A kill gives full XP only to the primary class.
    asyncio.run(session.grant_class_xp(75, content_level=1, content_scaled=True))
    assert issued == [(classes[0],75)], issued
    assert session.events[-1] == ('class_xp',75)
    assert 'tylko do klasy głównej' in session.messages[0]
    checks += 4

    # Huge XP source is capped once for the only class and banked normally.
    issued.clear()
    asyncio.run(session.grant_class_xp(1_000_000, content_level=1, content_scaled=True))
    assert issued == [(classes[0],multi_cap)], issued
    banks = {(kind,key):bal for kind,key,bal in db.experience_bank_rows_v2011(1)}
    assert len(banks) == 1
    assert banks[('class',classes[0])] == 1_000_000-multi_cap
    checks += 3

    # Different stats/professions are NOT charged against class awards.
    assert banked_experience_v2011(db, 1, 26_000, 'stat', 1, source_key='strength') == multi_cap
    assert banked_experience_v2011(db, 1, 26_000, 'stat', 1, source_key='dexterity') == multi_cap
    assert banked_experience_v2011(db, 1, 26_000, 'profession', 1, source_key='mining') == multi_cap
    assert banked_experience_v2011(db, 1, 26_000, 'tool', 1, source_key='pickaxe') == multi_cap
    checks += 4

    # Fame old 14x multiplier MUST NOT remain after class-split removal.
    fame = fame_cap_awards_v2103(session)
    assert fame['class_total'] == multi_cap
    checks += 1
    db.conn.close()
    return checks


if __name__ == '__main__':
    print('FULL MULTI CAP PER AXIS v2.32.18:', run_regression(), 'checks PASS')
