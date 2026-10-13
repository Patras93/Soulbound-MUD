# -*- coding: utf-8 -*-
"""v3.00.7: real catalog + SQLite progress for Boris fishing orders."""
from __future__ import annotations
import sqlite3

import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run_regression_fast():
    checks = 0
    for path in ("systems/boris_fishing_quests_v3007.py", "world/equipment_help.py", "player/session_mixins/quest_progress.py", "admin/audits.py"):
        ast.parse((ROOT / path).read_text(encoding="utf-8"))
        checks += 1
    source = (ROOT / "systems/boris_fishing_quests_v3007.py").read_text(encoding="utf-8")
    for name in ("fish_river", "fish_lake", "fish_sea", "fish_ocean", "collect_resource_set", "collect_distinct_category"):
        assert name.removeprefix("fish_") in source, name
        checks += 1
    help_src = (ROOT / "player/session_mixins/quest_progress.py").read_text(encoding="utf-8")
    for name in ("fish_river", "fish_lake", "fish_sea", "fish_ocean"):
        assert name in help_src, name
        checks += 1
    assert "install_boris_quests_v3007(QUESTS, NPCS, ITEMS)" in (ROOT / "world/equipment_help.py").read_text(encoding="utf-8")
    return checks + 1



def run_regression():
    count = 0
    def check(condition, message):
        nonlocal count
        if not condition:
            raise AssertionError('BORIS FISH v3.00.7: ' + message)
        count += 1

    import server
    from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
    from storage.db_quests import DatabaseQuestMixin
    from systems.boris_fishing_quests_v3007 import BORIS_QUEST_IDS_V3007, BORIS_WATERS_V3007, BORIS_SPECIES_V3007, BORIS_SETS_V3007, BORIS_DISCOVERY_V3007
    QUESTS, NPCS, ITEMS = server.QUESTS, server.NPCS, server.ITEMS
    npc = NPCS['fisher_tomas']
    check(npc['name'] == 'Rybak Borys', 'NPC identity')
    check(npc['room'] == 'fish_market', 'NPC location')
    check(npc['quest'] == 'fisher_30_fish', 'old starter quest')
    check(len(BORIS_QUEST_IDS_V3007) == 48, 'new quest count')
    check(len(set(BORIS_QUEST_IDS_V3007)) == 48, 'unique ids')
    check(len(BORIS_WATERS_V3007) == 4, 'four water habitats')
    check(len(BORIS_SPECIES_V3007) == 32, 'species count')
    check(len(BORIS_SETS_V3007) == 8, 'mixed set count')
    check(len(BORIS_DISCOVERY_V3007) == 4, 'distinct count')
    check(tuple(npc['specialist_quests']) == BORIS_QUEST_IDS_V3007, 'npc offer includes all')
    check(tuple(BORIS_QUEST_IDS_V3007[:4]) == tuple('boris_waters_'+h for h,_,_,_ in BORIS_WATERS_V3007), 'all four offered first')
    check(npc.get('shopkeeper'), 'rod seller preserved')
    for habitat, _, _, _ in BORIS_WATERS_V3007:
        q = QUESTS["boris_waters_" + habitat]
        check(q['target'] == 'fish_' + habitat, 'biome mapping '+habitat)
    for qid in BORIS_QUEST_IDS_V3007:
        q = QUESTS[qid]
        check(q['giver'] == npc['name'], f'{qid}: giver')
        check(q['repeatable'] and q['repeat_cooldown'] == QUEST_REPEAT_COOLDOWN_SECONDS,
              f'{qid}: hourly renewal')
        check(q['event_progress_only'], f'{qid}: only caught after acceptance')
        check(q['reward_profession'] == 'Wędkarstwo' and q['reward_tool_type'] == 'fishing',
              f'{qid}: correct xp axes')
        check(q['reward_profession_xp'] > 0 and q['reward_tool_xp'] > 0 and q['reward_silver'] > 0,
              f'{qid}: meaningful rewards')
        check(q['needed'] > 0, f'{qid}: required amount')
        if q['kind'] == 'collect_category':
            check(q['target'] in ('fish_river','fish_lake','fish_sea','fish_ocean'), f'{qid}: biome')
        elif q['kind'] == 'collect_resource':
            check(q['target'] in ITEMS and q['track_resource_progress'], f'{qid}: real fish item')
        elif q['kind'] == 'collect_resource_set':
            check(sum(q['resource_targets'].values()) == q['needed'], f'{qid}: sum targets')
            check(all(k in ITEMS for k in q['resource_targets']), f'{qid}: mixed items')
        else:
            check(q['kind'] == 'collect_distinct_category' and q['target'] == 'fish',
                  f'{qid}: supported category')
    check(QUESTS['boris_species_eternal_river_dragon']['reward_profession_xp'] >
          QUESTS['boris_species_river_bleak']['reward_profession_xp'],
          'high tier > low tier xp')
    check(QUESTS['boris_set_legendary_four']['reward_profession_xp'] >
          QUESTS['boris_set_river_market']['reward_profession_xp'],
          'hard sets pay more')

    # Real persistence methods, completely isolated SQLite; never live data.
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT,
            progress INTEGER DEFAULT 0, completed_at INTEGER DEFAULT 0,
            completion_count INTEGER DEFAULT 0,
            PRIMARY KEY(account_id,quest_id));
        CREATE TABLE quest_resource_progress_v0929 (
            account_id INTEGER, quest_id TEXT, target_id TEXT, progress INTEGER,
            PRIMARY KEY(account_id,quest_id,target_id));
    """)
    db = DatabaseQuestMixin()
    db.conn = conn
    single = 'boris_species_river_bleak'
    mixed = 'boris_set_river_market'
    distinct = 'boris_discovery_3'
    for qid in (single, mixed, distinct):
        db.start_quest(10, qid)
    db.start_quest(11, single)
    check(db.quest(10, single)['progress'] == 0, 'fresh start at zero')
    check(db.quest(11, single)['progress'] == 0, 'other player isolated')
    updates = db.increment_resource_quest(10, 'river_bleak', 4)
    check([t[0] for t in updates] == [single], 'only target species matches')
    check(db.quest(10, single)['progress'] == 4, 'proper progress 4')
    check(db.quest(11, single)['progress'] == 0, 'other account unchanged')
    check(db.increment_resource_quest(10, 'lake_smelt', 3) == [], 'different fish not credited')
    db.increment_resource_quest(10, 'river_bleak', 99)
    check(db.quest(10, single)['progress'] == QUESTS[single]['needed'], 'progress capped')
    check(db.increment_resource_quest(10, 'river_bleak', 1) == [], 'no repeat after completion')
    changes = db.increment_resource_set_quest_v0929(10, 'stone_loach', 4)
    check(len(changes) == 1 and changes[0][0] == mixed, 'mixed first species tracked')
    changes = db.increment_resource_set_quest_v0929(10, 'river_bleak', 5)
    check(len(changes) == 1 and changes[0][1] == QUESTS[mixed]['needed'],
          'mixed set completes after two species')
    check(db.increment_resource_set_quest_v0929(11, 'river_bleak', 9) == [],
          'other player has no mixed quest')
    n, added = db.mark_distinct_category_item_v023(10, distinct, 'river_bleak', 3)
    check(n == 1 and added, 'first distinct species')
    n, added = db.mark_distinct_category_item_v023(10, distinct, 'river_bleak', 3)
    check(n == 1 and not added, 'duplicate species ignored')
    for species in ('lake_smelt', 'garfish'):
        n, added = db.mark_distinct_category_item_v023(10, distinct, species, 3)
        check(added, f'unique species counted {species}')
    check(n == 3 and db.quest(10, distinct)['progress'] == 3, 'distinct complete')
    db.complete_quest(10, single)
    db.restart_quest(10, single)
    check(db.quest(10, single)['progress'] == 0, 'repeat start resets progress')
    check(db.quest(11, single)['progress'] == 0, 'other player still isolated')
    conn.close()
    return count

if __name__ == '__main__':
    print(f'BORIS v3.00.7 fast: {run_regression_fast()} checks PASS')
    import server
    print(f'BORIS v3.00.7 full: {run_regression()} checks PASS')
