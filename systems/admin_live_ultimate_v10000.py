# -*- coding: utf-8 -*-
"""Five incremental extensions to admin live; guarded, bounded, auditable.

1) Skill forge template cloning; 2) quest dependency/NPC diagnosis;
3) live character stat CAS in memory + SQLite; 4) in-session isolated
LAB snapshot using the source UOSS functions, NOT production 1:1;
5) declarative UOSS per-turn mana AI staged in DRAFT.
"""
from __future__ import annotations
import copy
import json
import re
from core.classes_skills import CLASS_SKILLS
from data.npcs import NPCS
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_five_v9900 import _load_json, _online, _rows
from systems.admin_live_characters_v7100 import FIELDS as STAT_FIELDS
from systems.admin_live_offline_v9700 import _audit
from systems.admin_live_integrity_v4900 import _effective, _issues
from systems.admin_guardian6_v4000 import _requirements
from systems.live_olc4_new_skills import validate_new_skills, FIELDS as SKILL_FIELDS
from systems.live_content_v1204 import ID
from systems.admin_live_v7500 import _boss
from systems.uoss_ai_v10000 import validate as validate_ai

HELP = (
 'ADMIN LIVE POMOC 65: skill kreator wzorce / skill kreator wzorzec plan NOWE_LIVE_ID WZOR_ID | {"name":"Nowa Nazwa","desc":"Opis"} / '
 'skill kreator wzorzec zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Kopia do DRAFT z istniejacego skilla, dozwolone tylko pola silnika; bez nowych rodzajow kodu. '
 'POMOC 66: questy doktor analiza QUEST_ID / questy doktor audyt [STRONA]. '
 'Zaleznosci (braki/cykle), NPC, sygnaly celow i aktywne questy w SQLite; zero automatycznych zmian. '
 'Naprawa reczna: pomoc 61. '
 'POMOC 67: postacie online raport NAZWA / postacie online staty plan NAZWA | strength=123,dexterity=45 / '
 'postacie online staty zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
 'Do 6 statystyk, jednoczesne CAS SQLite i sesji, tylko poza walka, bez EXPa, levelu, EQ i nagrod. '
 'POMOC 68: arena sesja start BOSS_ID OBRAZENIA / arena sesja krok / arena sesja status / arena sesja wyjdz. '
 'Uzywa HP administratora i zrodlowych funkcji UOSS na prywatnej kopii LAB; NIE pelna walka 1:1. '
 'Aby walczyc w pelnym silniku, arena real start POTWIERDZAM i osobny klient. '
 'POMOC 69: boss uoss ai karta BOSS / plan BOSS | {"phases":[{"below_hp":100,"every":3,"mode":"weakest","mana_percent":4,"label":"Wysysanie many"}]} / '
 'zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. DRAFT; publikacja OLC osobno i poza walka. '
 'AI: fazowe celowanie all/weakest/strongest/focus i wysysanie 1..10% many raz na ture. '
 'Bez uruchamiania kodu Python, edycji nagrod i ograniczania obrazen graczy.'
)

S_SKILL='adminlive10000_skill'; U_SKILL='adminlive10000_skill_undo'
S_AI='adminlive10000_ai'; U_AI='adminlive10000_ai_undo'
S_STATS='adminlive10000_stats'; U_STATS='adminlive10000_stats_undo'


def _template_skill(service,key):
    for cname, skills in CLASS_SKILLS.items():
        for skill in skills:
            if str(skill.get('id'))==key:
                return cname,dict(skill)
    record=service.draft['skills'].get(key)
    if record:
        return record['class_name'],dict(record)
    raise ValueError('Nieznany ID skilla wzorcowego.')


def skill_templates():
    return 'SKILL WZORCE: wprowadz ID istniejacego skilla (admin live katalog skill FRAZA); ' \
           'rodzaje dostepne tylko z silnika; najpierw plan, potem zatwierdz tylko DRAFT.'


