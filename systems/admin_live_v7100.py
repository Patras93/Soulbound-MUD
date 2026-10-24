# -*- coding: utf-8 -*-
"""v71: owner-only extensions using existing authoritative OLC validators.

Never publishes or modifies active combat/quest rewards.  The UOSS 'coverage'
report is deliberately not a claim of 1:1 production simulation.
"""
from __future__ import annotations
import copy
from collections import Counter
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from core.classes_skills import CLASS_SKILLS
from core.live_level_caps_v5200 import current as current_caps
from systems.admin_live_integrity_v4900 import _effective,_issues
from systems.admin_guardian6_v4000 import _requirements
from systems.live_olc6_skill_editor import stage_existing_skill
from systems.live_olc4_boss_phases import eligible_boss, default_boss_phases

HELP=('ADMIN LIVE POMOC 29: arena uoss pokrycie - granice laboratorium i zrodla; '
      'questy automaty typy [STRONA] / questy automaty cykle [STRONA] - audyt 18 typow i zaleznosci; '
      'skill pakiet plan ID POLE | WARTOSC ; ID POLE | WARTOSC - 1-8 zmian; '
      'skill pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj; '
      'boss fazy podglad ID / boss fazy plan ID / boss fazy zatwierdz POTWIERDZAM / '
      'boss fazy cofnij POTWIERDZAM; limity reszta - audyt mechanicznych luk. '
      'Zmiany skilli i faz TYLKO w DRAFT, bez automatycznej publikacji. '
      'UOSS nie jest walka 1:1; skryptowani superbossowie sa chronieni.')


