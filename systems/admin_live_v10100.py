# -*- coding: utf-8 -*-
"""Soulbound v101: composite boss rules, guarded live progression, private arena series.

No untrusted Python, no reward callbacks. Persistence is CAS + SQLite SAVEPOINT;
character fields are mirrored to the live Session atomically (without awaits).
"""
from __future__ import annotations
import copy
import json
import re
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_five_v9900 import _rows, _load_json, _online
from systems.admin_live_offline_v9700 import _audit, _existing_item
from systems.admin_live_progress_v9500 import FIELDS, _parsed
from systems.admin_live_mastery_v9600 import _valid_key, _current, _target
from systems.admin_live_advancement_v9800 import (_PATTERN, _row_current,
    _valid_progress, _valid_bank_amount, _bank_key)
from systems.admin_live_v7500 import _boss
from systems.live_mechanics_v10100 import validate as validate_mechanics
from systems.admin_live_ultimate_v10000 import arena_status
from systems.admin_guardian7_v4100 import _lab_turn

HELP = (
 'ADMIN LIVE POMOC 70: mechaniki karta BOSS / mechaniki plan BOSS | JSON / '
 'mechaniki zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Przyklad JSON: {"phases":[{"below_hp":100,"every":2,"target":"weakest",'
 '"actions":[{"type":"drain_mana","percent":5},{"type":"heal_boss","percent":2}],'
 '"label":"Uderzenie mocy"}]}. DRAFT, potem admin live sprawdz, aktywuj POTWIERDZAM. '
 'Efekty: drain_mana, restore_mana, heal_boss, restore_health. Warunki v102: conditions. Bez dowolnego kodu Python. '
 'POMOC 71: postacie online rozwoj karta NAZWA / plan NAZWA | postac=POZIOM,EXP; dusza=POZIOM,EXP; bron=POZIOM,EXP / '
 'zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. SQLite i pamiec, tylko poza walka; '
 'bez automatycznego awansu i nagrod. '
 'POMOC 72: arena sesja seria atak,obrona,magia:fire / arena sesja porownaj. '
 'Seria max 12 tur w prywatnym LAB w obecnej sesji; to NIE pelna walka 1:1. '
 'Autentyczny silnik 1:1 pozostaje na osobnym izolowanym porcie 4900. '
 'POMOC 73: postacie online wpisy plan NAZWA | klasa:NAZWA=LEVEL,XP; skill:ID=LEVEL,XP; '
 'profesja:NAZWA=LEVEL,XP; narzedzie:TYP=LEVEL,XP; bank:KIND:SOURCE=SALDO; '
 'plecak:ITEM_ID=ILOSC. postacie online wpisy zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Tylko istniejące, odblokowane, niechronione wpisy; wyposażone przedmioty są blokowane. '
 'Bez walki, zbierania, handlu i uruchomionych automatyzacji. Kopia bazy obowiazkowa.'
)
S_MECH='adminlive101_mechanic';U_MECH='adminlive101_mechanic_undo'
S_PROG='adminlive101_progress';U_PROG='adminlive101_progress_undo'
S_ENTRIES='adminlive101_entries';U_ENTRIES='adminlive101_entries_undo'


def mechanics_card(service,boss):
    _boss(boss)
    return ('MECHANIKI '+boss+' ACTIVE='+json.dumps(service.active['v101_rules'].get(boss,'AUTO'),ensure_ascii=False)
        +' DRAFT='+json.dumps(service.draft['v101_rules'].get(boss,'AUTO'),ensure_ascii=False))


def mechanics_plan(session,service,raw):
    setattr(session,S_MECH,None)
    rows=_rows(raw,8,19000);before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before);seen=set()
    for name,value in rows:
        _boss(name)
        if name in seen:raise ValueError('Boss powtorzony.')
        seen.add(name)
        if value.upper()=='AUTO':candidate['v101_rules'].pop(name,None)
        else:candidate['v101_rules'][name]=_load_json(value,10000)
    validate_mechanics(candidate['v101_rules']);service.validate(candidate)
    if candidate==before:raise ValueError('Brak zmian.')
    _plan(session,S_MECH,before,service.active,candidate,'MECHANIKI v101')
    return f'MECHANIKI PLAN {len(rows)} bossow, walidacja PASS, tylko DRAFT (nie ACTIVE).'


