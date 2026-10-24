# -*- coding: utf-8 -*-
"""v94: final-state quest plans, deterministic counter repairs and on-hit skill bundles.

Every operation is owner-only and DRAFT-only. Candidate validation is whole-world
and atomic, with active-quest recheck at both planning and confirmation.
"""
from __future__ import annotations
import copy
import json
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v9100 import _active_quests
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_v9200 import _apply_patch
from systems.live_quest_olc_v1209 import parse_quest_edit, QUEST_XP_ALIASES, QUEST_AUTO_FIELDS
from systems.live_olc18_multi_objective import validate_objectives
from systems.live_olc6_skill_editor import stage_existing_skill, _catalogue
from systems.live_olc19_status_skills import parse_statuses
from systems.admin_live_quest_refs_v6100 import _id, _names
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS

QUEST_SLOT='adminlive9400_quest_plan'
QUEST_UNDO='adminlive9400_quest_undo'
COUNTER_SLOT='adminlive9400_counter_plan'
COUNTER_UNDO='adminlive9400_counter_undo'
SKILL_SLOT='adminlive9400_skill_plan'
SKILL_UNDO='adminlive9400_skill_undo'
HELP=(
 'ADMIN LIVE POMOC 52: questy pakiet plan ID POLE | WARTOSC; ID POLE | WARTOSC '
 '(do 32 pol i 16 questow; calosc sprawdzana dopiero po naniesieniu zmian); '
 'questy pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'questy liczniki skan [STRONA] / plan [MAX 1-64] / zatwierdz POTWIERDZAM / '
 'cofnij POTWIERDZAM / anuluj: tylko bezdyskusyjne needed=sum(objectives/resource_targets), '
 'bez zgadywania celow lub nagrod. '
 'skill efekty pakiet plan ID | [{"kind":"poison","chance":0.5},{"kind":"burn","chance":0.4}]; '
 'ID2 | AUTO; ... (do 16 zwyklych skilli, podmiana starego olc_status na olc_statuses). '
 'skill efekty pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Wszystkie plany wymagaja POTWIERDZAM, nie publikuja swiata, nie zmieniaja SQLite ani EXP.'
)


def _parts(raw,maximum,limit):
    if not isinstance(raw,str) or not 1<=len(raw)<=limit:
        raise ValueError(f'Plan musi zawierac 1–{limit} znakow.')
    rows=[s.strip() for s in raw.split(';')]
    if not 1<=len(rows)<=maximum or any(not s for s in rows):
        raise ValueError(f'Podaj 1–{maximum} niepustych operacji oddzielonych srednikami.')
    result=[]
    for row in rows:
        if row.count('|')!=1:raise ValueError('Wymagany separator: |.')
        left,right=[s.strip() for s in row.split('|',1)]
        if not left or not right:raise ValueError('Brakuje ID, pola lub wartosci.')
        result.append((left,right))
    return result


def _touch_guard(service,touched):
    active={qid:n for qid,n in _active_quests(service,touched).items() if n}
    if active:
        preview=', '.join(f'{qid} ({n})' for qid,n in sorted(active.items())[:6])
        raise ValueError('Questy przyjete przez graczy, zmiana zablokowana: '+preview)


def _quest_field(field,text):
    field=QUEST_XP_ALIASES.get(field,field)
    if text.upper()=='BRAK' and field=='requires_quest':return field,None
    if text.upper()=='BRAK' and field=='requires_quests':return field,[]
    if text.upper()=='AUTO' and field in QUEST_AUTO_FIELDS:
        return field,'__CLEAR_OVERRIDE__'
    return parse_quest_edit(field,text)


