# -*- coding: utf-8 -*-
"""v90: durable OLC revision history, verified snapshots and DRAFT-only restore.

No production content is altered by history listing, audit or restore plans.
The existing `admin live aktywuj POTWIERDZAM` remains the only publisher.
"""
from __future__ import annotations

import copy
import hashlib
import json

from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.live_content_v1204 import LiveContentV1204

SLOT = 'adminlive9000_revisions_plan'
UNDO = 'adminlive9000_revisions_undo'
PAGE = 6
HELP = (
    'ADMIN LIVE POMOC 48: rewizje lista [STRONA] - historia publikacji OLC po 6 wpisow; '
    'rewizje audyt - spojnosc zapisanych rewizji i aktualnej bazy; '
    'rewizje karta NUMER - odcisk migawki i zakres zmian; '
    'rewizje porownaj STARA NOWA [STRONA] - szczegolowe roznice migawek; '
    'rewizje przywroc plan NUMER - bezpieczny plan przywrocenia dawnej rewizji TYLKO w DRAFT; '
    'rewizje przywroc zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'To NIE cofa EXP, kont, postaci, ekwipunku ani zadan graczy. '
    'Aktywacja wymaga osobno admin live aktualizacja publikacja sprawdz i admin live aktywuj POTWIERDZAM.'
)


def _number(raw, *, allow_zero=False):
    if not isinstance(raw,str) or not raw.isascii() or not raw.isdecimal() or len(raw)>10:
        raise ValueError('Wymagany numer rewizji / strony (cyfry 0-9).')
    n=int(raw)
    if n < (0 if allow_zero else 1):
        raise ValueError('Niepoprawny numer rewizji / strony.')
    return n


def _json(data):
    return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def _fingerprint(data):
    return hashlib.sha256(_json(data).encode('utf-8')).hexdigest()[:16]


def _db_current(service):
    row=service.conn.execute('SELECT revision,payload FROM live_content_v1204 WHERE id=1').fetchone()
    if row is None:
        if service.revision!=0:
            raise ValueError('Konflikt SQLite: brak zapisanej aktywnej rewizji.')
        if service.active!=service._compat({}):
            raise ValueError('Konflikt SQLite: rewizja zerowa nie jest pusta.')
    else:
        try: saved=service._compat(json.loads(row['payload']))
        except (TypeError,KeyError,ValueError) as exc:
            raise ValueError('Uszkodzony aktywny zapis OLC w SQLite.') from exc
        if int(row['revision'])!=service.revision or saved!=service.active:
            raise ValueError('Konflikt SQLite: inna rewizja lub zawartosc niz w pamieci. Nie publikuj; sprawdz restart serwera.')
    return row


def snapshot(service,revision):
    _db_current(service)
    if revision > service.revision:
        raise ValueError('Rewizja nie istnieje.')
    if revision == service.revision:
        return copy.deepcopy(service.active)
    row=service.conn.execute('SELECT payload FROM live_content_history_v1204 WHERE revision=?',(revision+1,)).fetchone()
    if row is None:
        raise ValueError(f'Brak migawki rewizji {revision}. Przywracanie zablokowane.')
    try:
        payload=service._compat(json.loads(row['payload']))
        service.validate(payload)
        return payload
    except (TypeError,ValueError,KeyError,OverflowError) as exc:
        raise ValueError(f'Migawka rewizji {revision} jest niepoprawna: {str(exc)[:140]}') from exc


def audit(service):
    _db_current(service)
    rows=service.conn.execute('SELECT revision,payload FROM live_content_history_v1204 ORDER BY revision').fetchall()
    indices=[int(row['revision']) for row in rows]
    if indices != list(range(1,service.revision+1)):
        raise ValueError('HISTORIA NIESPOJNA: brak rewizji lub luki w dzienniku. Przywracanie zablokowane.')
    for row in rows:
        index=int(row['revision'])
        try:
            record=service._compat(json.loads(row['payload']))
            service.validate(record)
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            raise ValueError(f'HISTORIA NIESPOJNA: uszkodzona migawka {index-1}. {str(exc)[:100]}') from exc
    return (f'REWIZJE AUDYT OK: aktywna {service.revision}; poprzednie migawki {len(rows)}; '
            f'odcisk ACTIVE {_fingerprint(service.active)}; '
            'SQLite zgodne z pamiecia; brak luk i bledow struktury. '
            'To kontrola spojnosc, nie kryptograficzny dowod autentycznosci i nie backup calej bazy.')


