# -*- coding: utf-8 -*-
"""v96: atomic offline corrections of *existing* class and learned-skill mastery.

Never creates/unlocks a class or skill, changes class slots, grants skill rewards,
consumes EXP bank, modifies combat counters, or touches online character state.
"""
from __future__ import annotations
import re
from core.live_level_caps_v5200 import cap, TECHNICAL_CEILING
from core.progression_resources import class_mastery_xp_to_next, skill_xp_to_next
from core.classes_skills import CLASSES, CLASS_SKILLS
from systems.admin_live_progress_v9500 import _row, _offline_account, MAX_XP

HELP = ('ADMIN LIVE POMOC 54: postacie bieglosci karta NAZWA [STRONA]; '
        'postacie bieglosci plan NAZWA | klasa:Mag=45,200; skill:SKILL_ID=7,30; '
        'postacie bieglosci zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
        'Do 16 istniejacych, odblokowanych klas i wyuczonych skilli jednej postaci OFFLINE. '
        'Jedna transakcja SQLite + CAS, audyt i jedno cofniecie. Bez nadawania klas, '
        'nauki skilli, zmian slotow, licznikow uzyc ani nagrod. '
        'postacie expbank karta NAZWA [STRONA] tylko odczytuje bank EXP. '
        'Komendy nie zmieniaja banku EXP. Kopia bazy przed naprawa.')
_NAME = re.compile(r'^(klasa|skill):(.+?)\s*=\s*([0-9]{1,8})\s*,\s*([0-9]{1,16})$', re.I)
_PAGE = 7


def _identity(session, name):
    row = _row(session, name)
    _offline_account(session, row)
    return row


def _catalog_skill_ids():
    return {str(skill['id']) for entries in CLASS_SKILLS.values() for skill in entries}


def _valid_key(kind, key):
    if not key or len(key) > 160 or any(ord(c)<32 or ord(c)==127 for c in key):
        raise ValueError('Zla nazwa klasy lub identyfikator skilla.')
    if kind == 'klasa' and key not in {name for name,*_ in CLASSES}:
        raise ValueError('Klasa nie istnieje w aktywnym katalogu.')
    if kind == 'skill' and key not in _catalog_skill_ids():
        raise ValueError('Skill nie istnieje w aktywnym katalogu.')


def _current(session, account, kind, key):
    con = session.server.db.conn
    if kind == 'klasa':
        r = con.execute('SELECT level,xp FROM class_progress WHERE account_id=? AND class_name=?', (account,key)).fetchone()
    else:
        r = con.execute('SELECT p.level,p.xp FROM skill_progress p '
                        'JOIN learned_skills l ON l.account_id=p.account_id AND l.skill_id=p.skill_id '
                        'WHERE p.account_id=? AND p.skill_id=?', (account,key)).fetchone()
    if r is None:
        raise ValueError(f'{kind} {key}: brak odblokowania lub zapisanego postepu. Niczego nie utworzono.')
    return int(r[0]),int(r[1])


def _progress_limit(kind):
    value=cap('bieglosc' if kind=='klasa' else 'skille')
    return min(TECHNICAL_CEILING, value if value is not None else TECHNICAL_CEILING)


def _target(kind, level_str, xp_str):
    level,xp=int(level_str),int(xp_str)
    limit=_progress_limit(kind)
    if not 1<=level<=limit:raise ValueError(f'{kind}: poziom musi byc 1..{limit}.')
    if not 0<=xp<=MAX_XP:raise ValueError('EXP przekracza bezpieczny zakres SQLite.')
    # An offline repair should not silently trigger a new level on the next action.
    if level<limit:
        threshold=(class_mastery_xp_to_next if kind=='klasa' else skill_xp_to_next)(level)
        if 0<threshold<=MAX_XP and xp>=threshold:
            raise ValueError(f'{kind}: EXP {xp} osiaga prog {threshold}; podaj poprawny poziom i pozostale EXP.')
    return level,xp


