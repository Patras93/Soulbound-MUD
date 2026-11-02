# -*- coding: utf-8 -*-
"""v105: trwały wybór żywiołu i jednorazowy Impuls Broni Duszy.

Nie zmienia bazowych przedmiotów, nie ingeruje w historyczne tabele Duszy.
Aktywacja ma trwały cooldown (SQLite), nawet po ponownym logowaniu.
"""
import time

ELEMENTS = {
    'ogień': ('fire', 'Ogień'), 'ogien': ('fire', 'Ogień'), 'fire': ('fire', 'Ogień'),
    'lód': ('ice', 'Lód'), 'lod': ('ice', 'Lód'), 'ice': ('ice', 'Lód'),
    'piorun': ('lightning', 'Piorun'), 'elektryczny': ('lightning', 'Piorun'),
    'lightning': ('lightning', 'Piorun'),
    'mrok': ('dark', 'Mrok'), 'dark': ('dark', 'Mrok'),
    'światło': ('holy', 'Światło'), 'swiatlo': ('holy', 'Światło'), 'holy': ('holy', 'Światło'),
    'woda': ('water', 'Woda'), 'water': ('water', 'Woda'),
}
PREFERRED = ('ogień', 'lód', 'piorun', 'mrok', 'światło', 'woda')
SELECT_KEY = 'soul_weapon_element_v10500'
COOLDOWN_KEY = 'soul_weapon_impulse_cooldown_v10500'
MIN_TIER = 1100
IMPULSE_SECONDS = 90
LIVE_TUNING = {'v10500_bron_duszy': {
    'passive_pct': 3, 'weakness_pct': 8, 'impulse_pct': 20,
    'impulse_cooldown': 90, 'shield_pct': 15,
    'shield_seconds': 30, 'shield_cooldown': 180,
}}

def tuning(key):
    return LIVE_TUNING['v10500_bron_duszy'][key]
_WEAKNESSES = {
    'fire': {'ice'}, 'ice': {'fire'}, 'water': {'fire'},
    'lightning': {'water'}, 'holy': {'dark', 'shadow'},
    'dark': {'holy'},
}


def normalize_element(value):
    return ELEMENTS.get(str(value or '').strip().casefold(), ('', ''))


def selected_element(actor):
    """Pamięć sesji, inaczej jeden bezpieczny odczyt stanu konta."""
    account_id = getattr(actor, 'account_id', None)
    cached = getattr(actor, '_v105_selected_element_cache', None)
    if isinstance(cached, tuple) and cached[0] == account_id:
        return cached[1]
    try:
        conn = actor.server.db.conn
        row = conn.execute(
            'SELECT text_value FROM player_records_v03051 '
            'WHERE account_id=? AND record_key=?',
            (actor.account_id, SELECT_KEY),
        ).fetchone()
        value = str(row[0] if row else '')
    except (AttributeError, TypeError):
        return ''  # Detached arena or historical fake actor: no settings.
    result = value if value in {v[0] for v in ELEMENTS.values()} else ''
    actor._v105_selected_element_cache = (account_id, result)
    return result


def choose_element(actor, raw):
    if int(getattr(actor.character, 'soul_tier', 0)) < MIN_TIER:
        return False, f'Wybór żywiołu Broni Duszy jest dostępny od Tieru {MIN_TIER}.'
    element, label = normalize_element(raw)
    if not element:
        return False, 'Nieznany żywioł. Dostępne: ' + ', '.join(PREFERRED) + '.'
    conn = actor.server.db.conn
    conn.execute(
        'INSERT INTO player_records_v03051(account_id,record_key,text_value) VALUES(?,?,?) '
        'ON CONFLICT(account_id,record_key) DO UPDATE SET '
        'text_value=excluded.text_value,updated_at=CURRENT_TIMESTAMP',
        (actor.account_id, SELECT_KEY, element),
    )
    conn.commit()
    actor._v105_selected_element_cache = (actor.account_id, element)
    return True, f'Broń Duszy — żywioł {label}. Wybór zapisano na postaci.'