def _ready(admin,name, *, workers=True):
    target=_online(admin,name)
    if target is admin:raise ValueError('Nie edytuj swojej postaci administracyjnej.')
    if target.account_id==admin.account_id:
        raise ValueError('Nie edytuj innej postaci z aktywnego konta administratora.')
    if getattr(target,'combat_mob_key',None) or getattr(target,'combat_pvp_target_id',None) or getattr(target,'combat_task',None) and not getattr(target.combat_task,'done',lambda:True)():
        raise ValueError('Postac jest w walce; korekta zablokowana.')
    if workers and any(bool(getattr(target,key,False)) for key in ('auto_fishing','auto_mining','auto_woodcutting','auto_herbalism','smelt_task_v1124','moving','resting','auto_queue_casting')):
        raise ValueError('Postac wykonuje aktywnosc lub automatyzacje; najpierw zatrzymaj.')
    return target


def progress_card(admin,name):
    target=_ready(admin,name,workers=False)
    con=admin.server.db.conn
    values=[]
    for key,(level,xp,_) in FIELDS.items():
        memory=(int(getattr(target.character,level)),int(getattr(target.character,xp)))
        row=con.execute(f'SELECT {level},{xp} FROM characters WHERE account_id=?',(target.account_id,)).fetchone()
        if row is None:raise ValueError('Brak postaci w bazie.')
        dbval=(int(row[0]),int(row[1]))
        values.append(f'{key} pamiec={memory[0]}/{memory[1]} SQLite={dbval[0]}/{dbval[1]}'+(' KONFLIKT' if memory!=dbval else ''))
    return 'ROZWOJ ONLINE '+target.character.name+': '+'; '.join(values)+'. Bez zapisu.'


def progress_plan(admin,raw):
    setattr(admin,S_PROG,None)
    if '|' not in raw:raise ValueError('Format: NAZWA | postac=LEVEL,EXP; ...')
    name,expr=(x.strip() for x in raw.split('|',1))
    target=_ready(admin,name)
    requested=_parsed(expr)
    con=admin.server.db.conn
    snapshot={}
    for key,(lv,xp,_) in FIELDS.items():
        mem=(int(getattr(target.character,lv)),int(getattr(target.character,xp)))
        row=con.execute(f'SELECT {lv},{xp} FROM characters WHERE account_id=?',(target.account_id,)).fetchone()
        if row is None or mem!=(int(row[0]),int(row[1])):
            raise ValueError('Konflikt pamiec/SQLite '+key+'. Najpierw zwykly zapis postaci.')
        snapshot[key]=mem
    changed={key:(snapshot[key],value) for key,value in requested.items() if value!=snapshot[key]}
    if not changed:raise ValueError('Brak zmian.')
    setattr(admin,S_PROG,(target,target.account_id,target.character.name,snapshot,changed))
    return 'ROZWOJ ONLINE PLAN '+name+': '+('; '.join(f'{key} {old}->{new}' for key,(old,new) in changed.items()))+'. Bez zapisu.'


