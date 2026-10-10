# -*- coding: utf-8 -*-
"""Fame: region-specific progress, with a single total across every floor of a dungeon.

Filters none/some/most/all select regions by completion status, not chat volume.
"""
from __future__ import annotations
from functools import lru_cache
import re
import time
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS fame_bosses_v1702 (
        account_id INTEGER NOT NULL,
        boss_id TEXT NOT NULL,
        region TEXT NOT NULL,
        first_defeated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(account_id,region,boss_id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS fame_pending_v1703 (
        account_id INTEGER NOT NULL,
        region TEXT NOT NULL,
        boss_id TEXT NOT NULL,
        boss_name TEXT NOT NULL,
        reward_xp INTEGER NOT NULL,
        due_at REAL NOT NULL,
        delivered INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(account_id,region,boss_id)
    )''')
    conn.commit()


def _is_fame_target(template):
    """Authored Fame enemies; fallback targets are chosen only in empty regions."""
    return bool(template.get('boss') or template.get('world_boss')
                or template.get('fame_mob') or template.get('fame_target')) and not (
                template.get('uoss_superboss_add') or template.get('monster_ai_summoned_v1160'))


def fame_region(room_id, rooms=None):
    """Keep the same group for every floor and room of a single dungeon."""
    rooms = ROOMS if rooms is None else rooms
    room_id = str(room_id or '')
    zone = str((rooms.get(room_id) or {}).get('zone') or '').strip()
    # Dynamically generated floors may not be materialized until a player enters.
    if not zone:
        patterns = (
            (r'^mythic_astral_floor_', 'Mityczna Wieża Astralna'),
            (r'^mythic_crypt_floor_', 'Mityczna Krypta'),
            (r'^crypt_floor_', 'Krypta Nieskończona'),
            (r'^v1500_echo_[0-9]+_', 'Nieskończony Labirynt Echa'),
        )
        for pattern, name in patterns:
            if re.match(pattern, room_id):
                return name
    return zone or 'Nieznana kraina'


@lru_cache(maxsize=1)
def fame_catalog():
    """Fame targets for placed monsters, preserving all previously authored regions.

    Areas with at least one authored Fame opponent keep their EXACT old list.
    In areas with no Fame at all, each naturally spawned mob type is a
    one-time regional Fame target. This never awards a repeat-kill bonus.
    """
    from systems.content_registry import MOB_SPAWNS
    authored = {}
    fallback = {}
    for rid, mid in MOB_SPAWNS:
        if rid not in ROOMS:
            continue
        template = MOB_TEMPLATES.get(mid)
        if not template or not _eligible_natural_fame_enemy(template):
            continue
        zone = fame_region(rid)
        if _is_fame_target(template):
            authored.setdefault(zone, set()).add(str(mid))
        else:
            fallback.setdefault(zone, set()).add(str(mid))
    # Do not inflate completion in older regions: existing achievements and
    # completed 'all' states remain valid after this update.
    regions = set(authored) | set(fallback)
    return {
        zone: tuple(sorted(authored.get(zone) or fallback.get(zone, ())))
        for zone in sorted(regions, key=str.casefold)
    }


def _eligible_natural_fame_enemy(template):
    """Only actual world opponents; not dummies or boss-spawned helpers."""
    return not any(template.get(k) for k in (
        'training_dummy', 'uoss_superboss_add', 'monster_ai_summoned_v1160',
        'ai_ephemeral_summon_v1160', 'boss_companion_v1281',
    ))


def _is_runtime_summoned_mob(mob):
    """A dynamically summoned copy cannot stand in for a natural Fame kill."""
    return bool(any(getattr(mob, key, None) for key in (
        'monster_ai_summoned_v1160', 'uoss_summon_parent_v1144',
        'ai_ephemeral_summon_v1160', 'boss_companion_v1281',
    )))


def record_fame_kill(conn, recipients, mob, template):
    if not _eligible_natural_fame_enemy(template) or _is_runtime_summoned_mob(mob):
        return []
    cat = fame_catalog()
    rid = str(getattr(mob, 'room_id', ''))
    region = fame_region(rid)
    tid = str(getattr(mob, 'template_id', ''))
    # A terrain-scaled / elite copy retains its natural spawn template identity.
    # Do not mistake its temporary generated ID for an additional Fame target.
    seen = set()
    while tid and tid not in seen and tid not in cat.get(region, ()):
        seen.add(tid)
        current = MOB_TEMPLATES.get(tid, {})
        base = str(current.get('base_template') or current.get('elite_base_template') or current.get('rare_base_template') or '')
        if not base or base == tid:
            break
        tid = base
    # Only the placed, catalogued targets grant Fame. For regions with prior
    # Fame objectives, ordinary mobs remain excluded as before.
    if tid not in cat.get(region, ()):
        return []
    ensure_schema(conn)
    announced = []
    for session in recipients:
        result = conn.execute(
            'INSERT OR IGNORE INTO fame_bosses_v1702(account_id,boss_id,region) VALUES(?,?,?)',
            (session.account_id, tid, region),
        )
        if result.rowcount:
            # Fame is recorded immediately to prevent repeat-kill farming,
            # but the visible credit and rewards arrive after a short delay.
            # A durable queue survives disconnects and server restarts.
            base=max(1,int(template.get('soul_reward',0) or 0),
                     int(template.get('class_xp_reward',0) or 0),
                     int(template.get('stat_reward',0) or 0)*4)
            amount=min(2_000_000_000,max(100,int(base*.50)))
            conn.execute(
                'INSERT OR IGNORE INTO fame_pending_v1703('
                'account_id,region,boss_id,boss_name,reward_xp,due_at) VALUES(?,?,?,?,?,?)',
                (session.account_id,region,tid,str(template.get('name') or tid),amount,time.time()+7),
            )
            announced.append((session, region))
    if announced:
        conn.commit()
    return announced


def _fame_status(done, total):
    if done == 0:
        return 'none'
    if done == total:
        return 'all'
    if done * 2 >= total:
        return 'most'
    return 'some'


def fame_report(conn, account_id, raw='', room_id=None):
    """At the player's location show *local* fame, not the world-wide total.

    'fame regiony' lists all zones; none/some/most/all filter that list.
    Optional room_id preserves the original API used by older tests/tools.
    """
    ensure_schema(conn)
    cat = fame_catalog()
    defeated = {(str(row[0]), str(row[1])) for row in conn.execute(
        'SELECT region,boss_id FROM fame_bosses_v1702 WHERE account_id=?', (account_id,))}
    pending={(str(r[0]),str(r[1])) for r in conn.execute(
        'SELECT region,boss_id FROM fame_pending_v1703 WHERE account_id=? AND delivered=0',
        (account_id,))}
    defeated.difference_update(pending)
    args = str(raw or '').strip().lower().split()
    if args and args[0]=='log':
        all_regions=len(args)>1 and args[1] in ('wszystko','calosc','regiony','swiat')
        zone=fame_region(room_id) if room_id else None
        rows=conn.execute('''SELECT f.region,f.boss_id,f.first_defeated_at,p.delivered,p.due_at
            FROM fame_bosses_v1702 f LEFT JOIN fame_pending_v1703 p
            ON p.account_id=f.account_id AND p.region=f.region AND p.boss_id=f.boss_id
            WHERE f.account_id=? ORDER BY f.first_defeated_at DESC, f.region,f.boss_id''',(account_id,)).fetchall()
        if not all_regions and zone:
            rows=[r for r in rows if r[0]==zone]
        page=1
        if len(args)>1 and args[-1].isdigit():page=max(1,int(args[-1]))
        start=(page-1)*15
        section=rows[start:start+15]
        heading=('cały świat' if all_regions or not zone else zone)
        lines=[f'FAME LOG — {heading}. Pokonani przeciwnicy: {len(rows)}. Strona {page}/{max(1,(len(rows)+14)//15)}.']
        for region,tid,when,delivered,due in section:
            label=MOB_TEMPLATES.get(tid,{}).get('name') or tid
            state='OCZEKUJE na zaliczenie i nagrodę' if delivered==0 else 'zaliczone'
            lines.append(f'{label} — {region}; {state}; pierwsze pokonanie: {when}.')
        if not section:lines.append('Brak zapisanych celów Fame.')
        lines.append('fame log — bieżący teren; fame log wszystko — wszystkie tereny.')
        return lines
    mode = ''
    page = 1
    local_tokens = ('', 'tutaj', 'tu', 'status', 'teren', 'lokacja')
    global_tokens = ('regiony', 'krainy', 'swiat', 'świat', 'lista')
    if not args or args[0] in local_tokens:
        if room_id is not None:
            region = fame_region(room_id)
            bosses = cat.get(region, ())
            done = sum((region, bid) in defeated for bid in bosses)
            count = len(bosses)
            status = _fame_status(done, count)
            # v1.70.4: quick, screen-reader-friendly current-area message.
            # All floors of a dungeon use the same region, but different
            # regions always retain independent completion statuses.
            # Pending awards do not count until their delayed delivery.
            messages = {
                'none': 'You have no fame in this area.',
                'some': 'You have some fame in this area.',
                'most': 'You have most fame in this area.',
                'all': 'You have all fame in this area.',
            }
            message = messages[status if count else 'none']
            # A final missing Fame target is useful in the short local command.
            # Fame queued for delayed credit is not yet in the completed count,
            # but don't tell the player to kill it again.
            missing = [bid for bid in bosses if (region, bid) not in defeated]
            if len(missing) == 1:
                bid = missing[0]
                name = str(MOB_TEMPLATES.get(bid, {}).get('name') or bid)
                if (region, bid) in pending:
                    message += f' Pending fame: {name} (awaiting confirmation).'
                else:
                    message += f' Missing fame: {name}.'
            return [message]
        # Internal API without room_id: preserve global reporting for older callers.
    elif args[0] in ('pomoc', 'help'):
        return ['fame — jedno zdanie: You have no/some/most/all fame in this area (zależnie od bieżącego terenu).',
                'W lochu Fame sumuje wszystkie piętra; każdy teren ma własny status.',
                'fame regiony — przegląd wszystkich terenów; fame none/some/most/all — filtr terenów.',
                'fame log — historia aktualnego terenu; fame log wszystko — historia całego świata.',
                'none=0%, some=1–49%, most=50–99%, all=100% dostępnych celów Fame.']
    elif args[0] in ('none', 'some', 'most', 'all'):
        mode = args[0]
        if len(args) > 1 and args[1].isdigit():
            page = max(1, int(args[1]))
    elif args[0] in global_tokens:
        if len(args) > 1 and args[1].isdigit():
            page = max(1, int(args[1]))
    elif args[0].isdigit():
        page = max(1, int(args[0]))
    else:
        return ['FAME: fame — aktualny teren; fame regiony — cały świat; fame none/some/most/all — tereny według postępu.']

    total = sum(len(values) for values in cat.values())
    collected = sum((region, boss) in defeated for region, bosses in cat.items() for boss in bosses)
    summary = []
    for region, bosses in cat.items():
        done = sum((region, t) in defeated for t in bosses)
        n = len(bosses)
        status = _fame_status(done, n)
        if not mode or mode == status:
            summary.append((region, done, n, status))
    from math import ceil
    page_size = 12
    pages = max(1, ceil(len(summary) / page_size))
    if page > pages:
        return [f'Fame: nie ma strony {page}. Dostępne strony: 1–{pages}.']
    lines = [f'FAME — PRZEGLĄD TERENÓW: {collected}/{total} odkrytych celów. '
             f'Tereny: {len(cat)}. Filtr: {mode or "wszystkie"}. Strona {page}/{pages}.',
             'Każdy teren liczy się osobno; wszystkie piętra jednego lochu sumują się.']
    if not summary:
        lines.append('Brak terenów odpowiadających temu filtrowi.')
    for region, done, n, status in summary[(page-1)*page_size:page*page_size]:
        lines.append(f'{region}: {done}/{n} Fame — {status}.')
    if page < pages:
        lines.append(f'Następna strona: fame {mode+" " if mode else "regiony "}{page+1}'.strip())
    lines.append('fame — stan bieżącego terenu. Fame nie blokuje awansów ani nagród EXP.')
    return lines


async def pay_due_fame(session):
    """Deliver persisted Fame rewards only to their owner and at most once normally.

    Summon events don't count. Offline due claims wait for the next login.
    EXP affects character, soul, class mastery and every stat; not professions.
    """
    if not getattr(session,'character',None) or getattr(session,'closed',False):
        return 0
    if getattr(session,'_fame_pay_busy_v1703',False):return 0
    session._fame_pay_busy_v1703=True
    try:
        conn=session.server.db.conn
        ensure_schema(conn)
        rows=conn.execute(
            'SELECT region,boss_id,boss_name,reward_xp FROM fame_pending_v1703 '
            'WHERE account_id=? AND delivered=0 AND due_at<=? ORDER BY due_at LIMIT 20',
            (session.account_id,time.time())).fetchall()
        count=0
        for region,bid,name,raw_amount in rows:
            if getattr(session,'closed',False) or not session.character:break
            xp=max(1,int(raw_amount))
            # Old and current character levels/progression use their ordinary
            # APIs, so this bonus respects the current XP requirements.
            fame_content_level=max(1,int(session.character.character_level))
            await session.grant_combat_soul_xp_v11350(xp,content_level=fame_content_level,content_scaled=True)
            await session.grant_class_xp(xp,single_level_cap=False,content_level=fame_content_level,content_scaled=True)
            await session.grant_stat_xp_v11342(xp,targets=None,content_level=fame_content_level,content_scaled=True)
            for line in session.add_character_xp_with_event(xp,single_level_cap=False,content_level=fame_content_level,content_scaled=True):
                await session.send(line)
            session.server.db.save_character(session.character)
            conn.execute('UPDATE fame_pending_v1703 SET delivered=1 '
                         'WHERE account_id=? AND region=? AND boss_id=? AND delivered=0',
                         (session.account_id,region,bid))
            conn.commit()
            await session.send(f'FAME — {region}: {name}, ZALICZONE. Premia: +{xp} EXP '
                               'do poziomu, Duszy, Biegłości i każdej statystyki. '
                               'Bez EXP profesji i narzędzi.')
            count+=1
        return count
    finally:
        session._fame_pay_busy_v1703=False


async def fame_pay_later(session):
    """Schedules online bonus, while SQLite handles logout and restart."""
    import asyncio
    if getattr(session,'closed',False) or not getattr(session,'character',None):return
    if getattr(session,'_fame_timer_running_v1703',False):return
    session._fame_timer_running_v1703=True
    try:
        conn=session.server.db.conn
        ensure_schema(conn)
        while not getattr(session,'closed',False) and getattr(session,'character',None):
            next_due=conn.execute('SELECT MIN(due_at) FROM fame_pending_v1703 '
                                  'WHERE account_id=? AND delivered=0',(session.account_id,)).fetchone()[0]
            if next_due is None:return
            await asyncio.sleep(max(0.0,float(next_due)-time.time()))
            if getattr(session,'closed',False):return
            await pay_due_fame(session)
            # Iterate again: more kills can have a later scheduled timestamp.
    finally:
        session._fame_timer_running_v1703=False
