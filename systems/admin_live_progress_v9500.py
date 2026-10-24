# -*- coding: utf-8 -*-
"""v95: offline repair of coherent character / Soul / Soul Weapon level+XP pairs.

Does not grant battle rewards, items or class mastery; no side effects to online
players. Compare-and-swap, transactional audit and one-step safe undo.
"""
from __future__ import annotations
import re
from core.live_level_caps_v5200 import cap, TECHNICAL_CEILING
from core.progression_resources import character_xp_to_next, soul_xp_to_next, soul_weapon_mastery_xp_to_next
from systems.admin_live_characters_v7100 import _offline

FIELDS={'postac':('character_level','character_xp',character_xp_to_next),
        'dusza':('soul_level','soul_xp',soul_xp_to_next),
        'bron':('soul_weapon_mastery_level','soul_weapon_mastery_xp',soul_weapon_mastery_xp_to_next)}
CAPS={'postac':'postac','dusza':'dusza','bron':'bron_duszy'}
MAX_XP=1_000_000_000_000_000  # deliberately below SQLite int64 maximum
HELP=('ADMIN LIVE POMOC 53: postacie rozwoj karta NAZWA; '
      'postacie rozwoj plan NAZWA | postac=POZIOM,EXP; dusza=POZIOM,EXP; bron=POZIOM,EXP; '
      'postacie rozwoj zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
      'Tylko postac OFFLINE; zmienia 1-3 PARY poziom+EXP; kontrola limitow runtime i SQLite, '
      'plan i porownanie, atomowy zapis CAS, audyt i jedno cofniecie. '
      'Nie zmienia poziomow klas, umiejetnosci, statystyk, EQ, waluty ani EXP banku. '
      'Nie wywoluje levelup i nie dopisuje nagrod. Wykonaj kopie bazy przed uzyciem.')


def _row(session,name):
    if not isinstance(name,str) or not 1<=len(name)<=40 or any(ord(ch)<32 for ch in name):
        raise ValueError('Nazwa postaci 1..40 znakow.')
    cols=['account_id','name']+[col for pair in FIELDS.values() for col in pair[:2]]
    row=session.server.db.conn.execute('SELECT '+','.join(cols)+' FROM characters WHERE name=? COLLATE NOCASE',(name,)).fetchone()
    if row is None:raise ValueError('Postac nie istnieje.')
    return dict(zip(cols,row))


def _offline_account(session,row):
    _offline(session,row['name'])
    for other in getattr(session.server,'sessions',()):
        if other is session or getattr(other,'closed',False):
            continue
        if getattr(other,'account_id',None)==row['account_id']:
            raise ValueError('Konto tej postaci jest zalogowane; operacja offline zablokowana.')


def card(session,name):
    row=_row(session,name); _offline_account(session,row)
    parts=[]
    for key,(lv,xp,requirement) in FIELDS.items():
        limit=cap(CAPS[key]); next_exp=requirement(int(row[lv]))
        parts.append(f'{key} {row[lv]}, EXP {row[xp]}, nastepny prog {next_exp}, limit {limit if limit is not None else "bezlimitu"}')
    return 'POSTAC ROZWOJ OFFLINE '+row['name']+': '+'; '.join(parts)+'. Tylko odczyt.'


def _parsed(raw):
    if not isinstance(raw,str) or not 1<=len(raw)<=350:
        raise ValueError('Plan: wymagane 1..350 znakow.')
    items=[item.strip() for item in raw.split(';')]
    if not 1<=len(items)<=3 or not all(items):raise ValueError('Podaj 1-3 pary dziedzin.')
    values={}
    for item in items:
        m=re.fullmatch(r'(postac|dusza|bron)\s*=\s*([0-9]{1,8})\s*,\s*([0-9]{1,16})',item,re.ASCII)
        if not m:raise ValueError('Format: postac=POZIOM,EXP; dusza=POZIOM,EXP; bron=POZIOM,EXP.')
        key=m[1];lv=int(m[2]);xp=int(m[3])
        if key in values:raise ValueError('Powtorzona dziedzina '+key)
        limit=cap(CAPS[key]);safe_max=min(TECHNICAL_CEILING,limit if limit is not None else TECHNICAL_CEILING)
        if not 1<=lv<=safe_max:raise ValueError(f'{key}: poziom poza limitem 1..{safe_max}.')
        if not 0<=xp<=MAX_XP:raise ValueError(f'{key}: EXP poza bezpiecznym zakresem 0..{MAX_XP}.')
        values[key]=(lv,xp)
    return values


