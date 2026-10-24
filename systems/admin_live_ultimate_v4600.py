# -*- coding: utf-8 -*-
"""v46: single `admin live` front-end for *isolated model* party and OLC checks.

No live combat callbacks, true character inventory, reward processing, world
spawning, SQL or publication. A staged quest fix is never published here.
"""
from __future__ import annotations
import copy
from types import SimpleNamespace
from data.quests import QUESTS
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from systems.admin_guardian6_v4000 import _signals, _combined, _matching_page
from systems.admin_guardian11_v4500 import _arena, _class_name, _turn
from systems.admin_guardian9_v4300 import _sync_actor, _draft_page
from systems.admin_guardian5_v3900 import _quest_rewards, _quest_compare
from systems.live_quest_olc_v1209 import parse_quest_edit
from world.uoss_superboss_runtime import superboss_healing_blocked_v11179

MAX_MEMBERS=4  # leader + 4 test members
MAX_TURNS=12
PAGE_SIZE=8
HELP={
 '1':('ADMIN LIVE ULTIMATE 1/3: arena pomoc; arena start ID HP ATAK; '
       'arena druzyna dodaj KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM; '
       'arena druzyna sklad; arena druzyna skille NUMER [STRONA]; '
       'arena druzyna skill NUMER ID POTWIERDZAM; '
       'Druzyna to prywatny model, nie rzeczywiste PvE 1:1.'),
 '2':('ADMIN LIVE ULTIMATE 2/3: arena druzyna prognoza TURY; '
       'arena druzyna tury TURY POTWIERDZAM; '
       'arena druzyna usun NUMER POTWIERDZAM; '
       'arena druzyna wyczysc POTWIERDZAM. '
       'Bez nagrod, zuzycia prawdziwej many lub SQLite. '
       'Stare admin live arena pozostaje.'),
 '3':('ADMIN LIVE ULTIMATE 3/3: questy karta ID; '
       'questy szukaj FRAGMENT [STRONA]; '
       'questy napraw plan FRAGMENT [STRONA]; '
       'questy napraw zatwierdz POTWIERDZAM; '
       'questy napraw cofnij POTWIERDZAM; '
       'questy draft [STRONA]; admin live sprawdz; '
       'admin live porownaj; admin live aktywuj POTWIERDZAM. '
       'Naprawy tylko DRAFT, nigdy automatyczna publikacja.'),
}

def _int(raw,low,high,description='liczba'):
    text=str(raw)
    if not text.isascii() or not text.isdecimal() or len(text)>16:
        raise ValueError(f'{description}: wpisz liczbe calkowita {low}-{high}.')
    n=int(text)
    if n<low or n>high:raise ValueError(f'{description}: zakres {low}-{high}.')
    return n

def _party(state):return state.setdefault('_adminlive46_party',[])

def _member(session, index):
    party=_party(_arena(session))
    i=_int(index,1,len(party),'numer postaci')-1
    return party[i]

def _member_skill(member,ident):
    rows=CLASS_SKILLS[member['class']]
    row=next((v for v in rows if v.get('id')==ident and int(v.get('unlock',1) or 1)<=member['mastery']),None)
    if row is None:raise ValueError('Brak skilla lub nieodblokowany na tej bieglosci.')
    kind=str(row.get('kind',''))
    if kind not in ('damage','heal'):
        raise ValueError('Ten skill wymaga pelnego silnika; LAB nie zgaduje jego efektu.')
    cost=effective_skill_mana_cost(row,member['class'])
    if cost<0 or cost>10**12:raise ValueError('Nieprawidlowy koszt many skilla.')
    mult=float(row.get('mult',1) or 1)
    if not 0<=mult<=10**6:raise ValueError('Nieprawidlowy mnoznik skilla.')
    return row,cost,mult

