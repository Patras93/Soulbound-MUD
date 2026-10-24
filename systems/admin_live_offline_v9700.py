# -*- coding: utf-8 -*-
"""v97: owner-only offline character stat bundles and guarded inventory corrections.

Intentional scope: NO currency, equipment, shop-purchase lots, crafting materials,
protected goods, bank or reward creation. The user supplies each exact desired value.
SAVEPOINT + compare-and-swap + admin audit = all-or-nothing, including safe undo.
"""
from __future__ import annotations
import re
from systems.admin_live_progress_v9500 import _row, _offline_account
from systems.admin_live_characters_v7100 import FIELDS as STATS
from core.mines_threat import ITEMS

STAT_PLAN='adminlive9700_stats_plan'
STAT_UNDO='adminlive9700_stats_undo'
ITEM_PLAN='adminlive9700_inventory_plan'
ITEM_UNDO='adminlive9700_inventory_undo'
_STAT_RE=re.compile(r'^([A-Za-z0-9_]{1,40})\s*\|\s*(.+)$',re.ASCII)
_PAIR_RE=re.compile(r'^([a-z_]{1,30})\s*=\s*([0-9]{1,12})$',re.ASCII)
_ITEM_RE=re.compile(r'^([A-Za-z0-9_]{1,40})\s*\|\s*([A-Za-z0-9_-]{1,100})\s*=\s*([0-9]{1,10})$',re.ASCII)
HELP=(
 'ADMIN LIVE POMOC 55: postacie staty pakiet plan NAZWA | strength=60,dexterity=20 / NAZWA2 | charisma=25; '
 'postacie staty pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Do 8 postaci OFFLINE i 24 wartosci z strength,dexterity,constitution,intelligence,willpower,charisma,deaths. '
 'postacie plecak karta NAZWA [STRONA] (pokazuje ilosci i ochrone); '
 'postacie plecak plan NAZWA | ITEM_ID=NOWA_ILOSC; NAZWA2 | ITEM_ID=NOWA_ILOSC; '
 'postacie plecak zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Do 16 istniejacych, niezabezpieczonych stosow. Bez zakupow, wyposazenia, surowcow, '
 'banku i przedmiotow premium; nie tworzy nowych stosow ani nie kasuje do zera. '
 'Jedna transakcja SQLite, kontrola konfliktow, dziennik i bezpieczne cofanie. '
 'Wymagana kopia bazy przed uzyciem.'
)


def _parse_stat_pack(session,raw):
    if not 1<=len(raw)<=3000:raise ValueError('Plan statystyk: 1..3000 znakow.')
    rows=[x.strip() for x in raw.split(' / ')]
    if not 1<=len(rows)<=8 or not all(rows):raise ValueError('Maksymalnie 8 postaci; rozdziel: / .')
    result=[];seen=set();total=0
    for entry in rows:
        match=_STAT_RE.fullmatch(entry)
        if not match:raise ValueError('Format: NAZWA | strength=20,dexterity=30 / DRUGA | charisma=20.')
        name,fields=match.groups()
        char=_row(session,name);_offline_account(session,char)
        account=int(char['account_id'])
        if account in seen:raise ValueError('Powtorzona postac lub konto.')
        seen.add(account)
        changes={}
        for item in fields.split(','):
            spec=_PAIR_RE.fullmatch(item.strip())
            if not spec:raise ValueError('Format: POLE=LICZBA, tylko statystyki i deaths.')
            field,number=spec.groups()
            if field not in STATS or field in changes:raise ValueError('Nieznane lub powtorzone pole: '+field)
            value=int(number)
            if not (0<=value<=1_000_000_000 if field=='deaths' else 1<=value<=1_000_000_000):
                raise ValueError('Wartosc statystyki poza bezpiecznym zakresem.')
            old=session.server.db.conn.execute('SELECT '+field+' FROM characters WHERE account_id=?',(account,)).fetchone()
            if old is None:raise ValueError('Postac zniknela podczas planowania.')
            old=int(old[0]);changes[field]=(old,value);total+=1
        if not changes or all(old==new for old,new in changes.values()):
            raise ValueError('Plan postaci nie zawiera zmian: '+name)
        result.append((account,char['name'],changes))
    if total>24:raise ValueError('Maksymalnie 24 pola w pakiecie.')
    return tuple(result)


def _audit(con,session,action,target):
    admin=str(session.server.db.account_name(session.master_account_id))[:64]
    con.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
                (admin,action,str(target)[:96]))
    con.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
                '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')


