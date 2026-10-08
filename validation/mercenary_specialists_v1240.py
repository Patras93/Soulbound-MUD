# -*- coding: utf-8 -*-
"""Mercenaries 4.0 checks: per-role skills, AI reactions, no new limits."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from systems.mercenary_taverns import MERCENARIES, COOLDOWN, mercenary_owner_full_power_v12213, mercenary_owner_real_action_power_v1231
from systems.mercenary_growth_v1220 import mercenary_attack_multiplier, mercenary_owner_level_v1228, mercenary_tactic
from systems.mercenary_specialists_v1240 import (SPECIALISTS, specialist_attack_v1240,
    specialist_description_v1240, specialist_support_on_strike_v1240)


def validate_mercenary_specialists_v1240():
    checks = 0
    def ok(condition, reason):
        nonlocal checks
        assert condition, 'Najemnicy 4.0: ' + reason
        checks += 1

    ok(set(MERCENARIES) == set(SPECIALISTS) and len(SPECIALISTS) == 15, 'all 15 native roles')
    for role, profile in SPECIALISTS.items():
        ok(len(profile) == 5 and len(set(profile[2:])) == 3, f'3 distinct techniques: {role}')
        ok(MERCENARIES[role]['ability'] == profile[2], f'keeps class default skill: {role}')
        ok(profile[0] in specialist_description_v1240(role), 'readable specialization')
    mob = SimpleNamespace(hp=500_000, max_hp=500_000)
    factor, skill, combo = specialist_attack_v1240(mob, 101, 'mag', 'magic', 100, 1000.0)
    ok(factor > 1 and 'Kula' in skill and not combo, 'first strike normal')
    factor2, skill2, combo2 = specialist_attack_v1240(mob, 101, 'wojownik', 'physical', 100, 1000.1)
    ok(combo2.startswith('Reakcja') and factor2 > factor and 'Roz' in skill2,
       'real alternating physical/magic chain and reactive move')
    factor3, _, combo3 = specialist_attack_v1240(mob, 101, 'berserker', 'physical', 100, 1000.2)
    ok('wspólny nacisk' in combo3, 'same-channel comrades combine')
    _, _, solo_combo = specialist_attack_v1240(mob, 202, 'lotrzyk', 'physical', 100, 1000.3)
    ok(not solo_combo, 'separate owners do not share combo notes')
    _, _, after_expire = specialist_attack_v1240(mob, 101, 'mag', 'magic', 100, 1020.)
    ok(not after_expire, 'stale combos expire during a break in combat')
    mob.hp = 100_000
    factor4, finishing, _ = specialist_attack_v1240(mob, 101, 'lotrzyk', 'physical', 100, 1020.1)
    ok(finishing == 'Ostatni Sztych' and factor4 > 1, 'finisher when remaining HP is below 35%')
    fake = SimpleNamespace(hp=500_000)
    _, boss_skill, _ = specialist_attack_v1240(fake, 101, 'mag', 'magic', 100, 1050., boss=True)
    ok(boss_skill == 'Arkaniczny Przełom', 'boss targeting changes technique')
    low = SimpleNamespace(character=SimpleNamespace(name='Towarzysz'), current_hp=500, skill_guard=0,
                          max_hp=lambda: 1000)
    ok(specialist_support_on_strike_v1240('kaplan', low, 100000, True, True) == '' and low.current_hp == 500,
       'UOSS healing block enforced')
    msg = specialist_support_on_strike_v1240('kaplan', low, 100000, True, False)
    ok('Regeneracja' in msg and low.current_hp == 540, 'passive heal does not consume attack')
    msg = specialist_support_on_strike_v1240('straznik', low, 100000, True, False)
    ok('Awaryjna osłona' in msg and low.skill_guard > 0, 'tank reacts to wounded ally')
    ok(not specialist_support_on_strike_v1240('straznik', low, 100000, True, False), 'no guard spam')
    mob = SimpleNamespace(hp=10**15, max_hp=10**15)
    early = specialist_attack_v1240(mob, 202, 'mag', 'magic', 10, 3000.)[0]
    late = specialist_attack_v1240(mob, 202, 'mag', 'magic', 10000, 3020.)[0]
    ok(late > early, 'no level ceiling in additional class training')

    src = Path(__file__).resolve().parents[1] / 'player/session_mixins/mercenary_taverns.py'
    tree = ast.parse(src.read_text(encoding='utf8'))
    fn = next(n for cls in tree.body if isinstance(cls, ast.ClassDef)
              for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'mercenary_combat_turn_v1170')
    ns = dict(time=SimpleNamespace(time=lambda: 5000.0), COOLDOWN=COOLDOWN, MERCENARIES=MERCENARIES,
              mercenary_owner_full_power_v12213=mercenary_owner_full_power_v12213,
              mercenary_owner_real_action_power_v1231=mercenary_owner_real_action_power_v1231,
              mercenary_attack_multiplier=mercenary_attack_multiplier,
              mercenary_owner_level_v1228=mercenary_owner_level_v1228, mercenary_tactic=mercenary_tactic,
              MOB_TEMPLATES={'raid_boss':{'boss':True,'name':'Wielki boss','max_hp':10**16}},
              superboss_healing_blocked_v11179=lambda p: False,
              v0314_adjust_damage_vs_template=lambda template, dmg, typ, role:(dmg, ''))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(src),'exec'),ns)
    class Owner:
        mercenary_combat_turn_v1170 = ns['mercenary_combat_turn_v1170']
        def __init__(self):
            self.character = SimpleNamespace(name='Bohater', room_id='room', character_level=1000)
            self.current_hp = 1_000_000
            self.skill_guard = 1
            self.account_id = 1
            self.messages = []
            self.kills = 0
            self.server = SimpleNamespace(db=SimpleNamespace(
                mercenary_contracts=lambda aid, now:[{'role':r,'expires_at':0} for r in ('mag','wojownik','berserker')],
                mercenary_progress_v1220=lambda aid, role:{'specialization':'automatyczna'}),
                party_sessions=lambda *a,**k:[self], party_combat_broadcast=self.broadcast)
        def max_hp(self):return 1_000_000
        def physical_power(self):return 100_000
        def spell_power(self):return 1_000
        async def apply_boss_defense(self,mob,raw):return raw
        async def broadcast(self,*a,**k):pass
        async def send_combat(self,message,detail='essential'):self.messages.append(message)
        async def mob_defeated(self,mob):
            self.kills += 1
            mob.alive = False
    async def combat():
        player = Owner()
        mob = SimpleNamespace(template_id='raid_boss', room_id='room', hp=10**16, alive=True)
        await player.mercenary_combat_turn_v1170(mob)
        ok(len(player.messages) == 3, 'all 3 mercenaries attack independently')
        ok(any('Reakcja:' in msg for msg in player.messages), 'real combo appears in combat')
        ok(all('obrażeń' in msg for msg in player.messages), 'combat outputs damage and not only buffs')
        ok(10**16-mob.hp >= 3*100_000, 'no class specialization damage downgrade')
        ok(player.kills == 0, 'no premature kill')
        await player.mercenary_combat_turn_v1170(mob)
        ok(len(player.messages) == 3, 'no extra action inside own cooldown')
    asyncio.run(combat())
    # Player-facing read-only specialization browser, no hire or training needed.
    from systems.mercenary_taverns import mercenary_role
    handler = next(n for cls in tree.body if isinstance(cls, ast.ClassDef)
                   for n in cls.body if isinstance(n, ast.AsyncFunctionDef)
                   and n.name == 'handle_mercenaries_v1170')
    cmd_ns = dict(mercenary_role=mercenary_role, MERCENARIES=MERCENARIES)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[handler], type_ignores=[])),
                 str(src), 'exec'), cmd_ns)
    class Browser:
        handle_mercenaries_v1170 = cmd_ns['handle_mercenaries_v1170']
        def __init__(self):
            self.character = SimpleNamespace(name='Podgląd')
            self.lines = []
        async def send(self, line): self.lines.append(line)
    async def browse():
        user = Browser()
        await user.handle_mercenaries_v1170('specjalizacje')
        ok(len(user.lines) == 16, '15 specialization records + auto-control note')
        for spec in MERCENARIES.values():
            ok(any(spec['name'] in line for line in user.lines),
               'all 15 specialists listed to screen reader')
        user.lines.clear()
        await user.handle_mercenaries_v1170('specjalizacje Vael')
        ok(len(user.lines) == 2 and 'Tkacz Żywiołów' in user.lines[0],
           'read-only details of individual hire before contracting')
    asyncio.run(browse())
    return checks


if __name__ == '__main__':
    print('MERCENARY SPECIALISTS v1.24.0:', validate_mercenary_specialists_v1240(), 'checks PASS')
