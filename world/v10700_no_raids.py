# -*- coding: utf-8 -*-
"""v107 staging: retire ALL legacy raid gameplay without discarding player history.

Legacy quest IDs and the items/recipes remain stable.  Quests become ordinary
solo-capable regional hunts; raid rooms, mobs and routes disappear.  No writes
are made to character/account SQLite by this catalog migration.
"""
from __future__ import annotations

import re

_OLD103 = re.compile(r'^v10300_([a-z0-9_]+)_raid_([123])$')
_OLD104 = re.compile(r'^v10400_raid_(\d{2})_stage_([123])$')
_OLD106 = re.compile(r'^v10600_raid_(\d{2})_stage_([123])$')


def raid_return_room_v107(room_id, rooms=None):
    """Resolve a character's old raid location, even when v106 is not loaded.

    Fallback is deliberately non-destructive and used only for known raid IDs.
    """
    room_id = str(room_id or '')
    match = _OLD103.fullmatch(room_id)
    if match:
        dest = f'v10300_{match.group(1)}_09'
    elif match := _OLD104.fullmatch(room_id):
        from world.v10400_raids_12_25 import RAIDS
        number = int(match.group(1))
        record = next((r for r in RAIDS if r[0] == number), None)
        if record is None:
            return None
        dest = f'v10400_{record[1]}_{record[2]:02d}'
    elif match := _OLD106.fullmatch(room_id):
        from world.v10600_raids_26_35 import RAID_ROWS
        from world.v10600_region_index import REGIONS
        number = int(match.group(1))
        record = next((r for r in RAID_ROWS if r[0] == number), None)
        if record is None:
            return None
        dest = f'v10600_{REGIONS[record[1]][0]}_23'
    else:
        return None
    if rooms is not None and dest not in rooms:
        # An old v106 saved location may be loaded with v106 catalog disabled.
        # Always prefer the regular public square over a missing destination.
        return 'square'
    return dest


def _raid_groups():
    from world.v10300_era_bez_granic import ERAS
    from world.v10400_raids_12_25 import RAIDS
    from world.v10600_raids_26_35 import RAID_ROWS
    from world.v10600_region_index import REGIONS
    groups = []
    for slug, region, *_ in ERAS:
        base = f'v10300_{slug}'
        groups.append({
            'number': len(groups)+1, 'era': 'v103', 'region': region,
            'entry': f'{base}_09', 'target_base': base,
            'rooms': [f'{base}_raid_{n}' for n in (1,2,3)],
            'mobs': [f'{base}_raid_boss_{n}' for n in (1,2,3)],
            'quests': [f'{base}_raid_quest_{n}' for n in (1,2,3)],
            'fragment': f'{base}_raid_fragment', 'seal': None,
            'relic': f'{base}_raid_relic',
        })
    for number, slug, room_no, *_ in RAIDS:
        base = f'v10400_raid_{number:02d}'
        groups.append({
            'number': number, 'era': 'v104', 'region': slug,
            'entry': f'v10400_{slug}_{room_no:02d}',
            'target_base': f'v10400_{slug}',
            'rooms': [f'{base}_stage_{n}' for n in (1,2,3)],
            'mobs': [f'{base}_boss_{n}' for n in (1,2,3)],
            'quests': [f'{base}_raid_quest_{n}' for n in (1,2,3)],
            'fragment': f'{base}_fragment', 'seal': f'{base}_seal',
            'relic': f'{base}_relic',
        })
    for number, index, *_ in RAID_ROWS:
        slug = REGIONS[index][0]
        base = f'v10600_raid_{number}'
        groups.append({
            'number': number, 'era': 'v106', 'region': slug,
            'entry': f'v10600_{slug}_23',
            'target_base': f'v10600_{slug}',
            'rooms': [f'{base}_stage_{n}' for n in (1,2,3)],
            'mobs': [f'{base}_boss_{n}' for n in (1,2,3)],
            'quests': [f'{base}_quest_{n}' for n in (1,2,3)],
            'fragment': f'{base}_fragment', 'seal': f'{base}_seal',
            'relic': f'{base}_relic',
        })
    assert len(groups) == 35 and len({g['number'] for g in groups}) == 35
    return groups


