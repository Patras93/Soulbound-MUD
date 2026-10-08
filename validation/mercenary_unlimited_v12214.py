# -*- coding: utf-8 -*-
"""v1.22.14: real independently acting hires, uncapped growth, single kill credit.

Purely synthetic combats. No game/world data or player saves are modified.
"""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_taverns import (
    COOLDOWN, MERCENARIES, mercenary_owner_full_power_v12213,
)
from systems.mercenary_growth_v1220 import (
    mercenary_attack_multiplier, mercenary_owner_level_v1228, mercenary_tactic,
)


def validate_mercenary_unlimited_v12214():
    checks = 0

    def ok(condition, label):
        nonlocal checks
        if not condition:
            raise AssertionError('v1.22.14 mercenaries: ' + label)
        checks += 1

    for level in (1, 100, 200, 600, 1000, 10000):
        ok(mercenary_attack_multiplier(level + 1, 'szturm') >
           mercenary_attack_multiplier(level, 'szturm'),
           'level bonuses must continue growing beyond former ceiling')
    ok(mercenary_attack_multiplier(10000, 'automatyczna') > 10.0,
       'no hidden late-game growth ceiling')
    ok(mercenary_owner_full_power_v12213(50000, 100, 1.5, 1.0, 2.0) == 150000,
       'full owner equipment, no cross-class reduction')

    source = Path(__file__).resolve().parents[1] / 'player/session_mixins/mercenary_taverns.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionMercenaryTavernsMixin')
    func = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'mercenary_combat_turn_v1170')
    clock = [100.0]
    ns = dict(
        time=SimpleNamespace(time=lambda: clock[0]), COOLDOWN=COOLDOWN,
        MERCENARIES=MERCENARIES,
        mercenary_owner_full_power_v12213=mercenary_owner_full_power_v12213,
        mercenary_attack_multiplier=mercenary_attack_multiplier,
        mercenary_owner_level_v1228=mercenary_owner_level_v1228,
        mercenary_tactic=mercenary_tactic,
        superboss_healing_blocked_v11179=lambda player: False,
        MOB_TEMPLATES={'test': {'name': 'Potężny przeciwnik'}},
        v0314_adjust_damage_vs_template=lambda template, power, dmg_type, role: (power, None),
    )
    exec(compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
                 str(source), 'exec'), ns)

    class Db:
        def __init__(self):
            self.roles = ['wojownik', 'mag']
            self.reads = 0
        def mercenary_contracts(self, owner, now):
            return [dict(role=r, expires_at=0) for r in self.roles]
        def mercenary_progress_v1220(self, owner, role):
            self.reads += 1
            return dict(specialization='automatyczna')
        def mercenary_gain_xp_v1220(self, *args):
            raise AssertionError('mercenaries do not save XP each action')

    class Owner:
        mercenary_combat_turn_v1170 = ns['mercenary_combat_turn_v1170']
        def __init__(self):
            self.character = SimpleNamespace(name='Bohater', room_id='room', character_level=1000)
            self.current_hp = 100000
            self.skill_guard = 1
            self.account_id = 1
            self.db = Db()
            self.messages = []
            self.kills = 0
            self.server = SimpleNamespace(db=self.db, party_sessions=lambda *a,**kw:[self],
                                          party_combat_broadcast=self.broadcast)
        def max_hp(self): return 100000
        def physical_power(self): return 50000
        def spell_power(self): return 100
        def equipment_damage_multiplier(self, channel): return 1.5 if channel == 'physical' else 1.0
        def total_set_damage_multiplier(self): return 1.2
        async def apply_boss_defense(self, mob, damage): return damage
        async def send_combat(self, msg, detail='essential'): self.messages.append(msg)
        async def broadcast(self, owner, msg, detail='essential'): pass
        async def mob_defeated(self, mob):
            ok(mob.hp == 0 and mob.alive, 'one defeat with remaining HP zero')
            mob.alive = False
            self.kills += 1

    async def run():
        owner = Owner()
        mob = SimpleNamespace(template_id='test', room_id='room', hp=10**12, alive=True)
        await owner.mercenary_combat_turn_v1170(mob)
        ok(len(owner.messages) == 2, 'both contracts act in first tick')
        ok(all(any(MERCENARIES[r]['name'] in msg for msg in owner.messages) for r in owner.db.roles),
           'both distinct mercenary skills fire')
        damage_first = 10**12 - mob.hp
        ok(damage_first >= 2 * 90000, 'each contributes full equipped power')
        await owner.mercenary_combat_turn_v1170(mob)
        ok(len(owner.messages) == 2 and mob.hp == 10**12 - damage_first,
           'each respects its cooldown without repeat spam')
        # Contract hired mid-cooldown acts straight away; earlier hires do not.
        owner.db.roles.append('berserker')
        await owner.mercenary_combat_turn_v1170(mob)
        ok(len(owner.messages) == 3 and 'Kord' in owner.messages[-1],
           'new hire does not inherit other hires cooldown')
        clock[0] += COOLDOWN
        await owner.mercenary_combat_turn_v1170(mob)
        ok(len(owner.messages) == 6, 'all three act independently after own cooldown')
        ok(owner.kills == 0, 'living mob remains in combat')
        # An instant finishing blow must stop other hires and settle credit once.
        clock[0] += COOLDOWN
        mob.hp = 1
        before = len(owner.messages)
        await owner.mercenary_combat_turn_v1170(mob)
        ok(not mob.alive and mob.hp == 0 and owner.kills == 1,
           'mercenary lethal blow grants one real kill')
        ok(len(owner.messages) == before + 1, 'other mercenaries stop after kill')
        await owner.mercenary_combat_turn_v1170(mob)
        ok(owner.kills == 1, 'no duplicate kill award')
    asyncio.run(run())
    return checks


if __name__ == '__main__':
    print('MERCENARY UNLIMITED v1.22.14:', validate_mercenary_unlimited_v12214(), 'checks PASS')
