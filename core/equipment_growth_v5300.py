# -*- coding: utf-8 -*-
"""v53: editable post-800 requirements for infinite-depth equipment.

Pure rules shared by drop authoring and admin read-only previews. Historical
600-mastery Rezonans gear retains its requirement at the default cap of 800.
An administrator's explicit expansion of EQ cap unlocks staged requirements.
"""
from __future__ import annotations
from core import live_level_caps_v5200 as caps


def infinite_equipment_requirement(source_stage):
    stage=max(600, int(source_stage))
    eq=caps.cap('eq')
    mastery=caps.cap('bieglosc')
    # Compatibility: no migration of legacy, already earned Rezonans variants.
    if eq is not None and eq <= 800:
        return 600
    maximum_eq=caps.effective_number(eq)
    maximum_mastery=caps.effective_number(mastery)
    return max(600, min(stage, maximum_eq, maximum_mastery))


def stage_report(stage):
    stage=int(stage)
    req=infinite_equipment_requirement(stage)
    limit_eq=caps.cap('eq')
    mastery=caps.cap('bieglosc')
    notes=[]
    if limit_eq is not None and stage>limit_eq:notes.append('etap ponad limitem EQ')
    if mastery is not None and stage>mastery:notes.append('etap ponad biegłością klasy')
    if limit_eq is None or mastery is None:notes.append('obowiązuje techniczny próg 1 mld')
    return {'stage':stage,'required_mastery':req,'notes':tuple(notes)}