def _add_party(session,parts):
    if len(parts)!=6 or parts[-1]!='POTWIERDZAM':
        raise ValueError('druzyna dodaj KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM.')
    cl=_class_name(parts[0])
    if cl is None:raise ValueError('Nieznana klasa. Wpisz nazwe jednej z 22 klas.')
    from core.live_level_caps_v5200 import cap, effective_number
    mastery=_int(parts[1],1,effective_number(cap('bieglosc')),'bieglosc')
    hp=_int(parts[2],1,10**12,'HP')
    attack=_int(parts[3],0,10**12,'atak')
    mana=_int(parts[4],0,10**12,'mana')
    party=_party(_arena(session))
    if len(party)>=MAX_MEMBERS:raise ValueError('Limit testowy: 4 pomocnikow + lider. W normalnej grze to nie limit.')
    party.append({'class':cl,'mastery':mastery,'hp':hp,'attack':attack,'mana':mana,'max_mana':mana,'skill':None})
    return f'ARENA DRUZYNA: dodano {len(party)}. {cl}, bieg. {mastery}, HP {hp}, atak {attack}, mana {mana}. Tylko model LAB.'

def _party_status(session):
    state=_arena(session); p=_party(state)
    if not p:return 'ARENA DRUZYNA: tylko lider; dodaj do czterech klas. Brak rzeczywistych graczy.'
    return 'ARENA DRUZYNA: lider plus '+str(len(p))+' testowych postaci. '+ '; '.join(
        f'{i}. {m["class"]} bieg {m["mastery"]}, HP {m["hp"]}, ATK {m["attack"]}, MP {m["mana"]}/{m["max_mana"]}, skill {m["skill"] or "auto"}'
        for i,m in enumerate(p,1)) + '. Bez produkcyjnej druzyny.'

