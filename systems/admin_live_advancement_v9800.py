# -*- coding: utf-8 -*-
"""v98: atomic offline profession/tool (level+XP) and EXP bank corrections.

Only existing rows are corrected. No level-up calls, new unlocks, grant/payout,
rewards, counters, action history, inventory or currency changes. Bank TEXT is
preserved exactly, and long nonnegative decimal balances stay unlimited by int64.
"""
from __future__ import annotations
import re
from core.bootstrap_economy_professions import (PROFESSION_RANK_NAMES,TOOL_PROFESSION_MAP,
    profession_max_level,tool_max_level)
from core.live_level_caps_v5200 import cap,TECHNICAL_CEILING
from systems.experience_cap_v2009 import KINDS
from systems.admin_live_progress_v9500 import _row,_offline_account,MAX_XP
from config.balance import profession_xp_requirement_v1401,tool_xp_requirement_v1402
from core.progression_resources import v0190_requirement

SLOT='adminlive9800_advancement_plan';UNDO='adminlive9800_advancement_undo'
HELP=(
 'ADMIN LIVE POMOC 59: postacie postepy karta NAZWA [STRONA]; '
 'postacie postepy plan NAZWA | profesja:Wędkarstwo=10,20; narzedzie:fishing=5,100; '
 'bank:profession:Wędkarstwo=10000. Do 16 istniejacych wpisow jednej postaci OFFLINE. '
 'bank:character:=10000 dla banku postaci (pusty source_key). '
 'postacie postepy zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Poziom i EXP sa para; bank EXP przechowuje saldo jako liczbe dziesietna TEXT, bez wyplaty. '
 'Nie tworzy profesji/narzedzi/kont banku, nie zmienia licznikow akcji, nagrod ani limitow. '
 'Transakcja SQLite, CAS, audyt i bezpieczne cofniecie; backup bazy przed naprawa.'
)
_PATTERN=re.compile(r'^(profesja|narzedzie|bank):([^=]+)=(.+)$')
_INT64_MAX=9223372036854775807

def _valid_bank_amount(text):
    if not isinstance(text,str) or not re.fullmatch(r'(?:0|[1-9][0-9]{0,127})',text,re.ASCII):
        raise ValueError('Bank EXP: kanoniczna liczba 0 lub dodatnie cyfry do 128 pozycji.')
    return text

def _bank_key(key):
    if ':' not in key:raise ValueError('Bank: bank:KIND:SOURCE=KWOTA; source moze byc pusty.')
    kind,source=key.split(':',1)
    if kind not in KINDS or len(source)>160 or any(ord(c)<32 for c in source):
        raise ValueError('Bank EXP: nieznana os lub niepoprawny source_key.')
    if kind in ('character','soul') and source:
        raise ValueError('Bank postaci i duszy ma pusty source_key.')
    return kind,source

def _row_current(session,account,category,key):
    con=session.server.db.conn
    if category=='profesja':
        if key not in PROFESSION_RANK_NAMES:raise ValueError('Nieznana profesja '+key)
        found=con.execute('SELECT level,xp FROM professions WHERE account_id=? AND profession=?',(account,key)).fetchone()
    elif category=='narzedzie':
        if key not in TOOL_PROFESSION_MAP:raise ValueError('Nieznany typ narzedzia '+key)
        found=con.execute('SELECT level,xp FROM tools WHERE account_id=? AND tool_type=?',(account,key)).fetchone()
    else:
        kind,source=_bank_key(key)
        found=con.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=? AND kind=? AND source_key=?',
                          (account,kind,source)).fetchone()
    if found is None:raise ValueError('Wpis nie istnieje; brak tworzenia odblokowan: '+key)
    return (int(found[0]),int(found[1])) if category!='bank' else str(found[0])

