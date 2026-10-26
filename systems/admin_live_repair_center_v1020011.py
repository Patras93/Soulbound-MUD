# -*- coding: utf-8 -*-
"""Soulbound v102.00.11: bounded, owner-only runtime error triage and safe quest recovery.

No dynamic Python execution, source rewriting or guessing of fixes. Existing
Guardian 2.0 CAS quest progress repair and its persistent undo ledger are reused.
The SB error register intentionally contains no command arguments or traceback.
"""
from __future__ import annotations

import re
import sqlite3

from systems.admin_error_quest_v36001 import _resolve_error, _is_quest_incident, _error_line

HELP = (
    'CENTRUM NAPRAW: admin live bledy [lista ILE] / pokaz NUMER / diagnoza NUMER; '
    'admin live napraw NUMER [NICK QUEST_ID] / sprawdz NUMER NICK QUEST_ID / '
    'zastosuj NUMER NICK QUEST_ID POTWIERDZAM / cofnij NUMER_KOREKTY POTWIERDZAM. '
    'NUMER: numer z listy lub SB-XXXXXXXX. Bez zgody i sprawdzenia nic nie zapisuje.'
)


def _row(conn, token):
    try:
        return _resolve_error(conn, token)
    except sqlite3.OperationalError as exc:
        raise ValueError('Nie znaleziono rejestru bledow; sprawdz migracje bazy. Nic nie zmieniono.') from exc


def _diagnosis(row):
    kind = str(row['exception'] or '')
    file = str(row['file'] or '').lower()
    handler = str(row['handler'] or '').lower()
    if kind in ('NameError', 'ImportError', 'ModuleNotFoundError', 'SyntaxError', 'AttributeError', 'UnboundLocalError'):
        hint = ('Znany blad diagnostyki questaccept z v102.00.9: poprawka kodu jest w v102.00.10 i nowszych. '
                if kind in ('NameError','UnboundLocalError') and 'quest_offers.py' in file and handler in ('quests','accept_quest_id','questaccept')
                else '')
        return ('BLAD KODU: '+kind+'. '+hint+'Nie naprawiam automatycznie plikow Python. '
                'Sprawdz log i przygotuj zweryfikowane wydanie; restart/wdrozenie moze byc konieczne.')
    if _is_quest_incident(row):
        return ('OBSLUGA QUESTOW: '+kind+'. Numer SB nie wskazuje postaci ani konkretnego zadania. '
                'Mozna zdiagnozowac podany quest; JEDYNA automatyczna korekta dotyczy ujemnego postepu '
                'aktywnego zadania u gracza offline. Nie naprawia bledu Python ani innej przyczyny wyjatku.')
    if 'live_content' in file or 'admin_live' in file or handler in ('admin', 'admin_live'):
        return ('ADMIN LIVE: '+kind+'. Sprawdz admin live sprawdz i porownaj; '
                'bledne dane poprawiaj przez istniejace edycje DRAFT. Nie wprowadzono automatycznego patchowania kodu.')
    return ('BRAK ZWERYFIKOWANEJ NAPRAWY: '+kind+'. Sprawdz log serwera i diagnoze konkretnej funkcji. '
            'Nie uruchamiam dowolnego kodu i nie zmieniam danych na podstawie samego SB-ID.')


def _quest_preview(s, row, nick, qid):
    if row['resolved_at']:
        return 'Zgloszenie oznaczone jako naprawione; najpierw zweryfikuj status. Brak zapisu.'
    if not _is_quest_incident(row):
        return 'Ten blad nie dotyczy obslugi questow. Brak bezpiecznej automatycznej korekty.'
    if str(row['exception'] or '') in ('NameError','ImportError','ModuleNotFoundError','SyntaxError','AttributeError','UnboundLocalError'):
        return 'To blad kodu Python: naprawa postepu nie usunie przyczyny. Nie wykonuje zmian.'
    from systems.admin_guardian2_v3600 import _quest_row, find_online
    char, quest, state = _quest_row(s, nick, qid)
    if not state:
        return f"QUEST {char['name']} {qid}: nieprzyjety. Nic do naprawy."
    status = str(state['status'])
    progress = int(state['progress'])
    offline = not bool(find_online(s, nick))
    ready = status == 'active' and progress < 0 and offline
    return (f"QUEST {char['name']} {qid}: status {status}, postep {progress}, "
            f"gracz {'OFFLINE' if offline else 'ONLINE'}, "
            f"korekta {'MOZLIWA: ujemny postep na zero' if ready else 'NIEDOZWOLONA'}. "
            'Zgloszenie SB samo w sobie nie dowodzi przyczyny; korekta nie oznacza bledu jako naprawionego.')