def _party_skills(session,index,page='1'):
    m=_member(session,index)
    rows=[x for x in CLASS_SKILLS[m['class']] if int(x.get('unlock',1) or 1)<=m['mastery'] and x.get('kind') in ('damage','heal')]
    p=_int(page,1,max(1,(len(rows)+PAGE_SIZE-1)//PAGE_SIZE),'strona')
    selected=rows[(p-1)*PAGE_SIZE:p*PAGE_SIZE]
    return f'DRUZYNA SKILLE {index} strona {p}/{max(1,(len(rows)+7)//8)}: '+('; '.join(
        f'{r["id"]} {r.get("name",r["id"])} {r.get("kind")}, MP {effective_skill_mana_cost(r,m["class"])}' for r in selected) or 'brak')+'.'

def _party_one_turn(detached):
    state=_arena(detached)
    if state['finished']:raise ValueError('Arena zakonczona.')
    _turn(detached,'atak','boss')  # actual *model* leader turn, detached effects and LAB RNG
    state=_arena(detached)
    log=[]
    # Explicit simple, documented allies model. Does not invoke production party hooks.
    for index,member in enumerate(_party(state),1):
        if state['finished']:break
        if member['hp']<=0:continue
        ident=member.get('skill')
        if ident:
            row,cost,mult=_member_skill(member,ident)
            if cost>member['mana']:
                log.append(f'{index} brak MP; atak zwykly')
                kind='damage';mult=1.0
            else:
                member['mana']-=cost;kind=row['kind']
        else:kind='damage';mult=1.0
        if kind=='heal':
            if superboss_healing_blocked_v11179(state['actor8']):
                log.append(f'{index} leczenie zablokowane UOSS')
            else:
                value=min(max(0,state['hero_max']-state['hero_hp']),max(1,int(member['attack']*mult)))
                state['hero_hp']+=value
                _sync_actor(state)
                log.append(f'{index} leczenie MODELOWE +{value}')
        else:
            dealt=min(state['boss'].hp, max(0,int(member['attack']*mult)))
            state['boss'].hp-=dealt;state['total_dealt']+=dealt
            log.append(f'{index} atak MODELOWY {dealt}')
            if state['boss'].hp<=0:
                state['boss'].alive=False;state['finished']=True
                break
    if log:
        state['notes'].append(f'ARENA DRUZYNA tura {state["round"]}: '+', '.join(log)[:360])
        state['notes']=state['notes'][-24:]
    return log

def _run_party(session,count,preview):
    turns=_int(count,1,MAX_TURNS,'tury')
    current=_arena(session)
    if current['finished']:raise ValueError('Arena zakonczona.')
    if not _party(current):raise ValueError('Najpierw dodaj co najmniej jedna testowa postac.')
    copy_session=SimpleNamespace(guardian7_lab=copy.deepcopy(current))
    done=0;actions=[]
    for _ in range(turns):
        if copy_session.guardian7_lab['finished']:break
        actions+=_party_one_turn(copy_session)
        done+=1
    result=copy_session.guardian7_lab
    if not preview:
        session.guardian7_lab=result  # transaction-like single swap, no partial state
    return (f'ARENA DRUZYNA {"PROGNOZA" if preview else "TURY"} {done}/{turns}; '
            f'boss HP {result["boss"].hp}, lider HP {result["hero_hp"]}, '
            f'obrazenia zadane {result["total_dealt"]}, otrzymane {result["total_taken"]}; '
            f'akcje testowe {len(actions)}. '
            +('Bez zmian biezacej areny i RNG.' if preview else 'Zmieniono tylko prywatna arene.')
            +' Model pomocnikow, nie pelne PvE 1:1.')

def _quest_card(service,qid):
    if qid not in _combined(service):raise ValueError('Nieznany ID questa; uzyj questy szukaj.')
    base=_combined(service)[qid]
    patch=service.draft.get('quest_edits',{}).get(qid,{})
    active=service.active.get('quest_edits',{}).get(qid,{})
    proposed=dict(base);proposed.update(patch)
    signal=_signals(service,qid,base)
    return (f'QUEST KARTA {qid}: {str(proposed.get("name",qid))[:65]}; '
        f'typ {proposed.get("kind")}; cel {proposed.get("target")}; '
        f'wymagane {proposed.get("needed")}; sygnaly {len(signal)} '
        f'[{", ".join(signal[:3]) or "brak oczywistych"}]; '
        f'AKTYWNE pola {len(active)}, DRAFT pola {len(patch)}. '
        'Zobacz: admin live questy nagrody ID / porownaj ID. Bez zmian.')

def _quest_find(service,phrase,page):
    rows,total,p=_matching_page(service,phrase,page)
    return f'QUEST SZUKAJ: {total} wynikow, strona {p}/{max(1,(total+11)//12)}: '+('; '.join(
        f'{id} ({str(q.get("name",id))[:55]})' for id,q in rows) or 'brak')+'.'

def _safe_fix_candidates(service,phrase,page):
    rows,total,p=_matching_page(service,phrase,page)
    changes={};flagged=[]
    for qid,base in rows:
        errors=_signals(service,qid,base)
        if errors:flagged.append((qid,errors))
        # Do not guess mob/item/quest IDs. Only negative/zero `needed` where
        # *all* other referential checks succeeded, and only after confirmation.
        if len(changes)>=8 or not errors or errors!=['needed ponizej 1']:
            continue
        try:
            f,value=parse_quest_edit('needed','1')
        except ValueError:continue
        changes[qid]={f:value}
    return rows,total,p,changes,flagged

def _preview_repairs(session,service,phrase,page):
    rows,total,p,changes,flagged=_safe_fix_candidates(service,phrase,page)
    candidate=copy.deepcopy(service.draft)
    for qid,patch in changes.items():
        candidate['quest_edits'].setdefault(qid,{}).update(patch)
    service.validate(candidate)
    # Guard stale operations: one preview can be committed only if OLC has not
    # changed, including the currently published content.
    session.adminlive46_plan=(copy.deepcopy(service.draft),copy.deepcopy(service.active),copy.deepcopy(candidate),tuple(changes))
    return (f'QUEST NAPRAW PLAN: {total} dopasowan, strona {p}; '
       f'problematyczne na stronie {len(flagged)}, mozliwe proste poprawki {len(changes)} '
       f'[{", ".join(changes) or "brak"}]. '
       'Wyłącznie needed ponizej 1 -> 1; brakujacych ID nie zgadujemy. '
       'To zmieni wymagania przyszlych oddan questa, sprawdz kazdy ID. '
       'Bez zmian. Potwierdz: admin live questy napraw zatwierdz POTWIERDZAM.')

def _commit_repairs(session,service):
    plan=getattr(session,'adminlive46_plan',None)
    if not plan:raise ValueError('Najpierw zrob: questy napraw plan FRAGMENT [STRONA].')
    before,active,after,ids=plan
    if not ids:raise ValueError('Brak bezpiecznych poprawek w planie.')
    if service.draft!=before or service.active!=active:raise ValueError('DRAFT lub publikacja zmienily sie. Utworz plan od nowa.')
    service.validate(after)
    session.adminlive46_undo=(copy.deepcopy(before),copy.deepcopy(after),copy.deepcopy(active))
    service.draft=copy.deepcopy(after)
    session.adminlive46_plan=None
    return (f'QUEST NAPRAW DRAFT: {len(ids)} questow [{", ".join(ids)}]. '
        'Tylko DRAFT. Postep graczy bez zmian. '
        'Sprawdz: admin live sprawdz, porownaj. '
        'Publikacja osobno: admin live aktywuj POTWIERDZAM.')

def _undo_repairs(session,service):
    saved=getattr(session,'adminlive46_undo',None)
    if not saved:raise ValueError('Nie ma bezpiecznej zmiany do cofniecia.')
    before,after,active=saved
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT lub publikacja zmienily sie od naprawy. Nie cofam obcych zmian.')
    # Restore the exact prior private DRAFT even if it was invalid: that is
    # precisely why the repair was planned. Do not publish or write SQLite.
    service.draft=copy.deepcopy(before)
    session.adminlive46_undo=None
    session.adminlive46_plan=None
    return 'QUEST NAPRAW COFNIETO: przywrocono poprzedni DRAFT. Bez zmian na serwerze gry.'

async def dispatch_live_ultimate(session,group,raw):
    """Return True when a v46 command was handled; old commands fall through."""
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    pieces=str(raw or '').split()
    if group=='pomoc':
        if len(pieces)!=1 or pieces[0] not in HELP:
            await session.send('ADMIN LIVE POMOC: dostepne strony 1, 2 i 3.')
        else:await session.send(HELP[pieces[0]])
        return True
    try:
        if group=='arena' and pieces and pieces[0].casefold()=='druzyna':
            sub=pieces[1].casefold() if len(pieces)>1 else ''
            if sub=='dodaj':
                if len(pieces)!=8:raise ValueError('druzyna dodaj KLASA BIEGLOSC HP ATAK MANA POTWIERDZAM')
                message=_add_party(session,pieces[2:])
            elif sub=='sklad' and len(pieces)==2:message=_party_status(session)
            elif sub=='skille' and len(pieces) in (3,4):
                message=_party_skills(session,pieces[2],pieces[3] if len(pieces)==4 else '1')
            elif sub=='skill' and len(pieces)==5 and pieces[4]=='POTWIERDZAM':
                m=_member(session,pieces[2]);_member_skill(m,pieces[3]);m['skill']=pieces[3]
                message=f'ARENA DRUZYNA: zapisano tylko testowy skill dla postaci {pieces[2]}.'
            elif sub=='usun' and len(pieces)==4 and pieces[3]=='POTWIERDZAM':
                party=_party(_arena(session));i=_int(pieces[2],1,len(party))-1
                del party[i];message='ARENA DRUZYNA: usunieto postac testowa.'
            elif sub=='wyczysc' and len(pieces)==3 and pieces[2]=='POTWIERDZAM':
                _party(_arena(session)).clear();message='ARENA DRUZYNA: usunieto sklad testowy.'
            elif sub=='prognoza' and len(pieces)==3:message=_run_party(session,pieces[2],True)
            elif sub=='tury' and len(pieces)==4 and pieces[3]=='POTWIERDZAM':
                message=_run_party(session,pieces[2],False)
            else:raise ValueError('Wpisz admin live pomoc 1/2: druzyna dodaj/sklad/skille/skill/prognoza/tury/usun/wyczysc.')
            await session.send(message);return True
        if group in ('questy','zadania') and pieces:
            sub=pieces[0].casefold();service=session.server.live_content_v1204
            if sub=='karta' and len(pieces)==2:message=_quest_card(service,pieces[1])
            elif sub=='szukaj' and len(pieces) in (2,3):message=_quest_find(service,pieces[1],pieces[2] if len(pieces)==3 else '1')
            elif sub=='napraw':
                op=pieces[1].casefold() if len(pieces)>1 else ''
                if op=='plan' and len(pieces) in (3,4):
                    message=_preview_repairs(session,service,pieces[2],pieces[3] if len(pieces)==4 else '1')
                elif op=='zatwierdz' and pieces[2:]==['POTWIERDZAM']:
                    message=_commit_repairs(session,service)
                elif op=='cofnij' and pieces[2:]==['POTWIERDZAM']:
                    message=_undo_repairs(session,service)
                else:raise ValueError('Questy napraw plan FRAZA [STRONA] / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM.')
            else:return False
            await session.send(message);return True
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        await session.send('ADMIN LIVE: '+str(exc)[:350]);return True
    return False
