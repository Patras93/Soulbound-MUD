# -*- coding: utf-8 -*-
"""v99: five bounded Admin Live extensions. All sensitive changes require plans.

New skill forge and boss regeneration are DRAFT-only; quest repair uses authored
field validators; online resources are transient CAS; arena parity is read-only.
"""
from __future__ import annotations
import copy
import json
import re
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v9400 import _touch_guard, _quest_field
from systems.admin_live_v9200 import _apply_patch
from systems.admin_live_integrity_v4900 import _effective, _issues
from systems.live_content_v1204 import ID
from systems.live_olc4_new_skills import validate_new_skills, FIELDS as SKILL_FIELDS
from systems.admin_live_v7500 import _boss
from systems.uoss_regeneration_v9900 import validate as validate_regen
from systems.admin_live_offline_v9700 import _audit

SLOTS = {'skill': ('adminlive9900_skill', 'adminlive9900_skill_undo'),
         'quest': ('adminlive9900_quest', 'adminlive9900_quest_undo'),
         'boss': ('adminlive9900_boss', 'adminlive9900_boss_undo')}
HELP = (
    'ADMIN LIVE POMOC 60: skill kreator karta ID / plan live_ID | JSON / zatwierdz POTWIERDZAM / '
    'cofnij POTWIERDZAM / anuluj. JSON: class_name,name,desc,kind,unlock,mana,cooldown,scale,mult,aliases '
    'oraz effect/element/olc_statuses. Nowe skille na istniejacym silniku, tylko DRAFT. '
    'POMOC 61: questy doktor pole ID / napraw plan ID POLE | WARTOSC; ID2 POLE | WARTOSC / '
    'napraw zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Walidator, aktywne questy i zaleznosci chronione; bez zgadywania ID. '
    'POMOC 62: arena real kontrola - autentycznosc osobnego silnika, dostep i granice izolacji; '
    'arena real start POTWIERDZAM, status, stop POTWIERDZAM jak dotad. '
    'POMOC 63: postacie online zasoby karta NAZWA / plan NAZWA | hp=LICZBA,mana=LICZBA / '
    'zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. Zmiany tylko biezacej sesji, '
    'bez trwałego poziomu i nagrod. '
    'POMOC 64: boss uoss odnowa karta BOSS / plan BOSS | {"phases":[{"below_hp":50,"every":3,"heal_percent":2,"label":"Regeneracja"}]} / '
    'zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Tylko DRAFT, publikacja OLC osobno i wylacznie poza aktywna walka.'
)


def _load_json(raw, maxlen=9000):
    if not 2 <= len(raw) <= maxlen:
        raise ValueError('JSON pusty albo zbyt dlugi.')
    try:
        value=json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError('Nieprawidlowy JSON.') from exc
    if type(value) is not dict:
        raise ValueError('Oczekiwany obiekt JSON.')
    return value


def _rows(raw, maximum=8, size=12000):
    if not 1 <= len(raw) <= size:
        raise ValueError('Plan pusty lub zbyt dlugi.')
    rows=[x.strip() for x in raw.split(';')]
    if not 1 <= len(rows) <= maximum or any(not x or '|' not in x for x in rows):
        raise ValueError(f'Plan: 1-{maximum} operacji oddzielonych srednikami, wymagany |.')
    return [tuple(x.strip() for x in row.split('|',1)) for row in rows]


def skill_card(service, sid):
    if not ID.fullmatch(sid):
        raise ValueError('ID nowego skilla ma zaczynac sie od live_.')
    data=service.draft['skills'].get(sid)
    return 'SKILL KREATOR '+sid+': '+(json.dumps(data, ensure_ascii=False, sort_keys=True) if data else 'BRAK W DRAFT')


