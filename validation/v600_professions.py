# -*- coding: utf-8 -*-
"""Soulbound v6.00.0: 8x jobs, real SQLite and atomicity gate (no production DB)."""
import asyncio
import os
import tempfile
import time
from types import SimpleNamespace

from core.classes_skills import RACES, CLASSES
from storage.database import Database
from systems.new_professions import AREAS, TIERS, PROFESSIONS, BASE_ACTIONS, work_for
from player.session_mixins.profesje6 import (
    SessionProfesje6Mixin, ORDER_GOODS, ensure_schema, _sum,
)

class _Practice(SessionProfesje6Mixin):
    def __init__(self, db, aid):
        self.server=SimpleNamespace(db=db)
        self.account_id=aid
        self.character=SimpleNamespace(room_id='market',silver=0,gold=0,mithril=0)
        self.output=[]
        self.break_reward=False

    async def send(self, text):
        self.output.append(str(text))

    def grant_profession_progress(self, prof, xp, tool, txp, *, content_level=None, **kw):
        # Existing Database facade, real profession/tool tables and commits.
        db=self.server.db
        p=db.profession(self.account_id,prof)
        t=db.tool(self.account_id,tool)
        db.save_profession(self.account_id,prof,p['level'],p['xp']+xp,p['actions']+1)
        db.save_tool(self.account_id,tool,t['level'],t['xp']+txp,t['uses']+1)
        if self.break_reward:
            raise RuntimeError('Simulated failure after profession XP write')
        return ([f'{prof}: +{xp} EXP, narzędzie +{txp} EXP'],p['level'],t['level'])

    async def do(self, command):
        self.output=[]
        await self.profesje6_command(command)
        return ' '.join(self.output)


def run_regression():
    assert len(PROFESSIONS)==8
    assert len({a[0] for a in PROFESSIONS.values()})==8
    assert len({a[1] for a in PROFESSIONS.values()})==8
    assert len(BASE_ACTIONS)>=24
    checks=4
    for action in BASE_ACTIONS:
        for tier in TIERS:
            got=work_for(action.prof,action.code,tier)
            assert got and got.xp>0 and got.tool_xp>0
            assert got.min_level==tier or tier==1
            assert got.region in AREAS and AREAS[got.region]
            assert got.xp>=action.xp and got.tool_xp>=action.tool_xp
            checks+=5
    checks+=asyncio.run(_run_sqlite())
    return checks


