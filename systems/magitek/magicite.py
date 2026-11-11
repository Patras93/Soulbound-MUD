# -*- coding: utf-8 -*-
"""Magitek v107 STAGING: durable Magicite pod/link and real AoE summons.

Original UOSS descriptions specify varying MP/effects but no numbers or source
Magicite catalogue. Four cores/costs/formulas below are NEW Soulbound prototype
adaptations, not claimed UOSS facts. No Eidolon Echo. Never active in v106.
"""
from __future__ import annotations
from systems.v11200_activation import enabled as _sb112_runtime_enabled

import os
import time
from core.player_math import character_attribute_power

# element, display name, provisional Soulbound MP cost, prototype strength
CORES = {
    'ogien': ('fire', 'Rdzeń Ognia', 24, 1.0),
    'lod': ('ice', 'Rdzeń Lodu', 24, 1.0),
    'piorun': ('lightning', 'Rdzeń Pioruna', 28, 1.1),
    'trucizna': ('poison', 'Rdzeń Trucizny', 30, 0.8),
}
REQUIRED_BEAMS = ('firebeam', 'icebeam', 'boltbeam')
TRAINER_ROOM = 'guild_arcane_chamber'


def _require_stage():
    if not _sb112_runtime_enabled():
        raise RuntimeError('Magicite wymaga zatwierdzonej v112 lub odizolowanego testu v112')


def ensure_magicite_schema(db):
    """Only append isolated v107 table; never rewrite existing player rows."""
    _require_stage()
    db.conn.execute('''CREATE TABLE IF NOT EXISTS magitek_magicite_link_v107 (
        account_id INTEGER PRIMARY KEY,
        unlocked INTEGER NOT NULL DEFAULT 0 CHECK(unlocked IN (0,1)),
        core TEXT NOT NULL DEFAULT '' CHECK(core IN ('','ogien','lod','piorun','trucizna')),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )''')
    db.conn.commit()


def read_link(db, account_id):
    _require_stage()
    # The read path does NOT create schema or alter an existing database.
    exists = db.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='magitek_magicite_link_v107'").fetchone()
    if not exists:
        return False, ''
    row = db.conn.execute('SELECT unlocked,core FROM magitek_magicite_link_v107 WHERE account_id=?', (int(account_id),)).fetchone()
    if not row:
        return False, ''
    unlocked, core = bool(int(row[0])), str(row[1])
    if core and core not in CORES:
        raise ValueError('Nieznany zapis Magicite; odmowa użycia')
    return unlocked, core if unlocked else ''


def unlock_link(db, account_id):
    """Called after an explicitly checked solo initiation at Iria."""
    ensure_magicite_schema(db)
    db.conn.execute('''INSERT INTO magitek_magicite_link_v107(account_id,unlocked,core)
      VALUES(?,1,'') ON CONFLICT(account_id) DO UPDATE SET unlocked=1''', (int(account_id),))
    db.conn.commit()


def bind_core(db, account_id, core):
    _require_stage()
    if core not in CORES:
        return False
    unlocked, _ = read_link(db, account_id)
    if not unlocked:
        return False
    db.conn.execute('UPDATE magitek_magicite_link_v107 SET core=?,updated_at=CURRENT_TIMESTAMP WHERE account_id=? AND unlocked=1', (core,int(account_id)))
    db.conn.commit()
    return True


def _active_magitek(actor):
    return bool(getattr(actor,'character',None) and actor.character.class_name=='Magitek'
                and not getattr(actor,'closed',False) and actor.current_hp>0
                and not actor.is_downed_v0371())


async def magicite_command(actor, args):
    """mtek magicite; mtek magicite odblokuj; mtek magicite powiaz ogien."""
    _require_stage()
    if not _active_magitek(actor):
        await actor.send('Magicite: wymaga żywej, aktywnej postaci klasy Magitek.')
        return
    chunks=str(args or '').strip().casefold().split()
    command=chunks[0] if chunks else 'status'
    if command in ('status','lista'):
        unlocked, core = read_link(actor.server.db,actor.account_id)
        message = ('Odblokowany' if unlocked else 'Zablokowany')
        message += f'. Powiązany rdzeń: {CORES[core][1]}.' if core else '. Brak powiązanego rdzenia.'
        await actor.send('Magicite Link: '+message+' Dostępne rdzenie: ogien, lod, piorun, trucizna.')
        return
    if command not in ('odblokuj','powiaz'):
        await actor.send('Magicite: mtek magicite [status|odblokuj|powiaz ogien/lod/piorun/trucizna].')
        return
    if actor.character.room_id != TRAINER_ROOM:
        await actor.send('Magicite: synchronizacja tylko u Inżynierki Irii w Komnacie Arkanów.')
        return
    if actor.class_mastery_level('Magitek') < 15:
        await actor.send('Magicite Link: wymaga Biegłości Magiteka 15.')
        return
    if not actor.server.db.knows_skill(actor.account_id,'v107_magitek_magicitelink'):
        await actor.send('Najpierw naucz się Magicite Link u Irii.')
        return
    if command=='odblokuj':
        missing=[name for name in REQUIRED_BEAMS if not actor.server.db.knows_skill(actor.account_id,'v107_magitek_'+name)]
        if missing:
            await actor.send('Próba Irii: najpierw naucz się trzech promieni: Fire Beam, Ice Beam i Bolt Beam.')
            return
        unlock_link(actor.server.db, actor.account_id)
        await actor.send('Próba Irii zaliczona. Odblokowano Magicite Link. Powiąż rdzeń przez mtek magicite powiaz ogien.')
        return
    if len(chunks)!=2 or chunks[1] not in CORES:
        await actor.send('Magicite: podaj rdzeń ogien, lod, piorun albo trucizna.')
        return
    if bind_core(actor.server.db,actor.account_id,chunks[1]):
        await actor.send(f'Magicite: powiązano {CORES[chunks[1]][1]}. Zapisano na postaci.')
    else:
        await actor.send('Magicite: najpierw ukończ próbę Irii przez mtek magicite odblokuj.')


