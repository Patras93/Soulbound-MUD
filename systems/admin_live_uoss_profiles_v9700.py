# -*- coding: utf-8 -*-
"""v97: multi-boss UOSS profile inheritance using real executable OLC rules.

All four protected UOSS rule sections are copied together or explicitly set
back to AUTO. Changes are DRAFT only and run full production OLC validation.
"""
from __future__ import annotations
import copy
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v7500 import _boss

SLOT='adminlive9700_uoss_profile_plan'
UNDO='adminlive9700_uoss_profile_undo'
SECTIONS=(('v24_rules','skala'),('v32_rules','fazy'),('v33_rules','leczenie'),('v34_rules','furia'))
HELP=(
 'ADMIN LIVE POMOC 56: boss uoss profil karta BOSS; '
 'boss uoss profil plan CEL | ZRODLO | DRAFT/ACTIVE; CEL2 | ZRODLO2 | DRAFT/ACTIVE (do 8 bossow). '
 'Kopiuje razem skale HP/obrazen, fazy, leczenie i furie z istniejacego skryptowanego UOSS. '
 'Nie kopiuje nagrod, spawnu ani HP jako stalej wartosci; brakujace reguly pozostaja AUTO. '
 'boss uoss profil zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Plan i cofanie dotycza tylko DRAFT, publikacja przez standardowe admin live sprawdz / aktywuj.'
)

def profile_card(service,boss):
    _boss(boss)
    text=[]
    for section,label in SECTIONS:
        active=service.active[section]['uoss'].get(boss)
        draft=service.draft[section]['uoss'].get(boss)
        text.append(f'{label}: ACTIVE={str(active)[:120] if active else "AUTO"}; DRAFT={str(draft)[:120] if draft else "AUTO"}')
    return 'UOSS PROFIL '+boss+': '+'; '.join(text)+'. Tylko odczyt.'


def plan(session,service,raw):
    setattr(session,SLOT,None)
    if not 1<=len(raw)<=2000:raise ValueError('Plan profili: 1..2000 znakow.')
    entries=[line.strip() for line in raw.split(';')]
    if not 1<=len(entries)<=8 or not all(entries):raise ValueError('Podaj 1-8 bossow.')
    before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before)
    source_active=copy.deepcopy(service.active)
    used=set();summary=[]
    for entry in entries:
        parts=[s.strip() for s in entry.split('|')]
        if len(parts)!=3:raise ValueError('Wymagane: CEL | ZRODLO | DRAFT albo ACTIVE.')
        target,source,mode=parts
        _boss(target);_boss(source)
        if target==source or target in used:raise ValueError('Cel identyczny ze zrodlem lub powtorzony boss.')
        if mode not in ('DRAFT','ACTIVE'):raise ValueError('Tryb musi byc DRAFT lub ACTIVE.')
        used.add(target)
        original=before if mode=='DRAFT' else source_active
        descriptions=[]
        for section,label in SECTIONS:
            dest=candidate[section]['uoss']
            rule=original[section]['uoss'].get(source)
            if rule is None:
                # Preserve unrelated custom UOSS keys in v24 if ever defined.
                if section=='v24_rules':
                    old=copy.deepcopy(dest.get(target,{}))
                    old.pop('max_hp_percent',None);old.pop('damage_percent',None)
                    if old:dest[target]=old
                    else:dest.pop(target,None)
                else:dest.pop(target,None)
                descriptions.append(label+':AUTO')
            elif section=='v24_rules':
                # Only copy documented scale fields; retain non-scale v24 settings.
                old=copy.deepcopy(dest.get(target,{}))
                for key in ('max_hp_percent','damage_percent'):old.pop(key,None)
                for key in ('max_hp_percent','damage_percent'):
                    if key in rule:old[key]=copy.deepcopy(rule[key])
                if old:dest[target]=old
                else:dest.pop(target,None)
                descriptions.append(label+':KOPIA')
            else:
                dest[target]=copy.deepcopy(rule)
                descriptions.append(label+':KOPIA')
        summary.append(target+'<-'+source+'('+mode+'): '+','.join(descriptions))
    service.validate(candidate)
    if candidate==before:raise ValueError('Plan nie zmienia DRAFT.')
    _plan(session,SLOT,before,service.active,candidate,'UOSS PROFIL')
    return ('UOSS PROFIL PLAN: '+'; '.join(summary)+'. Komplet 4 regul zweryfikowany; '
            'bez zapisu ACTIVE. boss uoss profil zatwierdz POTWIERDZAM.')


async def dispatch_v9700_uoss(session,cmd,tail):
    raw=str(tail or '').strip();words=raw.split()
    matched=(cmd=='pomoc' and raw=='56') or (cmd=='boss' and words[:2]==['uoss','profil'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif words[:3]==['uoss','profil','karta'] and len(words)==4:out=profile_card(service,words[3])
        elif words[:3]==['uoss','profil','plan'] and len(words)>=6:
            out=plan(session,service,raw.split('profil plan',1)[1].strip())
        elif words==['uoss','profil','zatwierdz','POTWIERDZAM']:out=_commit(session,service,SLOT,UNDO)
        elif words==['uoss','profil','cofnij','POTWIERDZAM']:out=_undo(session,service,SLOT,UNDO)
        elif words==['uoss','profil','anuluj']:
            setattr(session,SLOT,None);out='UOSS PROFIL: plan anulowano.'
        else:raise ValueError('Wpisz admin live pomoc 56.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE V97 UOSS: '+str(exc)[:290]
    await session.send(out)
    return True
