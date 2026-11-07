# -*- coding: utf-8 -*-
"""Bilans obrazen AoE rajdow 26–35 dla 1–6 graczy; tylko staging v106.

Nie leczy bohaterow ani bossow, nie zmienia ciosu gracza, exp, skladnikow,
questow czy mozliwosci wejscia. Zwykle obrazenia sa w pelni losowane,
liczone przez obrone, guard, klasy i rasy, a dopiero wynikowy cios zostaje
ograniczony do bezpiecznego budzetu na akcje jednego bossa. Mechaniki
specjalne i statusy nadal moga zadawac osobne obrazenia.
"""
from __future__ import annotations
import os

def cap_raid_incoming_v106(session, mob, template, incoming):
    incoming = max(1, int(incoming))
    if os.getenv('SOULBOUND_V106_STAGING') != '1':
        return incoming
    from systems.v106_raid_combat_dps import is_v106_raid_boss
    from data.rooms import ROOMS
    if not is_v106_raid_boss(mob,template,ROOMS.get(str(getattr(mob,'room_id','')),{})):
        return incoming
    party_size = int(getattr(mob,'adaptive_party_size_v11330',1) or 1)
    if not 1 <= party_size <= 6:
        return incoming
    c=getattr(session,'character',None)
    required = int(template.get('v106_authored_boss_stage') or 0)
    if c is None or int(getattr(c,'soul_level',0) or 0)*100 < required*95:
        return incoming  # postac mocno ponizej poziomu rajdu
    hp = max(1, int(session.max_hp()))
    # 3% max HP na zwykly cios AoE; bez darmowego leczenia i bez
    # nieśmiertelności. Daje czas na naturalne ataki i wsparcie w druzynie.
    return min(incoming, max(1, (hp*3 + 99)//100))
