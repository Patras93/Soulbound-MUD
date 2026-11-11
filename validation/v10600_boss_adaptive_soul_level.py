# -*- coding: utf-8 -*-
"""Rzeczywisty tor Adaptive Combat 30k–60k, bez zmian w v105 i bez skracania HP.

Dokładna symulacja czasu walki i nagród w TCP nadal jest otwartym testem.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    from world.dynamic_content import ROOMS, MOB_TEMPLATES
    from systems.v106_combat_encounter_level import effective_encounter_level_v106
    from systems.adaptive_combat import adaptive_target_max_hp_v11330, adaptive_target_incoming_fraction_v11330
    from player.session_mixins.combat_damage import SessionCombatDamageMixin
    from systems import adaptive_switch_v102006

    assert os.environ.get('SOULBOUND_V106_STAGING')=='1','Wyłącznie v106 staging.'
    checks=0
    def ck(flag, label):
        nonlocal checks
        if not flag:raise AssertionError('ADAPTIVE SOUL V106: '+label)
        checks+=1
    room_id='v10600_przedmurze_14';mob_id='v10600_przedmurze_boss_1'
    template=MOB_TEMPLATES[mob_id];room=ROOMS[room_id]
    mob=SimpleNamespace(room_id=room_id,template_id=mob_id,key='v106test',alive=True,
                        hp=template['max_hp'])
    def c(soul):return SimpleNamespace(soul_level=soul,character_level=800)
    lvls={v:effective_encounter_level_v106(c(v),mob,template,room)
          for v in (1,800,20000,30001,30500,30999,60000)}
    ck(lvls[30001]>30000 and lvls[30001]<template['generator_level'], 'regional deficit not ignored')
    ck(lvls[30500]>lvls[30001], 'increasing Soul reduces relative deficit')
    ck(lvls[30999]==30999,'Soul above enemy remains unchanged')
    ck(lvls[1]<lvls[800]<lvls[20000]<lvls[30001], 'newbie and prior eras not boosted to rank')
    expected=template['max_hp']
    high=adaptive_target_max_hp_v11330(expected,5_000_000,template,party_level=lvls[30001],room=room)
    equal=adaptive_target_max_hp_v11330(expected,5_000_000,template,party_level=lvls[30999],room=room)
    low=adaptive_target_max_hp_v11330(expected,5_000_000,template,party_level=800,room=room)
    ck(1<high/expected<50,'proportional boss HP has reasonable bounded pressure')
    ck(equal==expected,'no artificial buff at sufficient Soul')
    ck(low>high*1000,'underpowered character remains under pressure')
    ck(template['max_hp']==expected and template['generator_level']>30001,
       'no changes in template, normal authored HP')
    inc_adequate=adaptive_target_incoming_fraction_v11330(template,1,player_level=lvls[30999],room=room)
    inc_low=adaptive_target_incoming_fraction_v11330(template,1,player_level=lvls[1],room=room)
    ck(inc_low>inc_adequate,'incoming underlevel pressure remains')

    class Session(SessionCombatDamageMixin):
        def __init__(self,soul):
            self.character=c(soul)
            self.server=SimpleNamespace(sessions=[])
            self.account_id=1;self.current_hp=1000000;self.closed=False
            self.combat_mob_key=None
        def adaptive_party_members_v11330(self,_mob):return [self]
        def adaptive_party_dps_v1261(self,_members):return 5_000_000
        def adaptive_mob_has_active_fighters_v1261(self,_mob):return False
        def max_hp(self):return 1_000_000
        def consider_enemy_expected_hit(self,t):return float(t['damage'])*0.2
    with patch.object(adaptive_switch_v102006,'_ENABLED',True):
        real=Session(30001)
        scaled=real.apply_adaptive_mob_scale_v11330(mob)
        ck(scaled is not None,'original real scaling method invoked')
        ck(scaled['max_hp']==high, 'real scaling actually uses the Soul comparison')
        ck(mob.hp==high and mob.adaptive_max_hp_v11330==high, 'live HP matches newly scaled max')
        ck(mob.adaptive_party_size_v11330==1, 'player count unchanged')
        incoming=real.adaptive_enemy_damage_multiplier_v11330(mob,template)
        ck(incoming>=1 and incoming<1e9,'real incoming scaling terminates')
        # Switching to a character with more Soul, outside active combat,
        # decreases prior adaptive HP without resurrecting lost hit points.
        real.character=c(30999)
        lowered=real.apply_adaptive_mob_scale_v11330(mob)
        ck(lowered['max_hp']==expected and mob.hp==expected,'normal original HP restored')
        # A wounded boss never heals while the prospective difficulty falls.
        mob.hp=expected//3
        real.character=c(30001)
        increased=real.apply_adaptive_mob_scale_v11330(mob)
        ck(increased['max_hp']==high and mob.hp<high,'old combat damage retained')
        real.character=c(30999)
        reduced=real.apply_adaptive_mob_scale_v11330(mob)
        ck(0<mob.hp<expected and reduced['max_hp']==expected,'downscale preserves damage fraction')

    ck(effective_encounter_level_v106(c(60000),SimpleNamespace(template_id='v10500_x',room_id='v10500_y'),
         {'generator_level':5000},{'generator_level':5000})==800,'historical monster never affected')
    ck(effective_encounter_level_v106(c(60000),SimpleNamespace(template_id=mob_id,room_id='v10500_y'),
         template,room)==800,'cross-region copied boss not affected')
    ck(effective_encounter_level_v106(c(60000),mob,template,{'generator_level':800})==800,
       'non-high room not affected')
    ck(effective_encounter_level_v106(c(60000),mob,{'training_dummy':True},room)==800,
       'training dummy not affected')
    with patch.dict(os.environ,{'SOULBOUND_V106_STAGING':'0'}):
        ck(effective_encounter_level_v106(c(60000),mob,template,room)==800,'production behavior unchanged')
    for bad in (None,'abc',True):
        ck(effective_encounter_level_v106(c(bad),mob,template,room)<template['generator_level'],
           'invalid Soul cannot remove boss pressure')
    raid_bosses={key:value for key,value in MOB_TEMPLATES.items()
            if key.startswith('v10600_raid_') and '_boss_' in key and key.count('_')==4}
    ck(len(raid_bosses)==30,'all thirty authored raid bosses present')
    for ident,template in raid_bosses.items():
        stage_id=ident.replace('_boss_','_stage_')
        dummy=SimpleNamespace(room_id=stage_id,template_id=ident)
        stage=template.get('v106_authored_boss_stage')
        ck(type(stage) is int and 30001<=stage<=60000,'raid authored stage '+ident)
        nominal=effective_encounter_level_v106(c(stage),dummy,template,ROOMS[stage_id])
        ck(nominal==stage,'at-tier raid not penalized '+ident)
        entry=effective_encounter_level_v106(c(max(1,stage-900)),dummy,template,ROOMS[stage_id])
        ck(stage-60<entry<stage,'underlevel raid proportional threat '+ident)
        base=template['max_hp']
        matched=adaptive_target_max_hp_v11330(base,1000000,template,party_level=nominal,room=ROOMS[stage_id])
        ck(matched==base,'raid normal HP retained at-tier '+ident)
    print(f'V106 REAL ADAPTIVE BOSS SOUL: {checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
