# -*- coding: utf-8 -*-
"""v106: izolowana regresja prawdziwych metod ofert (AST z kodu v105+v106).

Bez startu serwera, portów TCP i baz danych. Testuje numerację, Strona 2,
Próby Elora, historię ukończeń oraz widoczność odnawialnych questów.
"""
from __future__ import annotations
import ast
import asyncio
import re
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from systems.quest_visibility_v10600 import (
    is_quest_offer_visible_v10600, filter_quest_offers_v10600,
)


def _method(file, name, globals_):
    """Uruchamia dokładnie istniejącą metodę źródłową bez importu serwera."""
    path=ROOT / 'player' / 'session_mixins' / file
    module=ast.parse(path.read_text(encoding='utf8'))
    cls=next(node for node in module.body if isinstance(node,ast.ClassDef) and
             any(isinstance(a,(ast.FunctionDef,ast.AsyncFunctionDef)) and a.name==name
                 for a in node.body))
    fn=next(f for f in cls.body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.name==name)
    fn.decorator_list=[]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec'),globals_)
    return globals_[name]


def run():
    checks=0
    def ck(flag,label):
        nonlocal checks
        if not flag:
            raise AssertionError('V106 QUEST LIST: '+label)
        checks+=1

    def q(name,repeatable=False,needed=1,tier=None):
        out={'name':name,'giver':'Mistrz Testowy','repeatable':repeatable,
             'description':'Zadanie demonstracyjne','kind':'kill','needed':needed,'reward_gold':20}
        if tier is not None:out['unlocks_soul_tier']=tier
        return out

    QUESTS={f'v10500_demo_hunt_{n:02d}':q(f'Polowanie {n}') for n in range(1,17)}
    QUESTS['repeat']=q('Godzinne',True)
    QUESTS['legacy_once']=q('Jednorazowe')
    QUESTS['legacy_repeat']=q('Powtarzalne',True)
    trial_ids={tier:f'trial_{tier}' for tier in range(1010,1110,10)}
    QUESTS.update({qid:q('Próba '+str(t),tier=t) for t,qid in trial_ids.items()})
    NPCS={
        'v10500_demo_npc_2':{'name':'Łowca Testowy','room':'v105_room',
                            'specialist_quests':tuple(f'v10500_demo_hunt_{n:02d}' for n in range(1,17))},
        'legacy':{'name':'Mistrz Testowy','room':'legacy_room',
                  'quest_chain':('legacy_once','legacy_repeat','repeat')},
        'priest_elor':{'name':'Kapłan Elor','room':'temple', 'specialist_quests':tuple(trial_ids.values())},
    }
    # Add the Elor trial names in order through giver lookup as in the real code.
    for tid in trial_ids.values(): QUESTS[tid]['giver']='Kapłan Elor'

    class DB:
        def __init__(self):self.rows={}
        def quest(self,account,qid):return self.rows.get(qid)
        def quest_rows(self,account):return [dict(row,quest_id=qid) for qid,row in self.rows.items()]
        def repeat_quest_seconds_remaining(self,*args):return 10
    db=DB()
    globals_={'QUESTS':QUESTS,'NPCS':NPCS,'re':re,
              'currency_reading_text':lambda coins,a,b:f'{coins} srebra',
              'v0190_quest_currency_reward':lambda quest:int(quest['reward_gold']),
              'find_by_name':lambda npcs,name:next(((nid,npc) for nid,npc in npcs.items()
                                               if name.lower() in npc['name'].lower()),None),
              'filter_quest_offers_v10600':filter_quest_offers_v10600,
              'QUEST_REPEAT_COOLDOWN_SECONDS':3600,
              'soul_trial_difficulty_band':lambda tier:'test'}
    class Probe:
        def __init__(self,room,db):
            self.server=SimpleNamespace(db=db)
            self.account_id=7
            self.character=SimpleNamespace(room_id=room,soul_tier=1000)
            self.quest_list_context=None
            self.messages=[]
        async def send(self,msg):self.messages.append(str(msg))
        def normalize_description_query(self,v):return str(v or '').strip().lower()
        def active_class_names(self):return {'wojownik'}
        def quest_offer_state(self,qid):return 'dostępne'
        def format_duration_short(self,s):return f'{s} s'
        def quest_is_available_to_accept_v099(self,qid):return True

    for filename,method in (
        ('quest_progress.py','quest_ids_for_npc'),
        ('quest_offers.py','local_quest_npcs'),
        ('quest_offers.py','show_npc_quest_offers'),
        ('quest_offers.py','quest_from_context'),
        ('quest_offers.py','direct_local_quest_for_number'),
        ('quest_offers.py','show_quest_npc_list'),
        ('quest_turnin.py','show_completed_quests'),
    ):
        setattr(Probe,method,_method(filename,method,globals_))

    ck(is_quest_offer_visible_v10600(q('x'),None),'nowe widoczne')
    ck(is_quest_offer_visible_v10600(q('x'),{'status':'active','completion_count':0}),'aktywne widoczne')
    ck(is_quest_offer_visible_v10600(q('x'),{'status':'active','completion_count':2}),'aktywne historycznie widoczne')
    ck(is_quest_offer_visible_v10600(q('x'),{'status':'abandoned','completion_count':0}),'porzucone widoczne')
    ck(is_quest_offer_visible_v10600(q('x'),{'status':'abandoned'}),'stary rekord bez completion_count')
    ck(not is_quest_offer_visible_v10600(q('x'),{'status':'completed','completion_count':1}),'jednorazowe ukończone ukryte')
    ck(not is_quest_offer_visible_v10600(q('x'),{'status':'abandoned','completion_count':1}),'historycznie jednorazowe ukryte')
    ck(is_quest_offer_visible_v10600(q('x',True),{'status':'completed','completion_count':30}),'odnawialne widoczne')

    v105=Probe('v105_room',db)
    npc=NPCS['v10500_demo_npc_2']
    ids=v105.quest_ids_for_npc('v10500_demo_npc_2',npc)
    ck(len(ids)==16,'v105 16 startowych ofert')
    first=ids[0]
    db.rows[first]={'status':'completed','completion_count':1,'completed_at':123}
    visible=v105.quest_ids_for_npc('v10500_demo_npc_2',npc)
    ck(visible==ids[1:],'ukończony pierwszy wypada z listy')

    async def scenario():
        got=await v105.show_npc_quest_offers('v10500_demo_npc_2',npc)
        ck(got==ids[1:11],'strona 1 po reindeksacji')
        ck('Strona 1 z 2' in v105.messages[0],'NVDA strona pierwsza')
        ck(not any(line.startswith(number+'. '+QUESTS[first]['name']+'.') for number in map(str,range(1,11)) for line in v105.messages),'nie mówi ukończonego')
        ck(v105.quest_list_context['quest_ids']==got,'kontekst ofert widocznych')
        v105.messages.clear()
        second=await v105.show_npc_quest_offers('v10500_demo_npc_2',npc,page_number=2)
        ck(second==ids[11:],'strona 2 wypełniona poprawnie')
        ck('Strona 2 z 2' in v105.messages[0],'NVDA strona druga')
        # Po odświeżeniu / ukończeniu, strona poza zakresem nie może
        # zostawić ostatniej listy i umożliwiać przyjęcia niewidocznego q.
        v105.messages.clear()
        beyond=await v105.show_npc_quest_offers('v10500_demo_npc_2',npc,page_number=3)
        ck(beyond==[] and v105.quest_list_context is None, 'błędna strona czyści kontekst')
        await v105.show_npc_quest_offers('v10500_demo_npc_2',npc,page_number=2)
        found,error=v105.quest_from_context('1')
        ck(found==ids[11] and error is None,'przyjmij 1 na stronie 2')
        v105.quest_list_context=None
        direct,npcid,err=v105.direct_local_quest_for_number('1')
        ck(direct==ids[1] and npcid=='v10500_demo_npc_2' and err is None,'przyjmij 1 bez listy')
        v105.messages.clear()
        await v105.show_completed_quests()
        ck(QUESTS[first]['name'] in '\n'.join(v105.messages),'historia ukończonych zachowana')
        ck(v105.quest_list_context['quest_ids']==[first],'numery historii nienaruszone')

        for qid in ids:db.rows[qid]={'status':'completed','completion_count':1,'completed_at':123}
        v105.messages.clear()
        ck(await v105.show_npc_quest_offers('v10500_demo_npc_2',npc)==[],'wszystkie ukończone => brak oferty')
        ck(v105.quest_list_context is None,'stary kontekst usunięty')
        ck('quest ukończone' in '\n'.join(v105.messages),'NVDA wskazuje historię')
        ck(not v105.local_quest_npcs(),'NPC bez nowych ofert')

        legacy=Probe('legacy_room',db)
        db.rows['legacy_once']={'status':'completed','completion_count':1,'completed_at':123}
        db.rows['legacy_repeat']={'status':'completed','completion_count':1,'completed_at':123}
        offered=legacy.quest_ids_for_npc('legacy',NPCS['legacy'])
        ck(offered==['legacy_repeat','repeat'],'legacy finished one-time hidden but repeatable stays')
        ck(await legacy.show_npc_quest_offers('legacy',NPCS['legacy'])==offered,'legacy NPC list consistent')
        direct,owner,err=legacy.direct_local_quest_for_number('1')
        ck(direct=='legacy_repeat' and owner=='legacy' and err is None,'legacy direct first visible')

        priest=Probe('temple',db)
        db.rows[trial_ids[1010]]={'status':'completed','completion_count':1,'completed_at':123}
        trial_page=list(trial_ids.values())
        offered=await priest.show_npc_quest_offers('priest_elor',NPCS['priest_elor'],quest_ids_override=trial_page)
        ck(offered==trial_page[1:],'Elor overridden page hides completed')
        ck(priest.quest_list_context['quest_ids']==trial_page[1:],'Elor context renumbered')
        found,error=priest.quest_from_context('1')
        ck(found==trial_ids[1020] and error is None,'Elor numer 1 to następna próba')
        # An explicitly requested page containing only done trials must not
        # leave the previous choice active.
        priest.messages.clear()
        ck(await priest.show_npc_quest_offers('priest_elor',NPCS['priest_elor'],quest_ids_override=[trial_ids[1010]])==[],
           'Elor completed-only page empty')
        ck(priest.quest_list_context is None,'Elor old context cleared')
        ck('quest ukończone' in '\n'.join(priest.messages),'Elor history message')

    asyncio.run(scenario())
    ck(QUESTS['legacy_once'].get('repeatable') is False,'definicja zadania bez zmian')
    ck(db.quest(7,first)['status']=='completed','SQLite / stan zadań bez modyfikacji')
    return checks


if __name__=='__main__':
    print('V106 QUEST LIST JEDNORAZOWE: '+str(run())+' PASS',flush=True)