def skill_plan(session, service, raw):
    slot,_=SLOTS['skill']; setattr(session,slot,None)
    changes=_rows(raw,8)
    before=copy.deepcopy(service.draft); candidate=copy.deepcopy(before)
    touched=set()
    for sid,value in changes:
        if not ID.fullmatch(sid) or sid in touched:
            raise ValueError('ID nowego skilla musi byc wolnym live_ID i nie moze sie powtarzac.')
        touched.add(sid)
        if value.upper() == 'AUTO':
            # Only revert an uncommitted skill; existing ACTIVE IDs are immutable.
            if sid in service.active['skills']:
                raise ValueError('Opublikowany skill wymaga osobnej migracji i nie moze zostac usuniety.')
            candidate['skills'].pop(sid,None)
        else:
            record=_load_json(value)
            allowed=SKILL_FIELDS | {'effect','element','olc_status','olc_statuses'}
            if not SKILL_FIELDS <= set(record) or not set(record) <= allowed:
                raise ValueError('Kreator: brakuje pol definicji lub nieznane pola.')
            candidate['skills'][sid]=record
    validate_new_skills(candidate['skills'],service.active['skills'])
    service.validate(candidate)
    if candidate == before:raise ValueError('Brak zmian w planie.')
    _plan(session,slot,before,service.active,candidate,'SKILL KREATOR v99')
    return f'SKILL KREATOR PLAN: {len(touched)} skilli, walidator silnika PASS. Bez zapisu i publikacji.'


def quest_fields(service,qid):
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Quest ID nie istnieje.')
    record=catalog[qid]
    errors, warnings=_issues(qid,record,catalog)
    return ('QUEST DOKTOR POLE '+qid+': rodzaj='+str(record.get('kind'))+
            '; pola='+', '.join(sorted(str(k) for k in record))+
            '; bledy='+('; '.join(errors) or 'BRAK')+
            '; ostrzezenia='+('; '.join(warnings) or 'BRAK')+
            '. Dla niejednoznacznych bledow podaj recznie poprawna wartosc.')


def quest_plan(session, service, raw):
    slot,_=SLOTS['quest'];setattr(session,slot,None)
    changes=_rows(raw,24,6500);before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before);catalog=_effective(service)
    touched=set();used=set()
    for left,value in changes:
        keys=left.split()
        if len(keys)!=2:raise ValueError('Format: QUEST_ID POLE | WARTOSC.')
        qid,field=keys
        if qid not in catalog:raise ValueError('Nieznany quest '+qid)
        canonical,parsed=_quest_field(field,value)
        if (qid,canonical) in used:raise ValueError('Powtorzone pole.')
        used.add((qid,canonical));touched.add(qid)
        if len(touched)>12:raise ValueError('Maksymalnie 12 questow w jednej transakcji.')
        if parsed == '__CLEAR_OVERRIDE__':
            patch=candidate.get('quest_edits',{}).get(qid)
            if patch:patch.pop(canonical,None)
            if qid in candidate.get('quests',{}):candidate['quests'][qid].pop(canonical,None)
        else:_apply_patch(candidate,qid,{canonical:parsed})
    if candidate==before:raise ValueError('Brak zmian.')
    _touch_guard(service,touched)
    service.validate(candidate)
    _plan(session,slot,before,service.active,candidate,'QUEST DOKTOR NAPRAW')
    session.adminlive9900_quest_touched=tuple(sorted(touched))
    return f'QUEST DOKTOR NAPRAW PLAN: {len(changes)} pol, {len(touched)} questow, walidacja PASS. Bez publikacji.'


def boss_card(service,boss):
    _boss(boss)
    return ('UOSS ODNOWA '+boss+': ACTIVE='+json.dumps(service.active['v99_rules'].get(boss,'AUTO'),ensure_ascii=False)
            +'; DRAFT='+json.dumps(service.draft['v99_rules'].get(boss,'AUTO'),ensure_ascii=False))


def boss_plan(session,service,raw):
    slot,_=SLOTS['boss'];setattr(session,slot,None)
    rows=_rows(raw,8);before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    seen=set()
    for boss,raw_value in rows:
        _boss(boss)
        if boss in seen:raise ValueError('Powtorzony boss.')
        seen.add(boss)
        if raw_value.upper()=='AUTO':candidate['v99_rules'].pop(boss,None)
        else:candidate['v99_rules'][boss]=_load_json(raw_value)
    validate_regen(candidate['v99_rules']);service.validate(candidate)
    if candidate==before:raise ValueError('Brak zmian.')
    _plan(session,slot,before,service.active,candidate,'UOSS ODNOWA')
    return f'UOSS ODNOWA PLAN: {len(seen)} bossow, 1-10% HP, tylko DRAFT. Bez publikacji.'


