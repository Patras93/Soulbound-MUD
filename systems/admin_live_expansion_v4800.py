# -*- coding: utf-8 -*-
"""Admin Live v48: quest-type triage and isolated party scenario tools.

All quest operations are read-only. LAB runs on deep copies of private model
state and never invokes production combat, rewards, SQL, or world mutation.
"""
from __future__ import annotations
import copy
from collections import Counter
from types import SimpleNamespace
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS
from data.npcs import NPCS
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from systems.admin_guardian6_v4000 import _combined, _requirements
from systems.admin_live_ultimate_v4600 import _add_party, _party, _party_one_turn, _int
from systems.admin_guardian11_v4500 import _arena, _class_name, _turn

KINDS = (
  'collect','collect_category','collect_distinct_category','collect_resource',
  'collect_resource_set','craft_set','deliver_npc','discover_secret',
  'explore_frontier','kill','legendary_rare','mini_dungeon','party_contract',
  'profession_action','talk_class_teacher','talk_npc','world_boss','world_event'
)
PAGE=8
HELP_5=('ADMIN LIVE POMOC 5/5: questy typy [STRONA] (liczba questow 18 typow); '
        'questy typ NAZWA [STRONA] (ID i nazwa); questy diagnoza ID (pola i '
        'wskazowki diagnostyczne); arena druzyna klasy [STRONA] (22 klasy); '
        'arena druzyna gotowy KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM; '
        'arena druzyna porownaj TURY (z druzyna i bez, 1-12). '
        'Raporty bez zmian. Model LAB to NIE produkcyjna walka 1:1.')