def listing(service,page='1'):
    _db_current(service)
    number=_number(page)
    rows=service.conn.execute('SELECT revision,admin_login,created_at FROM live_content_history_v1204 ORDER BY revision DESC').fetchall()
    pages=max(1,(len(rows)+1+PAGE-1)//PAGE)
    if number>pages:raise ValueError(f'Historia: dostepne strony 1..{pages}.')
    index=[(service.revision,'AKTYWNA','-')]
    index.extend((int(r['revision'])-1,'zapisana',str(r['created_at'])) for r in rows)
    shown=index[(number-1)*PAGE:number*PAGE]
    items=[f'{rev} ({state}, {when})' for rev,state,when in shown]
    return f'REWIZJE LISTA {number}/{pages}: '+('; '.join(items) or 'BRAK')+'. Tylko odczyt.'


def card(service,number):
    target=_number(number,allow_zero=True)
    obj=snapshot(service,target)
    sections=sorted(name for name in obj if obj[name]!=service.active[name])
    return (f'REWIZJE KARTA {target}: odcisk {_fingerprint(obj)}, '
            f'rozne sekcje wzgledem ACTIVE {len(sections)}: '+(', '.join(sections[:15]) or 'BRAK')+
            (f'; oraz {len(sections)-15} kolejnych.' if len(sections)>15 else '.')+
            ' Brak zmian; przywrocenie wymaga osobnego planu i potwierdzenia.')


_MISSING = object()


def _short(value):
    if value is _MISSING:return 'AUTO'
    encoded=_json(value)
    return encoded if len(encoded)<=100 else encoded[:97]+'...'


def compare(service,older,newer,page='1'):
    a=snapshot(service,_number(older,allow_zero=True))
    b=snapshot(service,_number(newer,allow_zero=True))
    lines=[]
    # Compare all persisted content domains, not just the eight batch editors.
    for section in sorted(a):
        left=a[section];right=b[section]
        if left==right:continue
        if isinstance(left,dict) and isinstance(right,dict):
            for key in sorted(left.keys()|right.keys()):
                av=left.get(key,_MISSING);bv=right.get(key,_MISSING)
                if av==bv:continue
                if isinstance(av,dict) and isinstance(bv,dict):
                    for field in sorted(av.keys()|bv.keys()):
                        before=av.get(field,_MISSING);after=bv.get(field,_MISSING)
                        if before!=after:
                            lines.append(f'{section}/{key}.{field}: {_short(before)} -> {_short(after)}')
                else:lines.append(f'{section}/{key}: {_short(av)} -> {_short(bv)}')
        else:lines.append(f'{section}: {_short(left)} -> {_short(right)}')
    index=_number(page)
    pages=max(1,(len(lines)+PAGE-1)//PAGE)
    if index>pages:raise ValueError(f'Porownanie: strony 1..{pages}.')
    output=lines[(index-1)*PAGE:index*PAGE]
    return (f'REWIZJE POROWNAJ {older} -> {newer}, STRONA {index}/{pages}: '
            f'roznic {len(lines)}; '+('; '.join(output) or 'BRAK')+'. Tylko odczyt.')


def plan(session,service,number):
    setattr(session,SLOT,None)
    target=_number(number,allow_zero=True)
    # Reject broken or incomplete histories before allowing a restore plan.
    audit(service)
    candidate=snapshot(service,target)
    if candidate==service.draft:
        raise ValueError('DRAFT juz odpowiada tej rewizji.')
    # Validation is on the whole historical payload; never bypass normal OLC constraints.
    service.validate(candidate)
    # Reuse the exact live activation safety guards on the proposed snapshot;
    # do not temporarily replace the shared DRAFT or ACTIVE data.
    service.apply(session.server, 'HISTORIA-OLC', dry_run=True, candidate=candidate)
    # Immutable published identifiers and professions cannot vanish: durable player data may refer to them.
    for section in ('items','quests','skills'):
        missing=set(service.active[section])-set(candidate[section])
        if missing:
            raise ValueError(f'Historia {target}: niedozwolone usuniecie opublikowanych {section} ({len(missing)}).')
    if set(service.active['v24_rules']['professions'])-set(candidate['v24_rules']['professions']):
        raise ValueError('Historia: brak posiadanych przez graczy profesji w dawnej rewizji.')
    _plan(session,SLOT,service.draft,service.active,candidate,f'REWIZJA {target} PRZYWROC')
    return (f'REWIZJE PRZYWROC PLAN {target}: pelny historyczny swiat zweryfikowany, '
            f'odcisk {_fingerprint(candidate)}. Nic nie zapisano. '
            'rewizje przywroc zatwierdz POTWIERDZAM. '
            'Zmiana dotyczy tylko DRAFT; publikacja ponownie sprawdzi walki, questy i graczy.')


async def dispatch_v9000(session,cmd,tail):
    args=str(tail or '').strip();parts=args.split()
    matched=(cmd=='pomoc' and args=='48') or (cmd=='rewizje' and bool(parts))
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif parts[0]=='lista' and len(parts) in (1,2):out=listing(service,parts[1] if len(parts)==2 else '1')
        elif parts==['audyt']:out=audit(service)
        elif parts[0]=='karta' and len(parts)==2:out=card(service,parts[1])
        elif parts[0]=='porownaj' and len(parts) in (3,4):
            out=compare(service,parts[1],parts[2],parts[3] if len(parts)==4 else '1')
        elif parts[:2]==['przywroc','plan'] and len(parts)==3:out=plan(session,service,parts[2])
        elif parts==['przywroc','zatwierdz','POTWIERDZAM']:
            _db_current(service)
            out=_commit(session,service,SLOT,UNDO)
        elif parts==['przywroc','cofnij','POTWIERDZAM']:
            _db_current(service)
            out=_undo(session,service,SLOT,UNDO)
        elif parts==['przywroc','anuluj']:
            setattr(session,SLOT,None);out='REWIZJE: plan anulowany, brak zmian.'
        else:raise ValueError('Wpisz admin live pomoc 48. Wymagane POTWIERDZAM.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RuntimeError) as exc:
        out='ADMIN LIVE V90: '+str(exc)[:380]
    await session.send(out)
    return True
