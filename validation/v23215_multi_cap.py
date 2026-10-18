# -*- coding: utf-8 -*-
"""SQLite-only regression for global Multi Cap and 14-class mastery persistence."""
import sqlite3
from types import SimpleNamespace

from config.balance import MULTICLASS_MAX_ACTIVE
from systems.multi_cap_v23215 import multi_cap_breakdown_v23215, multi_cap_experience_v23215
from systems.experience_bank_v2011 import banked_experience_v2011
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
from storage.db_progression import DatabaseProgressionMixin
from systems.milestone_cap_rewards_v2103 import fame_cap_awards_v2103, exploration_point_xp_v2103
from systems.experience_cap_v2009 import experience_cap_v2009


class TestDB(DatabaseProgressionMixin, DatabaseExperienceBankV2011Mixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE accounts (id INTEGER PRIMARY KEY);
            INSERT INTO accounts VALUES(1),(2);
            CREATE TABLE characters (
                account_id INTEGER PRIMARY KEY,
                character_level INTEGER, soul_level INTEGER, soul_tier INTEGER,
                soul_weapon_mastery_level INTEGER,
                strength INTEGER, dexterity INTEGER, constitution INTEGER,
                intelligence INTEGER, willpower INTEGER, charisma INTEGER);
            INSERT INTO characters VALUES (1,1,1,1,1,1,1,1,1,1,1);
            CREATE TABLE class_progress (account_id INTEGER,class_name TEXT,
                level INTEGER NOT NULL DEFAULT 1,xp INTEGER NOT NULL DEFAULT 0,
                active_slot INTEGER, PRIMARY KEY(account_id,class_name));
            CREATE TABLE professions (account_id INTEGER,profession TEXT,
                level INTEGER,PRIMARY KEY(account_id,profession));
            CREATE TABLE tools (account_id INTEGER,tool_type TEXT,
                level INTEGER,PRIMARY KEY(account_id,tool_type));
            CREATE TABLE learned_skills (account_id INTEGER,skill_id TEXT,
                PRIMARY KEY(account_id,skill_id));
            CREATE TABLE skill_progress (account_id INTEGER,skill_id TEXT,
                level INTEGER,PRIMARY KEY(account_id,skill_id));
            CREATE TABLE ascension_progress_v021 (account_id INTEGER,track TEXT,
                rank INTEGER,PRIMARY KEY(account_id,track));
        ''')
        self.create_experience_bank_schema_v2011()


def run_regression():
    checks = 0
    db = TestDB()
    assert MULTICLASS_MAX_ACTIVE == 1
    checks += 1
    # 4 core tracks + 6 stats + 1 primary-class fallback = 11.
    assert multi_cap_experience_v23215(db.conn, 1) == 5500
    assert multi_cap_experience_v23215(db.conn, 2) is None
    checks += 2
    classes = ['Test'+str(n) for n in range(14)]
    db.ensure_primary_class(1, classes[0])
    base = multi_cap_experience_v23215(db.conn, 1)
    assert base == 5500
    checks += 1
    # Old unlocked secondary classes and previously active slots are archived.
    for i, name in enumerate(classes[1:], start=2):
        db.ensure_class_progress(1, name)
        db.conn.execute('UPDATE class_progress SET active_slot=?,level=75 '
                        'WHERE account_id=1 AND class_name=?', (i,name))
        checks += 1
    assert len(db.active_class_rows(1, classes[0])) == 1
    assert db.active_class_names(1, classes[0]) == classes[:1]
    assert not db.activate_secondary_class(1, classes[0], 'TestExtra')[0]
    checks += 3
    assert multi_cap_experience_v23215(db.conn, 1) == base
    checks += 1
    # Archived class levels have NO impact on the new cap.
    db.conn.execute('UPDATE class_progress SET level=200 WHERE account_id=1 AND class_name=?', (classes[10],))
    assert multi_cap_experience_v23215(db.conn, 1) == base
    checks += 1
    db.conn.execute('UPDATE class_progress SET level=2 WHERE account_id=1 AND class_name=?', (classes[0],))
    assert multi_cap_experience_v23215(db.conn, 1) == base + 500
    assert not db.deactivate_secondary_class(1, classes[0], classes[0])[0]
    checks += 2
    db.conn.executescript('''
        INSERT INTO professions VALUES(1,'mining',3);
        INSERT INTO tools VALUES(1,'pickaxe',4);
        INSERT INTO learned_skills VALUES(1,'fireball');
        INSERT INTO skill_progress VALUES(1,'fireball',5);
        INSERT INTO skill_progress VALUES(1,'unlearned_cheat',1000000);
        INSERT INTO ascension_progress_v021 VALUES(1,'class:Test0',7);
    ''')
    bonus = (3 + 4 + 5 + 7) * 500
    assert multi_cap_experience_v23215(db.conn, 1) == base + 500 + bonus
    checks += 1
    # A skill without a learned_skills row must never add fictional cap.
    _, parts = multi_cap_breakdown_v23215(db.conn, 1)
    assert parts['skille'] == 5 and parts['profesje'] == 3 and parts['narzędzia'] == 4
    checks += 1
    cap = multi_cap_experience_v23215(db.conn, 1)
    assert banked_experience_v2011(db, 1, cap * 4, 'profession', 3, source_key='mining') == cap
    assert banked_experience_v2011(db, 1, cap * 4, 'class', 2, source_key=classes[0]) == cap
    assert banked_experience_v2011(db, 1, cap * 4, 'character', 1) == cap
    assert banked_experience_v2011(db, 1, cap * 4, 'stat', 1, source_key='strength') == cap
    assert banked_experience_v2011(db, 1, cap * 4, 'soul', 1, overcap=True) == cap * 2
    checks += 5
    # Real rewards are separate ledgers; bank repayment cannot exceed shared cap.
    assert banked_experience_v2011(db, 1, 1, 'class', 2, source_key=classes[0]) == 2
    assert banked_experience_v2011(db, 1, 1, 'tool', 4, source_key='pickaxe') == 1
    checks += 2
    db.conn.execute("UPDATE tools SET level=5 WHERE account_id=1 AND tool_type='pickaxe'")
    new_cap = multi_cap_experience_v23215(db.conn, 1)
    assert new_cap == cap + 500
    assert banked_experience_v2011(db, 1, 1, 'class', 2, source_key=classes[0]) == 2
    checks += 2
    # v11: each new Fame is exactly the live Multi Cap; existing EP helper is historical.
    ses = SimpleNamespace(account_id=1,
        character=SimpleNamespace(character_level=1, soul_level=1),
        server=SimpleNamespace(db=db),
        active_class_names=lambda: db.active_class_names(1, classes[0]),
        class_mastery_level=lambda name: int(db.class_progress_row(1, name)["level"]))
    fame = fame_cap_awards_v2103(ses)
    assert fame == dict.fromkeys(('character','soul','stat','class_total'), new_cap)
    assert exploration_point_xp_v2103(ses.character) == 120
    checks += 2
    assert db.active_class_names(1, classes[0])[0] == classes[0]
    checks += 1
    db.conn.close()
    return checks


if __name__ == '__main__':
    print('MULTI CAP v2.32.15:', run_regression(), 'checks PASS')