def _page(rows,raw='1',limit=6):
    if not isinstance(raw,str) or not raw.isascii() or not raw.isdecimal() or len(raw)>4:
        raise ValueError('Podaj numer strony 1..9999.')
    page=int(raw); pages=max(1,(len(rows)+limit-1)//limit)
    if not 1<=page<=pages:raise ValueError(f'Strony: 1..{pages}.')
    return page,pages,rows[(page-1)*limit:page*limit]


def arena_coverage():
    return ('ARENA UOSS POKRYCIE: odczyt zrodlowych zdolnosci i statusow TAK; '
        'modelowanie pasywow pomocnikow TAK; wybor zdolnosci na izolowanej kopii TAK; '
        'powtorzalne migawki i ziarno LAB TAK. '
        'IDENTYCZNA produkcyjna kolejka rund NIE; pelna losowosc spawn i AI NIE; '
        'wszystkie skutki prawdziwej smierci i obrazen NIE; produkcyjne nagrody NIE. '
        'Aby sprawdzic konkretna walke: arena start BOSS HP ATAK, potem '
        'arena uoss reguly 6, arena raport. Niczego nie zmieniono.')


def quest_kind_coverage(service,page='1'):
    catalog=_effective(service)
    kind_counts=Counter(str(q.get('kind','BRAK')) for q in catalog.values())
    counts=Counter()
    for qid,q in catalog.items():
        e,w=_issues(qid,q,catalog)
        if e or w:counts[str(q.get('kind','BRAK'))]+=1
    rows=[f'{k}: {n} questow, z sygnalami {counts[k]}' for k,n in sorted(kind_counts.items())]
    pg,pages,shown=_page(rows,page)
    return (f'QUEST TYPY POKRYCIE {pg}/{pages}: '+ '; '.join(shown)+
         f'. Typow wykrytych: {len(kind_counts)}, razem {len(catalog)}. '
         'Automat naprawia tylko jednoznaczne liczniki; inne cele, NPC i ID wymagaja jawnego planu. '
         'To audyt statyczny, nie dowod prawidlowego zaliczania questow.')


def quest_cycles(service,page='1'):
    catalog=_effective(service)
    graph={qid:tuple(dep for dep in _requirements(row) if dep in catalog)
           for qid,row in catalog.items()}
    color={}; stack=[]; found=set()
    def visit(start):
        todo=[(start,iter(graph.get(start,())))]
        color[start]=1;stack.append(start)
        while todo:
            key,neighbors=todo[-1]
            try:child=next(neighbors)
            except StopIteration:
                todo.pop();color[key]=2;stack.pop();continue
            if color.get(child)==1:
                cycle=stack[stack.index(child):]+[child]
                # canonical rotation (avoid reporting same cycle repeatedly).
                base=cycle[:-1];pivot=min(range(len(base)),key=lambda i:base[i]);rot=base[pivot:]+base[:pivot]
                found.add(' -> '.join(rot+[rot[0]]))
            elif not color.get(child):
                color[child]=1;stack.append(child);todo.append((child,iter(graph.get(child,()))))
    for key in graph:
        if not color.get(key):visit(key)
    rows=sorted(found)
    p,pages,shown=_page(rows,page)
    return f'QUEST ZALEZNOSCI CYKLE {p}/{pages}: wykryte {len(rows)}; '+('; '.join(shown) or 'BRAK')+'. Niczego nie zmieniono.'


def _plan(session, slot, before, active, candidate, label):
    session.__dict__[slot]=(copy.deepcopy(before),copy.deepcopy(active),copy.deepcopy(candidate),label)


def _commit(session,service,slot,undo_slot):
    data=getattr(session,slot,None)
    if not data:raise ValueError('Brak planu; wykonaj plan jeszcze raz.')
    before,active,candidate,label=data
    if service.draft!=before or service.active!=active:
        setattr(session,slot,None)
        raise ValueError('DRAFT/ACTIVE zmienione od planu; przygotuj nowy.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.__dict__[undo_slot]=(before,copy.deepcopy(candidate),active)
    setattr(session,slot,None)
    return f'{label}: zatwierdzono TYLKO w DRAFT. Publikacja wymaga admin live sprawdz i aktywuj POTWIERDZAM.'


def _undo(session,service,slot,undo_slot):
    data=getattr(session,undo_slot,None)
    if not data:raise ValueError('Brak ostatniej operacji do cofniecia.')
    before,after,active=data
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT/ACTIVE zmienione po operacji. Cofniecie zablokowane.')
    service.draft=copy.deepcopy(before)
    setattr(session,undo_slot,None)
    setattr(session,slot,None)
    return 'Cofnieto tylko DRAFT; aktywny swiat i SQLite bez zmian.'


def skill_batch_plan(session,service,raw):
    session.adminlive7100_skill_plan=None
    operations=[p.strip() for p in raw.split(';') if p.strip()]
    if not 1<=len(operations)<=8:raise ValueError('Dozwolone 1-8 operacji rozdzielonych srednikiem.')
    before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    summary=[]
    for step in operations:
        if '|' not in step:raise ValueError('Format: ID POLE | WARTOSC ; ID POLE | WARTOSC')
        lhs,val=step.split('|',1);parts=lhs.split();val=val.strip()
        if len(parts)!=2 or not val or len(val)>800:
            raise ValueError('Format: ID POLE | WARTOSC')
        ident,field=parts
        stage_existing_skill(candidate,ident,field,val)
        summary.append(ident+'.'+field)
    service.validate(candidate)
    _plan(session,'adminlive7100_skill_plan',before,service.active,candidate,'SKILL PAKIET')
    return 'SKILL PAKIET PLAN: '+', '.join(summary)+'. Bez zapisu. skill pakiet zatwierdz POTWIERDZAM.'


def boss_phase_preview(service,ident):
    if not isinstance(ident,str) or len(ident)>90:raise ValueError('Niepoprawne ID bossa.')
    template=dict(MOB_TEMPLATES.get(ident) or service.draft.get('mobs',{}).get(ident) or {})
    template.update(service.draft.get('mob_edits',{}).get(ident,{}))
    if not eligible_boss(template):raise ValueError('Boss nie jest zwyklym edytowalnym bossem; UOSS/skrypty chronione.')
    return default_boss_phases(template)


def boss_phase_plan(session,service,ident):
    session.adminlive7100_boss_plan=None
    candidate=copy.deepcopy(service.draft);before=copy.deepcopy(candidate)
    phases=boss_phase_preview(service,ident)
    candidate.setdefault('mob_edits',{}).setdefault(ident,{})['olc_boss_phases']=phases
    service.validate(candidate)
    _plan(session,'adminlive7100_boss_plan',before,service.active,candidate,'BOSS FAZY')
    return (f'BOSS FAZY PLAN {ident}: '+ ', '.join(str(x['hp_percent'])+'% HP' for x in phases)+
            '. Domyslny profil autora (nie zastapi skryptow). Bez zapisu. boss fazy zatwierdz POTWIERDZAM.')


def limits_remaining():
    caps=current_caps()
    axes=', '.join(f'{name}={"bezlimitu" if val is None else val}' for name,val in sorted(caps.items()))
    return ('LIMITY RESZTA: '+axes+'. Walidatory OLC skilli/EQ/wybranych receptur '
        'czytaja limity runtime; kreator, Soul Tier, liczby exp, budynki gildii, '
        'indeksy 81 progow biegłości oraz SQLite int64 maja oddzielne ograniczenia. '
        'Wlaczenie bezlimitu nie oznacza automatycznie nieskonczonej liczby nowych skilli ani bezpiecznego XP. '
        'Bez zmian danych.')


async def dispatch_v7100(session,group,raw):
    bits=str(raw or '').strip().split();service=session.server.live_content_v1204
    match=(group=='pomoc' and bits==['29'] or
        group=='arena' and bits==['uoss','pokrycie'] or
        group in ('questy','zadania') and bits[:2] in (['automaty','typy'],['automaty','cykle']) or
        group=='skill' and bits[:1]==['pakiet'] or
        group=='boss' and bits[:1]==['fazy'] or
        group=='limity' and bits==['reszta'])
    if not match:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':out=HELP
        elif group=='arena':out=arena_coverage()
        elif group in ('questy','zadania'):
            if len(bits)>3:raise ValueError('Podaj maksymalnie numer strony.')
            fn=quest_kind_coverage if bits[1]=='typy' else quest_cycles
            out=fn(service,bits[2] if len(bits)==3 else '1')
        elif group=='limity':out=limits_remaining()
        elif group=='skill':
            if len(bits)>1 and bits[1]=='plan':
                out=skill_batch_plan(session,service,raw.partition('plan')[2].strip())
            elif bits==['pakiet','zatwierdz','POTWIERDZAM']:
                out=_commit(session,service,'adminlive7100_skill_plan','adminlive7100_skill_undo')
            elif bits==['pakiet','cofnij','POTWIERDZAM']:
                out=_undo(session,service,'adminlive7100_skill_plan','adminlive7100_skill_undo')
            elif bits==['pakiet','anuluj']:
                session.adminlive7100_skill_plan=None;out='SKILL PAKIET: anulowano plan.'
            else:raise ValueError('skill pakiet plan / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj')
        else:
            if len(bits)==3 and bits[1]=='podglad':
                phases=boss_phase_preview(service,bits[2]);out='BOSS FAZY: '+'; '.join(str(x['hp_percent'])+'% HP x'+str(x['attack_multiplier']) for x in phases)
            elif len(bits)==3 and bits[1]=='plan':out=boss_phase_plan(session,service,bits[2])
            elif bits==['fazy','zatwierdz','POTWIERDZAM']:
                out=_commit(session,service,'adminlive7100_boss_plan','adminlive7100_boss_undo')
            elif bits==['fazy','cofnij','POTWIERDZAM']:
                out=_undo(session,service,'adminlive7100_boss_plan','adminlive7100_boss_undo')
            else:raise ValueError('boss fazy podglad ID / plan ID / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE V71: '+str(exc)[:260]
    await session.send(out)
    return True