def _write_progress(admin,data,reverse=False):
    target,account,name,snapshot,changes=data
    if _ready(admin,name) is not target or target.account_id!=account or target.character.name!=name:
        raise ValueError('Sesja lub konto postaci zmienione.')
    # A rollback is validated with the current runtime level caps too.
    from core.live_level_caps_v5200 import cap, TECHNICAL_CEILING
    from systems.admin_live_progress_v9500 import CAPS,MAX_XP
    for key,(old,new) in changes.items():
        lv,xp=old if reverse else new
        limit=cap(CAPS[key]) or TECHNICAL_CEILING
        if not 1<=lv<=min(limit,TECHNICAL_CEILING) or not 0<=xp<=MAX_XP:
            raise ValueError('Aktualne limity nie pozwalaja zapisac: '+key)
    con=admin.server.db.conn
    cols=[];before=[];after=[]
    for key,(lv,xp,_) in FIELDS.items():
        expected=(changes[key][1] if reverse else snapshot[key]) if key in changes else snapshot[key]
        for col,value in zip((lv,xp),expected):
            cols.append(col);before.append(value)
            if int(getattr(target.character,col))!=value:
                raise ValueError('Konflikt pamieci: '+col)
        for col,value in zip((lv,xp),(changes[key][0] if reverse else changes[key][1]) if key in changes else snapshot[key]):
            after.append(value)
    current=con.execute('SELECT '+','.join(cols)+' FROM characters WHERE account_id=?',(account,)).fetchone()
    if current is None or tuple(int(x) for x in current)!=tuple(before):
        raise ValueError('Konflikt SQLite: zmieniono postep postaci.')
    hp=int(target.current_hp);mp=int(target.current_mana)
    con.execute('SAVEPOINT adminlive101_progress')
    try:
        cur=con.execute('UPDATE characters SET '+','.join(f'{col}=?' for col in cols)+
            ' WHERE account_id=? AND name=? COLLATE NOCASE AND '+ ' AND '.join(f'{col}=?' for col in cols),
            (*after,account,name,*before))
        if cur.rowcount!=1:raise ValueError('Konflikt SQLite w chwili zapisu.')
        for col,value in zip(cols,after):setattr(target.character,col,value)
        if hp>int(target.max_hp()) or mp>int(target.max_mana()):
            raise ValueError('Nowy poziom obniza maksymalne HP/MP ponizej biezacych zasobow.')
        _audit(con,admin,'admin_live_v101_progress_undo' if reverse else 'admin_live_v101_progress',name)
        con.execute('RELEASE SAVEPOINT adminlive101_progress')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive101_progress')
        con.execute('RELEASE SAVEPOINT adminlive101_progress')
        for col,value in zip(cols,before):setattr(target.character,col,value)
        raise
    return 'ROZWOJ ONLINE '+('COFNIETO' if reverse else 'ZAPISANO')+' '+name+': SQLite+sesja, bez EXP nagrod.'


def _entries_plan(admin,raw):
    setattr(admin,S_ENTRIES,None)
    if '|' not in raw:raise ValueError('Format: NAZWA | klasa:NAZWA=LEVEL,XP; ...')
    name,details=(x.strip() for x in raw.split('|',1));target=_ready(admin,name)
    if not 1<=len(details)<=4000:raise ValueError('Zbyt dlugi plan.')
    entries=[x.strip() for x in details.split(';')]
    if not 1<=len(entries)<=12 or any(not x for x in entries):raise ValueError('Wymagane 1..12 zmian.')
    changes=[];seen=set()
    for entry in entries:
        m=_PATTERN.fullmatch(entry)
        if m:
            kind,key,expr=m.groups()
        else:
            other=re.fullmatch(r'(klasa|skill|plecak):([^=]{1,150})=(.+)',entry,re.S)
            if other is None:raise ValueError('Niepoprawna zmiana wpisu: '+entry[:65])
            kind,key,expr=other.groups()
        kind=kind.strip();key=key.strip();expr=expr.strip()
        if (kind,key) in seen:raise ValueError('Powtorzony wpis '+key)
        seen.add((kind,key))
        if kind in ('klasa','skill'):
            _valid_key(kind,key);old=_current(admin,target.account_id,kind,key)
            args=[x.strip() for x in expr.split(',')]
            if len(args)!=2 or any(not re.fullmatch(r'[0-9]{1,16}',x) for x in args):raise ValueError('LEVEL,XP wymagane.')
            new=_target(kind,*args)
        elif kind in ('profesja','narzedzie'):
            old=_row_current(admin,target.account_id,kind,key)
            args=[x.strip() for x in expr.split(',')]
            if len(args)!=2 or any(not re.fullmatch(r'[0-9]{1,16}',x) for x in args):raise ValueError('LEVEL,XP wymagane.')
            new=tuple(int(x) for x in args);_valid_progress(kind,key,new)
        elif kind=='bank':
            old=_row_current(admin,target.account_id,kind,key)
            _valid_bank_amount(old);new=_valid_bank_amount(expr)
        elif kind=='plecak':
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',key):raise ValueError('Zly item ID.')
            old=_existing_item(admin,target.account_id,key)
            if not re.fullmatch(r'[0-9]{1,10}',expr) or not 1<=int(expr)<=1_000_000_000:
                raise ValueError('Plecak: ilosc 1..1000000000.')
            new=int(expr)
        else:raise ValueError('Nieznana kategoria.')
        if old==new:raise ValueError('Wartosc juz ustawiona: '+key)
        changes.append((kind,key,old,new))
    setattr(admin,S_ENTRIES,(target,target.account_id,target.character.name,tuple(changes)))
    return 'WPISY ONLINE PLAN '+name+': '+str(len(changes))+' korekt, bez zapisu i nagrod.'