def arena_check(session):
    from systems import admin_live_native_arena_v8600 as native
    from pathlib import Path
    from systems.admin_live_v7100 import arena_coverage
    root=Path(__file__).resolve().parents[1]
    files_ok=all((root / x).is_file() for x in ('arena_real_izolowana.py','VERSION','START_Soulbound.bat'))
    state=native._current
    current='NIEURUCHOMIONA'
    if state:
        current='URUCHOMIONA' if state['process'].poll() is None else 'ZAKONCZONA'
    return ('ARENA REAL KONTROLA: osobny proces pelnego silnika='+('GOTOWY' if files_ok else 'BRAK PLIKOW')+
            '; instancja='+current+'; siec=127.0.0.1:4900; SQLite=prywatna migawka; '
            'wejscie z tej samej sesji MUD=NIE, osobny klient=TAK. '
            'Silnik produkcyjny z kopia danych, ale NIE jest to wspolny stan swiatowy. '+arena_coverage())


def _online(session,name):
    if not isinstance(name,str) or not re.fullmatch(r'[\w-]{1,40}',name,re.UNICODE):
        raise ValueError('Nieprawidlowa nazwa postaci.')
    matches=[s for s in getattr(session.server,'sessions',())
        if s is not None and not getattr(s,'closed',True) and
        getattr(getattr(s,'character',None),'name','').casefold()==name.casefold()]
    if len(matches)!=1:raise ValueError('Postac musi byc jednoznacznie zalogowana.')
    target=matches[0]
    if not isinstance(getattr(target,'account_id',None),int):raise ValueError('Brak poprawnego konta.')
    return target


def online_card(session,name):
    target=_online(session,name)
    return (f'POSTAC ONLINE ZASOBY {target.character.name}: HP {target.current_hp}/{target.max_hp()}, '
            f'MANA {target.current_mana}/{target.max_mana()}. Tylko chwilowa sesja; bez SQLite.')


def online_plan(session,raw):
    session.adminlive9900_online_plan=None
    rows=_rows(raw,1,250)
    name,values=rows[0];target=_online(session,name)
    # Do not race combat/critical transitions: online resource correction only out of battle.
    if getattr(target,'combat_mob_key',None) or getattr(target,'combat_pvp_target_id',None):
        raise ValueError('Postac walczy; zakoncz walke przed korekta zasobow.')
    maximum={'hp':int(target.max_hp()),'mana':int(target.max_mana())}
    old={'hp':int(target.current_hp),'mana':int(target.current_mana)}
    requested={}
    for item in values.split(','):
        match=re.fullmatch(r'\s*(hp|mana)\s*=\s*([0-9]{1,18})\s*',item,re.ASCII)
        if not match or match[1] in requested:raise ValueError('Wpisz hp=LICZBA,mana=LICZBA bez duplikatow.')
        field,num=match[1],int(match[2])
        if not (1 <= num <= maximum[field] if field=='hp' else 0 <= num <= maximum[field]):
            raise ValueError('Zasoby wykraczaja poza aktualny zakres.')
        requested[field]=num
    if all(old[k]==v for k,v in requested.items()):raise ValueError('Brak zmian.')
    session.adminlive9900_online_plan=(target, target.account_id, target.character.name,old,requested,maximum)
    return 'POSTAC ONLINE PLAN: '+name+'; '+', '.join(f'{k} {old[k]}->{v}' for k,v in requested.items())+'. Bez zmian.'


def _online_apply(session, plan, reverse=False):
    target,account,name,old,new,maximum=plan
    if _online(session,name) is not target or target.account_id!=account or target.character.name!=name:
        raise ValueError('Sesja postaci zmienila sie; plan wygasl.')
    if getattr(target,'combat_mob_key',None) or getattr(target,'combat_pvp_target_id',None):
        raise ValueError('Postac walczy; nie zmieniam HP ani many.')
    for field,value in maximum.items():
        current_max=int(target.max_hp() if field=='hp' else target.max_mana())
        if current_max!=value:raise ValueError('Zmiana maksymalnych zasobow uniewaznila plan.')
    for field,expected in (old if not reverse else new).items():
        if field in new and int(getattr(target,'current_'+field))!=expected:
            raise ValueError('Konflikt HP/many; brak zapisu.')
    for field,value in (new if not reverse else old).items():
        if field in new:setattr(target,'current_'+field,value)
    try:
        _audit(session.server.db.conn,session,'admin_live_v9900_online_undo' if reverse else 'admin_live_v9900_online',name)
    except BaseException:
        for field,expected in (old if not reverse else new).items():
            if field in new:setattr(target,'current_'+field,expected)
        raise
    return 'POSTAC ONLINE ZASOBY '+('COFNIETO' if reverse else 'ZMIENIONO')+' '+name+'; bez zmian poziomu, EQ, EXP i nagrod.'


