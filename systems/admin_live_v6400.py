# -*- coding: utf-8 -*-
"""v64: atomic repair of linked quest goals and counts; owner-only NVDA help.
No actual quest awards, real player progress, production combat or DB writes.
"""
from __future__ import annotations
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_quest_refs_v6100 import _npc_catalog
from systems.live_olc18_multi_objective import validate_objectives
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS

HELP = ('ADMIN LIVE POMOC 19: questy pakiet plan pole ID objectives JSON ; dopasuj ID. '
        'Lub pole ID resource_targets JSON ; pole ID target SUROWIEC ; dopasuj ID. '
        'Dopasuj MUSI byc na koncu: oblicza needed z celow i jest sprawdzane '
        'razem ze wszystkimi zmianami w jednym atomowym planie DRAFT. '
        'questy pakiet licznik ID - odczyt obecnego licznika. '
        'Zatwierdz / cofnij POTWIERDZAM jak dotychczas. '
        'Bledny plan nie zapisuje niczego ani nie pozostawia starego planu. '
        'Istniejace zaleznosci nie moga utworzyc nowego cyklu.')

def count_preview(service,qid):
    quest=_effective(service).get(qid)
    if quest is None:raise ValueError('Quest nie istnieje. Szukaj: admin live questy szukaj FRAGMENT.')
    kind=quest.get('kind')
    if kind=='multi_objective':
        mobs=set(MOB_TEMPLATES)|set(service.draft.get('mobs',{}))|set(service.active.get('mobs',{}))
        items=set(ITEMS)|set(service.draft.get('items',{}))|set(service.active.get('items',{}))
        _,goal=validate_objectives(quest.get('objectives'),mobs,items,set(_npc_catalog(service)))
    elif kind=='collect_resource_set':
        group=quest.get('resource_targets')
        if not isinstance(group,dict) or not group:raise ValueError('Brak zestawu surowcow.')
        if any(type(v) is not int or v<1 for v in group.values()):raise ValueError('Nieprawidlowe ilosci.')
        goal=sum(group.values())
    else:raise ValueError('Podglad licznika tylko multi_objective lub collect_resource_set.')
    actual=quest.get('needed')
    status='ZGODNY' if actual==goal else 'ROZBIEZNOSC'
    return f'QUEST LICZNIK {qid}: {kind}, needed {actual}, suma celow {goal}, {status}. Odczyt bez zapisu.'

async def dispatch_v64(session,group,raw):
    bits=str(raw or '').split()
    if not ((group=='pomoc' and bits==['19']) or
            (group in ('questy','zadania') and len(bits)>=2 and bits[0]=='pakiet' and bits[1]=='licznik')):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':output=HELP
        elif len(bits)==3:output=count_preview(session.server.live_content_v1204,bits[2])
        else:raise ValueError('questy pakiet licznik QUEST_ID')
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        output='ADMIN LIVE V64: '+str(exc)[:260]
    await session.send(output)
    return True
