# -*- coding: utf-8 -*-
"""Current release-only integrity inspection of the fully assembled world.

This replaces a historical advisory function whose host module is excluded
from the production runtime. It never asserts legacy 14-class/job counts and
never suppresses a real violation in the current catalogs.
"""
from __future__ import annotations
from collections import Counter


def audit_loaded_world(ns):
    errors=[]
    metrics={}
    registries=('ROOMS','ITEMS','MOB_TEMPLATES','QUESTS','NPCS',
                'SHOPS','CLASSES','CLASS_SKILLS','HELP_TOPICS')
    for name in registries:
        value=ns.get(name)
        if not value:
            errors.append(('empty_or_missing_catalog',name))
        else:
            metrics[name]=len(value)
    if errors:
        return {'error_count':len(errors),'warning_count':0,'errors':errors,
                'warnings':[],'metrics':metrics}
    rooms=ns['ROOMS']; quests=ns['QUESTS']; npcs=ns['NPCS']
    # The current game intentionally supports both generated levels and
    # genuinely named authored records; do not impose antique display-name
    # uniqueness on procedural variants.
    for name, table in (('rooms',rooms),('quests',quests),('npcs',npcs)):
        for key, value in table.items():
            if not isinstance(key,str) or not key.strip() or not isinstance(value,dict):
                errors.append(('bad_catalog_record',name,str(key)))
                continue
            if not str(value.get('name') or '').strip():
                errors.append(('missing_display_name',name,key))
    for room_id,room in rooms.items():
        if not isinstance(room,dict):continue
        if not isinstance(room.get('exits',{}),dict):
            errors.append(('invalid_exits',room_id))
    for quest_id,quest in quests.items():
        if not isinstance(quest,dict):continue
        if not str(quest.get('giver') or '').strip():
            errors.append(('missing_quest_giver',quest_id))
    # Current teacher help needs a real public route, not merely a catalog
    # entry that can only be reached with the internal topic ID.
    from systems.new_heroes_v900 import NEW_CLASSES
    from systems.content_registry import HELP_TOPICS
    from data.current_help import get_help_catalogs
    from storage.db_shared import normalize_lookup_text
    topics,aliases=get_help_catalogs()
    for row in NEW_CLASSES:
        name,_,_,_,slug,*_=row
        teacher=npcs.get('teacher_v900_'+slug)
        key=aliases.get(normalize_lookup_text(name))
        if not teacher or key not in topics or not any(
                ('Nauczyciel: '+teacher['name']) in str(line)
                for line in topics[key]):
            errors.append(('missing_teacher_help',name))
    return {'version':str(ns.get('VERSION','')),
            'checks':sum(metrics.values()), 'metrics':metrics,
            'error_count':len(errors),'warning_count':0,
            'errors':errors,'warnings':[]}
