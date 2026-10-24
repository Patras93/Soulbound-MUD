# -*- coding: utf-8 -*-
"""v71 offline character maintenance, positive CAS, atomic audit and one-step undo.
Only intrinsic stats and deaths; progression/economy/name are explicitly protected.
"""
from __future__ import annotations
import re

FIELDS={'strength','dexterity','constitution','intelligence','willpower','charisma','deaths'}
HELP=('ADMIN LIVE POMOC 31: postacie karta NAZWA; postacie plan NAZWA POLE LICZBA; '
    'postacie zatwierdz POTWIERDZAM; postacie cofnij POTWIERDZAM; postacie anuluj. '
    'Tylko postaci OFFLINE, pojedyncze pole na raz: strength, dexterity, '
    'constitution, intelligence, willpower, charisma, deaths. '
    'Zmiana jest atomowa z wpisem w admin_actions; jedna operacja cofania. '
    'Poziomy, EXP, przedmioty, konta i waluta sa CHRONIONE. Backup przed zmianami.')


def _row(session,name):
    if not isinstance(name,str) or not 1<=len(name)<=40 or any(ord(ch)<32 for ch in name):
        raise ValueError('Niepoprawna nazwa postaci.')
    row=session.server.db.conn.execute(
        'SELECT account_id,name,strength,dexterity,constitution,intelligence,willpower,charisma,deaths FROM characters WHERE name=? COLLATE NOCASE',(name,)).fetchone()
    if row is None:raise ValueError('Nie ma postaci o tej nazwie.')
    return dict(row)


def _offline(session,name):
    if any(not getattr(s,'closed',False) and getattr(s,'character',None) is not None
           and getattr(s.character,'name','').casefold()==name.casefold()
           for s in getattr(session.server,'sessions',())):
        raise ValueError('Postac jest online: najpierw bezpiecznie ja wyloguj.')


def card(session,name):
    row=_row(session,name)
    _offline(session,row['name'])
    return ('POSTAC OFFLINE '+row['name']+': '+
            ', '.join(f'{f}={row[f]}' for f in sorted(FIELDS))+'. '
            'Bez zmiany poziomow, EXP, waluty i bazy.')


def plan(session,name,field,raw):
    session.adminlive7100_character_plan=None
    if field not in FIELDS:raise ValueError('Pole nieobslugiwane; pomoc 31.')
    if not raw.isascii() or not raw.isdecimal() or len(raw)>12:raise ValueError('Wpisz liczbe calkowita.')
    value=int(raw)
    if not (0<=value<=1_000_000_000 if field=='deaths' else 1<=value<=1_000_000_000):
        raise ValueError('Wartosc spoza bezpiecznego zakresu 1..1000000000 (deaths od zera).')
    row=_row(session,name);_offline(session,row['name'])
    if row[field]==value:raise ValueError('Nowa wartosc jest juz ustawiona.')
    session.adminlive7100_character_plan=(row['account_id'],row['name'],field,row[field],value)
    return (f'POSTAC PLAN {row["name"]}: {field} {row[field]} -> {value}. '
            'Tylko offline, nie zmienia rozwoju klas ani poziomow. postacie zatwierdz POTWIERDZAM.')


def _write(session,account_id,name,field,old,new,action):
    _offline(session,name)
    db=session.server.db
    # Only internal enum fields are interpolated: SQL injection not possible.
    with db.conn:
        cur=db.conn.execute(f'UPDATE characters SET {field}=? WHERE account_id=? AND {field}=?',(new,account_id,old))
        if cur.rowcount!=1:raise ValueError('Postac zmienila sie od planu. Operacja przerwana.')
        admin=db.account_name(session.master_account_id)
        db.conn.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
            (str(admin)[:64], action, f'{name}:{field} {old}->{new}'[:96]))
        db.conn.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
            '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')


def commit(session):
    data=getattr(session,'adminlive7100_character_plan',None)
    if not data:raise ValueError('Brak planu postaci.')
    session.adminlive7100_character_plan=None
    _write(session,*data,'admin_live_v7100_set')
    session.adminlive7100_character_undo=data
    return f'POSTAC ZAPISANA: {data[1]}, {data[2]} {data[3]} -> {data[4]}. Audyt w bazie, bez zmiany konta/EXP.'


def undo(session):
    data=getattr(session,'adminlive7100_character_undo',None)
    if not data:raise ValueError('Brak ostatniej edycji postaci.')
    ident,name,field,old,new=data
    _write(session,ident,name,field,new,old,'admin_live_v7100_undo')
    session.adminlive7100_character_undo=None
    return f'POSTAC COFNIETO: {name}, {field}={old}. Audyt zapisany.'


async def dispatch_v7100_characters(session,group,raw):
    if not ((group=='pomoc' and raw.strip()=='31') or group=='postacie'):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    p=str(raw or '').split()
    try:
        if group=='pomoc':out=HELP
        elif len(p)==2 and p[0]=='karta':out=card(session,p[1])
        elif len(p)==4 and p[0]=='plan':out=plan(session,p[1],p[2],p[3])
        elif p==['zatwierdz','POTWIERDZAM']:out=commit(session)
        elif p==['cofnij','POTWIERDZAM']:out=undo(session)
        elif p==['anuluj']:
            session.adminlive7100_character_plan=None;out='POSTAC: plan anulowany.'
        else:raise ValueError('postacie karta NAZWA / plan NAZWA POLE LICZBA / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE POSTACIE: '+str(exc)[:240]
    await session.send(out)
    return True