def _valid_progress(category,key,value,strict=True):
    level,xp=value
    limit=min(TECHNICAL_CEILING,cap('profesje' if category=='profesja' else 'narzedzia') or TECHNICAL_CEILING,
              profession_max_level(key) if category=='profesja' else tool_max_level(key))
    if not 1<=level<=limit:raise ValueError(f'{key}: poziom poza aktualnym limitem 1-{limit}.')
    if not 0<=xp<=MAX_XP:raise ValueError(f'{key}: EXP poza bezpiecznym zakresem SQLite.')
    if strict and level<limit:
        base=v0190_requirement('profession' if category=='profesja' else 'tool',level)
        threshold=(profession_xp_requirement_v1401(base,key,level) if category=='profesja'
                   else tool_xp_requirement_v1402(base,key,level))
        if 0<threshold<=MAX_XP and xp>=threshold:
            raise ValueError(f'{key}: EXP przekracza prog {threshold}; dopasuj poziom i reszte EXP.')


def card(session,name,page='1'):
    if not page.isascii() or not page.isdecimal() or len(page)>4:raise ValueError('Zla strona.')
    char=_row(session,name);_offline_account(session,char);account=char['account_id'];con=session.server.db.conn
    items=[]
    for key,level,xp in con.execute('SELECT profession,level,xp FROM professions WHERE account_id=? ORDER BY profession',(account,)):
        items.append(f'profesja:{key}={level},{xp}')
    for key,level,xp in con.execute('SELECT tool_type,level,xp FROM tools WHERE account_id=? ORDER BY tool_type',(account,)):
        items.append(f'narzedzie:{key}={level},{xp}')
    for kind,key,balance in con.execute('SELECT kind,source_key,balance FROM experience_bank_v2011 WHERE account_id=? ORDER BY kind,source_key',(account,)):
        marker='' if re.fullmatch(r'(?:0|[1-9][0-9]*)',str(balance)) else ' UWAGA NIEPOPRAWNE'
        items.append(f'bank:{kind}:{key}={str(balance)[:150]}{marker}')
    pages=max(1,(len(items)+5)//6);index=int(page)
    if not 1<=index<=pages:raise ValueError(f'Strony 1..{pages}.')
    return (f'POSTAC POSTEPY {char["name"]} strona {index}/{pages}, {len(items)} wpisow: '+
           ('; '.join(items[(index-1)*6:index*6]) or 'BRAK')+'. Tylko odczyt.')


def plan(session,name,raw):
    setattr(session,SLOT,None)
    if not 1<=len(raw)<=4000:raise ValueError('Plan: 1-4000 znakow.')
    char=_row(session,name);_offline_account(session,char);account=int(char['account_id'])
    entries=[x.strip() for x in raw.split(';')]
    if not 1<=len(entries)<=16 or any(not x for x in entries):raise ValueError('Do 16 wpisow rozdzielonych srednikiem.')
    changes=[];seen=set()
    for entry in entries:
        m=_PATTERN.fullmatch(entry)
        if not m:raise ValueError('Format: profesja:NAZWA=LEVEL,EXP; narzedzie:TYP=LEVEL,EXP; bank:KIND:SOURCE=SALDO.')
        kind,key,amount=m.groups()
        if (kind,key) in seen:raise ValueError('Powtorzony wpis '+key)
        seen.add((kind,key))
        old=_row_current(session,account,kind,key)
        if kind=='bank':
            _valid_bank_amount(old)
            new=_valid_bank_amount(amount.strip())
        else:
            bits=[p.strip() for p in amount.split(',')]
            if len(bits)!=2 or any(not re.fullmatch(r'[0-9]{1,16}',p,re.ASCII) for p in bits):
                raise ValueError('Poziom i EXP: poziom,exp.')
            new=int(bits[0]),int(bits[1]);_valid_progress(kind,key,new)
            # Legacy overcapped saved EXP is possible: read old safely for undo;
            # do not normalize it or reject legal banked EXP during planning.
            if not 1<=old[0]<=TECHNICAL_CEILING or not 0<=old[1]<=_INT64_MAX:
                raise ValueError('Niepoprawny istniejacy postep: '+key)
        if old==new:raise ValueError('Wartosc juz ustawiona: '+key)
        changes.append((kind,key,old,new))
    setattr(session,SLOT,(account,char['name'],tuple(changes)))
    return (f'POSTAC POSTEPY PLAN {char["name"]}: '+
        '; '.join(f'{kind}:{key} {old}->{new}' for kind,key,old,new in changes)+
        '. Bez zapisu. postacie postepy zatwierdz POTWIERDZAM.')


def _write(session,data,reverse=False):
    account,name,changes=data
    char=_row(session,name);_offline_account(session,char)
    if int(char['account_id'])!=account:raise ValueError('Zmiana tozsamosci konta.')
    con=session.server.db.conn
    # Check current caps and all requested new values before any SQL writes.
    for kind,key,old,new in changes:
        if kind=='bank':
            _bank_key(key);_valid_bank_amount(old);_valid_bank_amount(new)
        else:
            _valid_progress(kind,key,old if reverse else new,strict=not reverse)
    con.execute('SAVEPOINT adminlive9800_postepy')
    try:
        for kind,key,old,new in changes:
            expected=new if reverse else old;target=old if reverse else new
            if kind=='bank':
                category,source=_bank_key(key)
                cur=con.execute('UPDATE experience_bank_v2011 SET balance=? '
                    'WHERE account_id=? AND kind=? AND source_key=? AND balance=?',
                    (target,account,category,source,expected))
            else:
                table,col=('professions','profession') if kind=='profesja' else ('tools','tool_type')
                cur=con.execute(f'UPDATE {table} SET level=?,xp=? WHERE account_id=? AND {col}=? AND level=? AND xp=?',
                                (*target,account,key,*expected))
            if cur.rowcount!=1:raise ValueError('Konflikt wpisu '+key+': cala operacja wycofana.')
        admin=str(session.server.db.account_name(session.master_account_id))[:64]
        con.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
            (admin,'admin_live_v9800_postepy_undo' if reverse else 'admin_live_v9800_postepy',
             f'{name}: {len(changes)} wpisow'[:96]))
        con.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
                    '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')
        con.execute('RELEASE SAVEPOINT adminlive9800_postepy')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive9800_postepy')
        con.execute('RELEASE SAVEPOINT adminlive9800_postepy')
        raise