async def _run_sqlite():
    checks=0
    with tempfile.TemporaryDirectory(prefix='soulbound_v600_') as d:
        db=Database(os.path.join(d,'v600.sqlite'))
        master=db.create_account('TestProfessionsSix','LongSecurePassword2026!')
        cases={k:'Testowy' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,slot=db.create_character_for_master(master,'TestowyMistrz',RACES[0],CLASSES[0],cases)
        second,slot=db.create_character_for_master(master,'TestowyUczennik',RACES[0],CLASSES[0],cases)
        db.set_shared_wallet_for_master(master,25000,0,0)
        sess=_Practice(db,aid)
        sess.character.silver=25000
        ensure_schema(db)
        for profession, (tool,item,name) in PROFESSIONS.items():
            message=await sess.do('kup '+profession)
            assert 'Kupiono' in message
            assert db.item_qty(aid,item)==1
            money=sess.character.silver
            assert 'nie można kupić drugiego' in (await sess.do('kup '+profession)).lower()
            assert money==sess.character.silver
            assert db.conn.execute('SELECT count(*) FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(aid,item)).fetchone()[0]==1
            checks+=5
        assert db.conn.execute('SELECT count(*) FROM prof6_tools_owned WHERE account_id=?',(second,)).fetchone()[0]==0
        checks+=1
        for profession,(tool,item,name) in PROFESSIONS.items():
            db.profession(aid,profession)
            db.tool(aid,tool)
            db.save_profession(aid,profession,700,0,0)
            db.save_tool(aid,tool,700,0,0)
        for action in BASE_ACTIONS:
            tier=700
            job=work_for(action.prof,action.code,tier)
            sess.character.room_id=sorted(AREAS[job.region])[0]
            for item,qty in job.ingredients:
                db.add_item(aid,item,qty+10)
            if job.pending in {'harvest','milk','delivery','return'}:
                source={'harvest':'sow','milk':'feed','delivery':'dispatch','return':'voyage'}[job.pending]
                db.conn.execute('INSERT INTO prof6_work_state(account_id,kind,tier,ready_at) VALUES(?,?,?,?) '
                                'ON CONFLICT(account_id,kind) DO UPDATE SET tier=excluded.tier,ready_at=excluded.ready_at',
                                (aid,source,700,int(time.time())-10))
                db.conn.commit()
            db.conn.execute('DELETE FROM prof6_work_state WHERE account_id=? AND kind=?',(aid,job.pending)) if job.pending in {'sow','feed','dispatch','voyage'} else None
            db.conn.execute('DELETE FROM prof6_cooldowns WHERE account_id=?',(aid,));db.conn.commit()
            prev_prof=db.profession(aid,action.prof)['xp']
            cmd='praca '+action.prof+' '+action.code+' 700'
            message=await sess.do(cmd)
            assert f'{action.prof} — ' in message, (cmd,message)
            assert db.profession(aid,action.prof)['xp']>prev_prof
            for item,qty in job.outputs:
                assert _sum(db,aid,item)>=qty, (cmd,item)
                checks+=1
            checks+=2
        # Character-scoped daily order, not account-wide and not repeatable.
        for prof in PROFESSIONS:
            sess.character.room_id='market'
            good=ORDER_GOODS[prof]
            db.add_item(aid,good,30)
            before=db.profession(aid,prof)['xp']
            txt=await sess.do('oddaj '+prof)
            assert 'zakończone' in txt, (prof,txt)
            assert db.profession(aid,prof)['xp']>before
            assert 'już dziś' in (await sess.do('oddaj '+prof))
            checks+=3
        # Monetary balance stored in the canonical silver ledger; in-memory
        # character must exactly match to avoid save_character wallet overwrite.
        assert db.shared_wallet_for_master(master)==(sess.character.silver,0,0)
        checks+=1
        # Deliberately fail mid-work after material consumption and XP update.
        sess.break_reward=True
        sess.character.room_id='meadow'
        db.add_item(aid,'v600_tracks',3)
        before=_sum(db,aid,'v600_tracks')
        before_xp=int(db.profession(aid,'Łowiectwo')['xp'])
        try:
            await sess.do('praca Łowiectwo opraw 1')
        except RuntimeError as exc:
            assert 'Simulated failure' in str(exc)
        else: raise AssertionError('XP exception was unexpectedly swallowed')
        assert _sum(db,aid,'v600_tracks')==before
        assert int(db.profession(aid,'Łowiectwo')['xp'])==before_xp
        checks+=3
        # Failure in order after reward write must roll back item/currency/XP.
        sess.character.room_id='market'
        prof='Rolnictwo';good=ORDER_GOODS[prof]
        db.conn.execute('DELETE FROM prof6_order_claims WHERE account_id=? AND profession=?',(aid,prof));db.conn.commit()
        db.add_item(aid,good,5)
        oldgood=_sum(db,aid,good)
        oldmoney=db.shared_wallet_for_master(master)
        oldxp=int(db.profession(aid,prof)['xp'])
        try:
            await sess.do('oddaj '+prof)
        except RuntimeError as exc:
            assert 'Simulated failure' in str(exc)
        else: raise AssertionError('Order XP exception was unexpectedly swallowed')
        assert _sum(db,aid,good)==oldgood
        assert db.shared_wallet_for_master(master)==oldmoney
        assert int(db.profession(aid,prof)['xp'])==oldxp
        assert db.conn.execute('SELECT count(*) FROM prof6_order_claims WHERE account_id=? AND profession=?',(aid,prof)).fetchone()[0]==0
        checks+=5
        db.conn.close()
        again=Database(os.path.join(d,'v600.sqlite'))
        ensure_schema(again)
        assert again.conn.execute('SELECT count(*) FROM prof6_tools_owned WHERE account_id=?',(aid,)).fetchone()[0]==8
        assert again.conn.execute('SELECT count(*) FROM prof6_tools_owned WHERE account_id=?',(second,)).fetchone()[0]==0
        assert again.conn.execute('SELECT count(*) FROM prof6_order_claims WHERE account_id=?',(aid,)).fetchone()[0]==7
        checks+=3
        again.conn.close()
    return checks


if __name__=='__main__':
    print('SOULBOUND V6.00.0 PROFESJE SQLITE:',run_regression(),'checks PASS')
