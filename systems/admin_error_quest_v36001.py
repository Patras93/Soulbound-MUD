# -*- coding: utf-8 -*-
"""Safe admin error triage by SB-ID or logged ordinal; conservative quest repair.

A runtime exception is not proof of any particular character/quest corruption.
Never treat marking a report resolved as a code fix. Guard writes by the precise
existing invariant implemented by Admin Guardian 2.0: negative active progress,
offline character, and the unchanged current row.
"""
import re

HELP = ('ADMIN BLAD: lista [ILE] / numer N / diagnoza N / questy NICK / skan NICK [ILE] / trop NICK QUEST_ID / npc QUEST_ID / '
        'napraw N NICK QUEST_ID POTWIERDZAM. N: numer z listy albo SB-XXXXXXXX. '
        'Zgloszenie pozostaje aktywne do potwierdzenia naprawy przyczyny.')


def _resolve_error(conn, number):
    number = str(number).strip().upper()
    if re.fullmatch(r'SB-[0-9A-F]{8}', number):
        return conn.execute('SELECT rowid AS numer, * FROM admin_errors_v1224 WHERE id=?',
                            (number,)).fetchone()
    if re.fullmatch(r'[1-9][0-9]{0,8}', number):
        return conn.execute('SELECT rowid AS numer, * FROM admin_errors_v1224 WHERE rowid=?',
                            (int(number),)).fetchone()
    raise ValueError('Podaj numer bledu z admin blad lista lub kod SB-XXXXXXXX.')


def _is_quest_incident(row):
    # Only trusted internal metadata is considered; runtime error messages
    # do not include user input, quest ID, or affected account.
    return any('quest' in str(row[k] or '').lower() for k in ('file', 'handler', 'subsystem'))


def _error_diagnosis(row):
    kind = str(row['exception'] or '')
    quest = _is_quest_incident(row)
    if quest:
        return ('Obszar QUEST. Wyjatek '+kind+'. Nie wiadomo, ktorej postaci '
                'dotyczy; sprawdz admin blad questy NICK i admin questdiag NICK QUEST_ID. '
                'Automatyczna korekta tylko przy ujemnym postepie aktywnego questa '
                'na postaci offline. Inne bledy wymagaja poprawki kodu albo recznej diagnozy.')
    return ('Wyjatek '+kind+' poza rozpoznana obsluga questow. '
            'Nie ma bezpiecznej automatycznej naprawy po samym numerze. '
            'Sprawdz log serwera i poprawke kodu; nie oznaczaj jako naprawiony bez testu.')


def _error_line(row):
    status = 'OZNACZONY' if row['resolved_at'] else 'AKTYWNY'
    return (f"NUMER {row['numer']} / {row['id']}: {row['exception']}; "
            f"{row['file']}:{row['line']}; modul {row['subsystem']}; "
            f"handler {row['handler']}; status {status}.")


