# -*- coding: utf-8 -*-
"""v89: publication readiness and complete cross-domain OLC DRAFT diff.

No new activation path and no user-data writes: preflight invokes exactly the
runtime safety checks in LiveContentV1204.apply(dry_run=True). The real publish
command remains unchanged and re-checks everything at activation time.
"""
from __future__ import annotations

import hashlib
import json
from systems.live_content_v1204 import blank

HELP = (
    'ADMIN LIVE POMOC 47: aktualizacja porownaj [STRONA] - pelne roznice DRAFT/ACTIVE '
    'we wszystkich 8 dziedzinach, 7 zmian na strone, odczyt z NVDA. '
    'aktualizacja publikacja sprawdz - sprawdzenie tych samych blokad co przy '
    'prawdziwej publikacji OLC: aktywne questy, walka, ochrona zapisanych ID. '
    'Wynik jest tylko migawka: rzeczywista publikacja ponownie sprawdza warunki. '
    'Publikacja pozostaje przez admin live aktywuj POTWIERDZAM. '
    'Nie zmienia DRAFT, ACTIVE, kont, postaci ani bazy SQLite.'
)

SECTIONS = (
    ('QUEST','quest_edits'), ('SKILL','skill_edits'), ('MOB','mob_edits'),
    ('EQ','item_edits'), ('RECEPTURA','recipe_edits'), ('SKLEP','shop_edits'),
    ('NPC','npc_edits'),
)
UOSS = (('SKALA','v24_rules'),('FAZY','v32_rules'),('LECZENIE','v33_rules'),('FURIA','v34_rules'))
PAGE_SIZE=7


def _fmt(value):
    if value is _MISSING:
        return 'AUTO'
    value=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return value if len(value)<=125 else value[:122]+'...'


_MISSING=object()


def _rows(service):
    active=service.active;draft=service.draft
    rows=[]
    for title,section in SECTIONS:
        a=active[section];b=draft[section]
        for key in sorted(a.keys()|b.keys()):
            left=a.get(key,{})
            right=b.get(key,{})
            for field in sorted(left.keys()|right.keys()):
                av=left.get(field,_MISSING)
                bv=right.get(field,_MISSING)
                if av!=bv:
                    rows.append(f'{title} {key}.{field}: ACTIVE={_fmt(av)}; DRAFT={_fmt(bv)}')
    for title,section in UOSS:
        a=active[section]['uoss'];b=draft[section]['uoss']
        for key in sorted(a.keys()|b.keys()):
            av=a.get(key,_MISSING);bv=b.get(key,_MISSING)
            if av!=bv:
                rows.append(f'UOSS {key}.{title}: ACTIVE={_fmt(av)}; DRAFT={_fmt(bv)}')
    # Complete OLC may change sectors outside the eight covered here; warn
    # rather than falsely claiming this is a complete global OLC diff.
    special={section for _,section in SECTIONS}
    special.update(section for _,section in UOSS)
    other=[key for key in blank() if key not in special and active[key]!=draft[key]]
    for _,section in UOSS:
        # UOSS changes were reported above; only unrelated rules are 'other'.
        ae={k:v for k,v in active[section].items() if k!='uoss'}
        de={k:v for k,v in draft[section].items() if k!='uoss'}
        if ae!=de:
            other.append(section+' (inne niz UOSS)')
    return rows,sorted(other)


def comparison(service,page='1'):
    if not page.isascii() or not page.isdecimal() or not 1<=len(page)<=4:
        raise ValueError('Podaj numer strony od 1 do 9999.')
    rows,other=_rows(service)
    pages=max(1,(len(rows)+PAGE_SIZE-1)//PAGE_SIZE)
    number=int(page)
    if not 1<=number<=pages:
        raise ValueError(f'Dostepne strony: 1..{pages}.')
    excerpt=rows[(number-1)*PAGE_SIZE:number*PAGE_SIZE]
    note=(f' UWAGA: inne sekcje OLC tez sie roznia: {", ".join(other[:8])}'
          +(' i kolejne.' if len(other)>8 else '.') if other else '')
    return (f'AKTUALIZACJA POROWNAJ {number}/{pages}: {len(rows)} zmienionych pol '
            'w 8 dziedzinach. '+('; '.join(excerpt) or 'BRAK')+'.'+note+
            ' Tylko odczyt, bez publikacji.')


def preflight(session,service):
    old_draft=json.dumps(service.draft,ensure_ascii=False,sort_keys=True)
    old_active=json.dumps(service.active,ensure_ascii=False,sort_keys=True)
    rev=service.revision
    db=service.conn
    changes=db.total_changes
    msg=service.apply(session.server,'PRZEGLAD',dry_run=True)
    if (rev!=service.revision or changes!=db.total_changes or
        old_draft!=json.dumps(service.draft,ensure_ascii=False,sort_keys=True) or
        old_active!=json.dumps(service.active,ensure_ascii=False,sort_keys=True)):
        raise RuntimeError('PRZEDPUBLIKACJA: niespodziewana zmiana stanu, przerwij publikacje.')
    digest=hashlib.sha256(old_draft.encode('utf-8')).hexdigest()[:12]
    return f'{msg} Odcisk DRAFT {digest}. Nastepnie admin live aktywuj POTWIERDZAM.'


async def dispatch_v8900(session,cmd,tail):
    args=str(tail or '').strip()
    parts=args.split()
    matched=(cmd=='pomoc' and args=='47') or (
        cmd=='aktualizacja' and bool(parts) and (
            parts[0]=='porownaj' or parts[:2]==['publikacja','sprawdz']))
    if not matched:
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif parts[0]=='porownaj' and len(parts) in (1,2):
            out=comparison(service,parts[1] if len(parts)==2 else '1')
        elif parts==['publikacja','sprawdz']:
            out=preflight(session,service)
        else:
            raise ValueError('Uzyj aktualizacja porownaj [STRONA] albo aktualizacja publikacja sprawdz.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RuntimeError) as exc:
        out='ADMIN LIVE V89: '+str(exc)[:400]
    await session.send(out)
    return True
