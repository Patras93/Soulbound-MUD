# -*- coding: utf-8 -*-
"""v106: 30 autentycznych bossow rajdowych, autorskie HP, fazy i prawdziwy respawn.

Ten test uruchamia World() i fazy AI, ale nie mierzy DPS prawdziwej
12-/25-osobowej druzyny ani czasu walki przez TCP.
"""
from __future__ import annotations
import os
from unittest.mock import patch


def run():
    assert os.environ.get('SOULBOUND_V106_STAGING') == '1', 'Test tylko staging v106.'
    import server
    from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
    from systems.v106_raid_phase_runtime import is_v106_raid_encounter
    from world.dynamic_content import MOB_TEMPLATES, ROOMS
    world = server.World()
    checks = 0
    def ok(expr, label):
        nonlocal checks
        if not expr:
            raise AssertionError('RAJD HP V106: ' + str(label))
        checks += 1
    spawned = {}
    for m in world.mobs.values():
        if m.template_id.startswith('v10600_raid_') and '_boss_' in m.template_id:
            root_id = str(MOB_TEMPLATES[m.template_id].get('base_template') or m.template_id)
            spawned[(m.room_id,root_id)] = m
    ok(len(spawned) == 30, '30 autentycznych spawnów')
    for no in range(26,36):
        for stage in range(1,4):
            mid = f'v10600_raid_{no}_boss_{stage}'
            rid = f'v10600_raid_{no}_stage_{stage}'
            mob = spawned[(rid,mid)]
            t = MOB_TEMPLATES[mob.template_id]
            initial = int(t['max_hp'])
            ok(initial > 0 and mob.hp == initial and mob.alive, mid+' pełne HP')
            ok(mob.template_id==mid and not t.get('world_threat_overdrive_v0384') and not t.get('terrain_runtime_clone_v0362'),mid+' bez starego generatora v0362/v0384')
            ok(initial == MOB_TEMPLATES[mid]['max_hp'],mid+' autorskie HP bez globalnego przemnożenia')
            ok(is_v106_raid_encounter(mob,t), mid+' wyłącznie dedykowany boss')
            ok(ROOMS[rid]['generator_level'] == t['generator_level'],mid+' poziom pokoju')
            ok([x['hp_percent'] for x in t['olc_boss_phases']]==[80,60,40,20],mid+' progi')
            # Autentyczna AI powinna po kolei reagować na 4 różne progi HP.
            for number,percent in enumerate((79,59,39,19),1):
                mob.hp=initial*percent//100
                msg=boss_tactics_phase_v1230(mob,t,now=100+number)
                ok(msg is not None and f'FAZA {number}/4' in msg,mid+f' próg {number}: {msg}')
                ok(mob.v1230_boss_phase==number,mid+' bieżąca faza')
                ok(mob.v1230_phase_attack_multiplier==t['olc_boss_phases'][number-1]['attack_multiplier'],mid+' mnożnik')
                ok(boss_tactics_phase_v1230(mob,t,now=100+number) is None,mid+' nie powtarza fazy')
            ok(mob.hp>0 and mob.hp<initial,mid+' AI nie leczy i nie skraca HP')
            # Przy skoku z pelnego HP do 15% AI nie moze zgubic faz 1-3.
            mob.v1230_boss_phase=0
            mob.v1230_phase_attack_multiplier=1
            mob.hp=initial*15//100
            for number in range(1,5):
                msg=boss_tactics_phase_v1230(mob,t,now=200+number)
                ok(msg is not None and f'FAZA {number}/4' in msg,mid+f' skok faz {number}')
            ok(boss_tactics_phase_v1230(mob,t,now=210) is None,mid+' skok bez duplikacji')
            ok(mob.hp==initial*15//100,mid+' brak modyfikacji HP')
            # Wszystkie trzy fazy rajdu muszą być niezależne od siebie.
            ok(t['quest_target']==mid,mid+' nagroda questa')
    # Realny refresh() wszystkich trzydziestu bossów po poprzedniej walce:
    # oddzielny runtime wariantu i stanu AI, nie zmieniamy bazy graczy.
    for mob in spawned.values():
        mob.v1230_boss_phase=4
        mob.v1230_phase_attack_multiplier=2.6
        mob.monster_ai_empowered_until_v1160=1e12
        mob.hp=0
        mob.alive=False
        mob.respawn_at=0.0
    world.refresh(force=True)
    for (rid,mid),mob in spawned.items():
        template=MOB_TEMPLATES[mob.template_id]
        ok(mob.alive and mob.hp==template['max_hp'],mid+' realny respawn przywraca pełne wariantowe HP')
        ok(getattr(mob,'v1230_boss_phase',None)==0,mid+' realny respawn kasuje numer fazy')
        ok(getattr(mob,'v1230_phase_attack_multiplier',None)==1.0,mid+' realny respawn kasuje poprzedni bonus')
        ok(not hasattr(mob,'monster_ai_empowered_until_v1160'),mid+' realny respawn kasuje czas wzmocnienia')
        mob.hp=mob.hp*79//100
        ok('FAZA 1/4' in (boss_tactics_phase_v1230(mob,template,now=300) or ''),
           mid+' pierwszy próg po odrodzeniu')
    # Jawnie wyłączona v106 i historie v105 nie dziedziczą reguły sekwencji.
    from types import SimpleNamespace
    t=MOB_TEMPLATES['v10600_raid_26_boss_1']
    fake=SimpleNamespace(template_id='v10600_raid_26_boss_1',room_id='v10600_raid_26_stage_1',hp=t['max_hp']//10,alive=True,v1230_boss_phase=0)
    with patch.dict(os.environ, {'SOULBOUND_V106_STAGING':'0'}):
        ok('FAZA 4/4' in (boss_tactics_phase_v1230(fake,t,now=123) or ''),'brak zmian poza staging')
    historic_id='v10400_raid_12_boss_1';historic=MOB_TEMPLATES[historic_id]
    old=SimpleNamespace(template_id=historic_id,room_id='v10400_raid_12_stage_1',hp=historic['max_hp']//10,alive=True,v1230_boss_phase=0)
    ok('FAZA 4/4' in (boss_tactics_phase_v1230(old,historic,now=123) or ''),'stara faza raid v104 zachowana')
    print(f'V106 RAID 26-35 REAL FULL HP + PHASES + RESPAWN: {checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