def quest_plan(session,service,raw):
    setattr(session,QUEST_SLOT,None)
    steps=_parts(raw,32,6000)
    before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before)
    catalog=_effective(service)
    touched=set(); used=set()
    for left,value in steps:
        tokens=left.split()
        if len(tokens)!=2:raise ValueError('Format: QUEST_ID POLE | WARTOSC.')
        qid,field=tokens
        _id(qid)
        if qid not in catalog:raise ValueError('Nieznany quest: '+qid)
        canonical,parsed=_quest_field(field,value)
        if (qid,canonical) in used:raise ValueError(f'Powtorzone pole {qid}.{canonical}.')
        used.add((qid,canonical));touched.add(qid)
        if len(touched)>16:raise ValueError('Maksymalnie 16 roznych questow.')
        if parsed=='__CLEAR_OVERRIDE__':
            # Clear only an explicit override, never overwrite original awards.
            patch=candidate.get('quest_edits',{}).get(qid)
            if patch:patch.pop(canonical,None)
            if qid in candidate.get('quests',{}):
                candidate['quests'][qid].pop(canonical,None)
        else:
            _apply_patch(candidate,qid,{canonical:parsed})
    if candidate==before:raise ValueError('Plan niczego nie zmienia.')
    _touch_guard(service,touched)
    # Crucial: validate the final combined quest after simultaneous needed/objectives,
    # repeatable/cooldown and resource_targets/target changes.
    service.validate(candidate)
    _plan(session,QUEST_SLOT,before,service.active,candidate,'QUEST PAKIET 18 TYPOW')
    session.adminlive9400_quest_touched=tuple(sorted(touched))
    return (f'QUEST PAKIET PLAN: {len(steps)} pol, {len(touched)} questow, '
            'pelna walidacja DRAFT OK. Bez zapisu. questy pakiet zatwierdz POTWIERDZAM.')


def _counter_candidates(service):
    """Only quantities determined exactly from validated source targets."""
    source=_effective(service)
    names=_names(service)
    known_npcs=set(names)
    result=[]
    from data.npcs import NPCS
    known_npcs.update(NPCS)
    for qid,q in sorted(source.items()):
        kind=q.get('kind')
        if kind=='multi_objective':
            try:
                cleaned,total=validate_objectives(q.get('objectives'),
                    {**MOB_TEMPLATES,**service.draft.get('mobs',{})},
                    {**ITEMS,**service.draft.get('items',{})},known_npcs)
                if cleaned!=q.get('objectives'):continue
            except (ValueError,TypeError,KeyError):continue
        elif kind=='collect_resource_set':
            targets=q.get('resource_targets')
            if (not isinstance(targets,dict) or not 2<=len(targets)<=8 or
                (q.get('target') is not None and q.get('target') not in targets) or
                any(type(v)!=int or not 1<=v<=10000 for v in targets.values())):continue
            total=sum(targets.values())
        else:continue
        if type(q.get('needed')) is int and q['needed']==total:continue
        if 1<=total<=10000:result.append((qid,q.get('needed'),total))
    return result


def counter_scan(service,page='1'):
    if not isinstance(page,str) or not page.isascii() or not page.isdecimal() or len(page)>4:
        raise ValueError('Podaj strone 1..9999.')
    rows=_counter_candidates(service)
    index=int(page);pages=max(1,(len(rows)+7)//8)
    if not 1<=index<=pages:raise ValueError(f'Dostepne strony 1..{pages}.')
    shown=rows[(index-1)*8:index*8]
    return (f'QUEST LICZNIKI SKAN {index}/{pages}: {len(rows)} jednoznacznych niespojnosci; '
        +('; '.join(f'{qid}: {old} -> {new}' for qid,old,new in shown) or 'BRAK')+
        '. Tylko odczyt, brak automatycznych zmian.')


def counter_plan(session,service,amount='64'):
    setattr(session,COUNTER_SLOT,None)
    if not amount.isascii() or not amount.isdecimal() or not 1<=len(amount)<=2 or not 1<=int(amount)<=64:
        raise ValueError('Maksymalnie 1-64 questy.')
    before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    rows=_counter_candidates(service)[:int(amount)]
    if not rows:raise ValueError('Nie ma jednoznacznych licznikow do naprawy.')
    touched={qid for qid,old,total in rows}
    _touch_guard(service,touched)
    for qid,old,total in rows:
        _apply_patch(candidate,qid,{'needed':total})
    service.validate(candidate)
    _plan(session,COUNTER_SLOT,before,service.active,candidate,'QUEST LICZNIKI')
    session.adminlive9400_counter_touched=tuple(sorted(touched))
    return (f'QUEST LICZNIKI PLAN: {len(rows)} poprawnych matematycznie zmian needed. '
            'Nie ruszono nagrod, EXP ani celow. Bez zapisu. '
            'questy liczniki zatwierdz POTWIERDZAM.')


def skill_plan(session,service,raw):
    setattr(session,SKILL_SLOT,None)
    steps=_parts(raw,16,6500)
    before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before)
    used=set();changed=[]
    known=_catalogue()
    for ident,value in steps:
        ident=_id(ident)
        if ident not in known:
            raise ValueError('Nieznany identyfikator skilla: '+ident)
        if ident in used:raise ValueError('Powtorzony skill ID: '+ident)
        used.add(ident)
        edits=candidate.setdefault('skill_edits',{}).setdefault(ident,{})
        edits.pop('olc_status',None)
        edits.pop('olc_statuses',None)
        if value.upper()!='AUTO':
            parsed=parse_statuses(value)
            if parsed is None:raise ValueError('Podaj liste efektow albo AUTO.')
            # Authoritative per-skill restrictions and familiar validator path.
            stage_existing_skill(candidate,ident,'olc_statuses',json.dumps(parsed,ensure_ascii=False))
        elif not edits:
            candidate['skill_edits'].pop(ident,None)
        changed.append(ident)
    if candidate==before:raise ValueError('Plan niczego nie zmienia.')
    service.validate(candidate)
    _plan(session,SKILL_SLOT,before,service.active,candidate,'SKILL EFEKTY PAKIET')
    return (f'SKILL EFEKTY PLAN: {len(changed)} skilli. Pelna walidacja DRAFT OK; '
            'dotychczasowe umiejetnosci i bieglose skille zachowane. Bez zapisu. '
            'skill efekty pakiet zatwierdz POTWIERDZAM.')


