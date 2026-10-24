# -*- coding: utf-8 -*-
"""Admin Live v87 — real, atomic multi-object OLC repair.

- Quests: edit *both* historical and modern prerequisites across several
  quests, validating the resulting entire DAG before any DRAFT mutation.
- Scripted UOSS: edit four existing executable combat-rule sections for
  several bosses as one validated transaction; no arbitrary code execution.
- Every operation is a plan / explicit commit / conflict-checked undo.
"""
from __future__ import annotations
import copy
import re
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.live_olc17_quest_dependencies import validate_dependency_graph
from systems.admin_live_v7500 import _boss, _integers

_SLOT_Q='adminlive8700_quest_plan'
_UNDO_Q='adminlive8700_quest_undo'
_SLOT_B='adminlive8700_boss_plan'
_UNDO_B='adminlive8700_boss_undo'
_ID=re.compile(r'[a-zA-Z0-9_-]{1,100}\Z',re.ASCII)
HELP=('ADMIN LIVE POMOC 45: questy caly pakiet plan QUEST | stare=ID/BRAK | dodatkowe=ID1,ID2/BRAK; '
      'QUEST2 | stare=BRAK | dodatkowe=BRAK (maksymalnie 8 questow). '
      'questy caly pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
      'boss uoss zbiorczy plan BOSS | fazy=HP:INTERWAL:MOC,HP:INTERWAL:MOC; '
      'BOSS2 | furia=INTERWAL:MOC:STOSY+leczenie=HP:INTERWAL:PROC+skala=HP:OBRAZENIA. '
      'Maksymalnie 8 bossow i 16 regul. Wartosc BRAK przywraca AUTO. '
      'boss uoss zbiorczy zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
      'Obie operacje zmieniaja WYŁĄCZNIE DRAFT; publikacja OLC osobno. '
      'Nie zmieniaja SQLite ani postepow graczy. Komendy starego edytora pozostaja.')


def _ident(text):
    if not _ID.fullmatch(text):
        raise ValueError('Niepoprawny ID (ASCII: litery, cyfry, podkreslenie, myslnik).')
    return text


def _sections(raw,maxlength,limit,label):
    if not 1<=len(raw)<=maxlength:
        raise ValueError(f'{label}: zbyt dlugi lub pusty plan.')
    entries=[p.strip() for p in raw.split(';')]
    if not 1<=len(entries)<=limit or any(not x for x in entries):
        raise ValueError(f'{label}: wymagane 1-{limit} niepustych zmian.')
    return entries


def quest_full_plan(session,service,raw):
    setattr(session,_SLOT_Q,None)
    entries=_sections(raw,1700,8,'Questy')
    catalog=_effective(service)
    original=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(original)
    edits={}
    for entry in entries:
        fields=[v.strip() for v in entry.split('|')]
        if len(fields)!=3:
            raise ValueError('Quest: QUEST | stare=ID/BRAK | dodatkowe=ID,ID/BRAK.')
        qid=_ident(fields[0])
        if qid not in catalog or qid in edits:
            raise ValueError('Quest nie istnieje lub jest powtorzony: '+qid)
        if not fields[1].startswith('stare=') or not fields[2].startswith('dodatkowe='):
            raise ValueError('Podaj stare= oraz dodatkowe= w tej kolejnosci.')
        parent=fields[1][len('stare='):].strip()
        addition=fields[2][len('dodatkowe='):].strip()
        if not parent or not addition:
            raise ValueError('Pusta wartosc nie jest dozwolona; uzyj BRAK.')
        old=None if parent.upper()=='BRAK' else _ident(parent)
        extras=[] if addition.upper()=='BRAK' else [_ident(x.strip()) for x in addition.split(',')]
        if len(extras)>8 or len(set(extras))!=len(extras):
            raise ValueError('Dodatkowe: maksymalnie 8 unikalnych ID.')
        dependencies=([old] if old else [])+extras
        if len(set(dependencies))!=len(dependencies):
            raise ValueError('Powtorzona zaleznosc w polu stare i dodatkowe.')
        for dep in dependencies:
            if dep not in catalog or dep==qid:
                raise ValueError('Nieznany lub wlasny wymagany quest: '+dep)
        edits[qid]={'requires_quest':old,'requires_quests':extras}
    for qid,update in edits.items():
        candidate.setdefault('quest_edits',{}).setdefault(qid,{}).update(update)
        catalog[qid]={**catalog[qid],**update}
    validate_dependency_graph(catalog)
    service.validate(candidate)
    if candidate==original:
        raise ValueError('Brak zmian wzgledem DRAFT.')
    _plan(session,_SLOT_Q,original,service.active,candidate,'QUESTY CALY PAKIET')
    lines=[f'{qid} stare={data["requires_quest"] or "BRAK"}, dodatkowe={",".join(data["requires_quests"]) or "BRAK"}' for qid,data in edits.items()]
    return ('QUESTY CALY PAKIET PLAN: '+'; '.join(lines)+
            '. Walidacja calosciowa starego i nowego grafu: OK. Bez zapisu. '
            'questy caly pakiet zatwierdz POTWIERDZAM.')


