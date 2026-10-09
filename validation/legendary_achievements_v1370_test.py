# -*- coding: utf-8 -*-
"""Legacy-safe v1.37.0 achievement regression suite."""
import sqlite3
from types import SimpleNamespace
from systems.legendary_achievements_v1370 import CATALOG_V1370, sync_v1370, snapshot_v1370


def run_legendary_achievement_regression_v1370():
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.executescript('''
    CREATE TABLE characters(account_id INTEGER PRIMARY KEY,character_level INTEGER,soul_level INTEGER,soul_weapon_mastery_level INTEGER);
    CREATE TABLE professions(account_id INTEGER,profession TEXT,level INTEGER);
    CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER);
    CREATE TABLE lifetime_statistics(account_id INTEGER,stat_key TEXT,value INTEGER);
    CREATE TABLE achievements(account_id INTEGER,achievement_id TEXT,name TEXT,tier TEXT,unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,achievement_id));
    CREATE TABLE unlocked_titles(account_id INTEGER,title_id TEXT,title_name TEXT,PRIMARY KEY(account_id,title_id));
    ''')
    db = SimpleNamespace(conn=con)
    def check(condition, message):
        if not condition:
            raise AssertionError(message)
    check(len(CATALOG_V1370) == 492, 'catalog must have 492 real challenges')
    check(len({a.identifier for a in CATALOG_V1370}) == 492, 'IDs must be stable and unique')
    check(sum(bool(a.reward_title) for a in CATALOG_V1370) == 102, 'title tiers')
    check(sync_v1370(db, 404) == 0, 'missing player must not get rewards')
    con.execute('INSERT INTO characters VALUES(1,300,200,150)')
    con.execute('INSERT INTO professions VALUES(1,?,?)', ('Wędkarstwo',500))
    con.execute('INSERT INTO class_progress VALUES(1,?,?)', ('Mag',300))
    con.execute('INSERT INTO lifetime_statistics VALUES(1,?,?)', ('boss_kills',50))
    first = sync_v1370(db, 1)
    check(first > 0, 'old character should retroactively unlock achievements')
    old_count = con.execute('SELECT COUNT(*) FROM achievements').fetchone()[0]
    old_titles = con.execute('SELECT COUNT(*) FROM unlocked_titles').fetchone()[0]
    check(old_titles > 0, 'important thresholds must grant usable permanent titles')
    check(sync_v1370(db, 1) == 0, 'idempotent resync')
    check(con.execute('SELECT COUNT(*) FROM achievements').fetchone()[0] == old_count, 'no duplicate grants')
    check(con.execute('SELECT COUNT(*) FROM unlocked_titles').fetchone()[0] == old_titles, 'no duplicate titles')
    check(('profession','Wędkarstwo') in snapshot_v1370(db,1), 'fishing progress must be read')
    check(con.execute('SELECT 1 FROM achievements WHERE achievement_id=?', ('legend:v1370:profession:Wędkarstwo:800',)).fetchone() is None, 'higher unreachable level should stay locked')
    con.execute('UPDATE professions SET level=800 WHERE account_id=1')
    con.execute('UPDATE characters SET character_level=800 WHERE account_id=1')
    check(sync_v1370(db,1) > 0, 'new progress must unlock only fresh thresholds')
    check(con.execute('SELECT COUNT(*) FROM achievements').fetchone()[0] > old_count, 'new level earned')
    con.execute('INSERT INTO characters VALUES(2,20,10,10)')
    check(sync_v1370(db,2)>0, 'second account isolated')
    check(con.execute('SELECT COUNT(*) FROM achievements WHERE account_id=1').fetchone()[0] > con.execute('SELECT COUNT(*) FROM achievements WHERE account_id=2').fetchone()[0], 'character progress isolation')
    check(con.execute('SELECT COUNT(*) FROM achievements WHERE account_id=1 AND achievement_id LIKE ?', ('legend:v1370:%',)).fetchone()[0] > 0, 'stable namespace')
    con.close()
    return {'passed': 12, 'catalog':len(CATALOG_V1370),'titles':102}


if __name__ == '__main__':
    print('LEGENDARNE OSIĄGNIĘCIA v1.37.0:', run_legendary_achievement_regression_v1370())