def _page(raw,total):
    n=_int(raw,1,10000,'strona')
    pages=max(1,(total+PAGE-1)//PAGE)
    if n>pages: raise ValueError(f'Dostepne strony: 1-{pages}.')
    return n,pages

def _kinds(service,page='1'):
    catalog=_combined(service)
    counts=Counter(str(q.get('kind','brak')) for q in catalog.values())
    # Includes dynamically added OLC types as well as the 18 known kinds.
    names=list(KINDS)+sorted(k for k in counts if k not in KINDS)
    p,pages=_page(page,len(names))
    body='; '.join(f'{i}. {k}: {counts[k]}'
             for i,k in enumerate(names[(p-1)*PAGE:p*PAGE],(p-1)*PAGE+1))
    return (f'QUEST TYPY: {len(catalog)} questow, {len(names)} rodzajow; '
            f'strona {p}/{pages}. {body}. Bez zmian.')

def _kind_page(service,kind,page='1'):
    if not 1<=len(kind)<=48 or not kind.replace('_','').isalnum():
        raise ValueError('Wpisz nazwe typu questu, np. kill.')
    rows=sorted((qid,q) for qid,q in _combined(service).items()
                if str(q.get('kind','')).casefold()==kind.casefold())
    p,pages=_page(page,len(rows))
    body='; '.join(f'{qid} ({str(q.get("name",qid))[:55]})'
        for qid,q in rows[(p-1)*PAGE:p*PAGE]) or 'brak'
    return f'QUEST TYP {kind}: {len(rows)} wynikow, strona {p}/{pages}: {body}. Bez zmian.'

def _diagnose(service,qid):
    catalog=_combined(service)
    if qid not in catalog:
        raise ValueError('Nieznany ID questa. Wpisz: admin live questy szukaj FRAZA.')
    q=dict(catalog[qid]);q.update(service.active.get('quest_edits',{}).get(qid,{}));q.update(service.draft.get('quest_edits',{}).get(qid,{}))
    kind=str(q.get('kind','brak'));target=q.get('target')
    findings=[];advice=[]
    def note(condition,message):
        if condition: findings.append(message)
    required=('kill','collect','collect_category','collect_distinct_category',
              'collect_resource','collect_resource_set','craft_set','party_contract','profession_action')
    if kind in required and 'needed' in q:
        n=q.get('needed')
        try:
            if isinstance(n,bool) or int(n)<1: findings.append('needed powinno byc dodatnie')
        except (ValueError,TypeError,OverflowError):findings.append('needed nie jest poprawna liczba')
    if kind in ('kill','world_boss','legendary_rare') and target not in ('*',None,''):
        if not any(target==key or target==m.get('quest_target') for key,m in MOB_TEMPLATES.items()) and target not in service.draft.get('mobs',{}):
            findings.append('brak bezposredniego dopasowania moba w katalogu (moze byc alias)')
    if kind=='collect' and target not in ITEMS and target not in service.draft.get('items',{}):
        findings.append('brak ID przedmiotu w katalogu')
    if kind=='deliver_npc':
        item=q.get('quest_item');dest=q.get('target_npc')
        if item and item not in ITEMS and item not in service.draft.get('items',{}):
            findings.append('quest_item nieznany')
        if dest and dest not in NPCS and dest not in service.draft.get('npcs',{}):
            findings.append('target_npc nieznany')
    if kind=='collect_resource_set':
        values=q.get('resource_targets')
        if values is not None:
            if not isinstance(values,dict):findings.append('resource_targets nie jest slownikiem')
            elif any(not isinstance(n,int) or isinstance(n,bool) or n<1 for n in values.values()):
                findings.append('resource_targets: zla ilosc')
    for required_id in _requirements(q):
        if required_id==qid:findings.append('zaleznosc do samego siebie')
        elif required_id not in catalog:findings.append('brak wymaganego questa '+str(required_id)[:45])
    for money in ('reward_silver','reward_gold','reward_mithril'):
        amount=q.get(money)
        if amount is not None:
            try:
                if isinstance(amount,bool) or int(amount)<0: findings.append(money+': ujemna nagroda')
            except (TypeError,ValueError,OverflowError):findings.append(money+': nieprawidlowa liczba')
    if kind not in KINDS and kind!='multi_objective':findings.append('typ spoza katalogu 18 standardowych')
    if kind in ('talk_npc','talk_class_teacher','deliver_npc'):advice.append('sprawdz relacje i pokoj NPC')
    if kind in ('world_event','mini_dungeon','world_boss','legendary_rare'):advice.append('sprawdz wyzwalacz zdarzenia i fabule')
    if kind in ('collect_category','collect_distinct_category','collect_resource','profession_action'):
        advice.append('sprawdz zdarzenie postepu, nie tylko plecak')
    if kind in ('explore_frontier','discover_secret'):advice.append('sprawdz warunki odkrywania')
    if kind in ('kill','party_contract'):advice.append('sprawdz uznawanie zabicia i sklad druzyny')
    if kind in ('collect_resource_set','craft_set'):advice.append('sprawdz zestaw receptur/surowcow')
    if not advice:advice.append('sprawdz przez gracza przyjecie, postep i oddanie u NPC')
    return (f'QUEST DIAGNOZA {qid}: {str(q.get("name",qid))[:55]}; rodzaj {kind}; '
            f'cel {str(target)[:50]}; needed {str(q.get("needed","brak"))[:25]}; '
            f'sygnaly {len(findings)}: {"; ".join(findings[:6]) or "brak statycznych"}; '
            f'kontrola: {", ".join(advice[:2])}. '
            'Wynik to POSZLAKI, nie potwierdzenie wykonania; zero zmian. '
            'Poprawki wyłącznie przez admin live edytuj quest i DRAFT.')

def _class_page(page='1'):
    names=sorted(CLASS_SKILLS)
    p,pages=_page(page,len(names))
    return (f'ARENA KLASY: {len(names)} klas, strona {p}/{pages}: '
            +'; '.join(f'{i}. {name}' for i,name in enumerate(names[(p-1)*PAGE:p*PAGE],(p-1)*PAGE+1))
            +'. Wpisz: admin live arena druzyna gotowy KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM.')

def _ready_member(session,values):
    if len(values)!=6:raise ValueError('gotowy KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM.')
    from core.live_level_caps_v5200 import cap, effective_number
    cl=_class_name(values[0]);_int(values[1],1,effective_number(cap('bieglosc')),'bieglosc')
    if cl is None:raise ValueError('Nieznana klasa. Wpisz arena druzyna klasy.')
    # Compute entire new state on a private detached copy first; if input fails,
    # the original live LAB and its RNG remain byte-for-byte unchanged.
    current=_arena(session)
    cloned=SimpleNamespace(guardian7_lab=copy.deepcopy(current))
    text=_add_party(cloned,list(values))
    member=_party(cloned.guardian7_lab)[-1]
    choices=[row for row in CLASS_SKILLS[cl]
             if int(row.get('unlock',1) or 1)<=member['mastery']
             and row.get('kind')=='damage']
    choices.sort(key=lambda row:(effective_skill_mana_cost(row,cl),str(row.get('id',''))))
    member['skill']=choices[0]['id'] if choices else None
    session.guardian7_lab=cloned.guardian7_lab
    return text+' Wybrany skill modelowy: '+str(member['skill'] or 'zwykly atak')+'.'

def _party_compare(session,count):
    turns=_int(count,1,12,'tury')
    current=_arena(session)
    if current['finished']:raise ValueError('Arena zakonczona.')
    if not _party(current):raise ValueError('Dodaj testowego pomocnika przez arena druzyna gotowy.')
    summaries=[]
    for with_party in (False,True):
        clone=SimpleNamespace(guardian7_lab=copy.deepcopy(current))
        if not with_party: clone.guardian7_lab['_adminlive46_party']=[]
        done=0
        for _ in range(turns):
            if clone.guardian7_lab['finished']:break
            if with_party:_party_one_turn(clone)
            else:_turn(clone,'atak','boss')
            done+=1
        st=clone.guardian7_lab
        summaries.append((done,st['boss'].hp,st['hero_hp'],st['total_dealt']))
    solo,team=summaries
    return (f'ARENA POROWNANIE {turns} tur (ten sam stan i RNG): '
            f'BEZ druzyny tury {solo[0]}, boss HP {solo[1]}, lider HP {solo[2]}, obrazenia {solo[3]}; '
            f'Z druzyna tury {team[0]}, boss HP {team[1]}, lider HP {team[2]}, obrazenia {team[3]}. '
            'Model LAB; aktualna arena, RNG serwera i postacie bez zmian.')

async def dispatch_v48(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    args=str(raw or '').split()
    try:
        if group=='pomoc' and args==['5']:msg=HELP_5
        elif group in ('questy','zadania') and args:
            service=session.server.live_content_v1204
            if args[0]=='typy' and len(args) in (1,2):msg=_kinds(service,args[1] if len(args)==2 else '1')
            elif args[0]=='typ' and len(args) in (2,3):msg=_kind_page(service,args[1],args[2] if len(args)==3 else '1')
            elif args[0]=='diagnoza' and len(args)==2:msg=_diagnose(service,args[1])
            else:return False
        elif group=='arena' and len(args)>=2 and args[0:2]==['druzyna','klasy'] and len(args) in (2,3):
            msg=_class_page(args[2] if len(args)==3 else '1')
        elif group=='arena' and args[:2]==['druzyna','gotowy']:
            msg=_ready_member(session,args[2:])
        elif group=='arena' and args[:2]==['druzyna','porownaj'] and len(args)==3:
            msg=_party_compare(session,args[2])
        else:return False
    except (ValueError,TypeError,KeyError,OverflowError,AttributeError,ZeroDivisionError) as exc:
        msg='ADMIN LIVE: '+str(exc)[:250]
    await session.send(msg)
    return True
