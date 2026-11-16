# -*- coding: utf-8 -*-
"""Global administrator control of Adaptive Combat.

Release v113.00.27 defaults to OFF, including legacy schema-1 ON settings.
A fresh, explicit administrator ON writes schema 2 and is still supported;
team skills, loot-sharing and aggro are independent of Adaptive Combat.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'LIVE_CONTENT' / 'adaptive_combat_global_v102006.json'
_ENABLED = None


def enabled():
    global _ENABLED
    if _ENABLED is None:
        if CONFIG_PATH.is_file():
            doc = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            if (type(doc) is not dict or doc.get('schema') not in (1, 2)
                    or type(doc.get('enabled')) is not bool):
                raise ValueError('Niepoprawne ustawienie Adaptive Combat w LIVE_CONTENT.')
            # A legacy ON setting cannot silently bring back unwanted party scaling.
            _ENABLED = doc['enabled'] if doc['schema'] == 2 else False
        else:
            _ENABLED = False  # Fresh installations do not scale by party size.
    return _ENABLED


def _store(choice):
    """Atomic write. Never claim success when the setting was not saved."""
    global _ENABLED
    if type(choice) is not bool:
        raise ValueError('Dozwolone tylko wlaczone/wylaczone.')
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.combat_global_', suffix='.tmp', dir=CONFIG_PATH.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'schema': 2, 'enabled': choice}, stream, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, CONFIG_PATH)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    _ENABLED = choice


def reset_mob(mob, template):
    """Remove previously accrued player/party scaling, retaining combat damage.

    Do not touch authored boss/region/floor definitions, combat phases or
    intrinsic buffs. Use integer ratios to support arbitrarily high HP.
    """
    previous = int(getattr(mob, 'adaptive_max_hp_v11330', 0) or 0)
    base = max(1, int((template or {}).get('max_hp', 1) or 1))
    if previous > 0 and getattr(mob, 'alive', False):
        old_hp = min(previous, max(0, int(getattr(mob, 'hp', 0) or 0)))
        if old_hp > 0:
            mob.hp = max(1, min(base, (base * old_hp + previous - 1) // previous))
        else:
            mob.hp = 0
    mob.adaptive_max_hp_v11330 = 0
    mob.adaptive_hp_multiplier_v11330 = 1.0
    mob.adaptive_reward_multiplier_v11330 = 1.0
    mob.adaptive_party_size_v11330 = 1
    mob.adaptive_party_dps_v11330 = 0.0
    mob.adaptive_rank_v11330 = ''
    return previous > 0


def reset_world(server):
    """Apply OFF immediately, also to already-engaged monsters on this server."""
    from data.mobs import MOB_TEMPLATES
    mobs = getattr(getattr(server, 'world', None), 'mobs', {})
    count = 0
    for mob in tuple(mobs.values()):
        template = MOB_TEMPLATES.get(getattr(mob, 'template_id', ''), {})
        if template and reset_mob(mob, template):
            count += 1
    return count


async def command(session, tail):
    """Accessible `admin live skalowanie off/on/status`. Admin-only."""
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    action = str(tail or '').strip().casefold()
    if action in ('', 'status'):
        state = 'WLACZONE' if enabled() else 'WYLACZONE'
        await session.send('ADMIN LIVE SKALOWANIE: '+state+'. Globalne dla wszystkich graczy. '
                           'admin live skalowanie off / on / status. '
                           'Zmiana bez restartu, trwala po restarcie.')
        return True
    if action not in ('on', 'off'):
        await session.send('Uzycie: admin live skalowanie off / on / status.')
        return True
    choice = action == 'on'
    was = enabled()
    if was == choice:
        if choice:
            await session.send('ADMIN LIVE SKALOWANIE: juz WLACZONE.')
        else:
            # Idempotent OFF is an operational command, not only a preference.
            # Stale world encounters must be normalized even if the persisted
            # switch was already disabled (e.g. after an interrupted battle).
            normalized = reset_world(session.server)
            await session.send('ADMIN LIVE SKALOWANIE: WYLACZONE. '
                               f'Sprawdzono aktywne potwory, usunieto dodatkowe skalowanie: {normalized}. '
                               'Bazowe statystyki potworow pozostaja bez zmian.')
        return True
    try:
        _store(choice)
    except (OSError, ValueError, TypeError) as exc:
        await session.send('ADMIN LIVE SKALOWANIE: nie zapisano zmiany: '+str(exc)[:200])
        return True
    normalized = reset_world(session.server) if not choice else 0
    db = getattr(session.server, 'db', None)
    if db and callable(getattr(db, 'record_admin_action_v1224', None)):
        try:
            db.record_admin_action_v1224(db.account_name(session.master_account_id),
                                          'adaptive_scaling_global', action)
        except (OSError, ValueError, TypeError, RuntimeError):
            # Setting is already durably committed; audit logging is secondary.
            import logging
            logging.getLogger(__name__).exception('Could not log adaptive scaling switch')
    await session.send(
        'ADMIN LIVE SKALOWANIE: '+('WLACZONE.' if choice else 'WYLACZONE.')+
        ' Wszyscy gracze, bez restartu. Ustawienie zapisane.'+
        (f' Usunieto skalowanie {normalized} aktywnych potworow; '
         'zachowano ich aktualne obrazenia i naturalne statystyki.' if not choice else
         ' Kolejne starcia ponownie uzyja Adaptive Combat.')
    )
    return True
