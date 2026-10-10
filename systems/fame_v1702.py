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


# An Alter-inspired spread of memorable Fame hunts. Preserve all older
# target IDs, then grow only with unique natural species already present.
# New Kingdoms use authored Fame; older zones can have as many as 30 if varied.
FAME_TARGET_GOAL_PER_REGION_V1802 = 30


def _fame_threat_rank(template_id):
    """Prefer significant natural enemies without touching their combat stats.

    Stable, fixed authored HP/damage matter here: procedurally inferred level
    may have an unrelated pseudo-random value and must not drive selection.
    """
    enemy = MOB_TEMPLATES.get(template_id, {})
    return (int(enemy.get('max_hp') or 0),
            int(enemy.get('damage') or 0),
            int(enemy.get('soul_reward') or 0),
            str(template_id))


@lru_cache(maxsize=1)
def fame_catalog():
    """Deterministic Fame objectives from naturally placed enemies.

    * Keep EVERY old authored objective and EVERY v1.80.1 fallback objective.
    * Where an existing Fame zone has fewer than the target objective count, include
      powerful non-boss natural enemies until there are six (if available).
    * Zones with no prior authored Fame keep all their fallback targets.
    * Never use random instances, temporary summons or spawn repetition as new
      objectives. Names remain distinct to avoid indistinguishable Fame hunts.
    """
    from systems.content_registry import MOB_SPAWNS
    authored = {}
    candidates = {}
    for rid, mid in MOB_SPAWNS:
        if rid not in ROOMS:
            continue
        template = MOB_TEMPLATES.get(mid)
        if not template or not _eligible_natural_fame_enemy(template):
            continue
        zone = fame_region(rid)
        candidates.setdefault(zone, set()).add(str(mid))
        if _is_fame_target(template):
            authored.setdefault(zone, set()).add(str(mid))
    results = {}
    for zone in sorted(candidates, key=str.casefold):
        placed = candidates[zone]
        old_authored = authored.get(zone, set())
        # v1.80.1: no Fame zone -> all natural types give one Fame each.
        if not old_authored:
            results[zone] = tuple(sorted(placed))
            continue
        chosen = set(old_authored)
        # Previously authored objectives keep their IDs and historical SQLite
        # credit intact. Older areas gain additional, attainable targets.
        seen_names = {str(MOB_TEMPLATES[t].get('name') or t).casefold()
                      for t in chosen}
        if len(chosen) < FAME_TARGET_GOAL_PER_REGION_V1802:
            for tid in sorted(placed - chosen, key=_fame_threat_rank, reverse=True):
                if len(chosen) >= FAME_TARGET_GOAL_PER_REGION_V1802:
                    break
                name = str(MOB_TEMPLATES[tid].get('name') or tid).casefold()
                if name in seen_names:
                    continue
                seen_names.add(name)
                chosen.add(tid)
        results[zone] = tuple(sorted(chosen))
    return results


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


def _fame_target_identity(mob, catalog, template=None):
    """Identify the real placed mob, even when it wandered or became elite.

    Catalog IDs are immutable: historical Fame entries keep their original
    primary keys. Runtime variants must resolve to that same original target.
    """
    original_room = str(getattr(mob, 'home_room_id', '') or '')
    current_room = str(getattr(mob, 'room_id', '') or '')
    zones = []
    if original_room and (original_room in ROOMS or fame_region(original_room) in catalog):
        zones.append(fame_region(original_room))
    if current_room in ROOMS and fame_region(current_room) not in zones:
        zones.append(fame_region(current_room))
    if not zones:
        zones.append(fame_region(current_room))
    template_id = str(getattr(mob, 'template_id', '') or '')
    lineage = []
    visited = set()
    current = template_id
    while current and current not in visited:
        visited.add(current)
        lineage.append(current)
        meta = (template if current == template_id and template else
                MOB_TEMPLATES.get(current, {}))
        current = str(meta.get('elite_base_template') or
                      meta.get('rare_base_template') or
                      meta.get('dense_dungeon_base_template') or
                      meta.get('elite_source_template_v11338') or
                      meta.get('base_template') or '')
    # A runtime elite/terrain form should not produce a new Fame objective.
    # Prefer natural/root IDs over elite names, but preserve all authored IDs.
    for zone in zones:
        candidates = catalog.get(zone, ())
        for base in reversed(lineage):
            if base in candidates:
                return zone, base
    # Some generated variants retain the canonical species in their exact name.
    # Resolve only an unambiguous same-species target inside a real Fame zone.
    name = str((template or {}).get('name') or '').casefold().strip()
    if name:
        for zone in zones:
            matches = [bid for bid in catalog.get(zone, ())
                       if str(MOB_TEMPLATES.get(bid, {}).get('name') or '').casefold().strip() == name]
            if len(matches) == 1:
                return zone, matches[0]
    return None