async def handle_repair_center(s, cmd, tail):
    """Return True for handled commands; never bypass owner access check."""
    if cmd not in ('bledy','błędy','napraw'):
        return False
    if not s.is_admin():
        await s.send('Nieznana komenda. Wpisz help.')
        return True
    args = str(tail or '').strip().split()
    conn = s.server.db.conn
    try:
        if cmd in ('bledy','błędy'):
            sub = args[0].casefold() if args else 'lista'
            if sub in ('pomoc','help'):
                await s.send(HELP)
            elif sub == 'lista':
                if len(args)>2: raise ValueError('Uzycie: admin live bledy lista [ILE od 1 do 50].')
                limit = _positive(args[1], 50) if len(args)==2 else 20
                try:
                    rows = conn.execute('SELECT rowid AS numer,* FROM admin_errors_v1224 ORDER BY rowid DESC LIMIT ?',
                                        (limit,)).fetchall()
                except sqlite3.OperationalError as exc:
                    raise ValueError('Rejestr bledow jest niedostepny; niczego nie zmieniono.') from exc
                await s.send(f'CENTRUM NAPRAW: {len(rows)} ostatnich zgloszen. Lista nie zawiera tresci komend ani hasel.')
                for row in rows:
                    await s.send(_error_line(row))
            elif sub in ('pokaz','pokaż','diagnoza'):
                if len(args)!=2: raise ValueError('Uzycie: admin live bledy pokaz NUMER.')
                row=_row(conn,args[1])
                if row is None: raise ValueError('Nie znaleziono bledu. Nie wykonano zmian.')
                await s.send(_error_line(row))
                if sub=='diagnoza': await s.send(_diagnosis(row))
                else: await s.send('Diagnoza: admin live bledy diagnoza '+str(row['id'])+'.')
            else:
                raise ValueError(HELP)
            return True

        if not args or args[0].casefold() in ('pomoc','help'):
            await s.send(HELP)
            return True
        sub=args[0].casefold()
        if sub in ('cofnij','cofnięcie'):
            if len(args)!=3 or args[2]!='POTWIERDZAM':
                raise ValueError('Uzycie: admin live napraw cofnij NUMER_KOREKTY POTWIERDZAM.')
            number=_positive(args[1], 1000000000)
            from systems.admin_guardian2_v3600 import _quest_revert
            result=_quest_revert(s,number)
            s.server.db.record_admin_action_v1224(
                s.server.db.account_name(s.master_account_id), 'live_repair_undo_v1020011', str(number))
            await s.send(result+' Zgloszenia bledow SB pozostaja bez zmian.')
            return True
        if sub in ('sprawdz','sprawdź','zastosuj','plan'):
            if len(args)<2: raise ValueError(HELP)
            if sub=='zastosuj':
                if len(args)!=5 or args[-1]!='POTWIERDZAM':
                    raise ValueError('Uzycie: admin live napraw zastosuj NUMER NICK QUEST_ID POTWIERDZAM.')
            elif len(args)!=4:
                raise ValueError('Uzycie: admin live napraw sprawdz NUMER NICK QUEST_ID.')
            ident,nick,qid=args[1:4]
        else:
            # admin live napraw NUMER [NICK QUEST_ID] is a read-only diagnosis/plan.
            if len(args) not in (1,3): raise ValueError('Uzycie: admin live napraw NUMER [NICK QUEST_ID].')
            ident=args[0]
            nick,qid=(args[1:3] if len(args)==3 else (None,None))
        row=_row(conn,ident)
        if row is None: raise ValueError('Nie znaleziono bledu. Niczego nie zmieniono.')
        await s.send(_error_line(row))
        await s.send(_diagnosis(row))
        if nick is None:
            await s.send('Plan: podaj NICK i QUEST_ID do sprawdzenia. Numer SB nie identyfikuje postaci ani questa. Bez zmian.')
            return True
        preview=_quest_preview(s,row,nick,qid)
        await s.send(preview)
        if sub!='zastosuj':
            await s.send('Podglad bez zapisu. Dostepna korekta (jesli MOZLIWA): '
                         f'admin live napraw zastosuj {row["id"]} {nick} {qid} POTWIERDZAM.')
            return True
        if 'korekta MOZLIWA:' not in preview:
            raise ValueError('Korekta niedozwolona: warunki musza byc spelnione i sprawdzone ponownie. Brak zmian.')
        from systems.admin_guardian2_v3600 import _quest_repair
        result=_quest_repair(s,nick,qid)  # CAS and offline conditions rechecked atomically.
        s.server.db.record_admin_action_v1224(
            s.server.db.account_name(s.master_account_id), 'live_repair_quest_v1020011',
            (str(row['id'])+':'+str(nick)+'/'+str(qid))[:96])
        await s.send(result+' Zgloszenie SB pozostaje AKTYWNE do osobnego zweryfikowania przyczyny. '
                     'Aby cofnac: admin live napraw cofnij NUMER_KOREKTY POTWIERDZAM.')
        return True
    except (ValueError, TypeError, OverflowError, sqlite3.Error) as exc:
        await s.send('CENTRUM NAPRAW: '+str(exc)[:350])
        return True


def _positive(raw, maximum):
    if not re.fullmatch(r'[1-9][0-9]{0,9}',str(raw)):
        raise ValueError('Podaj dodatnia liczbe.')
    result=int(raw)
    if result>maximum: raise ValueError('Przekroczono dozwolony limit liczby.')
    return result
