# -*- coding: utf-8 -*-
"""v72: bounded, explicit, reversible plans; no script injection or live fight rewrite.

Quest and boss changes alter DRAFT only. Offline character packs are SQLite CAS
transactions with a single audit record, no progression, accounts or economy.
"""
from __future__ import annotations
import copy
import re

from data.mobs import MOB_TEMPLATES
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_integrity_v4900 import _effective
from systems.live_olc4_boss_phases import eligible_boss, default_boss_phases, validate_boss_phases
from systems.live_olc17_quest_dependencies import validate_dependency_graph
from systems.admin_live_characters_v7100 import FIELDS, _row, _offline

HELP = (
    'ADMIN LIVE POMOC 32: questy zaleznosci karta ID; '
    'questy zaleznosci plan ID | ID1,ID2 lub BRAK; '
    'questy zaleznosci zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj; '
    'boss fazy zestaw ID 3/4/5; boss fazy ustaw ID NR POLE | WARTOSC; '
    'boss fazy zatwierdz POTWIERDZAM / cofnij POTWIERDZAM; '
    'postacie pakiet plan NAZWA | POLE=LICZBA; POLE=LICZBA; '
    'postacie pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Boss i quest tylko DRAFT, publikacja osobno. Postacie tylko OFFLINE i bez EXP/waluty. '
    'Arena UOSS nadal NIE 1:1, nowe klasy/rasy nie sa tworzone.'
)


def quest_card(service, qid):
    from systems.admin_guardian6_v4000 import _requirements
    catalog = _effective(service)
    if qid not in catalog:
        raise ValueError('Nieznany ID questa; szukaj przez admin live questy szukaj.')
    q = catalog[qid]
    req = _requirements(q)
    missing = [key for key in req if key not in catalog]
    return (f'QUEST ZALEZNOSCI {qid}: {", ".join(req) if req else "BRAK"}; '
            f'brakujace ID {", ".join(missing) if missing else "BRAK"}. '
            'requires_quest (pojedynczy) jest zachowany, plan zmienia tylko requires_quests. Bez zmian.')


def quest_plan(session, service, raw):
    session.adminlive7200_quest_plan = None
    if '|' not in raw:
        raise ValueError('Format: questy zaleznosci plan QUEST_ID | ID1,ID2 lub BRAK')
    qid, wanted = (t.strip() for t in raw.split('|', 1))
    catalog = _effective(service)
    if qid not in catalog:
        raise ValueError('Nieznany QUEST_ID.')
    if not wanted or len(wanted) > 500:
        raise ValueError('Brak listy ID lub lista za dluga.')
    deps = [] if wanted.casefold() == 'brak' else [x.strip() for x in wanted.split(',')]
    if (len(deps) > 8 or len(deps) != len(set(deps))
            or any(not re.fullmatch(r'[A-Za-z0-9_\-]{1,100}', d, flags=re.ASCII) for d in deps)):
        raise ValueError('Podaj 0..8 roznych poprawnych identyfikatorow questow.')
    if any(x not in catalog or x == qid for x in deps):
        raise ValueError('Quest wymagany nie istnieje lub wymaga samego siebie.')
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    candidate.setdefault('quest_edits', {}).setdefault(qid, {})['requires_quests'] = deps
    catalog[qid] = dict(catalog[qid], requires_quests=deps)
    validate_dependency_graph(catalog)
    service.validate(candidate)
    if candidate == before:
        raise ValueError('Nie ma zmiany do zapisania.')
    _plan(session, 'adminlive7200_quest_plan', before, service.active, candidate, 'QUEST ZALEZNOSCI')
    return (f'QUEST ZALEZNOSCI PLAN {qid}: dodatkowe wymagania: '
            f'{", ".join(deps) if deps else "BRAK"}. '
            'Istniejace requires_quest bez zmian; sprawdzono caly graf. '
            'Bez zapisu, zatwierdz przez questy zaleznosci zatwierdz POTWIERDZAM.')


def _boss_template(service, ident):
    original = MOB_TEMPLATES.get(ident) or service.draft.get('mobs', {}).get(ident)
    if not isinstance(original, dict):
        raise ValueError('Nieznany ID bossa.')
    meta = dict(original)
    meta.update(service.draft.get('mob_edits', {}).get(ident, {}))
    if not eligible_boss(meta):
        raise ValueError('Boss chroniony lub nie korzysta ze zwyklego edytowalnego AI.')
    return meta


