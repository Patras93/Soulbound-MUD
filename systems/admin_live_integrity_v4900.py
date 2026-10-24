# -*- coding: utf-8 -*-
"""Admin Live v49: conservative quest integrity audit and inert LAB trace.

Read-only inspections; references with legacy aliases are warnings, never a
mandate to change published content. Absolutely no SQL writes or quest awards.
"""
from __future__ import annotations
import copy
from collections import Counter
from types import SimpleNamespace
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from systems.admin_live_expansion_v4800 import KINDS, _page
from systems.admin_guardian6_v4000 import _combined, _requirements
from systems.admin_guardian11_v4500 import _arena
from systems.admin_live_ultimate_v4600 import _party, _party_one_turn, _int

HELP_6 = ('ADMIN LIVE POMOC 6/6: questy bledy [STRONA] - wszystkie potencjalne problemy; '
          'questy bledytyp TYP [STRONA] - tylko wskazany typ; '
          'questy sprawdz ID - szczegoly pewnych bledow i ostrzezen; '
          'questy lancuch ID - wymagane poprzednie questy; '
          'arena druzyna raport - sklad i obecny stan LAB; '
          'arena druzyna przebieg TURY - kroki symulacji bez zmian (1-12). '
          'Brak automatycznych poprawek, nagrod, zapisu SQLite i publikacji OLC.')

def _effective(service):
    base=_combined(service)
    active=service.active.get('quest_edits',{})
    draft=service.draft.get('quest_edits',{})
    # DRAFT is a full snapshot, not a delta over active edits.
    result={}
    for key,record in base.items():
        q=dict(record)
        changes=draft.get(key, active.get(key,{}))
        q.update(changes)
        result[key]=q
    return result

def _integer(value):
    if isinstance(value,bool) or value is None: return None
    if isinstance(value,int):return value
    if isinstance(value,str) and value.isascii() and len(value.strip())<=24 and value.strip().lstrip('-').isdigit():
        return int(value)
    return None

def _issues(qid,q,catalog):
    """Return unambiguous structural errors and cautious hints separately."""
    errors=[];hints=[]
    kind=str(q.get('kind',''))
    positive_needed={
      'collect','collect_category','collect_distinct_category','collect_resource',
      'collect_resource_set','craft_set','kill','party_contract','profession_action'
    }
    if kind in positive_needed:
        n=_integer(q.get('needed'))
        if n is None:errors.append('needed: nieprawidlowa liczba')
        elif n<1:errors.append('needed: mniej niz 1')
    for name in ('reward_silver','reward_gold','reward_mithril','reward_profession_xp',
                 'reward_tool_xp','reward_stat_xp','reward_stat_strength',
                 'reward_stat_dexterity','reward_stat_constitution',
                 'reward_stat_intelligence','reward_stat_willpower','reward_stat_charisma',
                 'olc_reward_stat_xp','olc_reward_stat_strength','olc_reward_stat_dexterity',
                 'olc_reward_stat_constitution','olc_reward_stat_intelligence',
                 'olc_reward_stat_willpower','olc_reward_stat_charisma',
                 'olc_reward_xp','olc_reward_soul_xp','olc_reward_class_xp'):
        if name not in q:continue
        n=_integer(q[name])
        if n is None:errors.append(name+': nieprawidlowa liczba')
        elif n<0:errors.append(name+': wartosc ujemna')
    if 'repeat_cooldown' in q:
        n=_integer(q['repeat_cooldown'])
        if n is None or n<0:errors.append('repeat_cooldown: niepoprawny')
    req=q.get('requires_quests')
    if req is not None and not isinstance(req,(list,tuple)):
        errors.append('requires_quests: wymagana lista')
    for dep in _requirements(q):
        if dep==qid:errors.append('zaleznosc do siebie')
        elif dep not in catalog:errors.append('brak quest ID '+dep[:48])
    if kind in ('kill','collect','world_boss','legendary_rare'):
        target=q.get('target')
        if not isinstance(target,str) or not target:
            hints.append('cel nieustalony: sprawdz definicje i aliasy')
        elif kind=='collect' and target not in ITEMS:
            hints.append('cel collect poza statycznymi ITEMS (moze byc OLC/crafting)')
        elif kind in ('kill','world_boss','legendary_rare') and target not in MOB_TEMPLATES and target!='*':
            hints.append('cel poza statycznymi mobami (sprawdz quest_target/alias)')
    if kind=='deliver_npc' and not (q.get('target_npc') or q.get('target')):
        hints.append('brak jawnego celu NPC; moze byc sterowany fabula')
    if kind=='collect_resource_set':
        vals=q.get('resource_targets')
        if vals is not None:
            if not isinstance(vals,dict):errors.append('resource_targets: wymagana mapa')
            elif any(_integer(v) is None or _integer(v)<1 for v in vals.values()):
                errors.append('resource_targets: niepoprawna ilosc')
    if kind not in KINDS and kind!='multi_objective':
        hints.append('niestandardowy typ - sprawdz handler postepu')
    items=q.get('reward_items')
    if items is not None:
        if not isinstance(items,dict): errors.append('reward_items: wymagana mapa')
        elif any(_integer(x) is None or _integer(x)<0 for x in items.values()):
            errors.append('reward_items: niepoprawna ilosc')
    return errors[:12],hints[:6]

def _problem_rows(service,kind=None):
    catalog=_effective(service)
    if kind and kind not in KINDS and kind!='multi_objective':
        raise ValueError('Nieznany typ. Uzyj admin live questy typy.')
    rows=[];count=0
    for qid,record in sorted(catalog.items()):
        if kind and str(record.get('kind'))!=kind:continue
        count+=1
        err,warn=_issues(qid,record,catalog)
        if err or warn:rows.append((qid,err,warn))
    return rows,count