def _write_entries(admin,plan,reverse=False):
    target,account,name,changes=plan
    if _ready(admin,name) is not target or target.account_id!=account or target.character.name!=name:
        raise ValueError('Zmiana sesji, odmowa.')
    con=admin.server.db.conn
    con.execute('SAVEPOINT adminlive101_entries')
    try:
        for kind,key,old,new in changes:
            before=new if reverse else old;after=old if reverse else new
            if kind in ('klasa','skill'):
                _valid_key(kind,key);_target(kind,str(after[0]),str(after[1]))
                if kind=='klasa':
                    cur=con.execute('UPDATE class_progress SET level=?,xp=? WHERE account_id=? AND class_name=? AND level=? AND xp=?',(*after,account,key,*before))
                else:
                    cur=con.execute('UPDATE skill_progress SET level=?,xp=? WHERE account_id=? AND skill_id=? AND level=? AND xp=? AND EXISTS (SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?)',(*after,account,key,*before,account,key))
            elif kind in ('profesja','narzedzie'):
                _valid_progress(kind,key,after,strict=not reverse)
                table,col=('professions','profession') if kind=='profesja' else ('tools','tool_type')
                cur=con.execute(f'UPDATE {table} SET level=?,xp=? WHERE account_id=? AND {col}=? AND level=? AND xp=?',(*after,account,key,*before))
            elif kind=='bank':
                category,source=_bank_key(key)
                _valid_bank_amount(after)
                cur=con.execute('UPDATE experience_bank_v2011 SET balance=? WHERE account_id=? AND kind=? AND source_key=? AND balance=?', (after,account,category,source,before))
            else:
                if _existing_item(admin,account,key)!=before:raise ValueError('Konflikt lub ochrona plecaka.')
                cur=con.execute('UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=? AND quantity=?',(after,account,key,before))
            if cur.rowcount!=1:raise ValueError('Konflikt CAS, cala paczka cofnięta: '+key)
        _audit(con,admin,'admin_live_v101_entries_undo' if reverse else 'admin_live_v101_entries',name)
        con.execute('RELEASE SAVEPOINT adminlive101_entries')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive101_entries')
        con.execute('RELEASE SAVEPOINT adminlive101_entries')
        raise
    return 'WPISY ONLINE '+('COFNIETO' if reverse else 'ZAPISANO')+f' {name}, {len(changes)} wpisow; audyt SQLite.'


def arena_series(session,raw):
    if not getattr(session,'adminlive10000_lab_owner',None):raise ValueError('Najpierw arena sesja start BOSS_ID OBRAZENIA.')
    if session.adminlive10000_lab_owner!=(session.account_id,session.character.name):
        raise ValueError('Wlasciciel laboratorium zmieniony.')
    if not 1<=len(raw)<=250:raise ValueError('Scenariusz 1..250 znakow.')
    steps=[x.strip().lower() for x in raw.split(',')]
    if not 1<=len(steps)<=12:raise ValueError('Wykonaj 1..12 krokow na raz.')
    for step in steps:
        if step not in ('atak','obrona') and not re.fullmatch(r'magia:[a-z_]{1,30}',step):
            raise ValueError('Kroki: atak,obrona,magia:fire.')
    if getattr(session,'combat_mob_key',None) or getattr(session,'combat_pvp_target_id',None):
        raise ValueError('Sesja uczestniczy w prawdziwej walce.')
    before=copy.deepcopy(session.guardian7_lab)
    reports=[]
    try:
        for step in steps:
            if session.guardian7_lab['finished']:break
            if step=='atak':output=_lab_turn(session)
            elif step=='obrona':output=_lab_turn(session,defend=True)
            else:output=_lab_turn(session,element=step.split(':',1)[1])
            reports.append(output[:190])
        return 'ARENA SERIA LAB: '+str(len(reports))+'/'+str(len(steps))+' tur. '+'; '.join(reports)+' Brak nagrod i zmian produkcyjnych.'
    except BaseException:
        session.guardian7_lab=before
        raise