def record_fame_kill(conn, recipients, mob, template):
    if not _eligible_natural_fame_enemy(template) or _is_runtime_summoned_mob(mob):
        return []
    identity = _fame_target_identity(mob, fame_catalog(), template)
    if identity is None:
        return []
    region, tid = identity
    # Canonical mob ID/region prevents elite and wandering duplicates.
    ensure_schema(conn)
    announced = []
    for session in recipients:
        result = conn.execute(
            'INSERT OR IGNORE INTO fame_bosses_v1702(account_id,boss_id,region) VALUES(?,?,?)',
            (session.account_id, tid, region),
        )
        if result.rowcount:
            # Fame and permanent credit occur now; only its EXP arrives later.
            # Durable EXP queue survives disconnects and server restarts.
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
    """Bare 'fame' gives the permanent world total; 'where fame' uses 'tutaj'.

    'fame regiony' lists all zones; none/some/most/all filter that list.
    All totals come from existing permanent SQLite kill credits, never EXP.
    """
    ensure_schema(conn)
    cat = fame_catalog()
    defeated = {(str(row[0]), str(row[1])) for row in conn.execute(
        'SELECT region,boss_id FROM fame_bosses_v1702 WHERE account_id=?', (account_id,))}
    pending={(str(r[0]),str(r[1])) for r in conn.execute(
        'SELECT region,boss_id FROM fame_pending_v1703 WHERE account_id=? AND delivered=0',
        (account_id,))}
    # Permanent Fame is earned on kill. Pending describes only deferred EXP,
    # never an uncredited target. Old SQLite progress stays valid.
    args = str(raw or '').strip().lower().split()
    if not args:
        # Preserve old kills even if a future content update removes a target.
        # A single (region, enemy) first defeat is exactly one point.
        available = sum(len(targets) for targets in cat.values())
        current = sum((region, bid) in defeated for region, bosses in cat.items()
                      for bid in bosses)
        return [f'Fame: {len(defeated)} punktów. Cele aktualnego świata: '
                f'{current}/{available}. Teren: where fame lub gdzie fame.']
    if args and args[0] in ('cele', 'targets', 'braki'):
        if room_id is None:
            return ['FAME CELE: podgląd jest dostępny z bieżącej lokacji w świecie.']
        zone = fame_region(room_id)
        all_targets = cat.get(zone, ())
        only_missing = args[0] == 'braki'
        ordered = sorted(all_targets, key=lambda tid: (
            str(MOB_TEMPLATES.get(tid, {}).get('name') or tid).casefold(), tid))
        if only_missing:
            ordered = [tid for tid in ordered if (zone, tid) not in defeated]
        page = max(1, int(args[1])) if len(args) > 1 and args[1].isdigit() else 1
        from math import ceil
        page_size = 12
        pages = max(1, ceil(len(ordered) / page_size))
        if page > pages:
            return [f'FAME: strona {page} nie istnieje. Dostępne strony: 1–{pages}.']
        done = sum((zone, tid) in defeated for tid in all_targets)
        pending_count = sum((zone, tid) in pending for tid in all_targets)
        lines = [f'FAME {"BRAKI" if only_missing else "CELE"} — {zone}: '
                 f'{done}/{len(all_targets)} zaliczono; '
                 f'{pending_count} oczekuje. Strona {page}/{pages}.']
        for tid in ordered[(page-1)*page_size:page*page_size]:
            name = str(MOB_TEMPLATES.get(tid, {}).get('name') or tid)
            status = ('zaliczone (premia EXP oczekuje)' if (zone, tid) in pending else
                      'zaliczone' if (zone, tid) in defeated else 'do zdobycia')
            lines.append(f'{name} — {status}.')
        if not ordered:
            lines.append('Brak celów Fame do wyświetlenia.')
        if page < pages:
            lines.append(f'Następna strona: fame {"braki" if only_missing else "cele"} {page+1}.')
        return lines
    if args and args[0] in ('bestiariusz','encyklopedia','bestiary'):
        if room_id is None:
            return ['FAME BESTIARIUSZ: wejdź do terenu, aby wyświetlić jego potwory.']
        zone=fame_region(room_id)
        targets=sorted(cat.get(zone, ()), key=lambda mid:
                       (str(MOB_TEMPLATES.get(mid, {}).get('name') or mid).casefold(),mid))
        page=max(1,int(args[1])) if len(args)>1 and args[1].isdigit() else 1
        page_size=10
        pages=max(1,(len(targets)+page_size-1)//page_size)
        if page>pages:
            return [f'FAME BESTIARIUSZ: dostępne strony 1-{pages}.']
        found=sum((zone,tid) in defeated for tid in targets)
        lines=[f'FAME BESTIARIUSZ — {zone}: odkryto {found}/{len(targets)} gatunków. '
               f'Strona {page}/{pages}.']
        for tid in targets[(page-1)*page_size:page*page_size]:
            known=(zone,tid) in defeated
            t=MOB_TEMPLATES.get(tid,{})
            lines.append(f'{str(t.get("name") or tid) if known else "Nieodkryty przeciwnik"}: '
                         f'{"zaliczony" if known else "do odnalezienia"}.')
        if page<pages:
            lines.append(f'Dalej: fame bestiariusz {page+1}.')
        return lines
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
            state='zaliczone (premia EXP oczekuje)' if delivered==0 else 'zaliczone'
            lines.append(f'{label} — {region}; {state}; pierwsze pokonanie: {when}.')
        if not section:lines.append('Brak zapisanych celów Fame.')
        lines.append('fame log — bieżący teren; fame log wszystko — wszystkie tereny.')
        return lines
    mode = ''
    page = 1
    local_tokens = ('tutaj', 'tu', 'status', 'teren', 'lokacja')
    global_tokens = ('regiony', 'krainy', 'swiat', 'świat', 'lista')
    if args[0] in local_tokens:
        if room_id is not None:
            region = fame_region(room_id)
            bosses = cat.get(region, ())
            done = sum((region, bid) in defeated for bid in bosses)
            count = len(bosses)
            status = _fame_status(done, count)
            # v1.70.4: quick, screen-reader-friendly current-area message.
            # All floors of a dungeon use the same region, but different
            # regions always retain independent completion statuses.
            # Fame counts immediately; only its EXP arrives with delay.
            messages = {
                'none': 'You have no fame in this area.',
                'some': 'You have some fame in this area.',
                'most': 'You have most fame in this area.',
                'all': 'You have all fame in this area.',
            }
            message = messages[status if count else 'none']
            # A final missing Fame target is useful in the short local command.
            # A queued EXP payout never hides already earned Fame.
            missing = [bid for bid in bosses if (region, bid) not in defeated]
            if len(missing) == 1:
                bid = missing[0]
                name = str(MOB_TEMPLATES.get(bid, {}).get('name') or bid)
                if (region, bid) in pending:
                    message += f' Fame zaliczone: {name} (EXP oczekuje).'
                else:
                    message += f' Missing fame: {name}.'
            return [message]
        return ['Fame terenu wymaga bieżącej lokacji. Wpisz where fame w grze.']
    elif args[0] in ('pomoc', 'help'):
        return ['fame — liczba zdobytych punktów Fame na całym świecie.',
                'where fame / gdzie fame — status obecnego terenu: none, some, most lub all.',
                'W lochu Fame sumuje wszystkie piętra; każdy teren ma własny status.',
                'fame regiony — przegląd wszystkich terenów; fame none/some/most/all — filtr terenów.',
                'fame log — historia aktualnego terenu; fame log wszystko — historia całego świata.',
                'fame cele — wszystkie cele bieżącego terenu; fame braki — niezliczone cele.',
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
        return ['FAME: fame — liczba punktów; where fame — obecny teren; fame regiony — cały świat; fame none/some/most/all — filtr terenów.']

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
    lines.append('fame — łączna liczba punktów; where fame — stan bieżącego terenu. Fame nie blokuje awansów ani nagród EXP.')
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