def calculate_damage(level, wisdom, willpower, skill_level, factor):
    """SOULBOUND prototype only: source UOSS provides no summon damage formula."""
    anchor=character_attribute_power(max(1,int(level)), max(1,(int(wisdom)+int(willpower))//2))
    return max(1, int((anchor//8+max(1,int(skill_level))*2)*float(factor)))


async def cast_magicite(actor, skill, query):
    """A real one-cast all-enemies spell using existing boss/kill/XP hooks."""
    _require_stage()
    if not _active_magitek(actor):
        await actor.send('Magicite Link: wymaga żywej, aktywnej klasy Magitek.')
        return
    from systems.magitek.support import _can_cast
    ok, reason = _can_cast(actor,skill)
    if not ok:
        await actor.send(reason)
        return
    if str(query or '').strip():
        await actor.send('Magicite Link obejmuje wszystkich wrogów w pokoju; nie podawaj celu.')
        return
    unlocked, core=read_link(actor.server.db,actor.account_id)
    if not unlocked or core not in CORES:
        await actor.send('Magicite Link: najpierw odblokuj moc i powiąż rdzeń u Irii.')
        return
    if float(getattr(actor,'v0319_silence_until',0) or 0)>time.time():
        await actor.send('Magicite Link: Silence blokuje przywołanie.')
        return
    element,name,mp_cost,factor=CORES[core]
    if int(actor.current_mana)<mp_cost:
        await actor.send(f'Magicite Link: za mało many, potrzeba {mp_cost} MP.')
        return
    room=actor.character.room_id
    # Honor exactly the same authored boss entry gates as other class skills.
    # Unknown templates are never a safe target, even if a mock world exposes one.
    from data.mobs import MOB_TEMPLATES
    from world.uoss_superboss_runtime import superboss_attack_gate_v11137
    monsters=[]
    for mob in actor.server.world.room_mobs(room):
        if not mob.alive or mob.room_id!=room or mob.hp<=0:
            continue
        template=MOB_TEMPLATES.get(mob.template_id)
        if not isinstance(template, dict) or not actor.server.engagement_allowed(actor,mob):
            continue
        passed,_reason=superboss_attack_gate_v11137(actor,template)
        if passed:
            monsters.append(mob)
    if not monsters:
        await actor.send('Magicite Link: brak dostępnych wrogów w pokoju; mana bez zmian.')
        return
    # No target can be a player/NPC. Use existing boss defense/kill hooks for each mob.
    progress=actor.server.db.skill_progress(actor.account_id,skill['id'])
    level=max(1,int(progress['level'])) if progress else 1
    base=calculate_damage(actor.character.character_level,actor.effective_intelligence(),actor.effective_willpower(),level,factor)
    # The genuine AoE opener initializes adaptive scaling, boss helper waves,
    # aggro and party assistance before the damage phase. This matters for
    # high-level bosses; bypassing it could give solo Magitek a free win.
    for mob in monsters:
        actor.server.sanitize_mob_engagement(mob)
        if not mob.engaged_by:
            mob.engaged_by=actor.character.name
            mob.engaged_at=time.monotonic()
            mob.combat_turn=0
            mob.player_hits=0
            mob.boss_opening_summoned_v1301=False
            mob.boss_last_summon_turn_v1281=-1
        if mob.engaged_by==actor.character.name:
            await actor.boss_summon_wave_v1301(mob,opening=True)
            mob.aoe_engaged_by=actor.character.name
        actor.apply_adaptive_mob_scale_v11330(mob)
    primary=next((mob for mob in monsters if mob.alive and mob.hp>0),None)
    if primary is not None:
        actor.combat_mob_key=primary.key
        await actor.server.auto_assist_party_combat(actor,primary)
    # MP charged once per real cast; the source Base AP is a LEARNING cost.
    actor.current_mana-=mp_cost
    damaged=0
    deaths=0
    for mob in monsters:
        if not mob.alive or mob.room_id!=room or mob.hp<=0:
            continue
        dealt=max(0,int(await actor.apply_boss_defense(mob,base)))
        dealt=min(int(mob.hp),dealt)
        if not dealt:
            continue
        mob.hp-=dealt
        damaged+=1
        if element=='poison' and mob.hp>0:
            mob.v0319_poison_until=time.time()+15
            mob.v0319_poison_power=max(1,base//10)
        if mob.hp<=0:
            await actor.mob_defeated(mob)
            deaths+=1
    await actor.grant_skill_use_xp(skill)
    await actor.send(f'Magicite Link ({name}): trafiono {damaged} przeciwników, pokonano {deaths}. Mana: {actor.current_mana}.')
    if damaged>deaths:
        await actor.ensure_realtime_combat()