def _boss_plan(session, service, ident, phases, description):
    before = copy.deepcopy(service.draft)
    candidate = copy.deepcopy(before)
    validate_boss_phases(_boss_template(service, ident), phases)
    candidate.setdefault('mob_edits', {}).setdefault(ident, {})['olc_boss_phases'] = phases
    service.validate(candidate)
    if candidate == before:
        raise ValueError('Fazy sa juz ustawione tak samo.')
    _plan(session, 'adminlive7100_boss_plan', before, service.active, candidate, 'BOSS FAZY')
    return f'BOSS FAZY PLAN {ident}: {description}. Tylko DRAFT; boss fazy zatwierdz POTWIERDZAM.'


def boss_set(session, service, raw):
    session.adminlive7100_boss_plan = None
    if '|' not in raw:
        raise ValueError('Format: boss fazy ustaw ID NR POLE | WARTOSC')
    lhs, value = (v.strip() for v in raw.split('|', 1))
    fields = lhs.split()
    if len(fields) != 3 or not fields[1].isascii() or not fields[1].isdecimal():
        raise ValueError('Format: ID NR POLE | WARTOSC')
    ident, idx_raw, field = fields
    meta = _boss_template(service, ident)
    phases = copy.deepcopy(meta.get('olc_boss_phases') or default_boss_phases(meta))
    idx = int(idx_raw) - 1
    if not 0 <= idx < len(phases):
        raise ValueError(f'Numer fazy 1..{len(phases)}.')
    if field in ('hp_percent', 'duration_seconds'):
        if not value.isascii() or not value.isdecimal() or len(value) > 3:
            raise ValueError('Wymagana dodatnia liczba calkowita.')
        parsed = int(value)
    elif field == 'attack_multiplier':
        if not re.fullmatch(r'[0-9]{1,2}(?:\.[0-9]{1,3})?', value, flags=re.ASCII):
            raise ValueError('Mnoznik w formacie 1.18..3.0 (kropka).')
        parsed = float(value)
    elif field == 'message':
        parsed = value
    else:
        raise ValueError('Pola: hp_percent, attack_multiplier, duration_seconds, message.')
    old = phases[idx][field]
    phases[idx][field] = parsed
    return _boss_plan(session, service, ident, phases, f'faza {idx+1}, {field}: {old} -> {parsed}')


def boss_layout(session, service, raw):
    session.adminlive7100_boss_plan = None
    parts = raw.split()
    if len(parts) != 2 or parts[1] not in ('3', '4', '5'):
        raise ValueError('Format: boss fazy zestaw ID 3/4/5')
    ident, count_raw = parts
    count = int(count_raw)
    meta = _boss_template(service, ident)
    phases = copy.deepcopy(default_boss_phases(meta))
    if count != 3:
        thresholds = [80,60,40,20] if count == 4 else [83,66,49,32,15]
        phases = [dict(hp_percent=hp, attack_multiplier=round(1.18 + 0.14*(i+1),2),
                       duration_seconds=20+5*i, message=f'{meta.get("name", ident)}: faza {i+1}')
                  for i,hp in enumerate(thresholds)]
    return _boss_plan(session, service, ident, phases, f'{count} faz: '+', '.join(str(p['hp_percent'])+'% HP' for p in phases))


def _pairs(raw):
    ops=[s.strip() for s in raw.split(';') if s.strip()]
    if not 1 <= len(ops) <= 7:
        raise ValueError('Podaj 1..7 zmian oddzielonych srednikiem.')
    result={}
    for op in ops:
        if '=' not in op:raise ValueError('Format POLE=LICZBA.')
        key,raw_val=(v.strip() for v in op.split('=',1))
        if key not in FIELDS or key in result:
            raise ValueError('Nieznane lub powtorzone pole. Dostepne: '+', '.join(sorted(FIELDS)))
        if not raw_val.isascii() or not raw_val.isdecimal() or len(raw_val)>10:
            raise ValueError('Wartosc musi byc dodatnia liczba calkowita.')
        val=int(raw_val)
        minimum=0 if key=='deaths' else 1
        if not minimum <= val <= 1_000_000_000:
            raise ValueError('Wartosc poza limitem 0..1000000000 (statystyki od 1).')
        result[key]=val
    return result


def character_batch_plan(session, name, raw):
    session.adminlive7200_character_plan = None
    vals=_pairs(raw)
    row=_row(session,name)
    _offline(session,row['name'])
    changed={k:(row[k],v) for k,v in vals.items() if row[k]!=v}
    if not changed:raise ValueError('Brak zmiany.')
    session.adminlive7200_character_plan=(row['account_id'],row['name'],changed)
    info=', '.join(f'{k} {old}->{new}' for k,(old,new) in changed.items())
    return (f'POSTAC PAKIET PLAN {row["name"]}: {info}. '
        'Nic jeszcze nie zmieniono. postacie pakiet zatwierdz POTWIERDZAM.')