def skill_clone_plan(session,service,raw):
    setattr(session,S_SKILL,None)
    m=re.fullmatch(r'\s*(live_[a-z0-9_]{3,55})\s+([a-zA-Z0-9_\-]{1,100})\s*\|\s*(.+)',raw,re.S)
    if not m:raise ValueError('Format: live_NOWY WZOR_ID | {"name":"Nazwa","desc":"Opis"}.')
    sid,source,override=m.groups()
    if not ID.fullmatch(sid):raise ValueError('Niepoprawny live_ID.')
    class_name,base=_template_skill(service,source)
    if sid==source or sid in service.active['skills']:raise ValueError('Opublikowany skill nie moze zostac podmieniony.')
    changes=_load_json(override,2000)
    allowed=SKILL_FIELDS | {'effect','element','olc_status','olc_statuses'}
    if not changes or not set(changes)<=allowed or 'name' not in changes:
        raise ValueError('Podaj przynajmniej nowa nazwe; pola musza pochodzic z walidatora skilli.')
    kind=str(base.get('kind',''))
    effective={'class_name':class_name,'name':base.get('name',''),'desc':base.get('desc','Nowa zdolnosc'),
               'kind':kind,'unlock':base.get('unlock',1),'mana':base.get('mana',0),
               'cooldown':base.get('cooldown',0),'scale':base.get('scale','strength'),
               'mult':base.get('mult',1.0),'aliases':[]}
    for k in ('element','olc_status','olc_statuses'):
        if k in base:effective[k]=copy.deepcopy(base[k])
    effects={'heal':'heal_pct','group_heal':'heal_pct','guard':'guard','drain':'drain_pct',
             'boost':'boost','execute':'execute_mult'}
    if kind in effects:
        value=base.get('effect',base.get(effects[kind]))
        if value is None:raise ValueError('Wzor ma nieobslugiwany efekt; zdefiniuj pelny skill recznie (pomoc 60).')
        effective['effect']=value
    effective.update(changes)
    before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before)
    candidate['skills'][sid]=effective
    validate_new_skills(candidate['skills'],service.active['skills'])
    service.validate(candidate)
    if candidate==before:raise ValueError('Brak zmian.')
    _plan(session,S_SKILL,before,service.active,candidate,'SKILL WZORZEC v100')
    return f'SKILL WZORZEC PLAN: {source} -> {sid}; walidacja PASS, bez publikacji.'


def _problem(service,qid,catalog):
    q=catalog[qid]
    errors,hints=_issues(qid,q,catalog)
    problems=list(errors)
    giver=q.get('giver')
    if isinstance(giver,str) and giver and giver not in NPCS and giver not in service.draft['npcs']:
        # Some legacy quests refer to NPC names, not IDs: deliberately a warning.
        hints.append('giver poza katalogiem NPC ID (moze byc imieniem)')
    path=[];visited=set();cycles=[];missing=[]
    def walk(key,depth):
        if depth>60 or len(visited)>500:return
        path.append(key);visited.add(key)
        for required in _requirements(catalog[key]):
            if required not in catalog:missing.append(f'{key}->{str(required)[:42]}')
            elif required in path:cycles.append('->'.join(path[path.index(required):]+[required])[:150])
            elif required not in visited:walk(required,depth+1)
        path.pop()
    walk(qid,0)
    problems += ['nieznana zaleznosc '+x for x in missing[:3]]
    problems += ['cykl '+x for x in cycles[:3]]
    return problems[:12],hints[:8],len(visited)