def uoss_bulk_plan(session,service,raw):
    setattr(session,_SLOT_B,None)
    entries=_sections(raw,1900,8,'UOSS')
    original=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(original)
    seen=set(); count=0; summary=[]
    for entry in entries:
        fields=[x.strip() for x in entry.split('|')]
        if len(fields)!=2:
            raise ValueError('UOSS: BOSS | fazy=... lub inne reguly.')
        boss=_boss(fields[0])
        if boss in seen:
            raise ValueError('Powtorzony superboss: '+boss)
        seen.add(boss)
        # Commas are used by phase sequences, so split *rules* on +.
        # One boss row supports one or more rules separated by '+'; phase comma is retained.
        parameters=[x.strip() for x in fields[1].split('+')]
        if not parameters or len(parameters)>4 or any(not p for p in parameters):
            raise ValueError('UOSS: 1-4 reguly na bossa rozdzielone plusem (+).')
        used=set()
        for param in parameters:
            if param.count('=')!=1:
                raise ValueError('UOSS: pole=wartosc, reguly lacz plusem (+).')
            label,value=(x.strip() for x in param.split('=',1))
            sections={'fazy':'v32_rules','leczenie':'v33_rules','furia':'v34_rules','skala':'v24_rules'}
            if label not in sections or label in used:
                raise ValueError('Nieznane lub powtorzone pole UOSS.')
            used.add(label); count+=1
            if count>16:
                raise ValueError('Maksymalnie 16 zmian regul w jednym pakiecie.')
            dest=candidate[sections[label]]['uoss']
            if value.upper()=='BRAK':
                if label=='skala':
                    row=copy.deepcopy(dest.get(boss,{}))
                    row.pop('max_hp_percent',None);row.pop('damage_percent',None)
                    if row:dest[boss]=row
                    else:dest.pop(boss,None)
                else:
                    dest.pop(boss,None)
                summary.append(boss+'.'+label+'=AUTO')
                continue
            if label=='fazy':
                phases=[]
                for spec in value.split(','):
                    below,every,power=_integers(spec.strip(),3,'fazy')
                    phases.append({'below_hp':below,'interval':every,'damage_percent':power})
                if not 1<=len(phases)<=5:
                    raise ValueError('Fazy: 1-5 wpisow.')
                dest[boss]={'phases':phases}
            elif label=='leczenie':
                below,every,restore=_integers(value,3,'leczenie')
                dest[boss]={'below_hp':below,'every':every,'restore_percent':restore}
            elif label=='furia':
                every,stack,cap=_integers(value,3,'furia')
                dest[boss]={'every':every,'stack_percent':stack,'max_stacks':cap}
            elif label=='skala':
                hp,dmg=_integers(value,2,'skala')
                dest.setdefault(boss,{})
                dest[boss].update(max_hp_percent=hp,damage_percent=dmg)
            summary.append(boss+'.'+label+'='+('('+str(len(phases))+' faz)' if label=='fazy' else value))
    service.validate(candidate)
    if candidate==original:
        raise ValueError('Brak zmian wzgledem DRAFT.')
    _plan(session,_SLOT_B,original,service.active,candidate,'BOSS UOSS ZBIORCZY')
    return ('BOSS UOSS ZBIORCZY PLAN: '+'; '.join(summary)+
            '. Produkcyjne walidatory 4 systemow PASS; bez zapisu, nagrod i publikacji. '
            'boss uoss zbiorczy zatwierdz POTWIERDZAM.')


async def dispatch_v8700(session,cmd,tail):
    args=str(tail or '').strip(); parts=args.split()
    help_query=(cmd=='pomoc' and args=='45')
    is_quest=cmd in ('questy','zadania') and parts[:2]==['caly','pakiet']
    is_boss=cmd=='boss' and parts[:2]==['uoss','zbiorczy']
    if not (help_query or is_quest or is_boss):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if help_query:
            answer=HELP
        elif is_quest or is_boss:
            slot,undo=(_SLOT_Q,_UNDO_Q) if is_quest else (_SLOT_B,_UNDO_B)
            sub=parts[2:]
            if len(sub)>=2 and sub[0]=='plan':
                plan_text=args.split('plan',1)[1].strip()
                answer=(quest_full_plan(session,service,plan_text) if is_quest else uoss_bulk_plan(session,service,plan_text))
            elif sub==['zatwierdz','POTWIERDZAM']:
                answer=_commit(session,service,slot,undo)
            elif sub==['cofnij','POTWIERDZAM']:
                answer=_undo(session,service,slot,undo)
            elif sub==['anuluj']:
                setattr(session,slot,None)
                answer='ADMIN LIVE v87: plan anulowany.'
            else:
                raise ValueError('Dostepne: plan, zatwierdz POTWIERDZAM, cofnij POTWIERDZAM, anuluj. Pomoc 45.')
        else:
            return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        answer='ADMIN LIVE V87: '+str(exc)[:260]
    await session.send(answer)
    return True