def retire_all_raids_v107(rooms, mobs, spawns, npcs, quests, items, recipes):
    """Fail-closed catalog cutover, no user SQLite writes; stable old quest IDs.

    Preflight *every* entry before mutation; permits absent v106 block (staging
    not installed), but rejects incomplete catalogs and any dangling route.
    """
    groups = _raid_groups()
    available = []
    for g in groups:
        present = [rid in rooms for rid in g['rooms']]
        if not any(present) and g['era'] == 'v106':
            if any(qid in quests for qid in g['quests']):
                raise RuntimeError(f'v107: niepełny dawny katalog zadań {g["number"]}')
            continue
        if (not all(present)
                or not all(mid in mobs for mid in g['mobs'])
                or not all(qid in quests for qid in g['quests'])):
            raise RuntimeError(f'v107: niekompletny dawny katalog {g["number"]}')
        if g['entry'] not in rooms:
            raise RuntimeError(f'v107: brak bezpiecznego wyjścia {g["number"]}')
        if not all(item_id in items for item_id in
                   (g['fragment'],g['relic']) + ((g['seal'],) if g['seal'] else ())):
            raise RuntimeError(f'v107: brak przedmiotów historycznych {g["number"]}')
        if g['relic'] not in recipes:
            raise RuntimeError(f'v107: brak przepisu relikwii {g["number"]}')
        entry_exits = rooms[g['entry']].get('exits', {})
        if g['rooms'][0] not in entry_exits.values():
            raise RuntimeError(f'v107: niemożliwe do ustalenia dawne wejście {g["number"]}')
        for stage in (1,2,3):
            target = f'{g["target_base"]}_mob_{stage+2}'
            if target not in mobs or not any(
                    mid == target and rid in rooms and rid not in g['rooms']
                    for rid,mid in spawns):
                raise RuntimeError(f'v107: brak normalnego celu solo {g["number"]}/{stage}')
        boss = f'{g["target_base"]}_boss_1'
        if boss not in mobs or not any(mid == boss and rid in rooms for rid,mid in spawns):
            raise RuntimeError(f'v107: brak normalnego bossa z relikwiami {g["number"]}')
        available.append(g)

    removed_rooms = {rid for g in available for rid in g['rooms']}
    removed_mobs = {mid for g in available for mid in g['mobs']}
    replaced_quests = {qid for g in available for qid in g['quests']}
    if len(removed_rooms) != len(available)*3 or len(removed_mobs) != len(available)*3:
        raise RuntimeError('v107: kolizja identyfikatorów wyłączanych komnat')
    # Preflight all outbound routes to prevent any active portal to the removed rooms.
    stale_links = [(rid, direction) for rid, meta in rooms.items()
                   if rid not in removed_rooms for direction,target in meta.get('exits',{}).items()
                   if target in removed_rooms]
    # Do not silently redirect unrelated routes: the official entrances only.
    for rid, direction in stale_links:
        if not any(rid == g['entry'] and rooms[rid]['exits'].get(direction) == g['rooms'][0]
                   for g in available):
            raise RuntimeError(f'v107: nieznane przejście do starej komnaty: {rid}/{direction}')
    if len(stale_links) != len(available):
        raise RuntimeError('v107: liczba usuwanych wejść niezgodna z historią')

    # Commit of the fully validated in-memory catalog. Never delete ITEMS,
    # CRAFT_RECIPES or historical QUESTS IDs, so character inventory/progress is safe.
    for rid,direction in stale_links:
        del rooms[rid]['exits'][direction]
    for g in available:
        for stage, qid in enumerate(g['quests'],1):
            q = quests[qid]
            target = f'{g["target_base"]}_mob_{stage+2}'
            q['kind'] = 'kill'
            q['target'] = target
            q['needed'] = 1
            q['name'] = f'{rooms[g["entry"]]["zone"]}: polowanie dziedzictwa {stage}/3'
            q['description'] = (
                f'Pokonaj {mobs[target]["name"]} w zwykłej krainie. '
                f'Wróć do {q.get("giver", "zleceniodawcy")}. '
                'Można ukończyć samodzielnie.')
            q['v107_retired_raid_converted'] = True
            # Keep existing XP, currency, other reward items and quest prerequisites.
            if stage == 3 and g['seal']:
                reward = dict(q.get('reward_items') or {})
                reward[g['seal']] = max(1, int(reward.get(g['seal'],0) or 0))
                q['reward_items'] = reward
        # Item IDs, types, levels, bonuses and recipe ingredients stay intact.
        # Only text visible in the game is de-raidified.
        for iid in (g['fragment'],g['seal'],g['relic']):
            if not iid: continue
            row = items[iid]
            for key in ('name','desc'):
                if isinstance(row.get(key),str):
                    row[key] = (row[key].replace('Rajdu ', 'Dziedzictwa ')
                               .replace('rajdu ', 'dawnej wyprawy ')
                               .replace('Rajd ', 'Wyprawa ')
                               .replace('rajdu', 'dawnej wyprawy')
                               .replace('rajdzie', 'dawnej wyprawie'))
        recipe = recipes[g['relic']]
        for key in ('name','desc'):
            if isinstance(recipe.get(key),str):
                recipe[key] = (recipe[key].replace('Rajdu ', 'Dziedzictwa ')
                               .replace('rajdu ', 'wyprawy ')
                               .replace('Rajd ', 'Wyprawa ')
                               .replace('rajdu', 'dawnej wyprawy')
                               .replace('rajdzie', 'dawnej wyprawie'))
        if recipe.get('category') == 'raid_relic':
            recipe['category'] = 'legacy_relic'
        # Repeatable, non-raid source for legacy crafting ingredients.
        boss = f'{g["target_base"]}_boss_1'
        if boss not in mobs or not any(mid == boss for _,mid in spawns):
            raise RuntimeError('v107: brak wcześniej zweryfikowanego regionalnego bossa')
        drop = mobs[boss].setdefault('drops', {})
        drop[g['fragment']] = max(0.25, float(drop.get(g['fragment'],0) or 0))
        if g['seal']:
            drop[g['seal']] = max(0.15, float(drop.get(g['seal'],0) or 0))
    for rid in removed_rooms:
        del rooms[rid]
    for mid in removed_mobs:
        del mobs[mid]
    spawns[:] = [pair for pair in spawns if pair[0] not in removed_rooms and pair[1] not in removed_mobs]
    assert not any(target in removed_rooms for room in rooms.values()
                   for target in room.get('exits', {}).values())
    assert all(quests[qid]['target'] in mobs for qid in replaced_quests)
    return {
        'retired_raids':len(available), 'removed_rooms':len(removed_rooms),
        'removed_bosses':len(removed_mobs), 'replaced_solo_quests':len(replaced_quests),
        'preserved_items':sum(2+bool(g['seal']) for g in available),
        'history_and_quest_ids_preserved':True,
        'online_character_db_unchanged':True,
    }