async def dispatch_v9400(session,group,tail):
    args=str(tail or '').strip().split()
    # v62 and v94 historically share `questy pakiet`.  Preserve v62's
    # space-delimited ID migrations and status/undo as well as v94's
    # final-state `ID POLE | WARTOSC` plans.  Do not consume older commands.
    if group in ('questy','zadania') and args[:1]==['pakiet']:
        if args[1:]==['status']:
            return False  # v62 owns the read-only status command
        if args[1:2]==['licznik']:
            return False  # v64 owns the safe multi-objective count preview
        if args[1:2]==['plan']:
            if '|' not in str(tail):
                session.adminlive_quest_pakiet_mode='v62'
                return False
            session.adminlive_quest_pakiet_mode='v94'
        elif args[1:2] in (['zatwierdz'], ['cofnij'], ['anuluj']):
            if getattr(session,'adminlive_quest_pakiet_mode',None)=='v62':
                return False
    recognized=(group=='pomoc' and args==['52']) or (
        group in ('questy','zadania') and args[:1] in (['pakiet'],['liczniki'])) or (
        group=='skill' and args[:2]==['efekty','pakiet'])
    if not recognized:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc':message=HELP
        elif group=='skill':
            rest=args[2:];slot=SKILL_SLOT;undo=SKILL_UNDO
            if rest[:1]==['plan']:
                prefix='efekty pakiet plan'
                message=skill_plan(session,service,str(tail).split(prefix,1)[1].strip())
            elif rest==['zatwierdz','POTWIERDZAM']:message=_commit(session,service,slot,undo)
            elif rest==['cofnij','POTWIERDZAM']:message=_undo(session,service,slot,undo)
            elif rest==['anuluj']:
                setattr(session,slot,None);message='SKILL EFEKTY: plan anulowany, zero zmian.'
            else:raise ValueError('Wpisz admin live pomoc 52.')
        else:
            topic=args[0];rest=args[1:]
            slot,undo=(QUEST_SLOT,QUEST_UNDO) if topic=='pakiet' else (COUNTER_SLOT,COUNTER_UNDO)
            touched_attr='adminlive9400_quest_touched' if topic=='pakiet' else 'adminlive9400_counter_touched'
            if topic=='pakiet' and rest[:1]==['plan']:
                message=quest_plan(session,service,str(tail).split('pakiet plan',1)[1].strip())
            elif topic=='liczniki' and rest[:1]==['skan'] and len(rest)<=2:
                message=counter_scan(service,rest[1] if len(rest)==2 else '1')
            elif topic=='liczniki' and rest[:1]==['plan'] and len(rest)<=2:
                message=counter_plan(session,service,rest[1] if len(rest)==2 else '64')
            elif rest==['zatwierdz','POTWIERDZAM']:
                if getattr(session,slot,None):
                    _touch_guard(service,getattr(session,touched_attr,()))
                message=_commit(session,service,slot,undo)
            elif rest==['cofnij','POTWIERDZAM']:message=_undo(session,service,slot,undo)
            elif rest==['anuluj']:
                setattr(session,slot,None);message='QUEST PLAN anulowany, zero zmian.'
            else:raise ValueError('Wpisz admin live pomoc 52.')
    except (ValueError,TypeError,KeyError,RuntimeError,OverflowError,AttributeError) as exc:
        message='ADMIN LIVE v94: '+str(exc)[:480]
    await session.send(message)
    return True
