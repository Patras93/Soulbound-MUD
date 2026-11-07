# -*- coding: utf-8 -*-
"""v106 STAGING ONLY: a player-facing Haldor command for one worn armor copy.

Never usable on an ordinary v105 database. A short confirmation code is tied
specifically to the physical instance ID so a changed numbered list cannot
silently upgrade a different copy. The material change is delegated entirely
to the tested SQLite savepoint routine; this module does not write SQL itself.
"""
from __future__ import annotations

import hashlib
import os

from systems.equipment_evolution_v10500 import (
    MAX_STAGE, required_materials, stage_stat_bonus, stage_defense_bonus,
)
from systems.equipment_evolution_stats_v10600 import evolve_equipped_copy_on_disposable_test
from systems.equipment_shadow_slots_v10600 import _check_account


def _code(instance_id):
    return hashlib.sha256(str(instance_id).encode('utf-8')).hexdigest()[:8]


def _worn_armor(db, aid):
    """Read and validate exact physical slots; no guesswork across copies."""
    from systems.v10700_eq_runtime_gate import is_enabled
    if not is_enabled(db):
        raise PermissionError('v107 EQ: fizyczne kopie nie są aktywne')
    catalog = getattr(db, '_v106_shadow_item_catalog', None)
    if not isinstance(catalog, dict):
        raise RuntimeError('v106: brak rejestru fizycznego EQ')
    _check_account(db.conn, int(aid), catalog)
    result = []
    for slot,uid,iid,stage in db.conn.execute('''
        SELECT s.slot,s.instance_id,i.item_id,i.evolution_stage
        FROM v106_equipped_instances s
        JOIN v106_item_instances i ON i.instance_id=s.instance_id
        WHERE s.account_id=? AND i.account_id=? ORDER BY s.slot,s.instance_id
    ''',(int(aid),int(aid))):
        item = catalog.get(str(iid))
        if item is not None and item.get('type') == 'armor':
            if type(stage) is not int or not 0 <= stage <= MAX_STAGE:
                raise ValueError('v106: nieprawidłowy etap EQ')
            result.append((str(slot),str(uid),str(iid),int(stage),item))
    codes = [_code(row[1]) for row in result]
    if len(set(codes)) != len(codes):
        raise RuntimeError('v106: niejednoznaczne kody sztuk EQ')
    return result


async def player_copy_evolution(session, raw):
    """`ewolucja kopia lista [strona]` / `ewolucja kopia N KOD POTWIERDZAM`."""
    db = session.server.db
    try:
        rows = _worn_armor(db, session.account_id)
    except (RuntimeError, ValueError):
        await session.send('niespójny rejestr fizycznego EQ. Niczego nie zmieniono.')
        return
    parts = str(raw or '').split()
    if parts and parts[0].casefold() == 'kopia':
        parts = parts[1:]
    if not parts or parts[0].casefold() in ('lista','list','pomoc','help'):
        page = int(parts[1]) if len(parts)==2 and parts[1].isdigit() else 1
        if len(parts)>2 or (len(parts)==2 and not parts[1].isdigit()):
            await session.send('Użycie: ewolucja kopia lista [strona].')
            return
        pages=max(1,(len(rows)+9)//10)
        if not 1<=page<=pages:
            await session.send(f'Ewolucja kopii: strony od 1 do {pages}.')
            return
        await session.send(f'Założone pancerze, strona {page}/{pages}. '
                           'Ewolucja: ewolucja kopia NUMER KOD POTWIERDZAM.')
        for i in range((page-1)*10,min(page*10,len(rows))):
            slot,uid,iid,stage,item=rows[i]
            await session.send(f'{i+1}. {item.get("name",iid)}, slot {slot}. '
                               f'Etap {stage}/{MAX_STAGE}. Kod {_code(uid)}.')
        if not rows:
            await session.send('Brak założonych pancerzy do ewolucji.')
        return
    if len(parts)!=3 or not parts[0].isdigit() or parts[2]!='POTWIERDZAM':
        await session.send('Użycie: ewolucja kopia NUMER KOD POTWIERDZAM. '
                           'Najpierw wpisz ewolucja kopia lista.')
        return
    if not session.at_haldor_forge_v0925():
        await session.send('Ewolucję pojedynczej kopii wykonuje Haldor w Kuźni.')
        return
    if getattr(session, 'combat_mob_key', None):
        await session.send('Nie można ewoluować EQ podczas walki.')
        return
    position=int(parts[0])
    if not 1<=position<=len(rows):
        await session.send('Nie ma takiej pozycji. Wpisz ewolucja kopia lista.')
        return
    slot,uid,iid,old_stage,item=rows[position-1]
    if _code(uid)!=parts[1].lower():
        await session.send('Kod nie zgadza się z fizyczną sztuką. '
                           'Odśwież listę; żadne materiały nie zostały zużyte.')
        return
    if old_stage==MAX_STAGE:
        await session.send(f'{item.get("name",iid)} osiągnął maksymalny etap {MAX_STAGE}.')
        return
    try:
        if getattr(db,'_v107_eq_live_active',False):
            from systems.v10700_live_equipment import production_copy_evolution
            done,new_stage=production_copy_evolution(db,session.account_id,slot,uid)
        else:
            done,new_stage=evolve_equipped_copy_on_disposable_test(
                db,session.account_id,slot,uid,confirm_disposable_copy=True)
    except (RuntimeError,ValueError):
        await session.send('Ewolucja przerwana przez niespójność EQ. '
                           'Żadne materiały nie zostały zużyte.')
        return
    except Exception:
        await session.send('błąd SQLite; ewolucja cofnięta, materiały zachowane.')
        raise
    if not done:
        materials=required_materials(old_stage+1)
        costs=', '.join(f'{iid}: {qty}' for iid,qty in materials.items())
        await session.send(f'Brak materiałów na etap {old_stage+1}. Potrzeba: {costs}.')
        return
    if hasattr(session,'_read_only_equipment_cache_v1262'):
        session._read_only_equipment_cache_v1262=None
    await session.send(f'{item.get("name",iid)}, slot {slot}. '
                       f'Ewolucja {new_stage}/{MAX_STAGE}. '
                       f'Bonus Konstytucji +{stage_stat_bonus(new_stage,item)}, '
                       f'obrona +{stage_defense_bonus(new_stage,item)}. '
                       'Ulepszono tylko tę fizyczną sztukę.')
