# -*- coding: utf-8 -*-
"""v58 read-only quest reward item ID check, including OLC-added items.

Unknown IDs are signals, not automatic deletions. OLC/quest handlers may have
runtime aliases. The script does not create drafts or change SQLite.
"""
from data.items import ITEMS
from systems.admin_live_integrity_v4900 import _effective, _integer
from systems.admin_live_expansion_v4800 import _page


def _item_alerts(service):
    catalog=_effective(service)
    known=set(ITEMS)
    for side in (service.active,service.draft):
        extras=side.get('items',{})
        if isinstance(extras,dict):known.update(extras)
    results=[]
    for qid,q in sorted(catalog.items()):
        reward=q.get('reward_items')
        if reward is None or reward=={}:continue
        if not isinstance(reward,dict):
            results.append((qid,('nagrody: nieprawidlowa mapa',)))
            continue
        alerts=[]
        for item_id,qty in reward.items():
            label=str(item_id)[:55]
            if item_id not in known:alerts.append('nieznane ID '+label)
            n=_integer(qty)
            if n is None or n<1:alerts.append('ilosc '+label+' = '+str(qty)[:30])
        if alerts:results.append((qid,tuple(alerts[:8])))
    return results


def quest_item_audit_v5800(service,selector='1'):
    rows=_item_alerts(service)
    if selector in {qid for qid,_ in rows}:
        selected=[(qid,notes) for qid,notes in rows if qid==selector]
    elif str(selector).isascii() and str(selector).isdecimal():
        page,pages=_page(selector,len(rows))
        selected=rows[(page-1)*8:page*8]
    else:
        catalog=_effective(service)
        if selector not in catalog:raise ValueError('Quest ID nie istnieje.')
        return 'QUEST ITEMY '+selector+': brak sygnalow nieprawidlowych nagrod przedmiotowych.'
    rendered='; '.join(qid+': '+', '.join(notes[:3]) for qid,notes in selected)
    return (f'QUEST ITEMY: sprawdzono nagrody, sygnaly {len(rows)}. '
            +(rendered or 'Brak sygnalow na stronie.')+' '
            'Nieznane ID moze istniec w runtime/OLC: sprawdz przed poprawka. '
            'Nic nie usunieto, DRAFT i SQLite bez zmian.')

async def dispatch_quest_items_v5800(session,group,raw):
    if group not in ('questy','zadania'):return False
    bits=str(raw or '').strip().split()
    if not bits or bits[0]!='itemy':return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if len(bits)>2:raise ValueError('Uzyj: admin live questy itemy [STRONA lub ID].')
        result=quest_item_audit_v5800(session.server.live_content_v1204,bits[1] if len(bits)==2 else '1')
    except (ValueError,TypeError) as exc:result='QUEST ITEMY: '+str(exc)[:200]
    await session.send(result)
    return True
