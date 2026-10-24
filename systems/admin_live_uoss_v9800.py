# -*- coding: utf-8 -*-
"""v98: safe, validated multi-boss UOSS tactical attacks, phases and AI."""
from __future__ import annotations
import copy,json
from systems.admin_live_v7100 import _plan,_commit,_undo
from systems.admin_live_v7500 import _boss
from systems.uoss_tactics_v9800 import validate
SLOT='adminlive9800_uoss_plan'; UNDO='adminlive9800_uoss_undo'
HELP=(
 'ADMIN LIVE POMOC 57: boss uoss taktyka karta BOSS; '
 'boss uoss taktyka plan BOSS | {"phases":[{"below_hp":100,"every":3,"attack_percent":150,"ai":"weakest","label":"Grom"}]}; '
 'BOSS2 | AUTO. Do 8 superbossow; 1-5 faz, malejace progi HP, moc 100-300%, rytm 1-30. '
 'AI: all (wszyscy), weakest (najnizsze HP), strongest (najwyzsze HP), focus (staly cel). '
 'Nie zastępuje skryptowanych atakow UOSS, tylko dodaje kontrolowany mnoznik do zwyklego trafienia. '
 'boss uoss taktyka zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Zmiany tylko DRAFT; opublikuj osobno przez sprawdz/aktywuj. Bez edycji nagrod.'
)

def card(service,key):
    _boss(key)
    def fmt(obj):return json.dumps(obj.get('v98_rules',{}).get(key,'AUTO'),ensure_ascii=False)
    return f'BOSS TAKTYKA {key}: ACTIVE={fmt(service.active)}; DRAFT={fmt(service.draft)}. Tylko odczyt.'

def plan(session,service,raw):
    setattr(session,SLOT,None)
    if not 1<=len(raw)<=7000:raise ValueError('Plan ma miec 1-7000 znakow.')
    parts=[item.strip() for item in raw.split(';')]
    if not 1<=len(parts)<=8 or any(not p for p in parts):raise ValueError('Podaj 1-8 bossow rozdzielonych srednikiem.')
    before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    touched=set();summary=[]
    for part in parts:
        if '|' not in part:raise ValueError('Format: BOSS | JSON albo BOSS | AUTO.')
        boss,source=[s.strip() for s in part.split('|',1)]
        _boss(boss)
        if boss in touched:raise ValueError('Powtorzony boss '+boss)
        touched.add(boss)
        if source.upper()=='AUTO':candidate['v98_rules'].pop(boss,None);summary.append(boss+': AUTO')
        else:
            try:value=json.loads(source)
            except (ValueError,TypeError) as exc:raise ValueError('Nieprawidlowy JSON taktyki '+boss) from exc
            candidate['v98_rules'][boss]=value;summary.append(f'{boss}: {len(value.get("phases",[])) if isinstance(value,dict) else "?"} faz')
    validate(candidate['v98_rules'])
    service.validate(candidate)
    if candidate==before:raise ValueError('Brak roznic w DRAFT.')
    _plan(session,SLOT,before,service.active,candidate,'SUPERBOSS 2.0')
    return 'SUPERBOSS 2.0 PLAN: '+'; '.join(summary)+'. Walidacja OK, bez publikacji. Zatwierdz POTWIERDZAM.'

async def dispatch_v9800_uoss(session,cmd,tail):
    raw=str(tail or '').strip();parts=raw.split()
    matched=(cmd=='pomoc' and raw=='57') or (cmd=='boss' and parts[:2]==['uoss','taktyka'])
    if not matched:return False
    if not session.is_admin():await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif parts[:3]==['uoss','taktyka','karta'] and len(parts)==4:out=card(service,parts[3])
        elif parts[:3]==['uoss','taktyka','plan'] and len(parts)>3:out=plan(session,service,raw.split('taktyka plan',1)[1].strip())
        elif parts==['uoss','taktyka','zatwierdz','POTWIERDZAM']:out=_commit(session,service,SLOT,UNDO)
        elif parts==['uoss','taktyka','cofnij','POTWIERDZAM']:out=_undo(session,service,SLOT,UNDO)
        elif parts==['uoss','taktyka','anuluj']:setattr(session,SLOT,None);out='SUPERBOSS 2.0: anulowano plan.'
        else:raise ValueError('Wpisz admin live pomoc 57.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as e:out='ADMIN LIVE V98 UOSS: '+str(e)[:340]
    await session.send(out)
    return True
