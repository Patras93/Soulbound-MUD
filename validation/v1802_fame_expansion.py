# -*- coding: utf-8 -*-
"""Fame 1.80.2 smoke test; invoke after the complete server bootstrap."""
import asyncio
import sqlite3
import time
from collections import defaultdict
from types import SimpleNamespace


def run_regression():
    from systems.fame_v1702 import (
        fame_catalog, fame_region, fame_report, record_fame_kill,
        pay_due_fame, _is_fame_target, _eligible_natural_fame_enemy, ensure_schema,
    )
    from systems.content_registry import MOB_SPAWNS
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES

    catalog = fame_catalog()
    old_bosses, old_natural = defaultdict(set), defaultdict(set)
    for room, key in MOB_SPAWNS:
        mob = MOB_TEMPLATES.get(key)
        if room not in ROOMS or not mob or not _eligible_natural_fame_enemy(mob):
            continue
        zone = fame_region(room)
        (old_bosses if _is_fame_target(mob) else old_natural)[zone].add(str(key))
    legacy = {zone: (old_bosses.get(zone) or old_natural.get(zone)) for zone in
              set(old_bosses) | set(old_natural)}
    assert catalog.keys() == legacy.keys()
    assert all(ids <= set(catalog[zone]) for zone, ids in legacy.items())
    assert len(catalog) >= 152 and sum(map(len, catalog.values())) >= 589
    assert len(catalog['Jaskinie Goblinów']) >= 6
    assert len(catalog['Nekropolia']) >= 6

    db = sqlite3.connect(':memory:')
    ensure_schema(db)
    zone = 'Jaskinie Goblinów'
    older = sorted(legacy[zone])[0]
    fresh = sorted(set(catalog[zone]) - set(legacy[zone]))[0]
    db.execute('INSERT INTO fame_bosses_v1702(account_id,region,boss_id) VALUES(?,?,?)',
               (100, zone, older))
    db.commit()
    room = next(r for r, key in MOB_SPAWNS if r in ROOMS and key == fresh and fame_region(r) == zone)
    mob = SimpleNamespace(room_id=room, template_id=fresh)
    class Player:
        def __init__(self, aid):
            self.account_id = aid
            self.character = SimpleNamespace(character_level=90)
            self.server = SimpleNamespace(db=SimpleNamespace(conn=db, save_character=lambda _:None))
            self.closed = False
            self.granted = 0
            self.messages = []
        async def grant_combat_soul_xp_v11350(self, xp, **kwargs): self.granted += xp
        async def grant_class_xp(self, xp, **kwargs): self.granted += xp
        async def grant_stat_xp_v11342(self, xp, **kwargs): self.granted += xp
        def add_character_xp_with_event(self, xp, **kwargs): self.granted += xp; return []
        async def send(self, message): self.messages.append(str(message))

    p1, p2 = Player(100), Player(101)
    assert len(record_fame_kill(db, [p1,p2], mob, MOB_TEMPLATES[fresh])) == 2
    assert not record_fame_kill(db, [p1,p2], mob, MOB_TEMPLATES[fresh])
    assert db.execute('SELECT count(*) FROM fame_bosses_v1702 WHERE account_id=100').fetchone()[0] == 2
    assert db.execute('SELECT count(*) FROM fame_pending_v1703 WHERE account_id=101').fetchone()[0] == 1
    assert any('oczekuje na nagrodę' in msg for msg in fame_report(db, 100, 'cele',room))
    assert any('do zdobycia' in msg for msg in fame_report(db, 100, 'braki',room))
    assert 'Jaskinie Goblinów' in fame_report(db, 100, 'cele',room)[0]
    assert fame_report(db, 100, '', room)[0].startswith('You have ')
    db.execute('UPDATE fame_pending_v1703 SET due_at=?', (time.time() - 1,))
    db.commit()
    async def pay():
        assert await pay_due_fame(p1) == 1
        assert await pay_due_fame(p1) == 0
        assert await pay_due_fame(p2) == 1
    asyncio.run(pay())
    assert p1.granted > 0 and p2.granted == p1.granted
    assert db.execute('SELECT count(*) FROM fame_pending_v1703 WHERE delivered=0').fetchone()[0] == 0
    assert db.execute('SELECT count(*) FROM fame_bosses_v1702').fetchone()[0] == 3
    assert any('ZALICZONE' in txt for txt in p1.messages)
    return {'regions':len(catalog), 'targets':sum(map(len,catalog.values())),
            'previous_targets':sum(map(len,legacy.values())),
            'new_targets':sum(map(len,catalog.values()))-sum(map(len,legacy.values())),
            'party_award':True,'duplicate_ignored':True,'sqlite_previous_credit':True,
            'pending_payout_once':True}
