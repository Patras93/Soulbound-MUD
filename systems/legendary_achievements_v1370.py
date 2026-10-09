# -*- coding: utf-8 -*-
"""Soulbound v1.37.0: persistent, retroactive legendary milestone catalogue.

Only milestones grounded in saved player progression are included. No invented
historical firsts and no gambling/random rewards. Reading never alters XP or cash.
"""
from __future__ import annotations

from dataclasses import dataclass
from core.classes_skills import CLASSES

VERSION_V1370 = "1.37.0"
PROFESSIONS_V1370 = (
    'Wędkarstwo', 'Górnictwo', 'Drwalstwo', 'Zielarstwo',
    'Gotowanie', 'Alchemia', 'Kowalstwo', 'Jubilerstwo',
    'Krawiectwo', 'Garbarstwo', 'Stolarstwo', 'Zaklinanie',
    'Archeologia', 'Kartografia',
)
CLASS_NAMES_V1370 = tuple(entry[0] for entry in CLASSES)
LEVEL_THRESHOLDS_V1370 = (10, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500, 800)
ACTIVITY_TRACKS_V1370 = (
    ('kills_total', 'Pokonani przeciwnicy', (10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)),
    ('boss_kills', 'Pokonani bossowie', (1, 3, 5, 10, 20, 50, 100, 200, 400, 800)),
    ('rare_kills', 'Rzadcy przeciwnicy', (1, 3, 5, 10, 20, 40, 75, 150, 300, 600)),
    ('rooms_discovered', 'Odkryte lokacje', (10, 25, 50, 100, 250, 500, 1000, 1500, 2000, 2500)),
    ('quests_completed', 'Ukończone zadania', (1, 3, 5, 10, 20, 50, 100, 200, 400, 800)),
    ('bounties_completed', 'Kontrakty łowców', (1, 3, 5, 10, 25, 50, 100, 200, 400, 800)),
    ('profession_actions', 'Akcje profesji', (10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)),
    ('crafted_items', 'Wytworzone przedmioty', (1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500)),
    ('packages_delivered', 'Dostarczone przesyłki', (1, 3, 5, 10, 20, 50, 100, 200, 400, 800)),
    ('crafting_orders_completed', 'Zamówienia rzemieślnicze', (1, 3, 5, 10, 20, 50, 100, 200, 400, 800)),
    ('legendary_contracts_completed', 'Legendarne kontrakty', (1, 2, 3, 5, 10, 20, 35, 50, 75, 100)),
    ('endless_sectors_discovered', 'Odkryte sektory bez końca', (1, 3, 5, 10, 20, 50, 100, 200, 400, 800)),
)

@dataclass(frozen=True)
class LegendaryMilestoneV1370:
    identifier: str
    category: str
    name: str
    source: str
    key: str
    threshold: int
    reward_title: str = ''


def create_catalog_v1370():
    milestones = []
    def add(source, key, category, label, levels):
        for level in levels:
            title = ''
            if source in ('profession', 'class') and level in (100, 300, 800):
                title = f"Legenda {label} — {level}"
            elif source == 'axis' and level in (300, 800):
                title = f"Legenda {label} — {level}"
            elif source == 'lifetime' and level == levels[-1]:
                title = f"Legenda: {label}"
            milestones.append(LegendaryMilestoneV1370(
                f"legend:v1370:{source}:{key}:{level}",
                category, f"{label} — próg {level}", source, key, int(level), title,
            ))
    for profession in PROFESSIONS_V1370:
        add('profession', profession, 'Profesje', profession, LEVEL_THRESHOLDS_V1370)
    for class_name in CLASS_NAMES_V1370:
        add('class', class_name, 'Klasy', f"Biegłość: {class_name}", LEVEL_THRESHOLDS_V1370)
    for key, label in (
        ('character_level', 'Poziom postaci'),
        ('soul_level', 'Poziom Duszy'),
        ('soul_weapon_mastery_level', 'Biegłość Broni Duszy'),
    ):
        add('axis', key, 'Rozwój', label, LEVEL_THRESHOLDS_V1370)
    for key, label, levels in ACTIVITY_TRACKS_V1370:
        add('lifetime', key, 'Wyczyny', label, levels)
    assert len({x.identifier for x in milestones}) == len(milestones)
    return tuple(milestones)


CATALOG_V1370 = create_catalog_v1370()
CATEGORIES_V1370 = ('Rozwój', 'Klasy', 'Profesje', 'Wyczyny')


def snapshot_v1370(db, account_id):
    """Single read of saved metrics; old characters unlock milestones retroactively."""
    account_id = int(account_id)
    data = {}
    row = db.conn.execute(
        'SELECT character_level,soul_level,soul_weapon_mastery_level '
        'FROM characters WHERE account_id=?', (account_id,)
    ).fetchone()
    if row:
        for field in ('character_level', 'soul_level', 'soul_weapon_mastery_level'):
            data[('axis', field)] = max(0, int(row[field] or 0))
    for row in db.conn.execute('SELECT profession,level FROM professions WHERE account_id=?', (account_id,)):
        data[('profession', str(row['profession']))] = max(1, int(row['level'] or 1))
    for row in db.conn.execute('SELECT class_name,level FROM class_progress WHERE account_id=?', (account_id,)):
        data[('class', str(row['class_name']))] = max(1, int(row['level'] or 1))
    for row in db.conn.execute('SELECT stat_key,value FROM lifetime_statistics WHERE account_id=?', (account_id,)):
        data[('lifetime', str(row['stat_key']))] = max(0, int(row['value'] or 0))
    return data


def sync_v1370(db, account_id):
    """Idempotent, batched rewards; neither cash nor existing progression is changed."""
    account_id = int(account_id)
    snapshot = snapshot_v1370(db, account_id)
    reached = [milestone for milestone in CATALOG_V1370
               if snapshot.get((milestone.source, milestone.key), 0) >= milestone.threshold]
    if not reached:
        return 0
    old_ids = {row['achievement_id'] for row in db.conn.execute(
        'SELECT achievement_id FROM achievements WHERE account_id=? AND achievement_id LIKE ?',
        (account_id, 'legend:v1370:%'))}
    new = [a for a in reached if a.identifier not in old_ids]
    if not new:
        return 0
    # One transaction: no per-achievement commits and no partial title awards.
    with db.conn:
        db.conn.executemany(
            'INSERT OR IGNORE INTO achievements(account_id,achievement_id,name,tier) VALUES(?,?,?,?)',
            [(account_id, a.identifier, a.name, 'Legendarne') for a in new],
        )
        titles = [(account_id, a.identifier, a.reward_title) for a in new if a.reward_title]
        if titles:
            db.conn.executemany(
                'INSERT OR IGNORE INTO unlocked_titles(account_id,title_id,title_name) VALUES(?,?,?)', titles
            )
        # Persistent history is owned by the existing achievements table itself.
    return len(new)


def records_v1370(db, limit=10):
    """Historical server records from durable values, not from guessed firsts."""
    limit = max(1, min(30, int(limit)))
    return db.conn.execute(
        'SELECT c.name,c.character_level,c.soul_level,c.soul_weapon_mastery_level '
        'FROM characters c ORDER BY c.character_level DESC,c.soul_level DESC,c.account_id ASC LIMIT ?',
        (limit,)).fetchall()