def _page(rows, page, label):
    if not 1<=page<=max(1,(len(rows)+_PAGE-1)//_PAGE):
        raise ValueError('Niepoprawna strona raportu.')
    start=(page-1)*_PAGE
    return (f'{label}: strona {page}/{max(1,(len(rows)+_PAGE-1)//_PAGE)}, '
            f'łącznie {len(rows)}. ' + ('; '.join(rows[start:start+_PAGE]) if rows else 'brak danych')+'.')


def card(session,name,page=1):
    row=_identity(session,name);con=session.server.db.conn
    classes=con.execute('SELECT class_name,level,xp FROM class_progress WHERE account_id=? ORDER BY class_name',
                        (row['account_id'],)).fetchall()
    skills=con.execute('SELECT s.skill_id,s.level,s.xp FROM skill_progress s '
                       'JOIN learned_skills l ON l.account_id=s.account_id AND l.skill_id=s.skill_id '
                       'WHERE s.account_id=? ORDER BY s.skill_id',(row['account_id'],)).fetchall()
    entries=[f'klasa:{n}={lev},{xp}' for n,lev,xp in classes]+[f'skill:{n}={lev},{xp}' for n,lev,xp in skills]
    return _page(entries,page,'BIEGLOSCI OFFLINE '+row['name'])


def bank_card(session,name,page=1):
    row=_identity(session,name)
    entries=[]
    for kind,source,balance in session.server.db.conn.execute(
            'SELECT kind,source_key,balance FROM experience_bank_v2011 WHERE account_id=? ORDER BY kind,source_key',
            (row['account_id'],)):
        raw=str(balance)
        # Do not normalize corrupt balances silently or write to the bank.
        try:
            value=int(raw)
            marker='UWAGA:ujemne' if value<0 else ('UWAGA:niekanoniczne' if not re.fullmatch(r'(?:0|[1-9][0-9]*)',raw) else '')
        except (ValueError,OverflowError):
            marker='UWAGA:niepoprawne'
        entries.append(f'{kind}:{source or "domyslne"}={raw[:80]} {marker}'.strip())
    return _page(entries,page,'BANK EXP ODCZYT '+row['name'])+' Bez wyplaty i bez zmiany salda.'


def plan(session,name,raw):
    session.adminlive9600_plan=None
    if not 1<=len(raw)<=2500:raise ValueError('Plan 1..2500 znakow.')
    items=[item.strip() for item in raw.split(';')]
    if not 1<=len(items)<=16 or not all(items):raise ValueError('Wymagane 1..16 zmian.')
    ident=_identity(session,name); account=ident['account_id']; selected={};summary=[]
    for item in items:
        m=_NAME.fullmatch(item)
        if m is None:raise ValueError('Format: klasa:NAZWA=POZIOM,EXP; skill:SKILL_ID=POZIOM,EXP.')
        kind,key=m[1].lower(),m[2].strip()
        _valid_key(kind,key)
        pair=(kind,key)
        if pair in selected:raise ValueError('Powtorzona dziedzina: '+key)
        old=_current(session,account,kind,key)
        # Refuse a repair that could never be undone due to invalid old values.
        _target(kind,str(old[0]),str(old[1]))
        new=_target(kind,m[3],m[4])
        if old==new:raise ValueError('Wartosc juz ustawiona: '+key)
        selected[pair]=(old,new)
        summary.append(f'{kind}:{key} {old[0]}/{old[1]} -> {new[0]}/{new[1]}')
    data=(account,ident['name'],selected)
    session.adminlive9600_plan=data
    return ('BIEGLOSCI PLAN '+ident['name']+': '+'; '.join(summary)+'. Brak zapisu. '
            'Zatwierdz: postacie bieglosci zatwierdz POTWIERDZAM.')


def _write(session,data,reverse=False):
    account,name,changes=data
    row=_identity(session,name)
    if row['account_id']!=account:raise ValueError('Zmiana tozsamosci postaci, odmowa zapisu.')
    db=session.server.db; con=db.conn
    # Pre-validate every key and target *before* beginning a write transaction.
    for (kind,key),(old,new) in changes.items():
        _valid_key(kind,key)
        level,xp=old if reverse else new
        _target(kind,str(level),str(xp))
    con.execute('SAVEPOINT adminlive9600_mastery')
    try:
        for (kind,key),(old,new) in sorted(changes.items()):
            expected=new if reverse else old
            target=old if reverse else new
            if kind=='klasa':
                cur=con.execute('UPDATE class_progress SET level=?,xp=? '
                                'WHERE account_id=? AND class_name=? AND level=? AND xp=?',
                                (*target,account,key,*expected))
            else:
                cur=con.execute('UPDATE skill_progress SET level=?,xp=? '
                                'WHERE account_id=? AND skill_id=? AND level=? AND xp=? '
                                'AND EXISTS (SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?)',
                                (*target,account,key,*expected,account,key))
            if cur.rowcount!=1:raise ValueError('Wykryto obca zmiane lub usuniete odblokowanie: '+key+'. Caly pakiet odrzucony.')
        admin=str(db.account_name(session.master_account_id))[:64]
        con.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
                    (admin,'admin_live_v9600_mastery_undo' if reverse else 'admin_live_v9600_mastery',
                     (name+':'+str(len(changes))+' wpisow')[:96]))
        con.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
                    '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')
        con.execute('RELEASE SAVEPOINT adminlive9600_mastery')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive9600_mastery')
        con.execute('RELEASE SAVEPOINT adminlive9600_mastery')
        raise


def commit(session):
    data=getattr(session,'adminlive9600_plan',None)
    if not data:raise ValueError('Brak planu biegłości.')
    _write(session,data)
    session.adminlive9600_plan=None
    session.adminlive9600_undo=data
    return f'BIEGLOSCI ZAPISANO {data[1]}: {len(data[2])} wpisow, audyt SQLite. Bez nagrod.'


def undo(session):
    data=getattr(session,'adminlive9600_undo',None)
    if not data:raise ValueError('Brak operacji do cofniecia.')
    _write(session,data,reverse=True)
    session.adminlive9600_undo=None
    return f'BIEGLOSCI COFNIETO {data[1]}: {len(data[2])} wpisow, audyt SQLite.'


async def dispatch_v9600(session,group,tail):
    words=str(tail or '').strip().split()
    relevant=(group=='pomoc' and words==['54']) or (group=='postacie' and words[:1] in (['bieglosci'],['expbank']))
    if not relevant:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':out=HELP
        elif words[:2]==['bieglosci','karta'] and len(words) in (3,4):out=card(session,words[2],int(words[3]) if len(words)==4 else 1)
        elif words[:2]==['expbank','karta'] and len(words) in (3,4):out=bank_card(session,words[2],int(words[3]) if len(words)==4 else 1)
        elif words[:2]==['bieglosci','plan'] and '|' in tail:
            name,raw=tail.split('bieglosci plan',1)[1].split('|',1)
            out=plan(session,name.strip(),raw.strip())
        elif words==['bieglosci','zatwierdz','POTWIERDZAM']:out=commit(session)
        elif words==['bieglosci','cofnij','POTWIERDZAM']:out=undo(session)
        elif words==['bieglosci','anuluj']:
            session.adminlive9600_plan=None;out='BIEGLOSCI: plan anulowano.'
        else:raise ValueError('Bieglosci karta/plan/zatwierdz/cofnij/anuluj; expbank karta NAZWA [STRONA]; pomoc 54.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE BIEGLOSCI: '+str(exc)[:240]
    await session.send(out)
    return True
