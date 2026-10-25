# -*- coding: utf-8 -*-
"""Regression for global ON/OFF: durable, admin-only, existing fights, rewards."""
from __future__ import annotations
import asyncio
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from data.mobs import MOB_TEMPLATES
from player.session_mixins.combat_damage import SessionCombatDamageMixin
from systems import adaptive_switch_v102006 as switch
from systems.monster_ecology_v1250 import adaptive_skills_v1250
from systems.team_learning_v1260 import enemy_team_pressure_v1260
from validation.v3600_admin_guardian2 import Fake
from validation.v2005_beginner_encounters import _CharacterSession


def run():
    checks = 0
    def check(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1

    old_path, old_state = switch.CONFIG_PATH, switch._ENABLED
    try:
        with tempfile.TemporaryDirectory(prefix='sb-adaptive-') as tmp:
            switch.CONFIG_PATH = Path(tmp) / 'LIVE_CONTENT' / 'adaptive.json'
            switch._ENABLED = None
            check(switch.enabled() is True, 'legacy mode ON before first decision')
            check(not switch.CONFIG_PATH.exists(), 'status does not write')
            admin=Fake();guest=Fake(False,admin.server.db)
            guest.server=admin.server
            mob_template=MOB_TEMPLATES['bandit']
            base=int(mob_template['max_hp'])
            scaled=base*100
            mob=SimpleNamespace(alive=True,template_id='bandit',key='bandit#1',room_id='temple',
                hp=scaled//2,adaptive_max_hp_v11330=scaled,
                adaptive_hp_multiplier_v11330=100.,adaptive_reward_multiplier_v11330=4.,
                adaptive_party_size_v11330=4,adaptive_party_dps_v11330=50000.,adaptive_rank_v11330='normal',
                player_hits=100,combat_turn=12)
            admin.server.world.mobs={'bandit#1':mob}
            async def call(session, command):
                await session.admin_command('live skalowanie '+command)
                return session.messages[-1]
            check('WLACZONE' in asyncio.run(call(admin,'status')), 'ON status')
            check('Nieznana' in asyncio.run(call(guest,'off')), 'unauthorized OFF denied')
            check(switch.enabled(), 'non-admin cannot modify state')
            check('WYLACZONE' in asyncio.run(call(admin,'off')), 'admin OFF succeeds')
            check(switch.enabled() is False, 'disabled without restart')
            check(switch.CONFIG_PATH.exists(), 'choice stored')
            check(json.loads(switch.CONFIG_PATH.read_text('utf-8')) == {'schema':1,'enabled':False}, 'durable format')
            check(mob.adaptive_max_hp_v11330==0, 'existing encounter de-scaled')
            check(mob.hp==max(1,(base+1)//2), 'fraction of prior damage preserved')
            check(mob.adaptive_party_dps_v11330==0, 'party DPS reset')
            check(mob.adaptive_reward_multiplier_v11330==1., 'adaptive rewards reset')
            check('WYLACZONE' in asyncio.run(call(admin,'status')), 'OFF status')
            check('Uzycie' in asyncio.run(call(admin,'blah')), 'invalid arg')
            check('WYLACZONE' in asyncio.run(call(admin,'off')), 'idempotent OFF')
            check(admin.server.db.logged and admin.server.db.logged[-1][-1]=='off', 'admin action logged')
            # OFF applies to new encounters, with no additional HP or DPS.
            fresh=SimpleNamespace(alive=True,template_id='bandit',hp=base,adaptive_max_hp_v11330=0)
            dummy=SimpleNamespace(character=SimpleNamespace(character_level=1000))
            result=SessionCombatDamageMixin.apply_adaptive_mob_scale_v11330(dummy,fresh)
            check(result is None and fresh.hp==base, 'no upscaling on new encounter')
            sim=_CharacterSession(1000,9999999)
            check(sim.adaptive_enemy_damage_multiplier_v11330(fresh,mob_template)==1.0,
                  'no adaptive damage multiplier for large player HP')
            preview=sim.consider_adaptive_preview_v11331(fresh,mob_template)
            check(preview['max_hp']==base, 'consider returns authored HP')
            check(preview['reward_multiplier']==1., 'consider adaptive rewards x1')
            check(preview['enemy_hit'] <= 1e10, 'damage preview finite without adaptive pressure')
            check(adaptive_skills_v1250(mob,mob_template,1000000,10)==1.0, 'no adaptive ecology multiplier')
            check(enemy_team_pressure_v1260(mob,mob_template)==1.0, 'no hit-count adaptive escalation')
            switch._ENABLED=None
            check(switch.enabled() is False,'restart loads OFF')
            check('WLACZONE' in asyncio.run(call(admin,'on')),'admin ON succeeds')
            check(switch.enabled() is True,'ON in memory')
            # Re-enable scaling for a subsequent encounter without restart.
            class CombatStub(SessionCombatDamageMixin):
                character=SimpleNamespace(character_level=100)
                def adaptive_party_members_v11330(self, mob): return [self]
                def adaptive_party_dps_v1261(self, members): return 1000000
                def adaptive_mob_has_active_fighters_v1261(self, mob): return False
            restored=SimpleNamespace(alive=True, template_id='bandit', room_id='temple', hp=base, key='again')
            after=CombatStub().apply_adaptive_mob_scale_v11330(restored)
            check(after is not None and restored.adaptive_max_hp_v11330 > base, 'ON re-enables scaling next encounter')
            check(restored.adaptive_reward_multiplier_v11330 >= 1., 'ON preserves adaptive reward mechanic')
            switch._ENABLED=None
            check(switch.enabled() is True,'restart loads ON')
            check('Nieznana' in asyncio.run(call(guest,'on')),'guest cannot control ON')
            async def help77():
                await admin.admin_live_v1204('pomoc 77')
                return admin.messages[-1]
            check('POMOC 77' in asyncio.run(help77()), 'NVDA help page 77')
            # Invalid persisted data must fail visibly instead of silently enabling.
            switch.CONFIG_PATH.write_text('{"schema":1,"enabled":"off"}','utf-8')
            switch._ENABLED=None
            try: switch.enabled()
            except ValueError: checks+=1
            else: raise AssertionError('invalid config accepted')
            return checks
    finally:
        switch.CONFIG_PATH=old_path
        switch._ENABLED=old_state

if __name__ == '__main__':
    print(f'GLOBAL ADAPTIVE v102.00.6: {run()} checks PASS', flush=True)