def activate_impulse(actor, now=None):
    if int(getattr(actor.character, 'soul_tier', 0)) < MIN_TIER:
        return False, f'Impuls Broni Duszy odblokowuje się od Tieru {MIN_TIER}.'
    if not selected_element(actor):
        return False, 'Najpierw wybierz żywioł: bronduszy zywiol piorun.'
    now = int(time.time() if now is None else now)
    conn = actor.server.db.conn
    row = conn.execute(
        'SELECT value FROM player_records_v03051 '
        'WHERE account_id=? AND record_key=?',
        (actor.account_id, COOLDOWN_KEY),
    ).fetchone()
    until = int(row[0]) if row else 0
    if until > now:
        return False, f'Impuls Broni Duszy: odnowienie za {until - now} s.'
    conn.execute(
        'INSERT INTO player_records_v03051(account_id,record_key,value) VALUES(?,?,?) '
        'ON CONFLICT(account_id,record_key) DO UPDATE SET '
        'value=excluded.value,updated_at=CURRENT_TIMESTAMP',
        (actor.account_id, COOLDOWN_KEY, now + tuning('impulse_cooldown')),
    )
    conn.commit()
    actor._v105_impulse_charged = actor.account_id
    return True, f'Impuls Broni Duszy gotowy. Następne trafienie Bronią Duszy zada dodatkowe obrażenia. Odnowienie: {tuning("impulse_cooldown")} s.'


def weapon_multiplier(actor, template):
    """Pasywna premia do rzeczywistego uderzenia; nie daje nic bez wyboru."""
    if int(getattr(actor.character, 'soul_tier', 0)) < MIN_TIER:
        return 1.0
    element = selected_element(actor)
    if not element:
        return 1.0
    from systems.elemental_combat import mob_element_affinities_v11339
    affinities = set(mob_element_affinities_v11339(template))
    return 1 + (tuning('weakness_pct') if affinities & _WEAKNESSES.get(element, set()) else tuning('passive_pct')) / 100


def consume_impulse(actor):
    if getattr(actor, '_v105_impulse_charged', None) == getattr(actor, 'account_id', None):
        actor._v105_impulse_charged = False
        return 1 + tuning('impulse_pct') / 100
    return 1.0


# v105: druga aktywna moc — trwała, czasowa Osłona Duszy.
SHIELD_MIN_TIER = 1200
SHIELD_SECONDS = 30
SHIELD_COOLDOWN_SECONDS = 180
SHIELD_ACTIVE_KEY = 'soul_weapon_shield_active_v10500'
SHIELD_COOLDOWN_KEY = 'soul_weapon_shield_cooldown_v10500'


def activate_shield(actor, now=None):
    """30 s obrony, cooldown w SQLite odporny na ponowne logowanie."""
    if int(getattr(actor.character, 'soul_tier', 0)) < SHIELD_MIN_TIER:
        return False, f'Osłona Duszy dostępna od Tieru {SHIELD_MIN_TIER}.'
    if not selected_element(actor):
        return False, 'Najpierw wybierz żywioł Broni Duszy.'
    now = int(time.time() if now is None else now)
    conn = actor.server.db.conn
    conn.execute('SAVEPOINT sb105_soul_shield')
    try:
        row = conn.execute(
            'SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
            (actor.account_id, SHIELD_COOLDOWN_KEY),
        ).fetchone()
        until = int(row[0]) if row else 0
        if until > now:
            conn.execute('RELEASE SAVEPOINT sb105_soul_shield')
            return False, f'Osłona Duszy: odnowienie za {until - now} s.'
        for key, value in ((SHIELD_ACTIVE_KEY, now + tuning('shield_seconds')),
                           (SHIELD_COOLDOWN_KEY, now + tuning('shield_cooldown'))):
            conn.execute(
                'INSERT INTO player_records_v03051(account_id,record_key,value) VALUES(?,?,?) '
                'ON CONFLICT(account_id,record_key) DO UPDATE SET '
                'value=excluded.value,updated_at=CURRENT_TIMESTAMP',
                (actor.account_id, key, value),
            )
        conn.execute('RELEASE SAVEPOINT sb105_soul_shield')
        conn.commit()
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb105_soul_shield')
        conn.execute('RELEASE SAVEPOINT sb105_soul_shield')
        raise
    return True, f'Osłona Duszy: Obrona i Obrona Magiczna +{tuning("shield_pct")}% na {tuning("shield_seconds")} s. Odnowienie {tuning("shield_cooldown")} s.'


def shield_multiplier(actor, now=None):
    if int(getattr(actor.character, 'soul_tier', 0)) < SHIELD_MIN_TIER:
        return 1.0
    now = int(time.time() if now is None else now)
    row = actor.server.db.conn.execute(
        'SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
        (actor.account_id, SHIELD_ACTIVE_KEY),
    ).fetchone()
    return 1 + tuning('shield_pct') / 100 if row and int(row[0]) > now else 1.0
