# -*- coding: utf-8 -*-
"""Additional retroactive level milestones for v103, no edits to v1370 ids.

Constructs only reached milestones; after level 5000 every 500 levels.
The sync batch is bounded so a bad administrator-set level cannot block login.
"""
from __future__ import annotations

PLANNED = (1000,1200,1500,2000,2500,3000,3500,4000,4500,5000)
PAGE = 500


def levels_reached(current, *, max_entries=PAGE):
    current=max(0,int(current or 0))
    out=[level for level in PLANNED if level<=current]
    if current>5000:
        count=min(max(0,int(max_entries)-len(out)),(current-5000)//500)
        out.extend(5500+500*i for i in range(count))
    return tuple(out[:max_entries])


def sync_v10300(db, account_id, snapshot=None):
    if snapshot is None:
        from systems.legendary_achievements_v1370 import snapshot_v1370
        snapshot=snapshot_v1370(db, account_id)
    account_id=int(account_id)
    # Read the existing namespace first. Repeated syncs must advance through
    # batches instead of getting stuck on the first 500 historical thresholds.
    found={row['achievement_id'] for row in db.conn.execute(
        'SELECT achievement_id FROM achievements WHERE account_id=? AND achievement_id LIKE ?',
        (account_id,'legend:v10300:%'))}
    fresh=[]
    budget=PAGE+len(found)
    for (source,key),value in snapshot.items():
        if source not in ('axis','class','profession'):
            continue
        for level in levels_reached(value, max_entries=budget):
            identifier=f'legend:v10300:{source}:{key}:{level}'
            if identifier in found:
                continue
            label=(f'Poziom {key}' if source=='axis' else str(key))
            fresh.append((identifier, f'Era Bez Granic — {label}, poziom {level}',
                          f'Legenda {label} — poziom {level}'))
            if len(fresh)>=PAGE:
                break
        if len(fresh)>=PAGE:
            break
    if not fresh:
        from systems.era_dungeon_plus_v10300 import sync_checkpoint_titles_v10300
        return sync_checkpoint_titles_v10300(db, account_id)
    with db.conn:
        db.conn.executemany('INSERT OR IGNORE INTO achievements '
            '(account_id,achievement_id,name,tier) VALUES(?,?,?,?)',
            [(account_id,identifier,name,'Era Bez Granic') for identifier,name,_ in fresh])
        db.conn.executemany('INSERT OR IGNORE INTO unlocked_titles '
            '(account_id,title_id,title_name) VALUES(?,?,?)',
            [(account_id,identifier,title) for identifier,_,title in fresh])
    from systems.era_dungeon_plus_v10300 import sync_checkpoint_titles_v10300
    return len(fresh) + sync_checkpoint_titles_v10300(db, account_id)
