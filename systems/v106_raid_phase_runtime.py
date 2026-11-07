# -*- coding: utf-8 -*-
"""Bezpieczne fazy rajdów 26–35 v106 – tylko izolowany staging.

Nie zmienia HP ani mnożników walki; w kolejnych turach nie pomija
ważnych ogłoszeń faz, gdy obrażenia przekroczą kilka progów naraz.
"""
from __future__ import annotations
import os
import re

_RAID_BOSS = re.compile(r"^v10600_raid_(?:2[6-9]|3[0-5])_boss_[1-3]$")


def is_v106_raid_encounter(mob, template):
    if os.environ.get('SOULBOUND_V106_STAGING') != '1':
        return False
    template_id = str(getattr(mob, 'template_id', '') or '')
    # Standardowe v106 walki w stagingu zachowują bazowe autorskie HP.
    # Zachowujemy obsługę starszych wariantów __world_v0384, aby stan
    # istniejących odizolowanych testów pozostał jednoznaczny.
    base = str(template.get('base_template') or template_id) if isinstance(template, dict) else template_id
    if not _RAID_BOSS.fullmatch(base):
        return False
    if template_id != base and not (
        template_id.startswith(base + '__world_v0384_') and
        template.get('base_template') == base
    ):
        return False
    if str(getattr(mob, 'room_id', '') or '') != base.replace('_boss_', '_stage_'):
        return False
    return bool(isinstance(template, dict) and template.get('boss') and
                template.get('world_boss') and
                isinstance(template.get('olc_boss_phases'), list) and
                len(template['olc_boss_phases']) == 4)


def next_raid_phase_v106(mob, template, current, target):
    """Maksymalnie jeden nowy próg na turę; brak sztucznego leczenia/odradzania."""
    if is_v106_raid_encounter(mob, template):
        return min(int(target), int(current) + 1)
    return target


def reset_raid_phase_v106(mob, template):
    """Usuwa fazę poprzedniego podejścia dopiero przy autentycznym respawnie."""
    if not is_v106_raid_encounter(mob, template):
        return False
    mob.v1230_boss_phase = 0
    mob.v1230_phase_attack_multiplier = 1.0
    return True