def quest_analysis(service,qid):
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Quest ID nie istnieje; katalog quest FRAZA.')
    errors,warnings,count=_problem(service,qid,catalog)
    con=service.conn
    active=con.execute("SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(qid,)).fetchone()[0]
    return (f'QUEST DOKTOR ANALIZA {qid}: zaleznosci sprawdzone {count}; aktywne u graczy {active}; '
            f'pewne problemy {len(errors)}: {"; ".join(errors) or "brak"}; '
            f'sygnaly {len(warnings)}: {"; ".join(warnings) or "brak"}. '
            'To audyt statyczny, nie dowod zrealizowania questa. '
            'Poprawki podaje administrator (pomoc 61), bez automatycznego wyboru NPC lub ID.')


def quest_audit(service,page='1'):
    if not re.fullmatch(r'[0-9]{1,4}',page) or int(page)<1:raise ValueError('Numer strony 1..9999.')
    catalog=_effective(service);rows=[]
    for qid in sorted(catalog):
        errors,hints,_=_problem(service,qid,catalog)
        if errors or hints:rows.append((qid,len(errors),len(hints)))
    pages=max(1,(len(rows)+7)//8);p=int(page)
    if p>pages:raise ValueError(f'Dostepne strony 1..{pages}.')
    return (f'QUEST DOKTOR AUDYT {p}/{pages}, przejrzano {len(catalog)}, z sygnalami {len(rows)}: '
            +('; '.join(f'{key}: bledy {err}, sygnaly {warn}' for key,err,warn in rows[(p-1)*8:p*8]) or 'BRAK')
            +'. Bez zapisu ani napraw automatycznych.')


def online_report(session,name):
    target=_online(session,name)
    char=target.character
    con=session.server.db.conn
    saved=con.execute('SELECT * FROM characters WHERE account_id=?',(target.account_id,)).fetchone()
    if saved is None:raise ValueError('Brak zapisanej postaci w bazie.')
    fields=('character_level','character_xp','soul_level','soul_xp','soul_weapon_mastery_level','soul_weapon_mastery_xp')
    progression=', '.join(f'{f}={getattr(char,f,"-")}' for f in fields)
    differences=[f for f in sorted(STAT_FIELDS) if getattr(char,f,None)!=saved[f]]
    return (f'POSTAC ONLINE RAPORT {char.name}: {progression}; '
            f'HP {target.current_hp}/{target.max_hp()}, MP {target.current_mana}/{target.max_mana()}; '
            f'staty {", ".join(f"{f}={getattr(char,f)}" for f in sorted(STAT_FIELDS))}; '
            f'niezgodnosc pamiec/SQLite: {", ".join(differences) or "BRAK"}. '
            'Rozwoj/ekwipunek online tylko do odczytu; korekty EXP, EQ, profesji po wylogowaniu.')


def online_stats_plan(session,raw):
    setattr(session,S_STATS,None)
    rows=_rows(raw,1,1500);name,details=rows[0]
    target=_online(session,name)
    if target is session:raise ValueError('Nie edytuj wlasnych statow w trakcie sesji administracyjnej.')
    if getattr(target,'combat_mob_key',None) or getattr(target,'combat_pvp_target_id',None):
        raise ValueError('Postac walczy; korekta zakazana.')
    changes={};con=session.server.db.conn
    row=con.execute('SELECT * FROM characters WHERE account_id=?',(target.account_id,)).fetchone()
    if row is None:raise ValueError('Brak rekordu SQLite.')
    for item in details.split(','):
        m=re.fullmatch(r'\s*([a-z_]+)=([0-9]{1,12})\s*',item,re.ASCII)
        if not m or m[1] not in STAT_FIELDS or m[1]=='deaths' or m[1] in changes:
            raise ValueError('Dozwolone tylko 6 podstawowych statystyk, bez deaths.')
        key,val=m[1],int(m[2]);old=int(getattr(target.character,key))
        if old!=int(row[key]):raise ValueError('Konflikt pamiec/SQLite '+key+'; najpierw zapisz postac normalnie.')
        if not 1<=val<=1_000_000_000:raise ValueError('Statystyka poza zakresem.')
        if old==val:raise ValueError('Brak zmiany: '+key)
        changes[key]=(old,val)
    # Assert no stat drift in other fields before editing a partially loaded object.
    if any(int(getattr(target.character,key))!=int(row[key]) for key in STAT_FIELDS if key!='deaths'):
        raise ValueError('Konflikt innych statystyk miedzy pamiecia i SQLite.')
    plan=(target,target.account_id,target.character.name,changes,
          {key:int(getattr(target.character,key)) for key in STAT_FIELDS if key!='deaths'})
    setattr(session,S_STATS,plan)
    return f'POSTAC ONLINE STATY PLAN {name}: '+', '.join(f'{k} {a}->{b}' for k,(a,b) in changes.items())+'. Bez zapisu.'


def _write_online(session,plan,reverse=False):
    target,account,name,changes,snapshot=plan
    if _online(session,name) is not target or target.account_id!=account or target.character.name!=name:
        raise ValueError('Sesja/identyfikator postaci zmieniony.')
    if getattr(target,'combat_mob_key',None) or getattr(target,'combat_pvp_target_id',None):
        raise ValueError('Postac jest w walce; zmiany zabronione.')
    con=session.server.db.conn
    for key,original in snapshot.items():
        expected=(changes[key][1] if reverse else original) if key in changes else original
        if int(getattr(target.character,key))!=expected:raise ValueError('Konflikt sesji: '+key)
        dbval=con.execute(f'SELECT {key} FROM characters WHERE account_id=?',(account,)).fetchone()
        if dbval is None or int(dbval[0])!=expected:raise ValueError('Konflikt SQLite: '+key)
    con.execute('SAVEPOINT adminlive10000_online')
    changed=[]
    try:
        for key,(old,new) in sorted(changes.items()):
            expected,targetvalue=(new,old) if reverse else (old,new)
            cur=con.execute(f'UPDATE characters SET {key}=? WHERE account_id=? AND {key}=?',
                            (targetvalue,account,expected))
            if cur.rowcount!=1:raise ValueError('Konflikt zapisu '+key)
            setattr(target.character,key,targetvalue);changed.append((key,expected))
        # Do not invalidate the real HP/max resource system silently. No free healing.
        if int(target.current_hp)>int(target.max_hp()) or int(target.current_mana)>int(target.max_mana()):
            raise ValueError('Nowe statystyki zmniejszaja max HP/MP ponizej zasobow; odrzucam bez zmian.')
        _audit(con,session,'admin_live_v10000_online_stats_undo' if reverse else 'admin_live_v10000_online_stats',name)
        con.execute('RELEASE SAVEPOINT adminlive10000_online')
    except BaseException:
        con.execute('ROLLBACK TO SAVEPOINT adminlive10000_online')
        con.execute('RELEASE SAVEPOINT adminlive10000_online')
        for key,value in changed:setattr(target.character,key,value)
        raise
    return 'POSTAC ONLINE STATY '+('COFNIETO' if reverse else 'ZAPISANO')+f' {name} ({len(changes)} pol), SQLite+sesja; audyt.'


def online_stats_commit(session):
    plan=getattr(session,S_STATS,None)
    if not plan:raise ValueError('Brak planu statystyk online.')
    msg=_write_online(session,plan)
    setattr(session,U_STATS,plan);setattr(session,S_STATS,None)
    return msg


def online_stats_undo(session):
    plan=getattr(session,U_STATS,None)
    if not plan:raise ValueError('Brak zapisu do cofniecia.')
    msg=_write_online(session,plan,True)
    setattr(session,U_STATS,None)
    return msg


def arena_snapshot_start(session,raw):
    parts=raw.split()
    if len(parts)!=2 or not re.fullmatch(r'[0-9]{1,15}',parts[1]):
        raise ValueError('Format: arena sesja start BOSS_ID OBRAZENIA.')
    if not getattr(session,'character',None) or int(getattr(session,'current_hp',0) or 0)<=0:
        raise ValueError('Administrator musi miec postac z HP > 0.')
    if getattr(session,'combat_mob_key',None) or getattr(session,'combat_pvp_target_id',None):
        raise ValueError('Przerwij prawdziwa walke przed symulacja.')
    from systems.admin_guardian7_v4100 import _lab_start
    strength=int(parts[1]);hp=int(session.current_hp)
    msg=_lab_start(session,session.server.live_content_v1204,parts[0],str(hp),str(strength))
    session.adminlive10000_lab_owner=(session.account_id,session.character.name)
    return 'ARENA SESJA: odczyt HP i modelowany atak. '+msg+' UWAGA: to LAB, nie walka 1:1.'


def arena_step(session):
    if not getattr(session,'adminlive10000_lab_owner',None):raise ValueError('Brak testu arena sesja.')
    from systems.admin_guardian7_v4100 import _lab_turn
    if session.adminlive10000_lab_owner!=(session.account_id,session.character.name):
        raise ValueError('Zmiana tozsamosci; test uniewazniony.')
    return 'ARENA SESJA LAB: '+_lab_turn(session)


def arena_status(session):
    from systems.admin_guardian7_v4100 import _lab_status
    if not getattr(session,'adminlive10000_lab_owner',None):raise ValueError('Brak testu arena sesja.')
    return 'ARENA SESJA: '+_lab_status(session)+' To model zrodlowy, NIE caly silnik.'


def ai_card(service,name):
    _boss(name)
    return ('UOSS AI '+name+': ACTIVE='+json.dumps(service.active['v100_rules'].get(name,'AUTO'),ensure_ascii=False)
        +'; DRAFT='+json.dumps(service.draft['v100_rules'].get(name,'AUTO'),ensure_ascii=False))


def ai_plan(session,service,raw):
    setattr(session,S_AI,None)
    rows=_rows(raw,8,12500);before=copy.deepcopy(service.draft);candidate=copy.deepcopy(before);seen=set()
    for name,value in rows:
        _boss(name)
        if name in seen:raise ValueError('Boss powtorzony.')
        seen.add(name)
        if value.upper()=='AUTO':candidate['v100_rules'].pop(name,None)
        else:candidate['v100_rules'][name]=_load_json(value,7500)
    validate_ai(candidate['v100_rules']);service.validate(candidate)
    if candidate==before:raise ValueError('Nie ma zmian.')
    _plan(session,S_AI,before,service.active,candidate,'UOSS AI v100')
    return f'UOSS AI PLAN: {len(seen)} bossow, walidacja PASS; tylko DRAFT, bez publikacji.'


async def dispatch_v10000(session,cmd,tail):
    raw=str(tail or '').strip();parts=raw.split()
    match=(cmd=='pomoc' and raw in {'65','66','67','68','69'} or
       cmd=='skill' and parts[:2] in (['kreator','wzorzec'],['kreator','wzorce']) or
       cmd in ('questy','zadania') and parts[:2] in (['doktor','analiza'],['doktor','audyt']) or
       cmd=='postacie' and parts[:2] in (['online','raport'],['online','staty']) or
       cmd=='arena' and parts[:1]==['sesja'] or
       cmd=='boss' and parts[:2]==['uoss','ai'])
    if not match:return False
    if not session.is_admin():await session.send('Nieznana komenda. Wpisz help.');return True
    service=session.server.live_content_v1204
    try:
        if cmd=='pomoc':msg=HELP
        elif cmd=='skill':
            tailargs=parts[2:]
            if parts==['kreator','wzorce']:msg=skill_templates()
            elif len(tailargs)>=2 and tailargs[0]=='plan':msg=skill_clone_plan(session,service,raw.split('wzorzec plan',1)[1].strip())
            elif tailargs==['zatwierdz','POTWIERDZAM']:msg=_commit(session,service,S_SKILL,U_SKILL)
            elif tailargs==['cofnij','POTWIERDZAM']:msg=_undo(session,service,S_SKILL,U_SKILL)
            elif tailargs==['anuluj']:setattr(session,S_SKILL,None);msg='SKILL WZORZEC: plan anulowany.'
            else:raise ValueError('Wpisz admin live pomoc 65.')
        elif cmd in ('questy','zadania'):
            if parts[:2]==['doktor','analiza'] and len(parts)==3:msg=quest_analysis(service,parts[2])
            elif parts[:2]==['doktor','audyt'] and len(parts) in (2,3):msg=quest_audit(service,parts[2] if len(parts)==3 else '1')
            else:raise ValueError('Wpisz admin live pomoc 66.')
        elif cmd=='postacie':
            if parts[:2]==['online','raport'] and len(parts)==3:msg=online_report(session,parts[2])
            elif parts[:3]==['online','staty','plan'] and '|' in raw:msg=online_stats_plan(session,raw.split('staty plan',1)[1].strip())
            elif parts==['online','staty','zatwierdz','POTWIERDZAM']:msg=online_stats_commit(session)
            elif parts==['online','staty','cofnij','POTWIERDZAM']:msg=online_stats_undo(session)
            elif parts==['online','staty','anuluj']:setattr(session,S_STATS,None);msg='POSTAC ONLINE STATY: anulowano plan.'
            else:raise ValueError('Wpisz admin live pomoc 67.')
        elif cmd=='arena':
            if parts[:2]==['sesja','start'] and len(parts)==4:msg=arena_snapshot_start(session,' '.join(parts[2:]))
            elif parts==['sesja','krok']:msg=arena_step(session)
            elif parts==['sesja','status']:msg=arena_status(session)
            elif parts==['sesja','wyjdz']:
                session.guardian7_lab=None;session.adminlive10000_lab_owner=None;msg='ARENA SESJA: test zamkniety, bez zmian produkcyjnych.'
            else:raise ValueError('Wpisz admin live pomoc 68.')
        else:
            tailargs=parts[2:]
            if len(tailargs)==2 and tailargs[0]=='karta':msg=ai_card(service,tailargs[1])
            elif len(tailargs)>=2 and tailargs[0]=='plan':msg=ai_plan(session,service,raw.split('ai plan',1)[1].strip())
            elif tailargs==['zatwierdz','POTWIERDZAM']:msg=_commit(session,service,S_AI,U_AI)
            elif tailargs==['cofnij','POTWIERDZAM']:msg=_undo(session,service,S_AI,U_AI)
            elif tailargs==['anuluj']:setattr(session,S_AI,None);msg='UOSS AI: anulowano plan.'
            else:raise ValueError('Wpisz admin live pomoc 69.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError) as exc:
        msg='ADMIN LIVE v100: '+str(exc)[:350]
    await session.send(msg)
    return True
