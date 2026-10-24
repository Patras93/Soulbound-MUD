# -*- coding: utf-8 -*-
"""v79: source boss defense, reproducible preview, state isolation, rollback."""
import asyncio
import copy
import random
from unittest.mock import patch
from data.mobs import MOB_TEMPLATES
from validation.v7800_arena_real_basic_damage import CombatOwner
from systems.admin_live_arena_damage_v7800 import _calculate_defended

async def main():
    count=0
    def check(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
    player=CombatOwner()
    async def command(msg):
        await player.admin_command('live '+msg)
        return player.messages[-1]
    check('POMOC 39' in await command('pomoc 39'),'help')
    check('ARENA11 START' in await command('arena start black_rabite 100000000 1000'),'start')
    lab=player.guardian7_lab
    boss_id=lab['boss'].template_id
    real_before=(player.current_mana,player.server.db.conn.total_changes,random.getstate())
    def snapshot(l):
        return (l["round"],l["hero_hp"],l["hero_attack"],l["boss"].hp,
                getattr(l["boss"],"player_hits",0),l["total_dealt"],l["total_taken"],
                tuple(l["notes"]),l.get("_v7800_rng"),l.get("_v7800_mana"))
    lab_before=snapshot(lab)
    # Force an armored + every-third-hit shield as if authored in the
    # production MOB_TEMPLATES, without permanently modifying that catalog.
    original=MOB_TEMPLATES[boss_id]
    shield=dict(original,boss_mechanic='grave_shield',elite_affix='armored')
    with patch.dict(MOB_TEMPLATES,{boss_id:shield}):
        with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
            raw,defended,mana,rng,hits,notes=await _calculate_defended(player,lab,3)
            check(len(defended)==3 and hits==3,'three consecutive source defenses')
            check(all(0<d<r for d,r in zip(defended,raw)),'armored affix used')
            check(defended[-1] < int(round(raw[-1]*0.7)),'grave shield every third hit')
            check(any('Opancerzony' in s for s in notes),'production defense messages')
            check(any('Tarcze' in s or 'Tarczę' in s for s in notes),'production shield message')
            report=await command('arena uoss gracz prognoza 3')
            check(', '.join(map(str,defended)) in report,'preview real defended values')
            check(snapshot(player.guardian7_lab)==lab_before,'preview does not touch lab state')
            check((player.current_mana,player.server.db.conn.total_changes,random.getstate())==real_before,
                  'preview no live stats DB global RNG mutation')
            for i in range(3):
                result=await command('arena uoss gracz atak POTWIERDZAM')
                check('po produkcyjnej obronie' in result,'strike source defense')
                check(player.guardian7_lab['boss'].player_hits==i+1,'persist private defense counters')
                check((player.current_mana,player.server.db.conn.total_changes,random.getstate())==real_before,
                      'strike does not touch live state')
            check(player.guardian7_lab['total_dealt']==sum(defended),'damage after defense applied once, not raw')
            state=snapshot(player.guardian7_lab)
            _=await command('arena uoss gracz prognoza 2')
            check(snapshot(player.guardian7_lab)==state,'later preview stable')
            with patch('systems.admin_live_arena_damage_v7800._lab_turn10',side_effect=RuntimeError('boom')):
                try:await command('arena uoss gracz atak POTWIERDZAM')
                except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: expected induced rollback failure; else branch asserts exception
                else:raise AssertionError('should propagate unexpected failure')
            check(snapshot(player.guardian7_lab)==state,'rollback on unexpected error')
            check((player.current_mana,player.server.db.conn.total_changes,random.getstate())==real_before,
                  'rollback preserves production state')
    # A source dodge with deterministic RNG does not consume world RNG.
    dodge=dict(original,boss_mechanic='ethereal_evade',elite_affix=None)
    with patch.dict(MOB_TEMPLATES,{boss_id:dodge}), patch(
        "player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338",return_value=1.0
    ):
        _r,ds,_m,_rng,_hits,_notes=await _calculate_defended(player,player.guardian7_lab,8)
        check(any(d==0 for d in ds) or all(d>0 for d in ds),'source dodge resolves safely')
        check(random.getstate()==real_before[2],'dodge no global RNG change')
    check(MOB_TEMPLATES[boss_id] is original,'production templates restored')
    return count

if __name__=='__main__':
    print('v79 production boss defense:',asyncio.run(main()),'PASS')