def commit(session):
    data=getattr(session,SLOT,None)
    if not data:raise ValueError('Brak planu.')
    _write(session,data)
    setattr(session,SLOT,None);setattr(session,UNDO,data)
    return f'POSTAC POSTEPY ZAPISANO {data[1]}: {len(data[2])} wpisow. Audyt SQLite.'

def undo(session):
    data=getattr(session,UNDO,None)
    if not data:raise ValueError('Brak operacji do cofniecia.')
    _write(session,data,True)
    setattr(session,UNDO,None)
    return f'POSTAC POSTEPY COFNIETO {data[1]}: {len(data[2])} wpisow.'

async def dispatch_v9800_advancement(session,cmd,tail):
    raw=str(tail or '').strip();words=raw.split()
    match=(cmd=='pomoc' and raw=='59') or (cmd=='postacie' and words[:1]==['postepy'])
    if not match:return False
    if not session.is_admin():await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if cmd=='pomoc':out=HELP
        elif words[:2]==['postepy','karta'] and len(words) in (3,4):out=card(session,words[2],words[3] if len(words)==4 else '1')
        elif words[:2]==['postepy','plan'] and '|' in raw:
            name,details=raw.split('postepy plan',1)[1].split('|',1)
            out=plan(session,name.strip(),details.strip())
        elif words==['postepy','zatwierdz','POTWIERDZAM']:out=commit(session)
        elif words==['postepy','cofnij','POTWIERDZAM']:out=undo(session)
        elif words==['postepy','anuluj']:setattr(session,SLOT,None);out='POSTAC POSTEPY: anulowano plan.'
        else:raise ValueError('Wpisz admin live pomoc 59.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as e:out='ADMIN LIVE POSTEPY V98: '+str(e)[:320]
    await session.send(out);return True