def online_commit(session):
    plan=getattr(session,'adminlive9900_online_plan',None)
    if not plan:raise ValueError('Brak planu online.')
    answer=_online_apply(session,plan)
    session.adminlive9900_online_undo=plan
    session.adminlive9900_online_plan=None
    return answer


def online_undo(session):
    plan=getattr(session,'adminlive9900_online_undo',None)
    if not plan:raise ValueError('Brak operacji do cofniecia.')
    answer=_online_apply(session,plan,True)
    session.adminlive9900_online_undo=None
    return answer


async def dispatch_v9900(session,cmd,tail):
    raw=str(tail or '').strip();bits=raw.split()
    help_mode=(cmd=='pomoc' and raw in {'60','61','62','63','64'})
    skill=(cmd=='skill' and bits[:1]==['kreator'])
    quest=(cmd in ('questy','zadania') and bits[:2]==['doktor','napraw'] or cmd in ('questy','zadania') and bits[:2]==['doktor','pole'])
    arena=(cmd=='arena' and bits==['real','kontrola'])
    online=(cmd=='postacie' and bits[:2]==['online','zasoby'])
    boss=(cmd=='boss' and bits[:2]==['uoss','odnowa'])
    if not (help_mode or skill or quest or arena or online or boss):return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    service=session.server.live_content_v1204
    try:
        if help_mode:out=HELP
        elif arena:out=arena_check(session)
        elif online:
            args=bits[2:]
            if len(args)==2 and args[0]=='karta':out=online_card(session,args[1])
            elif len(args)>=2 and args[0]=='plan':out=online_plan(session,raw.split('plan',1)[1].strip())
            elif args==['zatwierdz','POTWIERDZAM']:out=online_commit(session)
            elif args==['cofnij','POTWIERDZAM']:out=online_undo(session)
            elif args==['anuluj']:session.adminlive9900_online_plan=None;out='ONLINE: plan anulowany.'
            else:raise ValueError('Wpisz admin live pomoc 63.')
        else:
            key=('skill' if skill else 'quest' if quest else 'boss')
            slot,undo=SLOTS[key]
            if skill:
                args=bits[1:]
                if len(args)==2 and args[0]=='karta':out=skill_card(service,args[1])
                elif len(args)>=2 and args[0]=='plan':out=skill_plan(session,service,raw.split('plan',1)[1].strip())
                else:out=None
            elif quest:
                args=bits[2:]
                if len(args)==1 and bits[1]=='pole':out=quest_fields(service,args[0])
                elif len(args)>=1 and args[0]=='plan' and bits[1]=='napraw':out=quest_plan(session,service,raw.split('plan',1)[1].strip())
                else:out=None
            else:
                args=bits[2:]
                if len(args)==2 and args[0]=='karta':out=boss_card(service,args[1])
                elif len(args)>=2 and args[0]=='plan':out=boss_plan(session,service,raw.split('plan',1)[1].strip())
                else:out=None
            # For all three OLC editors the confirmation verbs are common.
            if out is None:
                if args==['zatwierdz','POTWIERDZAM']:
                    if key=='quest' and getattr(session,slot,None):
                        _touch_guard(service,getattr(session,'adminlive9900_quest_touched',()))
                    out=_commit(session,service,slot,undo)
                elif args==['cofnij','POTWIERDZAM']:out=_undo(session,service,slot,undo)
                elif args==['anuluj']:setattr(session,slot,None);out='ADMIN LIVE V99: anulowano plan.'
                else:raise ValueError('Wpisz admin live pomoc 60-64.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE V99: '+str(exc)[:350]
    await session.send(out)
    return True