def plan(session,name,raw):
    session.adminlive9500_progress_plan=None
    requested=_parsed(raw);row=_row(session,name);_offline_account(session,row)
    pairs={}
    summary=[]
    for key,values in requested.items():
        level,exp,_=FIELDS[key];old=(int(row[level]),int(row[exp]))
        if old!=values:
            pairs[key]=(old,values)
            summary.append(f'{key}: {old[0]}/{old[1]} -> {values[0]}/{values[1]}')
    if not pairs:raise ValueError('Nowe wartosci sa juz ustawione.')
    session.adminlive9500_progress_plan=(row['account_id'],row['name'],pairs)
    return ('POSTAC ROZWOJ PLAN '+row['name']+': '+'; '.join(summary)+'. '
            'Brak zapisu i levelup. postacie rozwoj zatwierdz POTWIERDZAM.')


def _write(session,data,reverse=False):
    account,name,pairs=data
    row=_row(session,name)
    if row['account_id']!=account:raise ValueError('Tozsamosc postaci zmienila sie od planu.')
    _offline_account(session,row)
    db=session.server.db
    changes=[]
    expected=[]
    replacement=[]
    for key,(old,new) in sorted(pairs.items()):
        # Protect even undo against reduced limits and new game configurations.
        value=old if reverse else new
        limit=cap(CAPS[key]); ceiling=limit if limit is not None else TECHNICAL_CEILING
        if not 1<=value[0]<=ceiling:raise ValueError('Limit poziomu zmieniony; odmowa zapisu '+key)
        for col in FIELDS[key][:2]:changes.append(col)
        expected.extend(new if reverse else old)
        replacement.extend(value)
    # SQL identifiers only from hardcoded FIELDS; optimistic check detects writes between plan and commit.
    # SAVEPOINT avoids rolling back unrelated, already active transactions on
    # this shared connection when the compare-and-swap or audit fails.
    db.conn.execute('SAVEPOINT adminlive9500_progress')
    try:
        where=' AND '.join(f'{col}=?' for col in changes)
        set_sql=', '.join(f'{col}=?' for col in changes)
        cur=db.conn.execute(f'UPDATE characters SET {set_sql} WHERE account_id=? AND name=? COLLATE NOCASE AND {where}',
                            (*replacement,account,name,*expected))
        if cur.rowcount!=1:raise ValueError('Postac/EXP zmienione po utworzeniu planu; nie zapisano.')
        admin=str(db.account_name(session.master_account_id))[:64]
        info=','.join(f'{key}:{(new if reverse else old)[0]}>{(old if reverse else new)[0]}'
                      for key,(old,new) in sorted(pairs.items()))
        db.conn.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
                        (admin,'admin_live_v9500_progress_undo' if reverse else 'admin_live_v9500_progress',
                         (name+':'+info)[:96]))
        db.conn.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
                        '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')
        db.conn.execute('RELEASE SAVEPOINT adminlive9500_progress')
    except BaseException:
        db.conn.execute('ROLLBACK TO SAVEPOINT adminlive9500_progress')
        db.conn.execute('RELEASE SAVEPOINT adminlive9500_progress')
        raise


def commit(session):
    data=getattr(session,'adminlive9500_progress_plan',None)
    if not data:raise ValueError('Brak planu rozwoju.')
    _write(session,data)
    session.adminlive9500_progress_plan=None
    session.adminlive9500_progress_undo=data
    return 'POSTAC ROZWOJ ZAPISANO '+data[1]+': atomowy zapis 1-3 dziedzin i audyt. Nie przyznano nagrod.'


def undo(session):
    data=getattr(session,'adminlive9500_progress_undo',None)
    if not data:raise ValueError('Brak operacji do cofniecia.')
    _write(session,data,reverse=True)
    session.adminlive9500_progress_undo=None
    return 'POSTAC ROZWOJ COFNIETO '+data[1]+': wczesniejsze wartosci przywrocone, audyt zapisany.'


async def dispatch_v9500(session,group,tail):
    words=str(tail or '').strip().split()
    recognized=(group=='pomoc' and words==['53']) or (group=='postacie' and words[:1]==['rozwoj'])
    if not recognized:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':out=HELP
        elif len(words)==3 and words[:2]==['rozwoj','karta']:out=card(session,words[2])
        elif len(words)>=4 and words[:2]==['rozwoj','plan'] and '|' in str(tail):
            name,raw=str(tail).split('rozwoj plan',1)[1].split('|',1)
            out=plan(session,name.strip(),raw.strip())
        elif words==['rozwoj','zatwierdz','POTWIERDZAM']:out=commit(session)
        elif words==['rozwoj','cofnij','POTWIERDZAM']:out=undo(session)
        elif words==['rozwoj','anuluj']:
            session.adminlive9500_progress_plan=None;out='POSTAC ROZWOJ: plan anulowano.'
        else:raise ValueError('postacie rozwoj karta/plan/zatwierdz/cofnij/anuluj; pomoc 53.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as e:
        out='ADMIN LIVE ROZWOJ: '+str(e)[:270]
    await session.send(out)
    return True