def _problems(service,page='1',kind=None):
    rows,total=_problem_rows(service,kind)
    p,pages=_page(page,len(rows))
    found=rows[(p-1)*8:p*8]
    rendered=[]
    for qid,err,warn in found:
        rendered.append(f'{qid}: pewne {len(err)} [{", ".join(err[:2]) or "brak"}], '
                        f'sygnaly {len(warn)} [{", ".join(warn[:1]) or "brak"}]')
    return (f'QUEST BLEDY {kind or "WSZYSTKIE"}: przejrzano {total}, z sygnalami {len(rows)}, '
           f'strona {p}/{pages}. '+('; '.join(rendered) or 'Brak wynikow na stronie.')+
           ' Pewne = nieprawidlowe pola lub ID; sygnaly = wymagaja sprawdzenia, nie dowod bledu. '
           'Bez zmian; edycja tylko admin live edytuj quest ID POLE | WARTOSC.')

def _one(service,qid):
    catalog=_effective(service)
    if qid not in catalog: raise ValueError('Nieznane ID; szukaj przez admin live questy szukaj.')
    q=catalog[qid];errors,warnings=_issues(qid,q,catalog)
    changes=service.draft.get('quest_edits',{}).get(qid,{})
    active=service.active.get('quest_edits',{}).get(qid,{})
    return (f'QUEST SPRAWDZ {qid}: {str(q.get("name",qid))[:50]}, typ {q.get("kind")}; '
            f'pewne {len(errors)}: {"; ".join(errors) or "brak"}; '
            f'ostroznosciowe {len(warnings)}: {"; ".join(warnings) or "brak"}; '
            f'ACTIVE {len(active)} pol, DRAFT {len(changes)} pol. '
            'Statyczna kontrola, nie potwierdza ukonczenia w grze. Zero zmian.')

def _chain(service,qid):
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Nieznane ID questa.')
    output=[];errors=[];seen=set()
    def walk(key,path):
        if len(seen)>=120:return
        seen.add(key)
        for req in _requirements(catalog[key]):
            if req not in catalog:
                errors.append(f'{key}->{req}: brak ID')
            elif req in path:
                errors.append('cykl: '+' -> '.join((path+(req,))[-8:]))
            else:
                output.append(f'{key} wymaga {req}')
                if req not in seen and len(path)<12:walk(req,path+(req,))
    walk(qid,(qid,))
    return (f'QUEST LANCUCH {qid}: odwiedzone {len(seen)}, relacje {len(output)}, '
            f'problemy {len(errors)}; '+('; '.join((errors+output)[:10]) or 'brak zaleznosci')+
            '. Limit kontroli: 120 questow/12 poziomow; tylko odczyt.')

def _party_report(session):
    state=_arena(session)
    members=_party(state)
    body='; '.join(f'{i}: {m["class"]} bieg {m["mastery"]}, '
                   f'HP {m["hp"]}, MP {m["mana"]}, skill {m.get("skill") or "atak"}'
                   for i,m in enumerate(members,1)) or 'brak'
    return (f'ARENA DRUZYNA RAPORT: boss {state["name"]}, '
            f'HP {state["boss"].hp}/{state["boss"].max_hp}; '
            f'lider HP {state["hero_hp"]}/{state["hero_max"]}, '
            f'tura {state["round"]}; pomocnicy {len(members)}: {body}. '
            'Tylko model LAB; bez zmian.')

def _party_trace(session,count):
    turns=_int(count,1,12,'tury')
    state=_arena(session)
    if state['finished']:raise ValueError('Arena juz zakonczona.')
    if not _party(state):raise ValueError('Brak testowych postaci w druzynie.')
    replica=SimpleNamespace(guardian7_lab=copy.deepcopy(state))
    report=[]
    for _ in range(turns):
        s=replica.guardian7_lab
        if s['finished']:break
        before=(s['boss'].hp,s['hero_hp'])
        actions=_party_one_turn(replica)
        after=replica.guardian7_lab
        report.append(f'{after["round"]}: boss {before[0]}->{after["boss"].hp}, '
                      f'lider {before[1]}->{after["hero_hp"]}, pomocnicy akcje {len(actions)}')
    return (f'ARENA DRUZYNA PRZEBIEG {len(report)}/{turns}: '
            +'; '.join(report)+'; bez zmian areny/RNG/SQLite. '
             'Model LAB - NIE produkcyjna walka 1:1.')

async def dispatch_v49(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    args=str(raw or '').split()
    try:
        if group=='pomoc' and args==['6']:message=HELP_6
        elif group in ('questy','zadania') and args:
            service=session.server.live_content_v1204
            if args[0]=='bledy' and len(args) in (1,2):
                message=_problems(service,args[1] if len(args)==2 else '1')
            elif args[0]=='bledytyp' and len(args) in (2,3):
                message=_problems(service,args[2] if len(args)==3 else '1',args[1])
            elif args[0]=='sprawdz' and len(args)==2:message=_one(service,args[1])
            elif args[0]=='lancuch' and len(args)==2:message=_chain(service,args[1])
            else:return False
        elif group=='arena' and args[:2]==['druzyna','raport'] and len(args)==2:
            message=_party_report(session)
        elif group=='arena' and args[:2]==['druzyna','przebieg'] and len(args)==3:
            message=_party_trace(session,args[2])
        else:return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        message='ADMIN LIVE: '+str(exc)[:280]
    await session.send(message)
    return True