async def handle_error_quest_command(s, parts):
    """True for new subcommands; allow legacy `admin blad SB-...` unchanged."""
    if not parts or parts[0].casefold() not in ('blad', 'błąd'):
        return False
    if len(parts) <= 1:
        await s.send(HELP)
        return True
    sub = parts[1].casefold()
    if sub not in ('lista', 'numer', 'diagnoza', 'analiza', 'questy', 'napraw', 'skan', 'trop', 'npc'):
        return False
    conn = s.server.db.conn
    try:
        if sub in ('skan','trop','npc'):
            from systems.admin_quest_diagnostics_v36002 import scan_quests, trace_quest, npc_quest
            if sub == 'skan':
                if len(parts) not in (3,4): raise ValueError('Uzycie: admin blad skan NICK [ILE].')
                amount=_int_number(parts[3] if len(parts)==4 else '20',1,30)
                lines=scan_quests(s.server.db,parts[2],amount)
            elif sub == 'trop':
                if len(parts)!=4: raise ValueError('Uzycie: admin blad trop NICK QUEST_ID.')
                lines=trace_quest(s.server.db,parts[2],parts[3])
            else:
                if len(parts)!=3: raise ValueError('Uzycie: admin blad npc QUEST_ID.')
                lines=npc_quest(parts[2])
            for line in lines: await s.send(line)
            return True
        if sub == 'lista':
            if len(parts)>3: raise ValueError(HELP)
            amount = _int_number(parts[2] if len(parts)==3 else '20',1,50)
            rows = conn.execute('SELECT rowid AS numer,* FROM admin_errors_v1224 ORDER BY rowid DESC LIMIT ?',
                                (amount,)).fetchall()
            await s.send(f'BLEDY SERWERA: pokazuje {len(rows)} ostatnich. Numery sa wazne dopoki wpis istnieje.')
            for row in rows:
                await s.send(_error_line(row))
            return True
        if sub == 'questy':
            if len(parts)!=3: raise ValueError('Uzycie: admin blad questy NICK.')
            name=parts[2]
            character=conn.execute('SELECT name,account_id FROM characters WHERE name=? COLLATE NOCASE',
                                   (name,)).fetchone()
            if not character: raise ValueError('Brak postaci o tym nicku.')
            rows=conn.execute('SELECT quest_id,progress FROM quests WHERE account_id=? AND status=? AND progress<0 ORDER BY quest_id LIMIT 21',
                              (character['account_id'],'active')).fetchall()
            if not rows: await s.send(f"QUESTY {character['name']}: brak ujemnych postepow. Pozostale przyczyny wymagaja analizy.")
            else:
                await s.send(f"QUESTY {character['name']}: {min(len(rows),20)} ujemnych postepow" + (' (wiecej niz 20)' if len(rows)>20 else '') + '.')
                for row in rows[:20]: await s.send(f"{row['quest_id']}: postep {row['progress']}; admin questdiag {character['name']} {row['quest_id']}.")
            return True
        if sub in ('numer','diagnoza','analiza'):
            if len(parts)!=3: raise ValueError('Uzycie: admin blad diagnoza NUMER lub SB-XXXXXXXX.')
            row=_resolve_error(conn,parts[2])
            if not row: raise ValueError('Brak tego numeru w rejestrze. Nie podejmowano zmian.')
            await s.send(_error_line(row))
            if sub!='numer': await s.send(_error_diagnosis(row))
            return True
        if len(parts)!=6 or parts[5]!='POTWIERDZAM':
            raise ValueError('Uzycie: admin blad napraw NUMER NICK QUEST_ID POTWIERDZAM.')
        row=_resolve_error(conn,parts[2])
        if not row: raise ValueError('Brak bledu w rejestrze. Nic nie zmieniono.')
        if row['resolved_at']:
            raise ValueError('Zgloszenie oznaczone jako naprawione. Najpierw diagnoza; brak zapisu.')
        if not _is_quest_incident(row):
            raise ValueError('To nie jest blad z obszaru questow. Brak bezpiecznej automatycznej poprawki.')
        from systems.admin_guardian2_v3600 import _quest_repair, _quest_data
        nick,qid=parts[3:5]
        # The repair function rechecks the actual account, offline state, and
        # exact progress before any mutation; nothing inferred from report ID.
        await s.send('DIAGNOZA PRZED: '+_quest_data(s,nick,qid))
        result=_quest_repair(s,nick,qid)
        s.server.db.record_admin_action_v1224(
            s.server.db.account_name(s.master_account_id),
            'g2_error_quest_repair', f"{row['id']}:{nick}/{qid}"[:96])
        await s.send(result+' Zgloszenie '+row['id']+' pozostaje aktywne: '
                     'sprawdz przyczyne bledu i testuj komende, potem admin blad naprawiony '+row['id']+'.')
        return True
    except (ValueError, TypeError, OverflowError) as exc:
        await s.send('ADMIN BLAD: '+str(exc)[:290])
        return True


def _int_number(text,minimum,maximum):
    if not str(text).isdecimal(): raise ValueError('Podaj dodatni numer.')
    value=int(text)
    if not minimum<=value<=maximum: raise ValueError(f'Numer: zakres {minimum}-{maximum}.')
    return value