def stats_plan(session,raw):
    setattr(session,STAT_PLAN,None)
    values=_parse_stat_pack(session,raw)
    setattr(session,STAT_PLAN,values)
    rows=[f'{name}: '+','.join(f'{field} {old}->{new}' for field,(old,new) in sorted(changes.items()) if old!=new)
          for _,name,changes in values]
    return ('STATY PAKIET PLAN: '+ '; '.join(rows)+'. Bez zapisu. '
            'postacie staty pakiet zatwierdz POTWIERDZAM.')


def _stats_write(session,rows,reverse=False):
    con=session.server.db.conn
    for account,name,changes in rows:
        current=_row(session,name);_offline_account(session,current)
        if int(current['account_id'])!=account:raise ValueError('Zmieniono tozsamosc postaci.')
    con.execute('SAVEPOINT adminlive9700_stats')
    try:
        for account,name,changes in rows:
            for field,(old,new) in sorted(changes.items()):
                expected=new if reverse else old
                target=old if reverse else new
                if not (0<=target<=1_000_000_000 if field=='deaths' else 1<=target<=1_000_000_000):
                    raise ValueError('Wartosc docelowa poza limitem.')
                if expected==target:continue
                cur=con.execute(f'UPDATE characters SET {field}=? WHERE account_id=? AND name=? COLLATE NOCASE AND {field}=?',
                                (target,account,name,expected))
                if cur.rowcount!=1:raise ValueError('Konflikt statystyk lub postac online: '+name+'. Nic nie zapisano.')
        _audit(con,session,'admin_live_v9700_stats_undo' if reverse else 'admin_live_v9700_stats',
               ','.join(name for _,name,_ in rows))
        con.execute('RELEASE SAVEPOINT adminlive9700_stats')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive9700_stats')
        con.execute('RELEASE SAVEPOINT adminlive9700_stats')
        raise


def _existing_item(session,account,item):
    if item not in ITEMS:raise ValueError('Nieznany, dynamiczny lub nieaktywny ID przedmiotu: '+item)
    # Never repair reward tokens, quest objects, currency, tools, Soul relics or raw resources here.
    if ITEMS[item].get('type') not in ('armor','equipment','consumable','loot'):
        raise ValueError('Ten typ przedmiotu wymaga dedykowanego edytora: '+item)
    con=session.server.db.conn
    found=con.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(account,item)).fetchone()
    if found is None or not 1<=int(found[0])<=1_000_000_000:raise ValueError('Brak poprawnego, istniejacego stosu: '+item)
    # The following tables must exist. A missing table is NOT proof of zero protection.
    guards=(('shop_purchase_lots_v1175','item_id'),('protected_inventory_v1280','item_id'),
            ('equipment','item_id'))
    for table,col in guards:
        if con.execute(f'SELECT 1 FROM {table} WHERE account_id=? AND {col}=? LIMIT 1',(account,item)).fetchone():
            raise ValueError('Przedmiot ma historie zakupu, ochrone lub jest wyposazony: '+item)
    from storage.db_shared import is_craft_material_storage_item
    if is_craft_material_storage_item(item):raise ValueError('Surowce sa poza zwyklym plecakiem.')
    return int(found[0])


