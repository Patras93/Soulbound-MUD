# -*- coding: utf-8 -*-
"""Szybki AUDYT TESTOWY DPS i przeżywalności rajdów 26–35, nie rzeczywista walka.

Tylko izolowana kopia SQLite. Rzeczywiste formuły sesji gry potrafią dopisywać
leniwie rekordy klasy, dlatego raport NIGDY nie może dotknąć bazy graczy.
Wynik zakłada N IDENTYCZNYCH postaci (bez EQ/skilli/summonów/leczenia).
"""
from __future__ import annotations
import math
import os
from pathlib import Path
from systems.adaptive_combat import adaptive_target_max_hp_v11330
from systems.v106_combat_encounter_level import effective_encounter_level_v106


def forecast_raid_profile_v106(session, count, mob, template, room):
    if os.environ.get('SOULBOUND_V106_STAGING') != '1':
        raise RuntimeError('Audyt rajdów działa wyłącznie w staging.')
    if type(count) is not int or not 1 <= count <= 6:
        raise ValueError('Drużyna audytu: 1–6 identycznych postaci.')
    db = getattr(getattr(session,'server',None),'db',None)
    path = Path(str(getattr(db,'path','') or '/')).resolve()
    if not (getattr(db,'_v106_raid_forecast_disposable_copy',False) is True
            and path.parent.name.startswith('soulbound-v106-dps-offline-')
            and path.name == 'only_test.sqlite'):
        raise RuntimeError('Audyt musi działać na jawnie oznaczonej, tymczasowej kopii SQLite.')
    c = getattr(session,'character',None)
    if (not c or session.closed or session.current_hp <= 0
            or c.room_id != getattr(mob,'room_id',None)):
        raise ValueError('Niepoprawna sesja lub lokalizacja.')
    ident = str(getattr(mob,'template_id','')).split('__',1)[0]
    if (not ident.startswith('v10600_raid_') or '_boss_' not in ident
            or mob.room_id != ident.replace('_boss_','_stage_')):
        raise ValueError('Niepoprawny boss i sala rajdu v106.')
    if (not isinstance(template,dict) or int(template.get('max_hp') or 0) <= 0
            or not isinstance(room,dict) or int(room.get('generator_level') or 0)<30001):
        raise ValueError('Niepoprawne HP albo poziom krainy.')
    # This is the authentic member estimator, then an explicit homogenous-party
    # projection. No party_synergy, heals, abilities, equipment or custom perks.
    from systems.v106_raid_combat_dps import raid_autoattack_dps_v106
    dps_per_player = float(raid_autoattack_dps_v106(session, template))
    if not math.isfinite(dps_per_player) or dps_per_player <= 0:
        raise ValueError('Niepoprawny DPS postaci.')
    party_dps = dps_per_player * count
    effective = effective_encounter_level_v106(c,mob,template,room)
    max_hp = adaptive_target_max_hp_v11330(int(template['max_hp']),party_dps,
                                            template,party_level=effective,room=room)
    raw_incoming = float(session.consider_enemy_expected_hit(template))
    if not math.isfinite(raw_incoming) or raw_incoming <= 0:
        raise ValueError('Niepoprawna prognoza uderzenia bossa.')
    # Actual adaptive incoming multiplier can only increase the damage.
    # Thus this value is an upper bound, NOT a guarantee of survival.
    hits_upper_bound = max(1,math.ceil(session.max_hp()/raw_incoming))
    return {'raid_boss':ident, 'players_assumed_identical':count,
        'base_hp':int(template['max_hp']), 'adaptive_hp':max_hp,
        'base_autoattack_dps_one':dps_per_player, 'party_autoattack_dps':party_dps,
        'autoattack_seconds_no_enemy_healing':max_hp/party_dps,
        'maximum_base_hits_before_fall':hits_upper_bound}
