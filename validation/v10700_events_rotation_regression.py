# -*- coding: utf-8 -*-
"""Real v107 event calendar and quest acceptance path regressions."""
from __future__ import annotations
from pathlib import Path
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from world.v10700_saga_events_calendar import (
    active_quest_ids,is_active,is_event,slot,until_next_window,until_active,
)


def run():
    count=0
    def ck(value,text):
        nonlocal count
        assert value,text
        count+=1
    all_ids=set()
    for hour in range(6):
        ids=active_quest_ids(hour*3600)
        ck(len(ids)==10,f'Expected 10 events per window {hour}')
        ck(len(set(ids))==10,'duplicate event within same window')
        ck(not set(ids)&all_ids,'event wrongly offered in two windows')
        all_ids.update(ids)
        for qid in ids:
            ck(is_active(qid,hour*3600),'event not active in its own window')
            ck(not is_active(qid,(hour+1)*3600),'event active too long')
    ck(len(all_ids)==60,'60 different events must rotate in 6 hours')
    ck(active_quest_ids(0)==active_quest_ids(6*3600),'six-hour cycle must repeat')
    ck(until_next_window(3600-1)==1,'end of UTC hour boundary')
    ck(until_next_window(3600)==3600,'start of UTC hour boundary')
    ck(until_active('v10700_saga_events_002',0)==3600,'next hour wait')
    ck(until_active('v10700_saga_events_001',0)==0,'active wait is zero')
    ck(until_active('v10700_saga_events_001',3600)==5*3600,'next rotation after five hours')
    ck(not is_event('v10700_saga_events_061'),'nonexisting event must not rotate')
    ck(not is_event('v10700_saga_events_001_bad'),'spoofed event ID')
    # Execute the actual `quest_lock_reasons` AST in an isolated fixture.
    # Importing all historical game session modules outside server.py triggers
    # unrelated catalogue-order assertions; this uses the REAL handler body.
    import ast
    import types
    from unittest.mock import patch
    tree=ast.parse((ROOT/'player/session_mixins/quest_offers.py').read_text(encoding='utf-8'))
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef)
             and node.name=='SessionQuestOffersMixin')
    fn=next(node for node in cls.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
            and node.name=='quest_lock_reasons')
    cls.body=[fn]
    section=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]))
    scope={'QUESTS':{'v10700_saga_events_001':{
        'name':'Test wydarzenia','v10700_event_rotation':True}},'NPCS':{}}
    exec(compile(section,str(ROOT/'player/session_mixins/quest_offers.py'),'exec'),scope)
    class DB:
        def quest(self,*_):return None
    class Session(scope['SessionQuestOffersMixin']):
        server=type('Server',(),{'db':DB()})()
        account_id=1
        character=type('Char',(),{'race':'Test','room_id':'start'})()
        def active_class_names(self):return ()
        def quest_completed(self,*_):return True
    fake={}
    for modname,member,value in (
        ('systems.live_olc29_creation','quest_choice_text',lambda *_:''),
        ('systems.live_olc26_world','conflicting_quests',lambda *_:()),
        ('systems.live_olc17_quest_dependencies','quest_requirements',lambda *_:()),
    ):
        module=types.ModuleType(modname)
        setattr(module,member,value)
        fake[modname]=module
    qid='v10700_saga_events_001'
    with patch.dict(sys.modules,fake):
        with patch('world.v10700_saga_events_calendar.time.time',return_value=3600):
            reasons=Session().quest_lock_reasons(qid)
            ck(any('nieaktywne' in text for text in reasons),'inactive event must block real accept flow')
        with patch('world.v10700_saga_events_calendar.time.time',return_value=0):
            reasons=Session().quest_lock_reasons(qid)
            ck(not any('nieaktywne' in text for text in reasons),'active event blocked')
        scope['QUESTS']['v10700_saga_events_061']={'name':'bad','v10700_event_rotation':True}
        reasons=Session().quest_lock_reasons('v10700_saga_events_061')
        ck(any('nieprawidłowy' in text for text in reasons),'invalid admin event must be rejected')
    return count

if __name__=='__main__':print('V107 WYDARZENIA - KALENDARZ I PRZYJECIE:',run(),'PASS',flush=True)
