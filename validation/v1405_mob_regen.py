# -*- coding: utf-8 -*-
"""Regressions for fleeing combat, party aggro and out-of-combat HP recovery."""
from types import SimpleNamespace
from systems.mob_recovery_v1405 import (
    preserve_hp_when_encounter_ends_v1405, restore_idle_hp_tick_v1405,
)


def _mob(hp, *, alive=True, owner=None, adaptive=0, key='mob'):
    return SimpleNamespace(key=key, template_id='fixture', hp=hp, alive=alive,
        engaged_by=owner, aoe_engaged_by=None, adaptive_max_hp_v11330=adaptive,
        adaptive_hp_multiplier_v11330=1.0, adaptive_reward_multiplier_v11330=1.0,
        adaptive_party_size_v11330=1, adaptive_party_dps_v11330=0,
        adaptive_rank_v11330='', engaged_at=0, combat_turn=0, player_hits=0)


def run_mob_regen_regression_v1405(runtime=None):
    checks = 0
    errors = []

    def check(ok, msg):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(msg)

    check(preserve_hp_when_encounter_ends_v1405(400,1000,100)==40,
          'boss HP fraction must be retained on abandoning adaptive encounter')
    check(preserve_hp_when_encounter_ends_v1405(1,1000,100)==1,
          'surviving boss must retain at least one HP')
    check(preserve_hp_when_encounter_ends_v1405(0,1000,100)==0,
          'dead boss must stay dead')
    check(preserve_hp_when_encounter_ends_v1405(999,1000,100)==100,
          'rounding must not exceed base maximum')
    check(preserve_hp_when_encounter_ends_v1405(10**55,10**56,10**50)==10**49,
          'huge boss HP must use integer arithmetic')
    check(preserve_hp_when_encounter_ends_v1405(25,100,100)==25,
          'ordinary mob damage must not be cleared on flee')

    mob=_mob(25)
    check(restore_idle_hp_tick_v1405(mob, {'max_hp': 100})==10 and mob.hp==35,
          'idle mob must regenerate 10 percent each tick')
    for _ in range(8):
        restore_idle_hp_tick_v1405(mob, {'max_hp': 100})
    check(mob.hp==100, 'idle mob must eventually heal to full health')
    check(restore_idle_hp_tick_v1405(mob, {'max_hp': 100})==0,
          'full HP must never increase')
    engaged=_mob(25, owner='Hero')
    check(restore_idle_hp_tick_v1405(engaged, {'max_hp':100})==0 and engaged.hp==25,
          'mob fighting another player must not heal')
    engaged.aoe_engaged_by='Hero'; engaged.engaged_by=None
    check(restore_idle_hp_tick_v1405(engaged, {'max_hp':100})==0,
          'AoE engagement must prevent healing')
    dead=_mob(0,alive=False)
    check(restore_idle_hp_tick_v1405(dead, {'max_hp':100})==0 and dead.hp==0,
          'regen must not revive slain boss')
    adaptive=_mob(250,adaptive=1000)
    check(restore_idle_hp_tick_v1405(adaptive, {'max_hp':100})==0,
          'active adaptive scaling must not be bypassed')
    giant=_mob(10**49)
    check(restore_idle_hp_tick_v1405(giant, {'max_hp':10**50})==10**49,
          'huge-HP regen must work without floating-point overflow')
    tiny=_mob(1)
    check(restore_idle_hp_tick_v1405(tiny, {'max_hp':2})==1 and tiny.hp==2,
          'small mobs must heal by at least one point')

    if runtime is not None:
        class FakeWorld:
            def __init__(self, mobs):
                self.mobs = {m.key:m for m in mobs}
        class FakeCharacter:
            def __init__(self, room):
                self.room_id=room
                self.name='Hero'
        class FakeSession:
            closed=False
            current_hp=100
            def __init__(self, combat_key=None, name='Hero'):
                self.character=FakeCharacter('room')
                self.character.name=name
                self.combat_mob_key=combat_key
        # Methods are production MudServer methods, not local test copies.
        server=runtime.MudServer.__new__(runtime.MudServer)
        fixture_template=runtime.MOB_TEMPLATES
        template_id=next((tid for tid,t in fixture_template.items()
            if isinstance(t,dict) and int(t.get('max_hp',0) or 0)>=100),None)
        check(bool(template_id),'must have at least one real mob template')
        if template_id:
            cap=int(fixture_template[template_id]['max_hp'])
            m=_mob(max(1,cap//4),key='r1'); m.template_id=template_id; m.room_id='room'
            m2=_mob(max(1,cap//4),key='r2'); m2.template_id=template_id; m2.room_id='room'; m2.engaged_by='Hero'
            m3=_mob(max(1,cap//4),key='r3'); m3.template_id=template_id; m3.room_id='room'
            m4=_mob(max(1,cap//4),key='r4'); m4.template_id=template_id; m4.room_id='room'
            server.world=FakeWorld([m,m2,m3,m4]); server.sessions={FakeSession('r3', name='Friend'), FakeSession('r2', name='Hero')}
            # Inject no production data: actual template ID above is real.
            before=[z.hp for z in (m,m2,m3,m4)]
            recovered=server.regenerate_idle_mobs_v1405()
            check(recovered==2, 'only unengaged non-targeted mobs should regenerate')
            check(m.hp>before[0] and m4.hp>before[3], 'idle mobs must heal')
            check(m3.hp==before[2], 'active player target must not heal even if aggro is temporarily unset')
            check(m2.hp==before[1], 'combat owner must retain damage during fight')
            # Validate adaptive reset on actual production class.
            m.adaptive_max_hp_v11330=cap*4
            m.hp=cap*2
            server.reset_adaptive_mob_encounter_v11330(m)
            check(m.hp==cap//2 and m.adaptive_max_hp_v11330==0,
                  'flee must retain 50 percent boss HP after adaptive scaling reset')
    return {'checks':checks,'errors':errors}


if __name__=='__main__':
    report=run_mob_regen_regression_v1405()
    print('MOB REGEN v1.40.5:', report)
    if report['errors']:
        raise SystemExit(1)