def arena_compare(session):
    if not getattr(session,'adminlive10000_lab_owner',None):raise ValueError('Najpierw arena sesja start.')
    a=getattr(session,'guardian7_lab',None)
    if not a:raise ValueError('Brak prywatnego LAB.')
    from data.mobs import MOB_TEMPLATES
    original=MOB_TEMPLATES.get(a['name'])
    if original is None:raise ValueError('Boss usuniety z aktywnego katalogu.')
    differences=[k for k in ('max_hp','damage','boss_mechanic','damage_type') if original.get(k)!=a['template'].get(k)]
    return ('ARENA POROWNAJ: '+('Konfiguracja bossa zmieniona od startu LAB: '+','.join(differences) if differences else 'podstawowe parametry bossa zgodne z aktualnym katalogiem')+
            '; LAB uzywa wybranych funkcji UOSS, nie testuje pelnego PVP, losowania, skilli i nagrod. '
            'Dla walki 1:1: admin live arena real start POTWIERDZAM, polaczenie osobnym klientem.')


async def dispatch_v10100(session,cmd,tail):
    raw=str(tail or '').strip();p=raw.split()
    relevant=(cmd=='pomoc' and raw in ('70','71','72','73') or
        cmd=='mechaniki' or
        cmd=='postacie' and p[:2] in (['online','rozwoj'],['online','wpisy']) or
        cmd=='arena' and p[:2] in (['sesja','seria'],['sesja','porownaj']))
    if not relevant:return False
    if not session.is_admin():await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if cmd=='pomoc':out=HELP
        elif cmd=='mechaniki':
            service=session.server.live_content_v1204
            if p[:1]==['karta'] and len(p)==2:out=mechanics_card(service,p[1])
            elif p[:1]==['plan'] and '|' in raw:out=mechanics_plan(session,service,raw.split('plan',1)[1].strip())
            elif p==['zatwierdz','POTWIERDZAM']:out=_commit(session,service,S_MECH,U_MECH)
            elif p==['cofnij','POTWIERDZAM']:out=_undo(session,service,S_MECH,U_MECH)
            elif p==['anuluj']:setattr(session,S_MECH,None);out='MECHANIKI: plan anulowany.'
            else:raise ValueError('Wpisz admin live pomoc 70.')
        elif cmd=='postacie' and p[:2]==['online','rozwoj']:
            if p[:3]==['online','rozwoj','karta'] and len(p)==4:out=progress_card(session,p[3])
            elif p[:3]==['online','rozwoj','plan'] and '|' in raw:out=progress_plan(session,raw.split('rozwoj plan',1)[1].strip())
            elif p==['online','rozwoj','zatwierdz','POTWIERDZAM']:
                data=getattr(session,S_PROG,None)
                if not data:raise ValueError('Brak planu.')
                out=_write_progress(session,data);setattr(session,U_PROG,data);setattr(session,S_PROG,None)
            elif p==['online','rozwoj','cofnij','POTWIERDZAM']:
                data=getattr(session,U_PROG,None)
                if not data:raise ValueError('Brak korekty do cofniecia.')
                out=_write_progress(session,data,True);setattr(session,U_PROG,None)
            elif p==['online','rozwoj','anuluj']:setattr(session,S_PROG,None);out='ROZWOJ ONLINE: anulowano.'
            else:raise ValueError('Wpisz admin live pomoc 71.')
        elif cmd=='postacie':
            if p[:3]==['online','wpisy','plan'] and '|' in raw:out=_entries_plan(session,raw.split('wpisy plan',1)[1].strip())
            elif p==['online','wpisy','zatwierdz','POTWIERDZAM']:
                data=getattr(session,S_ENTRIES,None)
                if not data:raise ValueError('Brak planu.')
                out=_write_entries(session,data);setattr(session,U_ENTRIES,data);setattr(session,S_ENTRIES,None)
            elif p==['online','wpisy','cofnij','POTWIERDZAM']:
                data=getattr(session,U_ENTRIES,None)
                if not data:raise ValueError('Brak korekty do cofniecia.')
                out=_write_entries(session,data,True);setattr(session,U_ENTRIES,None)
            elif p==['online','wpisy','anuluj']:setattr(session,S_ENTRIES,None);out='WPISY ONLINE: anulowano.'
            else:raise ValueError('Wpisz admin live pomoc 73.')
        else:
            if p[:2]==['sesja','seria'] and len(p)>2:out=arena_series(session,raw.split('seria',1)[1].strip())
            elif p==['sesja','porownaj']:out=arena_compare(session)
            else:raise ValueError('Wpisz admin live pomoc 72.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError) as e:
        out='ADMIN LIVE v101: '+str(e)[:380]
    await session.send(out)
    return True