def inventory_card(session,name,page='1'):
    if not page.isascii() or not page.isdecimal() or not 1<=len(page)<=4:raise ValueError('Strona musi byc liczba.')
    row=_row(session,name);_offline_account(session,row)
    account=int(row['account_id'])
    rows=session.server.db.conn.execute('SELECT item_id,quantity FROM inventory WHERE account_id=? ORDER BY item_id',
                                        (account,)).fetchall()
    entries=[]
    for item,qty in rows:
        try:
            _existing_item(session,account,item)
            flag='EDYTOWALNY'
        except (ValueError,TypeError,OverflowError):flag='CHRONIONY LUB NIEPOPRAWNY'
        entries.append(f'{item}={qty} ({flag})')
    number=int(page);pages=max(1,(len(entries)+6)//7)
    if number>pages:raise ValueError(f'Dostepne strony 1..{pages}.')
    return (f'PLECAK {row["name"]} {number}/{pages}, razem {len(entries)}: '+
            ('; '.join(entries[(number-1)*7:number*7]) or 'PUSTY')+'. Tylko odczyt.')


def inventory_plan(session,raw):
    setattr(session,ITEM_PLAN,None)
    if not 1<=len(raw)<=3200:raise ValueError('Plecak: 1..3200 znakow.')
    specs=[x.strip() for x in raw.split(';')]
    if not 1<=len(specs)<=16 or any(not x for x in specs):raise ValueError('Maksymalnie 16 wpisow.')
    seen=set();rows=[]
    for spec in specs:
        match=_ITEM_RE.fullmatch(spec)
        if not match:raise ValueError('Format: NAZWA | ITEM_ID=NOWA_ILOSC; ...')
        name,item,value=match.groups();val=int(value)
        if not 1<=val<=1_000_000_000:raise ValueError('Ilosc musi byc 1..1000000000; brak usuwania stosow.')
        char=_row(session,name);_offline_account(session,char)
        account=int(char['account_id'])
        if (account,item) in seen:raise ValueError('Powtorzony stos: '+item)
        seen.add((account,item));old=_existing_item(session,account,item)
        if old==val:raise ValueError('Ilosc juz ustawiona: '+item)
        rows.append((account,char['name'],item,old,val))
    setattr(session,ITEM_PLAN,tuple(rows))
    return ('PLECAK PLAN: '+'; '.join(f'{name} {item} {old}->{val}' for _,name,item,old,val in rows)+
            '. Bez zapisu. postacie plecak zatwierdz POTWIERDZAM.')


def _inventory_write(session,rows,reverse=False):
    con=session.server.db.conn
    for account,name,item,old,new in rows:
        char=_row(session,name);_offline_account(session,char)
        if int(char['account_id'])!=account:raise ValueError('Zmieniono konto postaci.')
        _existing_item(session,account,item)
    con.execute('SAVEPOINT adminlive9700_inventory')
    try:
        for account,name,item,old,new in rows:
            expected=new if reverse else old
            target=old if reverse else new
            cur=con.execute('UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=? AND quantity=?',
                            (target,account,item,expected))
            if cur.rowcount!=1:raise ValueError('Plecak zmieniony od planu; wszystkie zmiany anulowane.')
            _existing_item(session,account,item)
        _audit(con,session,'admin_live_v9700_inventory_undo' if reverse else 'admin_live_v9700_inventory',
               ','.join(f'{name}:{item}' for _,name,item,_,_ in rows))
        con.execute('RELEASE SAVEPOINT adminlive9700_inventory')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive9700_inventory')
        con.execute('RELEASE SAVEPOINT adminlive9700_inventory')
        raise


def _commit(session,slot,undo,writer,label):
    data=getattr(session,slot,None)
    if not data:raise ValueError('Brak planu.')
    writer(session,data)
    setattr(session,slot,None);setattr(session,undo,data)
    return label+' ZAPISANO: '+str(len(data))+' pozycji, atomowy audyt SQLite.'


def _undo(session,undo,writer,label):
    data=getattr(session,undo,None)
    if not data:raise ValueError('Brak operacji do cofniecia.')
    writer(session,data,reverse=True)
    setattr(session,undo,None)
    return label+' COFNIETO: '+str(len(data))+' pozycji.'


async def dispatch_v9700_offline(session,cmd,tail):
    words=str(tail or '').strip().split()
    match=(cmd=='pomoc' and words==['55']) or (cmd=='postacie' and (
        words[:2]==['staty','pakiet'] or words[:1]==['plecak']))
    if not match:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if cmd=='pomoc':output=HELP
        elif words[:2]==['staty','pakiet']:
            if len(words)>=4 and words[2]=='plan':output=stats_plan(session,tail.split('pakiet plan',1)[1].strip())
            elif words==['staty','pakiet','zatwierdz','POTWIERDZAM']:output=_commit(session,STAT_PLAN,STAT_UNDO,_stats_write,'STATY PAKIET')
            elif words==['staty','pakiet','cofnij','POTWIERDZAM']:output=_undo(session,STAT_UNDO,_stats_write,'STATY PAKIET')
            elif words==['staty','pakiet','anuluj']:
                setattr(session,STAT_PLAN,None);output='STATY PAKIET: anulowano.'
            else:raise ValueError('Wpisz admin live pomoc 55.')
        elif words[:2]==['plecak','karta'] and len(words) in (3,4):
            output=inventory_card(session,words[2],words[3] if len(words)==4 else '1')
        elif words[:2]==['plecak','plan'] and len(words)>=3:output=inventory_plan(session,tail.split('plecak plan',1)[1].strip())
        elif words==['plecak','zatwierdz','POTWIERDZAM']:output=_commit(session,ITEM_PLAN,ITEM_UNDO,_inventory_write,'PLECAK')
        elif words==['plecak','cofnij','POTWIERDZAM']:output=_undo(session,ITEM_UNDO,_inventory_write,'PLECAK')
        elif words==['plecak','anuluj']:
            setattr(session,ITEM_PLAN,None);output='PLECAK: anulowano.'
        else:raise ValueError('Wpisz admin live pomoc 55.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        output='ADMIN LIVE V97 OFFLINE: '+str(exc)[:290]
    await session.send(output)
    return True
