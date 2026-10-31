# -*- coding: utf-8 -*-
"""Era Bez Granic — additional dungeon XP after floor 800, never an XP cap.

Existing boss gates, portals and player's EXP Bank still own progression.
The extra reward is applied once to a combat reward, before XP distribution.
"""
from __future__ import annotations

from core.bootstrap_economy_professions import V019_SAFE_INT

# Source metadata belongs to the generated monster, never the player's level.
FLOOR_KEYS = (
    ('mythic_crypt', 'mythic_crypt_floor'),
    ('crypt', 'crypt_floor'),
    ('mythic_tower', 'mythic_astral_floor'),
    ('tower', 'astral_floor'),
    ('deep', 'uoss_deep_dungeon_floor'),
)
DISPLAY_NAMES = {
    'deep': 'Deep Dungeon', 'crypt': 'Krypta',
    'mythic_crypt': 'Mityczna Krypta', 'tower': 'Wieża Astralna',
    'mythic_tower': 'Mityczna Wieża',
}


def dungeon_identity(template):
    if not isinstance(template, dict):
        return None, 0
    for kind, key in FLOOR_KEYS:
        value = template.get(key)
        if value is None:
            continue
        try:
            floor = int(value)
        except (TypeError, ValueError, OverflowError):
            return None, 0
        return (kind, floor) if floor > 0 else (None, 0)
    return None, 0


def effective_pct(kind, floor, admin_pct=100):
    """No reduction below floor 801, bounded gain even at infinite depths."""
    if kind not in DISPLAY_NAMES or floor <= 800:
        return 100
    base = min(300, 125 + (floor - 801) // 100 * 5)
    if kind in ('mythic_crypt', 'mythic_tower'):
        base = min(325, base + 15)
    return min(650, base * int(admin_pct) // 100)


def reward_xp_v10300(template, axis, base):
    """Preserve zeros, coins and XP-bank semantics. Only boost real XP axes."""
    if axis not in ('class', 'character', 'soul', 'stat') or not isinstance(base, int) or base <= 0:
        return base
    kind, floor = dungeon_identity(template)
    if not kind or floor <= 800:
        return base
    from systems.admin_live_era_settings_v10300 import active_bonus_pct
    try:
        pct = effective_pct(kind, floor, active_bonus_pct(kind))
    except (OSError, ValueError):
        # Corrupt admin config must never abort combat or quest kill credit.
        # Admin Live exposes the file error; the safe fallback is old XP.
        return base
    return min(V019_SAFE_INT, (base * pct + 50) // 100)


def checkpoint_title(kind, floor):
    """Milestone titles require a real cleared checkpoint/boss, never visiting."""
    kind = {'astral': 'tower', 'mythic_astral': 'mythic_tower'}.get(kind, kind)
    if kind not in DISPLAY_NAMES or floor < 800 or floor % 100:
        return None
    return (f'era103:{kind}:{floor}', f'{DISPLAY_NAMES[kind]} — zdobywca progu {floor}')


def sync_checkpoint_titles_v10300(db, account_id):
    """Backfill milestone titles using *cleared* boss/Apanda records.

    Never infer a completion from a visited Deep floor. Existing legacy
    crypt/astral checkpoint also represents an already beaten boss.
    Inserts are idempotent; the player's other achievements stay untouched.
    """
    conn = db.conn
    names = {r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type="table"')}
    if 'unlocked_titles' not in names:
        return 0
    awards = set()
    if 'boss_floor_clears' in names:
        for kind, floor in conn.execute(
            'SELECT dungeon_kind,floor FROM boss_floor_clears '
            'WHERE account_id=? AND floor>=800 AND floor%100=0 LIMIT 2000',
            (int(account_id),),
        ):
            title = checkpoint_title(kind, int(floor))
            if title:
                awards.add(title)
    if 'characters' in names:
        columns = {r[1] for r in conn.execute('PRAGMA table_info(characters)')}
        if 'crypt_checkpoint' in columns:
            row=conn.execute('SELECT crypt_checkpoint FROM characters WHERE account_id=?', (int(account_id),)).fetchone()
            highest=int(row[0] or 0) if row else 0
            for floor in range(800, min(highest, 20000)+1, 100):
                awards.add(checkpoint_title('crypt', floor))
    if 'astral_progress' in names:
        row=conn.execute('SELECT checkpoint FROM astral_progress WHERE account_id=?',(int(account_id),)).fetchone()
        highest=int(row[0] or 0) if row else 0
        for floor in range(800, min(highest, 20000)+1, 100):
            awards.add(checkpoint_title('tower', floor))
    if 'collection_codex' in names:
        from world.uoss_superboss_world import UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331
        for (text_floor,) in conn.execute(
            'SELECT entry_id FROM collection_codex WHERE account_id=? AND category=? '
            'AND CAST(entry_id AS INTEGER)>=800 LIMIT 2000',
            (int(account_id), UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331),
        ):
            try:floor=int(text_floor)
            except (TypeError, ValueError):continue
            title=checkpoint_title('deep',floor)
            if title:awards.add(title)
    if not awards:return 0
    with conn:
        return sum(
            conn.execute('INSERT OR IGNORE INTO unlocked_titles '
                         '(account_id,title_id,title_name) VALUES(?,?,?)',
                         (int(account_id), title_id,title_name)).rowcount
            for title_id,title_name in sorted(awards)
        )
