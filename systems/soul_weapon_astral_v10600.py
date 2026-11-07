# -*- coding: utf-8 -*-
"""v106 staging: 3 new affinities and non-dominant two-element resonance.

Separate secondary slot, never rewrites v105 primary, Impulse, Shield or their
cooldown records. Real attack modifier and command are enabled only in STAGING.
"""
from __future__ import annotations
from systems.soul_weapon_elements_v10500 import normalize_element

SECONDARY_KEY='soul_weapon_secondary_v10600'
MIN_SECONDARY_TIER=3100
SECONDARY={
 'astral':('astral','Astral'), 'gwiazdy':('astral','Astral'),
 'natura':('nature','Natura'), 'nature':('nature','Natura'),
 'próżnia':('void','Próżnia'), 'proznia':('void','Próżnia'),
 'pustka':('void','Próżnia'), 'void':('void','Próżnia'),
}


def normalize_secondary(value):
    return SECONDARY.get(str(value or '').strip().casefold(),('',''))


def get_secondary(conn,account_id):
    row=conn.execute('SELECT text_value FROM player_records_v03051 '
        'WHERE account_id=? AND record_key=?',(int(account_id),SECONDARY_KEY)).fetchone()
    element=str(row[0]) if row else ''
    return element if element in ('astral','nature','void') else ''


def select_secondary(conn,account_id,soul_tier,name):
    if int(soul_tier)<MIN_SECONDARY_TIER:
        return False,f'Drugi żywioł od Tieru {MIN_SECONDARY_TIER}.'
    secondary,label=normalize_secondary(name)
    if not secondary:
        return False,'Nowe żywioły: astral, natura, próżnia.'
    primary=conn.execute('SELECT text_value FROM player_records_v03051 '
        'WHERE account_id=? AND record_key=?',(account_id,'soul_weapon_element_v10500')).fetchone()
    if not primary or normalize_element(primary[0])[0]=='':
        return False,'Najpierw wybierz podstawowy żywioł Broni Duszy z v105.'
    outer=conn.in_transaction
    conn.execute('SAVEPOINT sb_v106_secondary')
    try:
        conn.execute('INSERT INTO player_records_v03051 '
            '(account_id,record_key,text_value) VALUES(?,?,?) '
            'ON CONFLICT(account_id,record_key) DO UPDATE SET '
            'text_value=excluded.text_value,updated_at=CURRENT_TIMESTAMP',
            (account_id,SECONDARY_KEY,secondary))
        conn.execute('RELEASE SAVEPOINT sb_v106_secondary')
        if not outer:conn.commit()
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb_v106_secondary')
        conn.execute('RELEASE SAVEPOINT sb_v106_secondary')
        raise
    return True,f'Żywioł pomocniczy: {label}. Pierwotny żywioł i cooldowny pozostają bez zmian.'


def resonance_profile(primary,secondary,*,boss=False):
    """Pure bounded formula, no permanent superiority across all contexts.

    Return bounded factors; damage and on-hit recovery have live staging hooks.

    Defense effect is design-only until separately wired and tested.
    """
    p=normalize_element(primary)[0] or str(primary)
    if p not in {'fire','ice','lightning','dark','holy','water'}:
        return {'damage':1.0,'regeneration':1.0,'defense':1.0}
    s=normalize_secondary(secondary)[0]
    if not s:return {'damage':1.0,'regeneration':1.0,'defense':1.0}
    if s=='astral':
        return {'damage':1.05 if not boss else 1.025,
                'regeneration':1.0,'defense':0.97}
    if s=='nature':
        return {'damage':0.98,'regeneration':1.08,
                'defense':1.02 if not boss else 1.01}
    # Void earns higher boss pressure but weakens ordinary encounters.
    return {'damage':1.08 if boss else 0.95,'regeneration':0.96,
            'defense':0.96}


def secondary_damage_multiplier(actor, template):
    """Real weapon-attack factor, no state mutation; gated at source caller.

    Does not affect damage from regular class skills or any legacy v105
    damage when staging is disabled. Defense is not yet wired.
    """
    if int(getattr(actor.character, 'soul_tier', 0)) < MIN_SECONDARY_TIER:
        return 1.0
    from systems.soul_weapon_elements_v10500 import selected_element
    primary=selected_element(actor)
    if not primary:
        return 1.0
    secondary=get_secondary(actor.server.db.conn, actor.account_id)
    if not secondary:
        return 1.0
    from systems.uoss_basic_weapon_shared_v8000 import BOSS_FLAGS
    boss=any(bool(template.get(flag)) for flag in BOSS_FLAGS)
    return float(resonance_profile(primary,secondary,boss=boss)['damage'])


def secondary_regeneration_multiplier(actor):
    """Only existing Soul Weapon on-hit HP/MP restoration (no free healing).

    Caller must enforce SOULBOUND_V106_STAGING; no mutation or cooldown reset.
    """
    if int(getattr(actor.character, 'soul_tier', 0)) < MIN_SECONDARY_TIER:
        return 1.0
    from systems.soul_weapon_elements_v10500 import selected_element
    primary=selected_element(actor)
    if not primary:
        return 1.0
    secondary=get_secondary(actor.server.db.conn, actor.account_id)
    if not secondary:
        return 1.0
    factor=float(resonance_profile(primary,secondary)['regeneration'])
    if not 0.8 <= factor <= 1.2:
        raise ValueError('v106: invalid regeneration multiplier')
    return factor
