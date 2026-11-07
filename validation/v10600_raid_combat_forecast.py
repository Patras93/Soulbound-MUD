# -*- coding: utf-8 -*-
"""Odczyt prawdziwych wzorów do prognozy 1/3/6 IDENTYCZNYCH bohaterów.

To NIE jest pomiar rzeczywistych ataków TCP, nie obiecuje przeżycia bossa.
"""
from __future__ import annotations
import os
import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def run():
    assert os.getenv('SOULBOUND_V106_STAGING')=='1','Wyłącznie staging.'
    with socket.socket() as sk:
        sk.bind(('127.0.0.1',0)); port=sk.getsockname()[1]
    os.environ['SOULBOUND_HOST']='127.0.0.1'
    os.environ['SOULBOUND_PORT']=str(port)
    for k in ('PORT','RAILWAY_TCP_APPLICATION_PORT','DATABASE_URL','SOULBOUND_DB'):
        os.environ.pop(k,None)
    import server  # only canonical registry bootstrap on a random local port
    from storage.database import Database
    from core.classes_skills import CLASSES,RACES
    from player.character import Character
    from player.session import Session
    from world.dynamic_content import MOB_TEMPLATES,ROOMS
    from world.v10600_raids_26_35 import RAID_ROWS
    from systems.v106_raid_combat_forecast import forecast_raid_profile_v106
    from systems import adaptive_switch_v102006
    checks=0
    def ck(ok,label):
        nonlocal checks
        if not ok:raise AssertionError('PROGNOZA RAID: '+label)
        checks+=1
    # Cheap structural gate across every stage of every raid (30 bosses).
    for number,*_ in RAID_ROWS:
        for stage in (1,2,3):
            ident=f'v10600_raid_{number}_boss_{stage}'
            roomid=f'v10600_raid_{number}_stage_{stage}'
            t=MOB_TEMPLATES[ident]
            ck(int(t['max_hp'])>0 and int(t['damage'])>0, 'boss HP/atak')
            ck(int(t['generator_level'])>=30001, 'boss poziom')
            ck(int(ROOMS[roomid]['generator_level'])>=30001, 'sala poziom')
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-dps-offline-') as d:
        db=Database(str(Path(d)/'only_test.sqlite'))
        db._v106_raid_forecast_disposable_copy=True
        aid=db.create_account('forecast106','test_only_tcp_2026_password')
        name='PrognozaRajdu106'
        db.create_character_for_master(aid,name,RACES[0],CLASSES[0],
            {key:name for key in ('nom','gen','dat','acc','ins','loc','voc')})
        db.conn.commit()
        c=Character.from_row(db.character_for_account(aid))
        s=Session.__new__(Session)
        s.server=SimpleNamespace(db=db,sessions=[s],party_sessions=lambda *_a,**_kw:[s])
        s.character=c;s.account_id=aid;s.current_mana=10**9;s.current_hp=1
        s.active_skill_buffs={};s.combat_player_interval=1.35
        s.closed=False;s.admin_god_v35005=False;s.current_summons={}
        with patch.object(adaptive_switch_v102006,'_ENABLED',True):
            for stat in (800,5000):
                for raid in (26,35):
                    bid=f'v10600_raid_{raid}_boss_1'
                    rid=f'v10600_raid_{raid}_stage_1'
                    template=MOB_TEMPLATES[bid];room=ROOMS[rid]
                    c.room_id=rid;c.character_level=800
                    c.soul_level=int(template['generator_level'])
                    c.soul_tier=min(6000,c.soul_level//10)
                    for key in ('strength','dexterity','constitution','intelligence','willpower'):
                        setattr(c,key,stat)
                    s.current_hp=s.max_hp()
                    boss=SimpleNamespace(room_id=rid,template_id=bid,hp=template['max_hp'])
                    for count in (1,3,6):
                        pre=(boss.hp,db.conn.total_changes)
                        result=forecast_raid_profile_v106(s,count,boss,template,room)
                        ck(result['base_hp']==template['max_hp'],'baza HP')
                        ck(result['adaptive_hp']>=result['base_hp'],'skala nie obniża HP')
                        ck(result['players_assumed_identical']==count,'liczebność')
                        ck(result['party_autoattack_dps']>0,'dps realnych funkcji')
                        ck(result['autoattack_seconds_no_enemy_healing']>0,'czas orientacyjny')
                        ck(result['maximum_base_hits_before_fall']>=1,'ryzyko powalenia')
                        ck(boss.hp==pre[0],'prognoza zmieniła żywego bossa')
                        if stat==5000 and raid==26 and count==6:
                            legacy=s.adaptive_member_dps_v11330(s)
                            ck(result['base_autoattack_dps_one']>legacy*30,
                               'pominięte premie Broni Duszy i krytyków')
                        print(f'RAJD {raid} | {count} jednakowych postaci | staty {stat} | '
                              f'DPS drużyny {result["party_autoattack_dps"]:,.0f} | '
                              f'HP bossa po adaptive {result["adaptive_hp"]:,} | '
                              f'sam autoatak ~{result["autoattack_seconds_no_enemy_healing"]:.0f} s | '
                              f'górna granica ciosów na jedną postać '
                              f'{result["maximum_base_hits_before_fall"]}',flush=True)
            boss=SimpleNamespace(room_id='v10600_raid_26_stage_1',
                template_id='v10600_raid_26_boss_1',hp=1)
            t=MOB_TEMPLATES[boss.template_id];room=ROOMS[boss.room_id]
            # Invalid room, counts, staging and unsafe DB paths are hard errors.
            for count in (0,7,26,True):
                try:forecast_raid_profile_v106(s,count,boss,t,room)
                except ValueError:ck(True,'odmowa nieprawidłowego składu')
                else:raise AssertionError('Przyjęto nieprawidłowy skład')
            with patch.dict(os.environ,{'SOULBOUND_V106_STAGING':'0'}):
                try:forecast_raid_profile_v106(s,6,boss,t,room)
                except RuntimeError:ck(True,'poza staging odmowa')
                else:raise AssertionError('Przyjęto poza staging')
            db._v106_raid_forecast_disposable_copy=False
            try:forecast_raid_profile_v106(s,6,boss,t,room)
            except RuntimeError:ck(True,'brak zgody na kopię')
            else:raise AssertionError('Przyjęto nieoznakowaną DB')
            db.conn.close()
    print(f'V106 RAID HOMOGENOUS PROFILE FORECAST: {checks} PASS; NIE realne TCP',flush=True)
    return checks

if __name__=='__main__':run()
