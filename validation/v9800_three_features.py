# -*- coding: utf-8 -*-
"""v98 integration: real Admin Live routing, UOSS runtime and SQLite safety."""
from __future__ import annotations
import asyncio,copy,sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_advancement_v9800 as advancement
from systems import uoss_tactics_v9800 as uoss
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from data.quests import QUESTS
from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES,TOOL_PROFESSION_MAP

async def main():
    count=0
    def ok(value,label):
        nonlocal count
        assert value,label
        count+=1
    fake=Fake();db=fake.server.db;con=db.conn
    con.executescript('''DROP TABLE professions;
      DROP TABLE characters;
      CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE,
        character_level INTEGER,character_xp INTEGER,soul_level INTEGER,soul_xp INTEGER,
        soul_weapon_mastery_level INTEGER,soul_weapon_mastery_xp INTEGER);
      INSERT INTO characters VALUES(2,'Friend',30,10,1,0,1,0);
      CREATE TABLE professions(account_id INTEGER,profession TEXT,level INT,xp INT,actions INT,
        PRIMARY KEY(account_id,profession));
      CREATE TABLE tools(account_id INTEGER,tool_type TEXT,level INT,xp INT,uses INT,
        PRIMARY KEY(account_id,tool_type));
      CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,
        PRIMARY KEY(account_id,kind,source_key));
      INSERT INTO experience_bank_v2011 VALUES(2,'character','','999999999999999999999999999999');''')
    pname=next(iter(PROFESSION_RANK_NAMES));tool=next(iter(TOOL_PROFESSION_MAP))
    con.execute('INSERT INTO professions VALUES(?,?,?,?,?)',(2,pname,5,12,42))
    con.execute('INSERT INTO tools VALUES(?,?,?,?,?)',(2,tool,4,13,89))
    con.commit()
    host=Fake(True,db);guest=Fake(False,db)
    host.server.sessions=[host];guest.server.sessions=[host]
    service=LiveContentV1204(SimpleNamespace(conn=con));host.server.live_content_v1204=service
    guest.server.live_content_v1204=service
    async def call(raw,actor=host):
        await actor.admin_command('live '+raw)
        return actor.messages[-1]
    try:
        # Old dispatch remains live; never expose owner-only cards to guests.
        for helpno in (55,56,57,58,59):
            ok('POMOC '+str(helpno) in await call(f'pomoc {helpno}'),'help '+str(helpno))
        for command in ('pomoc 57','pomoc 58','pomoc 59',
            'questy doktor skan',f'postacie postepy karta Friend',
            'boss uoss taktyka karta spekkio'):
            ok('Nieznana komenda' in await call(command,guest),'protected '+command)
        ok('POSTAC POSTEPY Friend' in await call('postacie postepy karta Friend'),'card online protected read')
        ok('profesja:' in host.messages[-1] and 'narzedzie:' in host.messages[-1] and 'bank:' in host.messages[-1],'all three card')
        original=tuple(con.execute('SELECT level,xp,actions FROM professions WHERE account_id=2').fetchone())
        oldtool=tuple(con.execute('SELECT level,xp,uses FROM tools WHERE account_id=2').fetchone())
        oldbank=con.execute('SELECT balance FROM experience_bank_v2011').fetchone()[0]
        plan=f'postacie postepy plan Friend | profesja:{pname}=6,20; narzedzie:{tool}=5,40; bank:character:=1234567890123456789012345678901234567890'
        ok('POSTAC POSTEPY PLAN' in await call(plan),'advancement plan')
        ok(tuple(con.execute('SELECT level,xp,actions FROM professions WHERE account_id=2').fetchone())==original,'read only planned')
        ok('POSTAC POSTEPY ZAPISANO' in await call('postacie postepy zatwierdz POTWIERDZAM'),'commit')
        ok(tuple(con.execute('SELECT level,xp,actions FROM professions WHERE account_id=2').fetchone())==(6,20,42),'profession persisted')
        ok(tuple(con.execute('SELECT level,xp,uses FROM tools WHERE account_id=2').fetchone())==(5,40,89),'tool uses preserved')
        ok(con.execute('SELECT balance FROM experience_bank_v2011').fetchone()[0]=='1234567890123456789012345678901234567890','bank big TEXT')
        ok('POSTAC POSTEPY COFNIETO' in await call('postacie postepy cofnij POTWIERDZAM'),'undo')
        ok(tuple(con.execute('SELECT level,xp,actions FROM professions WHERE account_id=2').fetchone())==original,'profession undid')
        ok(tuple(con.execute('SELECT level,xp,uses FROM tools WHERE account_id=2').fetchone())==oldtool,'tool undid')
        ok(con.execute('SELECT balance FROM experience_bank_v2011').fetchone()[0]==oldbank,'bank undid')
        for invalid in (f'profesja:{pname}=0,20',f'narzedzie:{tool}=2,-4',
            f'profesja:{pname}=99999999,0','bank:character:=0002','bank:character:foo=15',
            f'narzedzie:{tool}=5,9999999999999999','profesja:NOT_EXISTS=6,1',
            'bank:skill:non_existing=10',f'profesja:{pname}=6,2; profesja:{pname}=7,3'):
            ok('ADMIN LIVE POSTEPY V98' in await call('postacie postepy plan Friend | '+invalid),'invalid '+invalid)
        ok('POSTAC POSTEPY PLAN' in await call(plan),'CAS plan')
        con.execute('UPDATE tools SET xp=50 WHERE account_id=2')
        ok('Konflikt wpisu' in await call('postacie postepy zatwierdz POTWIERDZAM'),'CAS detected')
        ok(tuple(con.execute('SELECT level,xp FROM professions WHERE account_id=2').fetchone())==(5,12),'atomic rollback')
        con.execute('UPDATE tools SET xp=13 WHERE account_id=2')
        ok('POSTAC POSTEPY ZAPISANO' in await call('postacie postepy zatwierdz POTWIERDZAM'),'CAS retry')
        ok('COFNIETO' in await call('postacie postepy cofnij POTWIERDZAM'),'CAS undo')
        ok('POSTAC POSTEPY PLAN' in await call(plan),'audit plan')
        con.execute('DROP TABLE admin_actions_v1224')
        try:advancement.commit(host)
        except sqlite3.OperationalError:count+=1
        else:raise AssertionError('audit write failure not propagated')
        ok(tuple(con.execute('SELECT level,xp FROM professions WHERE account_id=2').fetchone())==(5,12),'audit rollback')
        con.execute('CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY,admin_login TEXT,action TEXT,target TEXT)')
        ok('POSTAC POSTEPY ZAPISANO' in await call('postacie postepy zatwierdz POTWIERDZAM'),'recover after audit failure')
        ok('COFNIETO' in await call('postacie postepy cofnij POTWIERDZAM'),'undo after failed audit')
        host.server.sessions.append(SimpleNamespace(closed=False,account_id=2,character=SimpleNamespace(name='Friend')))
        ok('ADMIN LIVE POSTEPY V98' in await call('postacie postepy karta Friend'),'online rejected')
        host.server.sessions.pop()
        # UOSS profile plans and real runtime selection, untouched old abilities.
        ids=list(UOSS_SUPERBOSS_ENCOUNTERS_V11134);key=ids[0];key2=ids[1]
        rules={'phases':[{'below_hp':100,'every':3,'attack_percent':150,'ai':'weakest','label':'Grom'},
                         {'below_hp':50,'every':1,'attack_percent':225,'ai':'strongest','label':'Nawałnica'}]}
        uoss.validate({key:rules});count+=1
        bad=[{'below_hp':80,'every':0,'attack_percent':120,'ai':'all','label':'Grom'},
             {'below_hp':50,'every':3,'attack_percent':900,'ai':'all','label':'Grom'},
             {'below_hp':50,'every':3,'attack_percent':120,'ai':'hack','label':'Grom'}]
        for phase in bad:
            try:uoss.validate({key:{'phases':[phase]}})
            except ValueError:count+=1
            else:raise AssertionError('invalid tactic accepted')
        import json
        pre=copy.deepcopy(service.draft)
        raw=f'boss uoss taktyka plan {key} | '+json.dumps(rules,ensure_ascii=False)
        ok('SUPERBOSS 2.0 PLAN' in await call(raw),'tactic draft plan')
        ok(service.draft==pre,'draft no change preapproval')
        ok('zatwierdzono' in await call('boss uoss taktyka zatwierdz POTWIERDZAM'),'tactic approval')
        ok(key in service.draft['v98_rules'] and key not in service.active['v98_rules'],'DRAFT-only')
        ok('Cofnieto' in await call('boss uoss taktyka cofnij POTWIERDZAM'),'tactic undo')
        ok(service.draft==pre,'exact draft undo')
        ok('SUPERBOSS 2.0 PLAN' in await call(raw),'replan')
        service.draft['v98_rules'][key2]={'phases':[{'below_hp':100,'every':1,'attack_percent':100,'ai':'all','label':'Cios'}]}
        ok('ADMIN LIVE V98 UOSS' in await call('boss uoss taktyka zatwierdz POTWIERDZAM'),'DRAFT conflict blocked')
        service.draft=copy.deepcopy(pre)
        ok('SUPERBOSS 2.0 PLAN' in await call(raw),'plan recovery')
        ok('zatwierdzono' in await call('boss uoss taktyka zatwierdz POTWIERDZAM'),'plan recovery commit')
        uoss.sync(service.draft['v98_rules'])
        targets=[SimpleNamespace(account_id=7,current_hp=90,closed=False),SimpleNamespace(account_id=8,current_hp=10,closed=False)]
        mob=SimpleNamespace(hp=70,max_hp=100,combat_turn=3)
        phase,selected=uoss.tactic(mob,{'uoss_unique_superboss_key':key},targets)
        ok(phase['label']=='Grom' and selected==8,'weakest selection')
        ok(uoss.modifier(phase,selected,targets[0])==1 and uoss.modifier(phase,selected,targets[1])==1.5,'single focus boost')
        mob.hp=40;phase,selected=uoss.tactic(mob,{'uoss_unique_superboss_key':key},targets)
        ok(phase['label']=='Nawałnica' and selected==7,'strongest phase')
        mob.combat_turn=2;mob.hp=70
        ok(uoss.tactic(mob,{'uoss_unique_superboss_key':key},targets)[0] is None,'cadence')
        uoss.sync({})
        # Quest Doctor uses full quest catalogue, not guessed references.
        ok('QUEST DOCTOR SKAN' in await call('questy doktor skan'),'doctor scan')
        qid=next(q for q,meta in QUESTS.items() if meta.get('kind') in ('multi_objective','collect_resource_set'))
        ok('QUEST DOCTOR' in await call('questy doktor karta '+qid),'doctor card')
        before=copy.deepcopy(service.draft)
        # Simulate a corrupted old DRAFT where needed is stale. The plan must
        # restore an exact mathematical sum and preserve all rewards.
        from systems.admin_live_v9400 import _counter_candidates
        baseline=_counter_candidates(service)
        service.draft.setdefault('quest_edits',{}).setdefault(qid,{})['needed']=9999
        fixes=dict((key,(old,new)) for key,old,new in _counter_candidates(service))
        ok(qid in fixes,'quest actual mathematical mismatch detected')
        from systems.admin_live_quest_doctor_v9800 import _problems
        problem_rows,_=_problems(service)
        doctor_page=next(i//8+1 for i,entry in enumerate(problem_rows) if entry[0]==qid)
        ok('LICZNIK DO NAPRAWY' in await call(f'questy doktor skan {doctor_page}'),'doctor scan categorizes')
        ok('JEDNOZNACZNE' in await call('questy doktor karta '+qid),'doctor exact fix')
        ok('QUEST DOCTOR PLAN' in await call('questy doktor plan 1'),'doctor plan')
        ok('zatwierdzono' in await call('questy doktor zatwierdz POTWIERDZAM'),'doctor draft approval')
        ok(service.draft['quest_edits'][qid]['needed']==fixes[qid][1],'exact new counter')
        ok('Cofnieto' in await call('questy doktor cofnij POTWIERDZAM'),'doctor undo')
        ok(service.draft['quest_edits'][qid]['needed']==9999,'doctor exact undo')
        service.draft=copy.deepcopy(before)
        ok('ok'==con.execute('PRAGMA integrity_check').fetchone()[0],'SQLite integrity')
        print(f'V98 THREE MAJOR FEATURES: {count} PASS',flush=True)
    finally:con.close()

if __name__=='__main__':asyncio.run(main())
