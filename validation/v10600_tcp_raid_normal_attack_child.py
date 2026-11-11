# -*- coding: utf-8 -*-
"""Odizolowany serwer testu NORMALNYCH ciosów rajdów v106.

Nie osłabia bossa, nie używa admin strike, nie zmienia wzoru ciosu.
Telemetria obejmuje wyłącznie wykonania oryginalnej rundy gracza.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    n=int(os.environ.get('SOULBOUND_V106_NATURAL_COUNT','0'))
    raid=int(os.environ.get('SOULBOUND_V106_NATURAL_RAID','0'))
    stage=int(os.environ.get('SOULBOUND_V106_NATURAL_STAGE','1'))
    path=Path(os.environ['SOULBOUND_DB']).resolve()
    assert 1 <= n <= 6 and 26 <= raid <= 35 and 1 <= stage <= 3
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V106_STAGING')=='1'
            and os.environ.get('SOULBOUND_V106_NATURAL_RAID_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')==str(n)
            and path.parent.name.startswith('soulbound-v106-natural-party-')
            and path.name=='natural_raid.sqlite'
            and not os.environ.get('SOULBOUND_ADMIN_ACCOUNTS'))
    import server
    from storage.database import Database
    from core.classes_skills import RACES,CLASSES
    from world.dynamic_content import ROOMS,QUESTS,MOB_TEMPLATES
    from player.session import Session
    room=f'v10600_raid_{raid}_stage_{stage}'
    quest=f'v10600_raid_{raid}_quest_{stage}'
    assert room in ROOMS and quest in QUESTS
    boss_level=int(MOB_TEMPLATES[f'v10600_raid_{raid}_boss_{stage}']['generator_level'])
    db=Database(str(path))
    try:
        for i in range(1,n+1):
            username=f'natural106{i:02d}'
            name=f'Natural106{i:02d}'
            aid=db.create_account(username,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,name,RACES[0],CLASSES[(i-1)%len(CLASSES)],
                {key:name for key in ('nom','gen','dat','acc','ins','loc','voc')})
            # Wyłącznie syntetyczny profil testowy, bez wyposażenia/bonusów.
            # 5000 statów odpowiada profilowi sprawdzonemu w prognozie DPS.
            db.conn.execute('''UPDATE characters SET soul_level=?, soul_tier=?,
                character_level=800, strength=5000, dexterity=5000,
                constitution=5000, intelligence=5000, willpower=5000,
                charisma=? WHERE account_id=?''',
                (boss_level, min(6000,boss_level//10),
                 500 if i==1 else 40,aid))
            for prior_stage in range(1,stage):
                prior_quest=f'v10600_raid_{raid}_quest_{prior_stage}'
                assert db.start_quest(aid,prior_quest) is not False
                db.complete_quest(aid,prior_quest)
            assert db.start_quest(aid,quest) is not False
        db.conn.commit()
    finally:
        db.conn.close()
    original_enter=Session.enter_world
    async def enter(self):
        await original_enter(self)
        if self.character and str(self.character.name).startswith('Natural106'):
            self.character.room_id=room
            self.server.db.save_character(self.character)
            await self.look()
    Session.enter_world=enter

    original_scale=Session.apply_adaptive_mob_scale_v11330
    from systems.v106_combat_encounter_level import effective_encounter_level_v106
    from world.dynamic_content import MOB_TEMPLATES,ROOMS
    scale_log=path.parent/'natural_scale.jsonl'
    def observed_scale(self,mob):
        if not mob or not str(mob.template_id).startswith('v10600_raid_'):
            return original_scale(self,mob)
        before=int(mob.hp)
        old=getattr(mob,'adaptive_max_hp_v11330',None)
        t=MOB_TEMPLATES.get(mob.template_id,{})
        roomdata=ROOMS.get(mob.room_id,{})
        stage=effective_encounter_level_v106(self.character,mob,t,roomdata)
        result=original_scale(self,mob)
        record={'who':self.character.name if self.character else None,'soul':getattr(self.character,'soul_level',None),
                'effective':stage,'mob_id':mob.template_id,'room_id':mob.room_id,
                'staging':os.environ.get('SOULBOUND_V106_STAGING'),
                'template_stage':t.get('generator_level'),
                'base_hp':t.get('max_hp'),
                'room_stage':roomdata.get('generator_level'),
                'template_dummy':t.get('training_dummy'),
                'before_hp':before,'after_hp':int(mob.hp),
                'old_max':old,'new_max':getattr(mob,'adaptive_max_hp_v11330',None),
                'dps':getattr(mob,'adaptive_party_dps_v11330',None),
                'partysize':getattr(mob,'adaptive_party_size_v11330',None)}
        with scale_log.open('a',encoding='utf8') as output: output.write(json.dumps(record)+'\n')
        return result
    Session.apply_adaptive_mob_scale_v11330=observed_scale
    # Obserwacja, a nie podmiana ciosu. Tylko testowy proces child.
    original_action=Session.realtime_player_action
    telemetry=path.parent/'natural_hits.jsonl'
    # An async action may suspend while other fighters hit the same boss.
    # Measuring (hp_before-hp_after) over the whole await DOUBLE-COUNTS them.
    # Contextvars attribute *synchronous* weapon hit/echo mutations precisely
    # to the acting session, without modifying authentic damage or boss logic.
    from contextvars import ContextVar
    _active_weapon=ContextVar('v106_natural_weapon_observation',default=None)
    from systems import uoss_basic_weapon_shared_v8000 as _weapon_module
    _real_hits=_weapon_module.apply_weapon_hit_series
    def exact_hits(mob,damage,count):
        before_hp=int(mob.hp)
        result=_real_hits(mob,damage,count)
        frame=_active_weapon.get()
        if frame is not None:
            frame['weapon']+=max(0,min(before_hp,int(result[0])))
            frame['hit_count']+=int(result[1])
        return result
    _weapon_module.apply_weapon_hit_series=exact_hits
    _real_echo=_weapon_module.weapon_after_hit
    def exact_echo(actor,mob,damage,traits,mastery,*,disabled=False):
        before_hp=int(mob.hp)
        result=_real_echo(actor,mob,damage,traits,mastery,disabled=disabled)
        frame=_active_weapon.get()
        if frame is not None:
            frame['echo']+=max(0,min(max(0,before_hp),int(result[0])))
        return result
    _weapon_module.weapon_after_hit=exact_echo
    async def observed(self,mob):
        before=int(mob.hp)
        alive=bool(mob.alive)
        frame={'weapon':0,'echo':0,'hit_count':0}
        token=_active_weapon.set(frame)
        try:
            await original_action(self,mob)
        finally:
            _active_weapon.reset(token)
        after=int(mob.hp)
        if alive and self.character and str(self.character.name).startswith('Natural106'):
            record={'name':self.character.name,'at':__import__('time').time(),'before':before,'after':after,
                    'damage':frame['weapon']+frame['echo'],'weapon':frame['weapon'],
                    'echo':frame['echo'],'hit_count':frame['hit_count'],'alive':bool(mob.alive),
                    'phase':int(getattr(mob,'phase_stage',0) or 0),
                    'player_hp':int(self.current_hp),
                    'mob_key':str(mob.key),'template':str(mob.template_id),
                    'soul_level':int(self.character.soul_level),
                    'adaptive_dps':str(getattr(mob,'adaptive_party_dps_v11330',None)),
                    'adaptive_hp':str(getattr(mob,'adaptive_max_hp_v11330',None)),
                    'adaptive_party':str(getattr(mob,'adaptive_party_size_v11330',None))}
            with telemetry.open('a',encoding='utf-8') as output:
                output.write(json.dumps(record,ensure_ascii=False)+'\n')
    Session.realtime_player_action=observed
    # Test success is settled rewards, not merely mob.alive=False. The
    # victory animation can precede async quest-credit and SQLite commits.
    original_defeated=Session.mob_defeated
    async def observed_defeated(self,mob):
        # Dwie sesje moga rownolegle wywolac callback po smierci bossa.
        # Tylko zwyciezca wylacznego claim przed pierwszym await moze
        # oglosic KONIEC ROZLICZENIA; odrzucony wtorny callback NIE jest PASS.
        owns_claim=bool(mob and getattr(mob,'alive',False)
                        and not getattr(mob,'v1400_kill_in_progress',False))
        result=await original_defeated(self,mob)
        if owns_claim and str(getattr(mob,'template_id','')).startswith('v10600_raid_'):
            with (path.parent/'natural_settled.jsonl').open('a',encoding='utf8') as out:
                out.write(json.dumps({'mob_id':str(mob.template_id),'at':__import__('time').time(),
                    'name':getattr(self.character,'name','')},ensure_ascii=False)+'\n')
        return result
    Session.mob_defeated=observed_defeated
    # Temporary transactional tracer: determine precisely whether quest
    # advancement was invoked on each real kill; no writes beyond the
    # original canonical quest-settlement call.
    import systems.atomic_kill_quest_progress_v10400 as _settlement
    _real_settle=_settlement.settle_all_kill_quests_v10400
    def trace_settle(db,account_id,template_id,**kwargs):
        qid=f'v10600_raid_{raid}_quest_{stage}'
        before=db.quest(account_id,qid)
        result=_real_settle(db,account_id,template_id,**kwargs)
        after=db.quest(account_id,qid)
        with (path.parent/'natural_credit_trace.jsonl').open('a',encoding='utf8') as out:
            out.write(json.dumps({'account':account_id,'template':template_id,
                'before':int(before['progress']) if before else None,
                'after':int(after['progress']) if after else None,
                'n_simple':len(result[0])},ensure_ascii=False)+'\n')
        return result
    _settlement.settle_all_kill_quests_v10400=trace_settle
    original_die=Session.die
    async def observed_die(self,killer):
        if self.character and str(self.character.name).startswith('Natural106'):
            with (path.parent/'natural_deaths.jsonl').open('a',encoding='utf8') as out:
                out.write(json.dumps({'name':self.character.name,'killer':str(killer),
                    'at':__import__('time').time(),'hp':int(self.current_hp),
                    'room':str(self.character.room_id)},ensure_ascii=False)+'\n')
        return await original_die(self,killer)
    Session.die=observed_die
    # Timings only in the disposable TCP child; no changes to gameplay and
    # no profiling code runs in the actual v105/v106 server.
    import time as _perf_clock
    perf_log=path.parent/'natural_timing.jsonl'
    def _log_timing(method, seconds, who):
        if seconds >= .25:
            with perf_log.open('a',encoding='utf8') as output:
                output.write(json.dumps({'method':method,'seconds':round(seconds,4),
                                         'name':who},ensure_ascii=False)+'\n')
    _original_scale_timed=Session.apply_adaptive_mob_scale_v11330
    def _timed_scale(self,mob):
        start=_perf_clock.perf_counter()
        try:return _original_scale_timed(self,mob)
        finally:_log_timing('adaptive-scale',_perf_clock.perf_counter()-start,
                            getattr(getattr(self,'character',None),'name',''))
    Session.apply_adaptive_mob_scale_v11330=_timed_scale
    for _name in ('attack','realtime_player_action','send'):
        _original=getattr(Session,_name)
        def _wrap(_original=_original,_name=_name):
            async def _timed(self,*args,**kwargs):
                if _name=='send' and args and 'Pętla walki została zatrzymana' in str(args[0]):
                    print('V106 STOP COMBAT LOOP: '+str(getattr(getattr(self,'character',None),'name',''))
                          +' '+str(args[0]),flush=True)
                start=_perf_clock.perf_counter()
                try:return await _original(self,*args,**kwargs)
                finally:_log_timing(_name,_perf_clock.perf_counter()-start,
                                    getattr(getattr(self,'character',None),'name',''))
            return _timed
        setattr(Session,_name,_wrap())
    print('TEST_TCP_ACCOUNTS_READY V106 NATURAL RAID',n,raid,stage,flush=True)
    server.main()

if __name__=='__main__':main()
