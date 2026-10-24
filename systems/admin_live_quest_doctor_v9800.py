# -*- coding: utf-8 -*-
"""v98: exact quest diagnostics + safe, deterministic count repairs.

No guessed NPC/target IDs, reward changes, character progress resets or ACTIVE
publication. Existing authoritative DRAFT validator is the final gate.
"""
from __future__ import annotations
import copy
from systems.admin_live_integrity_v4900 import _effective,_issues
from systems.admin_live_v9400 import _counter_candidates,_touch_guard
from systems.admin_live_v9200 import _apply_patch
from systems.admin_live_v7100 import _plan,_commit,_undo
SLOT='adminlive9800_doctor_plan';UNDO='adminlive9800_doctor_undo'
HELP=(
 'ADMIN LIVE POMOC 58: questy doktor skan [STRONA] (8/strona), '
 'questy doktor karta QUEST_ID - realne bledy/ostrzezenia i stan aktywnosci u graczy. '
 'questy doktor plan [LICZBA 1-64] - tylko matematycznie jednoznaczne poprawki needed '
 'dla multi_objective i collect_resource_set; questy doktor zatwierdz POTWIERDZAM / '
 'cofnij POTWIERDZAM / anuluj. Brak zgadywania brakujacych ID i NPC, '
 'brak automatycznej publikacji i nagrod. Zmiany wylacznie DRAFT.'
)

def _num_page(raw,pages):
    if not isinstance(raw,str) or not raw.isascii() or not raw.isdecimal() or len(raw)>5:
        raise ValueError('Strona: podaj liczbe dodatnia.')
    number=int(raw)
    if not 1<=number<=pages:raise ValueError(f'Strony 1..{pages}.')
    return number


def _problems(service):
    catalog=_effective(service)
    correct={qid:(old,new) for qid,old,new in _counter_candidates(service)}
    rows=[]
    for qid,q in sorted(catalog.items()):
        errors,warnings=_issues(qid,q,catalog)
        if qid in correct:
            errors=['needed niezgodne z suma celow']+errors
        if errors or warnings:
            rows.append((qid,errors,warnings,qid in correct))
    return rows,correct


def scan(service,page='1'):
    rows,fixable=_problems(service)
    pages=max(1,(len(rows)+7)//8);n=_num_page(page,pages)
    selected=rows[(n-1)*8:n*8]
    summary='; '.join(f'{qid}: {len(errors)} bledow, {len(warns)} ostrzezen, '+
                     ('LICZNIK DO NAPRAWY' if candidate else 'WYMAGA ANALIZY')
                     for qid,errors,warns,candidate in selected)
    return (f'QUEST DOCTOR SKAN {n}/{pages}: problemy lub ostrzezenia {len(rows)}, '
            f'jednoznaczne korekty {len(fixable)}. '+(summary or 'BRAK')+'. Bez zmian.')


def card(service,qid):
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Quest ID nie istnieje.')
    errors,hints=_issues(qid,catalog[qid],catalog)
    fix={qid0:(old,new) for qid0,old,new in _counter_candidates(service)}
    count=int(service.conn.execute("SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(qid,)).fetchone()[0])
    repair=(f'JEDNOZNACZNE needed {fix[qid][0]}->{fix[qid][1]}' if qid in fix else 'brak bezpiecznej poprawki automatycznej')
    return (f'QUEST DOCTOR {qid}: typ {catalog[qid].get("kind")}; aktywnych {count}; '
            'bledy: '+('; '.join(errors) or 'BRAK')+'; ostrzezenia: '+('; '.join(hints) or 'BRAK')+
            '; plan: '+repair+'. Bez zmian; aktywne questy sa chronione.')


def plan(session,service,amount='64'):
    setattr(session,SLOT,None)
    n=_num_page(amount,64)
    changes=_counter_candidates(service)[:n]
    if not changes:raise ValueError('Brak jednoznacznych licznikow do poprawy.')
    touched=tuple(qid for qid,_,_ in changes)
    _touch_guard(service,touched)
    before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    for qid,old,new in changes:_apply_patch(candidate,qid,{'needed':new})
    service.validate(candidate)
    _plan(session,SLOT,before,service.active,candidate,'QUEST DOCTOR')
    session.adminlive9800_doctor_touched=touched
    return (f'QUEST DOCTOR PLAN: {len(changes)} jednoznacznych korekt needed; '
            'kontrola calego DRAFT OK. Bez zapisu. questy doktor zatwierdz POTWIERDZAM.')

async def dispatch_v9800_doctor(session,cmd,tail):
    raw=str(tail or '').strip();parts=raw.split()
    match=(cmd=='pomoc' and raw=='58') or (cmd in ('questy','zadania') and parts[:1]==['doktor'])
    if not match:return False
    if not session.is_admin():await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif parts[:2]==['doktor','skan'] and len(parts)<=3:out=scan(service,parts[2] if len(parts)==3 else '1')
        elif parts[:2]==['doktor','karta'] and len(parts)==3:out=card(service,parts[2])
        elif parts[:2]==['doktor','plan'] and len(parts)<=3:out=plan(session,service,parts[2] if len(parts)==3 else '64')
        elif parts==['doktor','zatwierdz','POTWIERDZAM']:
            if getattr(session,SLOT,None):_touch_guard(service,getattr(session,'adminlive9800_doctor_touched',()))
            out=_commit(session,service,SLOT,UNDO)
        elif parts==['doktor','cofnij','POTWIERDZAM']:out=_undo(session,service,SLOT,UNDO)
        elif parts==['doktor','anuluj']:setattr(session,SLOT,None);out='QUEST DOCTOR: anulowano plan.'
        else:raise ValueError('Wpisz admin live pomoc 58.')
    except (ValueError,TypeError,KeyError,OverflowError,AttributeError) as exc:out='ADMIN LIVE QUEST DOCTOR: '+str(exc)[:320]
    await session.send(out);return True