def _character_batch_write(session, data, reverse=False):
    account,name,changes=data
    _offline(session,name)
    db=session.server.db
    existing=_row(session,name)
    if existing['account_id']!=account:
        raise ValueError('Tozsamosc postaci zmienila sie od planu.')
    old={k:(v[1] if reverse else v[0]) for k,v in changes.items()}
    new={k:(v[0] if reverse else v[1]) for k,v in changes.items()}
    if any(existing[k]!=v for k,v in old.items()):
        raise ValueError('Postac zmienila sie od planu. Zapis zablokowany.')
    ordered=sorted(changes)
    values=[new[k] for k in ordered]
    guards=[old[k] for k in ordered]
    set_clause=', '.join(f'{k}=?' for k in ordered)
    where_clause=' AND '.join(f'{k}=?' for k in ordered)
    # SQL identifiers come exclusively from the closed FIELDS set.
    with db.conn:
        cur=db.conn.execute(
            f'UPDATE characters SET {set_clause} WHERE account_id=? AND name=? COLLATE NOCASE AND {where_clause}',
            (*values,account,name,*guards))
        if cur.rowcount!=1:
            raise ValueError('Zmiana rownolegla; nie zapisano danych.')
        admin=str(db.account_name(session.master_account_id))[:64]
        verb='admin_live_v7200_undo' if reverse else 'admin_live_v7200_batch'
        audit=','.join(f'{k}:{old[k]}>{new[k]}' for k in ordered)
        db.conn.execute('INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES(?,?,?)',
                        (admin,verb,(name+':'+audit)[:96]))
        db.conn.execute('DELETE FROM admin_actions_v1224 WHERE id NOT IN '
                        '(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)')
    return f'POSTAC PAKIET {"COFNIETO" if reverse else "ZAPISANO"} {name}: '+', '.join(f'{k}={new[k]}' for k in ordered)+'.'


def character_batch_commit(session):
    data=getattr(session,'adminlive7200_character_plan',None)
    if data is None:raise ValueError('Brak planu postaci.')
    session.adminlive7200_character_plan=None
    message=_character_batch_write(session,data)
    session.adminlive7200_character_undo=data
    return message


def character_batch_undo(session):
    data=getattr(session,'adminlive7200_character_undo',None)
    if data is None:raise ValueError('Brak operacji do cofniecia.')
    message=_character_batch_write(session,data,reverse=True)
    session.adminlive7200_character_undo=None
    return message


async def dispatch_v7200(session, group, raw):
    parts=str(raw or '').split()
    is_help = group=='pomoc' and parts==['32']
    is_quest = group in ('questy','zadania') and parts[:1]==['zaleznosci']
    is_boss = group=='boss' and parts[:1]==['fazy'] and len(parts)>1 and parts[1] in ('ustaw','zestaw')
    is_char = group=='postacie' and parts[:1]==['pakiet']
    if not (is_help or is_quest or is_boss or is_char):return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    service=session.server.live_content_v1204
    try:
        if is_help:out=HELP
        elif is_quest:
            if len(parts)==3 and parts[1]=='karta':out=quest_card(service,parts[2])
            elif len(parts)>=3 and parts[1]=='plan':
                out=quest_plan(session,service,raw.partition('plan')[2].strip())
            elif parts==['zaleznosci','zatwierdz','POTWIERDZAM']:
                out=_commit(session,service,'adminlive7200_quest_plan','adminlive7200_quest_undo')
            elif parts==['zaleznosci','cofnij','POTWIERDZAM']:
                out=_undo(session,service,'adminlive7200_quest_plan','adminlive7200_quest_undo')
            elif parts==['zaleznosci','anuluj']:
                session.adminlive7200_quest_plan=None;out='QUEST ZALEZNOSCI: plan anulowano.'
            else:raise ValueError('questy zaleznosci karta/plan/zatwierdz/cofnij/anuluj (pomoc 32)')
        elif is_boss:
            if parts[1]=='zestaw':out=boss_layout(session,service,raw.partition('zestaw')[2].strip())
            else:out=boss_set(session,service,raw.partition('ustaw')[2].strip())
        else:
            if len(parts)>=4 and parts[1]=='plan' and '|' in raw:
                target, sep, ops=raw.partition('plan')[2].strip().partition('|')
                out=character_batch_plan(session,target.strip(),ops.strip())
            elif parts==['pakiet','zatwierdz','POTWIERDZAM']:out=character_batch_commit(session)
            elif parts==['pakiet','cofnij','POTWIERDZAM']:out=character_batch_undo(session)
            elif parts==['pakiet','anuluj']:
                session.adminlive7200_character_plan=None;out='POSTAC PAKIET: plan anulowano.'
            else:raise ValueError('postacie pakiet plan NAZWA | pole=liczba; ... / zatwierdz/cofnij/anuluj')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE V72: '+str(exc)[:260]
    await session.send(out)
    return True
