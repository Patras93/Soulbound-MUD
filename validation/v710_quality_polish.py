# -*- coding: utf-8 -*-
"""v7.10.0: actual SQLite transaction, quest offering and NVDA regression.

Works only on a TemporaryDirectory database. No production characters touched.
"""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import asyncio
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from storage.database import Database
    from core.classes_skills import CLASSES, RACES
    from systems.new_professions import PROFESSIONS, AREAS
    from systems.living_empire_v7000 import UPGRADES, STORY_IDS, MASTER_INPUT
    from player.session_mixins.living_empire_v7000 import (
        SessionLivingEmpireV7000Mixin, ensure_schema, _sum,
    )
    from player.session_mixins.profesje6 import ensure_schema as ensure_prof6
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from validation.v600_professions import _Practice
    checks=0
    def ok(condition,context):
        nonlocal checks
        assert condition, 'v7.10.0: '+context
        checks+=1
    ok(runtime.VERSION in ('7.10.0','7.10.1','8.00.0','9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18','11.00.19','11.00.20','12.00.0','12.00.1','12.00.2','12.00.3','12.00.4','12.00.5','12.00.6','12.00.7','12.00.8','12.00.9','12.00.10','12.00.11', '12.00.12','12.00.13','12.10.0','13.00.0','13.10.0','14.00.0','15.00.0','15.10.0','15.20.0','15.30.0','15.40.0','16.00.0','17.00.0','18.00.0','19.00.0','20.00.0','21.00.0','22.00.0','35.00.0','35.00.1','35.00.2','35.00.3','35.00.4',),'release identity')
    if str(runtime.VERSION).startswith('35.'):
        ok(len(runtime.QUESTS)==6793, 'historical quest catalog retained in modern v35')
    else:
        ok(len(runtime.QUESTS)==(expected_quest_total_v1100() if runtime.VERSION in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18','11.00.19','11.00.20','12.00.0','12.00.1','12.00.2','12.00.3','12.00.4','12.00.5','12.00.6','12.00.7','12.00.8','12.00.9','12.00.10','12.00.11', '12.00.12','12.00.13','12.10.0','13.00.0','13.10.0','14.00.0','15.00.0','15.10.0','15.20.0','15.30.0','15.40.0','16.00.0','17.00.0','18.00.0','19.00.0','20.00.0','21.00.0','22.00.0',) else 6585 if runtime.VERSION in ('10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18','11.00.19','11.00.20','12.00.0','12.00.1','12.00.2','12.00.3','12.00.4','12.00.5','12.00.6','12.00.7','12.00.8','12.00.9','12.00.10','12.00.11', '12.00.12','12.00.13','12.10.0','13.00.0','13.10.0','14.00.0','15.00.0','15.10.0','15.20.0','15.30.0','15.40.0','16.00.0','17.00.0','18.00.0','19.00.0','20.00.0','21.00.0','22.00.0',) else 6573 if runtime.VERSION == '9.00.0' else 5605 if runtime.VERSION=='8.00.0' else 3925),'all old quests remain')
    ok(len(STORY_IDS)==64,'no duplicate or lost chronicle quest')
    ok(len(MASTER_INPUT)==22,'all professions preserved')
    class Practice(SessionLivingEmpireV7000Mixin,_Practice):
        async def do7(self,cmd):
            self.output=[]
            await self.imperium7_command(cmd)
            return '\n'.join(self.output)
    class StoryChecker(SessionQuestProgressMixin):
        pass
    with TemporaryDirectory(prefix='soulbound_710_') as d:
        path=Path(d)/'quality.sqlite'
        db=Database(str(path))
        master=db.create_account('TestQuestPolish710','LongSecurePassword710!')
        cases={k:'Tester' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'Kontroler710',RACES[0],CLASSES[0],cases)
        another,_=db.create_character_for_master(master,'Czytelnik710',RACES[0],CLASSES[0],cases)
        db.set_shared_wallet_for_master(master,180000,0,0)
        ensure_schema(db)
        ensure_prof6(db)
        session=Practice(db,aid)
        session.character.silver=180000
        story=StoryChecker()
        story.server=SimpleNamespace(db=db)
        story.account_id=aid
        # 8 mentors: unreached chapters must not advertise locked missions.
        for chapter in range(8):
            nid=f'v700_chronicle_npc_{chapter+1}'
            npc=runtime.NPCS[nid]
            visible=story.quest_ids_for_npc(nid,npc)
            ok(visible==([STORY_IDS[0]] if chapter==0 else []),nid+' not prematurely offered')
        # Traverse all 64 steps: native quest state unlocks precisely one next.
        for pos,qid in enumerate(STORY_IDS):
            ch=pos//8
            nid=f'v700_chronicle_npc_{ch+1}'
            npc=runtime.NPCS[nid]
            ok(story.quest_ids_for_npc(nid,npc)==[qid],qid+' visible only after prerequisites')
            db.start_quest(aid,qid)
            ok(story.quest_ids_for_npc(nid,npc)==[qid],qid+' active, not duplicated')
            db.complete_quest(aid,qid)
            ok(db.quest(aid,qid)['status']=='completed',qid+' completed in SQLite')
            ok(db.quest(another,qid) is None,qid+' never leaked to other character')
        for chapter in range(8):
            nid=f'v700_chronicle_npc_{chapter+1}'
            ok(story.quest_ids_for_npc(nid,runtime.NPCS[nid])==[],nid+' empty after completion')
        # At cost-preview time, neither goods nor progression can be modified.
        session.character.room_id=sorted(AREAS['field'])[0]
        before_rows=db.conn.execute('SELECT COUNT(*) FROM v700_improvements WHERE account_id=?',(aid,)).fetchone()[0]
        text=asyncio.run(session.do7('koszt pole'))
        ok('etap 1/8' in text and 'Brakuje:' in text,'actionable missing-material message')
        ok(before_rows==db.conn.execute('SELECT COUNT(*) FROM v700_improvements WHERE account_id=?',(aid,)).fetchone()[0], 'cost preview is read only')
        ok('Projekty:' in asyncio.run(session.do7('koszt nieznany')),'bad project recognized')
        ok('brak' in asyncio.run(session.do7('status')).lower(),'empty work list explicitly announced')
        # Existing resources in the craftbox must also count for the preview.
        db.add_storage_item(aid,'craftbox','field_grain',3)
        db.add_item(aid,'stone_blocks',1)
        text=asyncio.run(session.do7('koszt pole'))
        ok('Brakuje: nic' in text,'preview counts craftbox stock')
        # Canonical profession level and tool level remain unchanged by mere preview.
        prof='Rolnictwo'; tool,item,_=PROFESSIONS[prof]
        db.add_item(aid,item,1)
        db.conn.execute('INSERT INTO prof6_tools_owned(account_id,item_id) VALUES(?,?)',(aid,item))
        db.save_profession(aid,prof,700,0,0)
        db.save_tool(aid,tool,700,0,0)
        db.conn.commit()
        text=asyncio.run(session.do7('ulepsz pole'))
        ok('Ulepszono pole: 1/8' in text,'native SQL upgrade committed')
        ok('EXP profesji +' in text and 'EXP narzędzia +' in text,'compact NVDA reports XP numbers')
        ok(session._v7_upgrade('pole')==1,'upgrade persisted')
        ok(db.storage_qty(aid,'craftbox','field_grain')==0,'consumed craftbox materials')
        ok('pole 1/8' in asyncio.run(session.do7('status')),'NVDA status shows current upgrade')
        text=asyncio.run(session.do7('koszt pole'))
        ok('etap 2/8' in text,'next project has increased material requirements')
        asyncio.run(session.do7('nvda pełne'))
        msg=asyncio.run(session.do7('status'))
        ok('ERA ŻYJĄCEGO IMPERIUM' in msg and 'pole: 1/8' in msg,'expanded NVDA status')
        asyncio.run(session.do7('nvda zwięźle'))
        # Simulate an exception *after* item deduction and wallet update.
        # This detects any premature commit in a multi-table transaction.
        db.add_item(aid,'field_grain',9)
        prev_item=db.item_qty(aid,'field_grain')
        prev_silver=db.shared_wallet_for_master(master)[0]
        original=session.grant_profession_progress
        def fail_reward(*args,**kwargs):
            raise RuntimeError('Injected rollback before XP grant')
        session.grant_profession_progress=fail_reward
        try:
            try:
                session._v7_exec((('field_grain',4),), (('stone_blocks',3),),prof,1,coin_reward=5000,
                                 update=lambda: db.conn.execute("INSERT INTO v700_jobs(account_id,kind,destination,tier,ready_at) VALUES(?,?,?,?,?)",(aid,'qa710','test',1,0)))
            except RuntimeError as exc:
                ok('Injected rollback' in str(exc),'simulated error propagated')
            else:
                ok(False,'failure must be raised')
        finally:
            session.grant_profession_progress=original
        ok(db.item_qty(aid,'field_grain')==prev_item,'rolled back deducted inventory')
        ok(db.shared_wallet_for_master(master)[0]==prev_silver,'rolled back credited silver')
        ok(db.conn.execute("SELECT COUNT(*) FROM v700_jobs WHERE account_id=? AND kind='qa710'",(aid,)).fetchone()[0]==0,'rolled back job')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        db.conn.close()
        persisted=Database(str(path))
        ensure_schema(persisted)
        ok(persisted.conn.execute('SELECT level FROM v700_improvements WHERE account_id=? AND key=?',(aid,'pole')).fetchone()[0]==1,'project survived reopen')
        ok(persisted.conn.execute("SELECT COUNT(*) FROM v700_jobs WHERE kind='qa710'").fetchone()[0]==0,'failed operation remains absent after reopen')
        ok(persisted.conn.execute('SELECT COUNT(*) FROM quests WHERE account_id=?',(another,)).fetchone()[0]==0,'no cross-character quest leak after restart')
        persisted.conn.close()
    return checks


if __name__=='__main__':
    print('v7.10.0 quality regression:',run_regression(),'checks PASS')
