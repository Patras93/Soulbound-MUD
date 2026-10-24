# -*- coding: utf-8 -*-
"""v90 regression: end-to-end real SQLite publication history and isolation."""
import asyncio
import copy
import json
import random
import sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204

async def run():
    n=0
    def ok(test,label):
        nonlocal n
        assert test,label
        n+=1
    owner=Fake();db=owner.server.db;service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    async def ask(cmd, session=owner):
        await session.admin_command('live '+cmd)
        return session.messages[-1]
    baseline=copy.deepcopy(service.active);rng=random.getstate()
    try:
        ok('POMOC 48' in await ask('pomoc 48'),'help')
        for command in ('pomoc 48','rewizje lista','rewizje karta 0','rewizje audyt','rewizje przywroc plan 0','rewizje przywroc zatwierdz POTWIERDZAM'):
            ok('Nieznana komenda' in await ask(command,guest),'permissions '+command)
        ok('REWIZJE LISTA' in await ask('rewizje lista'),'listing zero')
        ok('AKTYWNA' in await ask('rewizje lista'),'active entry')
        ok('AUDYT OK' in await ask('rewizje audyt'),'audit empty')
        ok('REWIZJE KARTA 0' in await ask('rewizje karta 0'),'card zero')
        ok('ADMIN LIVE V90' in await ask('rewizje karta -1'),'reject negative')
        ok('ADMIN LIVE V90' in await ask('rewizje karta 999'),'reject missing')
        ok('ADMIN LIVE V90' in await ask('rewizje lista 77'),'page invalid')
        ok('ADMIN LIVE V90' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'no plan')
        ok('ADMIN LIVE V90' in await ask('rewizje przywroc plan 0'),'identical draft')
        ok(db.conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==0,'empty DB history')
        service.draft['quest_edits']['temple_rats']={'reward_gold':100}
        ok('PRZEDPUBLIKACJA OK' in await ask('aktualizacja publikacja sprawdz'),'preflight')
        ok('Aktywowano' in service.apply(owner.server,'testowner'),'publish 1')
        ok(service.revision==1,'revision 1')
        ok('AUDYT OK' in await ask('rewizje audyt'),'audit 1')
        ok('REWIZJE KARTA 0' in await ask('rewizje karta 0'),'history 0')
        ok('REWIZJE KARTA 1' in await ask('rewizje karta 1'),'current 1')
        service.draft['quest_edits']['temple_rats']={'reward_gold':200}
        ok('Aktywowano' in service.apply(owner.server,'testowner'),'publish 2')
        ok(service.revision==2,'revision 2')
        ok('AUDYT OK' in await ask('rewizje audyt'),'audit 2')
        ok('REWIZJE LISTA' in await ask('rewizje lista'),'listing 2')
        ok('REWIZJE KARTA 1' in await ask('rewizje karta 1'),'historical 1')
        ok('REWIZJE KARTA 0' in await ask('rewizje karta 0'),'historical 0')
        compare=await ask('rewizje porownaj 0 2')
        ok('REWIZJE POROWNAJ 0 -> 2' in compare,'historic comparison')
        ok('quest_edits/temple_rats' in compare,'changed quest field shown')
        ok('200' in compare,'historic value shown')
        ok('BRAK' in await ask('rewizje porownaj 1 1'),'same revision has no differences')
        ok('ADMIN LIVE V90' in await ask('rewizje porownaj 0 2 999'),'comparison page reject')
        ok('Nieznana komenda' in await ask('rewizje porownaj 0 2',guest),'comparison admin only')
        before=copy.deepcopy(service.active)
        change0=db.conn.total_changes
        ok('REWIZJE PRZYWROC PLAN 1' in await ask('rewizje przywroc plan 1'),'plan older')
        ok(service.draft==service.active,'plan read only')
        ok(db.conn.total_changes==change0,'plan did not write')
        ok('zatwierdzono' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'confirm restore draft')
        ok(service.draft['quest_edits']['temple_rats']['reward_gold']==100,'draft restored 1')
        ok(service.active==before,'active untouched')
        ok(db.conn.total_changes==change0,'confirm no sqlite writes')
        ok('Cofnieto' in await ask('rewizje przywroc cofnij POTWIERDZAM'),'undo only draft')
        ok(service.draft==service.active,'draft undo exact')
        ok('REWIZJE PRZYWROC PLAN 0' in await ask('rewizje przywroc plan 0'),'plan baseline')
        ok('anulowany' in await ask('rewizje przywroc anuluj'),'cancel')
        ok('ADMIN LIVE V90' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'cancel prevents commit')
        ok('REWIZJE PRZYWROC PLAN 1' in await ask('rewizje przywroc plan 1'),'replan')
        service.draft['quest_edits'].setdefault('temple_rats',{})['needed']=12
        ok('DRAFT/ACTIVE zmienione' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'reject concurrent draft')
        service.draft=copy.deepcopy(service.active)
        ok('REWIZJE PRZYWROC PLAN 1' in await ask('rewizje przywroc plan 1'),'plan again')
        service.active['quest_edits']['temple_rats']['reward_gold']=201
        ok('Konflikt SQLite' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'reject changed active')
        service.active=copy.deepcopy(before)
        ok('AUDYT OK' in await ask('rewizje audyt'),'audit after attempted stale plan')
        # Cross-process style stale SQLite record must be detected without touching registries.
        stored=db.conn.execute('SELECT revision,payload FROM live_content_v1204 WHERE id=1').fetchone()
        original_payload=stored['payload'];changes=db.conn.total_changes
        db.conn.execute('UPDATE live_content_v1204 SET payload=? WHERE id=1', (json.dumps({}),))
        ok('Konflikt SQLite' in await ask('rewizje audyt'),'detect tampered live database')
        ok('Konflikt SQLite' in await ask('aktualizacja publikacja sprawdz'),'preflight stale blocked')
        service.draft['quest_edits']['temple_rats']={'reward_gold':300}
        try:service.apply(owner.server,'testowner')
        except ValueError as e:ok('Konflikt SQLite' in str(e),'publish conflict blocked')
        else:ok(False,'publish conflict accepted')
        ok(service.revision==2 and service.active==before,'stale guard does not modify memory')
        db.conn.execute('UPDATE live_content_v1204 SET payload=? WHERE id=1',(original_payload,))
        ok('AUDYT OK' in await ask('rewizje audyt'),'recovery after mismatch')
        # Missing history should not be treated as a valid restore chain.
        saved_history=db.conn.execute('SELECT payload,admin_login FROM live_content_history_v1204 WHERE revision=1').fetchone()
        db.conn.execute('DELETE FROM live_content_history_v1204 WHERE revision=1')
        ok('NIESPOJNA' in await ask('rewizje audyt'),'detect missing revision')
        ok('NIESPOJNA' in await ask('rewizje przywroc plan 0'),'no restore from broken chain')
        db.conn.execute('INSERT INTO live_content_history_v1204 (revision,payload,admin_login) VALUES (1,?,?)',
                        (saved_history['payload'],saved_history['admin_login']))
        ok('AUDYT OK' in await ask('rewizje audyt'),'restore history test fixture')
        # A valid restore to historical DRAFT can subsequently publish a new revision.
        service.draft=copy.deepcopy(service.active)
        ok('REWIZJE PRZYWROC PLAN 1' in await ask('rewizje przywroc plan 1'),'plan published 1')
        ok('zatwierdzono' in await ask('rewizje przywroc zatwierdz POTWIERDZAM'),'confirm again')
        ok('Aktywowano' in service.apply(owner.server,'testowner'),'publish recovery as new revision')
        ok(service.revision==3,'revision monotonically increases')
        ok(service.active['quest_edits']['temple_rats']['reward_gold']==100,'restored published value')
        ok('AUDYT OK' in await ask('rewizje audyt'),'history 3 valid')
        ok(db.conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==3,'append only 3')
        # Deliberate SQLite failure *after* the runtime has begun hot-publish:
        # history PK collision must roll back world registries and DB together.
        from data.quests import QUESTS
        original_quest=copy.deepcopy(QUESTS['temple_rats'])
        published=copy.deepcopy(service.active)
        db.conn.execute('INSERT INTO live_content_history_v1204 (revision,payload,admin_login) VALUES (4,?,?)',
                        (json.dumps(service.active,ensure_ascii=False), 'fault_injection'))
        db.conn.commit()
        service.draft['quest_edits']['temple_rats']={'reward_gold':400}
        try:service.apply(owner.server,'testowner')
        except sqlite3.IntegrityError:ok(True,'sql collision rejected')
        else:ok(False,'sql collision accepted')
        ok(service.revision==3,'failed publish kept revision')
        ok(service.active==published,'failed publish kept active')
        ok(QUESTS['temple_rats']==original_quest,'failed publish restored runtime quest registry')
        ok(db.conn.execute('SELECT revision FROM live_content_v1204 WHERE id=1').fetchone()[0]==3,
           'failed publish left database revision unchanged')
        db.conn.execute('DELETE FROM live_content_history_v1204 WHERE revision=4')
        db.conn.commit()
        service.draft=copy.deepcopy(service.active)
        ok('AUDYT OK' in await ask('rewizje audyt'),'history valid after simulated failure')
        ok(random.getstate()==rng,'random unchanged')
        print(f'ADMIN LIVE v90 REWIZJE: {n} PASS',flush=True)
    finally:
        db.conn.close()

if __name__=='__main__':asyncio.run(run())
