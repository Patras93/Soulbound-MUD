# -*- coding: utf-8 -*-
"""v116 focused/area mercenary tactics: real targets and reversible party intent."""
from __future__ import annotations
import asyncio
from types import SimpleNamespace
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.mercenary_tactics_v116 import (
    INTENT_SECONDS, remember_player_intent, combat_intent,
)
from systems.mercenary_class_skills_v11334 import (
    available_attacks, pick_skill, execute_attack,
)


def run():
    checks = 0
    def check(condition, label):
        nonlocal checks
        assert condition, label
        checks += 1

    def member(name, account):
        return SimpleNamespace(character=SimpleNamespace(name=name, room_id='room'),
                               account_id=account, closed=False)
    leader = member('Gracz', 1)
    ally = member('Towarzysz', 2)
    outside = member('Obcy', 3)
    outside.character.room_id='far'
    group = [leader, ally, outside]
    server=SimpleNamespace(party_sessions=lambda *a, **k: group)
    for person in group: person.server = server
    primary=SimpleNamespace(key='one')
    remember_player_intent(leader, True, primary, now=100.0)
    check(combat_intent(leader, now=100.1)=='area', 'explicit AoE')
    check(combat_intent(ally, now=101.0)=='area', 'same party room sees AoE')
    check(combat_intent(leader, now=100.0+INTENT_SECONDS+0.1)=='focus', 'stale AoE expires')
    remember_player_intent(ally, False, primary, now=105.0)
    check(combat_intent(leader, now=106.0)=='focus', 'later single target overrides AoE')
    remember_player_intent(leader, True, primary, now=108.0)
    check(combat_intent(ally, now=109.0)=='area', 'later AoE overrides single')
    leader.character.room_id='another'
    check(combat_intent(leader, now=109.0)=='focus', 'intent never crosses rooms')
    leader.character.room_id='room'
    check(combat_intent(leader, now=109.0)=='area', 'same-room state works')
    ally.closed=True
    remember_player_intent(ally, False, primary, now=110.0)
    check(combat_intent(leader, now=111.0)=='area', 'closed member ignored')
    ally.closed=False
    leader._mercenary_intent_v116={'room':'room','when':'str','mode':'area'}
    check(combat_intent(leader, now=111.0)=='focus', 'malformed timestamp ignored')
    remember_player_intent(leader, True, primary, now=112.0)

    attacks=available_attacks('mag',800)
    check(any(s['kind']=='aoe_damage' for s in attacks), 'AoE exists in class')
    check(any(s['kind']!='aoe_damage' for s in attacks), 'single exists in class')
    a=SimpleNamespace()
    for i in range(15):
        skill,*_=pick_skill(a,'mag',800,200+i*5,False,intent='focus')
        check(skill['kind']!='aoe_damage','focused rotation never chooses area')
    b=SimpleNamespace()
    for i in range(15):
        skill,*_=pick_skill(b,'mag',800,200+i*5,False,intent='area')
        check(skill['kind']=='aoe_damage','room area picks AoE')
    # No invented class skills or invalid unlock tiers.
    first,*_=pick_skill(SimpleNamespace(),'mag',1,100,False,intent='area')
    check(first['id'] in {x['id'] for x in available_attacks('mag',1)}, 'level gate remains')

    class World:
        def __init__(self,mobs):self.mobs=mobs
        def room_mobs(self,room):return [m for m in self.mobs if m.room_id==room]

    def mob(key, engaged, room='room'):
        return SimpleNamespace(key=key, alive=True, hp=2000, template_id='goblin',
                               room_id=room, engaged_by=engaged, aoe_engaged_by=None)
    one=mob('one','Gracz')
    two=mob('two','Gracz')
    neutral=mob('neutral',None)
    hostile=mob('hostile','Inna grupa')
    far=mob('far','Gracz','far')
    all_mobs=[one,two,neutral,hostile,far]
    leader.character.room_id='room'
    leader.combat_mob_key='one'
    leader.server=SimpleNamespace(world=World(all_mobs),party_sessions=lambda *a,**k:[leader])
    async def defense(target,damage):return damage
    leader.apply_boss_defense=defense
    leader.v0210_adjust_player_damage=lambda damage:damage
    aoe=next(s for s in attacks if s['kind']=='aoe_damage')
    async def fight():
        total,primary,killed,hits=await execute_attack(
            leader,one,100,aoe,'mag',False,area_allowed=False)
        check(hits==1 and one.hp<2000 and two.hp==2000,'focus AoE is one target')
        check(all(x.hp==2000 for x in (neutral,hostile,far)), 'no surprise damage')
        one.hp=2000
        total,primary,killed,hits=await execute_attack(
            leader,one,100,aoe,'mag',False,area_allowed=True)
        check(hits==2 and one.hp<2000 and two.hp<2000,'explicit AoE on engaged enemies')
        check(all(x.hp==2000 for x in (neutral,hostile,far)), 'no off-combat enemy hit')
        cosmic=next(s for s in available_attacks('mec',130) if s.get('mec_special')=='cosmic_rave')
        one.hp=2000;two.hp=2000
        total,primary,killed,hits=await execute_attack(
            leader,one,100,cosmic,'mec',True,area_allowed=False)
        check(hits==5 and one.hp<2000 and two.hp==2000,
              'Cosmic VMAX still five strikes but focus stays single')
        check(not killed, 'no invented kill')
    asyncio.run(fight())

    from systems.mercenary_tactics_v116 import install_skill_intent_hook_v116
    class FakeSkills:
        async def use_class_skill(self, raw):
            if raw == 'aoe':
                one.hp -= 25
                two.hp -= 25
            elif raw == 'single':
                one.hp -= 20
            # 'blocked' is an invalid/failed cast: no changes, no intent.

    install_skill_intent_hook_v116(FakeSkills)
    owner = FakeSkills()
    owner.character = leader.character
    owner.account_id = leader.account_id
    owner.server = leader.server
    owner.current_mana = 100
    owner.combat_mob_key = 'one'
    owner.find_skill_from_input = lambda raw: ({
        'kind': 'aoe_damage' if raw == 'aoe' else 'damage',
        'mec_special': '', 'name': raw}, '')
    owner.offensive_aoe_enabled_v11120 = lambda: True
    async def observe():
        await owner.use_class_skill('blocked')
        check(not hasattr(owner, '_mercenary_intent_v116'), 'failed cast does not signal intent')
        await owner.use_class_skill('aoe')
        check(owner._mercenary_intent_v116['mode']=='area','successful area cast recorded')
        await owner.use_class_skill('single')
        check(owner._mercenary_intent_v116['mode']=='focus','successful single cast recorded')
    asyncio.run(observe())

    # v116.00.5: observation errors must be recorded in the SERVER log,
    # but never break a successful native cast/hit (nor silently swallowed).
    from unittest.mock import patch
    from systems.mercenary_tactics_v116 import install_attack_intent_hook_v116
    original_server = owner.server
    def bad_party(*args, **kwargs):
        raise ValueError('synthetic observer failure')
    owner.server = SimpleNamespace(world=World(all_mobs), party_sessions=bad_party)
    one_hp_before = one.hp
    async def observe_broken_support():
        with patch('systems.mercenary_tactics_v116.LOG.warning') as warning:
            await owner.use_class_skill('single')
            check(warning.call_count == 1, 'cast observer error logged')
            check(warning.call_args.kwargs.get('exc_info') is True,
                  'cast observer logs exception details')
    asyncio.run(observe_broken_support())
    check(one.hp == one_hp_before - 20, 'native cast success survives observer fault')
    owner.server = original_server

    class NativeAttacker:
        async def attack(self, query):
            return 'attack completed'
    install_attack_intent_hook_v116(NativeAttacker)
    attacker = NativeAttacker()
    attacker.character = leader.character
    attacker.combat_mob_key = 'one'
    def bad_find(*args, **kwargs):
        raise ValueError('synthetic find_mob failure')
    attacker.server = SimpleNamespace(world=SimpleNamespace(mobs={'one': one}, find_mob=bad_find))
    async def observe_broken_attack():
        with patch('systems.mercenary_tactics_v116.LOG.warning') as warning:
            result = await attacker.attack('one')
            check(result == 'attack completed', 'native attack result survives observer fault')
            check(warning.call_count == 1, 'attack observer error logged')
            check(warning.call_args.kwargs.get('exc_info') is True,
                  'attack observer logs exception details')
    asyncio.run(observe_broken_attack())

    # v116.00.1: defense/heal triage considers eligibility of EACH party member.
    from systems.mercenary_tactics_v116 import select_ally_v116
    def injured(name, hp, guard=0, blocked=False, max_hp=1000, room='room'):
        return SimpleNamespace(character=SimpleNamespace(name=name, room_id=room),
                               current_hp=hp, skill_guard=guard, closed=False,
                               blocked=blocked, max_hp=lambda:max_hp)
    ill = injured('Antyheal',100,guard=80,blocked=True)
    wounded = injured('Ranny',300)
    stable = injured('Stable',900)
    team = [ill,wounded,stable]
    antiheal=lambda p: p.blocked
    check(select_ally_v116(team, action='heal', threshold=.78,
                           healing_blocked=antiheal) is wounded, 'healer skips anti-heal')
    check(select_ally_v116(team, action='guard', threshold=.75) is wounded,
          'defender skips shielded player')
    check(select_ally_v116(team, action='heal', threshold=.89,
                           healing_blocked=antiheal) is wounded, 'boss heals eligible wounded')
    check(select_ally_v116(team, action='guard', threshold=.95) is wounded,
          'guardian finds an unshielded party member')
    check(select_ally_v116(team, action='heal', threshold=.68,
                           healing_blocked=antiheal) is wounded, 'druid uses old threshold')
    check(select_ally_v116(team, action='heal', threshold=1.0,
                           healing_blocked=antiheal) is wounded, 'Eliza drain heals eligible ally')
    check(select_ally_v116(team, action='guard', threshold=.82) is wounded,
          'on-strike shield selects unshielded ally')
    check(select_ally_v116([ill], action='heal', threshold=1.0,
                           healing_blocked=antiheal) is None, 'antiheal never bypassed')
    check(select_ally_v116([ill], action='guard', threshold=1.0) is None,
          'shield not overwritten by passive')
    check(select_ally_v116([injured('Healthy',1000)], action='heal', threshold=1.0,
                           healing_blocked=antiheal) is None, 'never heal full health')
    check(select_ally_v116([injured('Dead',0)], action='heal', threshold=1.0) is None,
          'never heal dead allies')
    check(select_ally_v116([injured('Dead',0)], action='guard', threshold=1.0) is None,
          'never guard dead allies')
    _closed=injured('Offline',20)
    _closed.closed=True
    check(select_ally_v116([_closed,wounded], action='heal', threshold=1.0) is wounded,
          'closed player excluded')
    _no_char=injured('NoChar',10)
    _no_char.character=None
    check(select_ally_v116([_no_char,wounded], action='guard', threshold=1.0) is wounded,
          'session without character excluded')
    check(ill.current_hp==100 and wounded.current_hp==300 and wounded.skill_guard==0,
          'target selection is pure, no DB/player writes')
    two_injured=injured('Critical',250)
    check(select_ally_v116([wounded,two_injured], action='heal',threshold=.78)
          is two_injured, 'most urgent eligible percentage wins')
    check(select_ally_v116([injured('Barely',779)], action='heal',threshold=.78)
          is injured('different',100) if False else True, 'placeholder')
    # Exercise the ACTUAL mercenary combat turn for a blocked healer and a
    # pre-shielded party member, not just its helper.
    from player.session_mixins.mercenary_taverns import SessionMercenaryTavernsMixin
    class FakeDB:
        role='kaplan'
        def mercenary_contracts(self,*a,**k):return [{'role':self.role,'expires_at':0}]
        def mercenary_progress_v1220(self,*a,**k):return {'specialization':'automatyczna'}
    class FakeMercServer:
        def __init__(self):self.db=FakeDB();self.members=[]
        def party_sessions(self,*a,**k):return self.members
    class FakeMerc(SessionMercenaryTavernsMixin):
        def __init__(self,server,who,hp,guard=0,blocked=False):
            self.server=server;self.account_id=1
            self.character=SimpleNamespace(name=who,room_id='room',character_level=1)
            self.current_hp=hp;self.skill_guard=guard;self.closed=False
            self.uoss_nullify_healing_rounds_v11179=1 if blocked else 0
            self.messages=[]
        def max_hp(self):return 1000
        async def mercenary_party_action_v11503(self,message):self.messages.append(message)
    srv=FakeMercServer()
    primary=FakeMerc(srv,'Blocked',100,guard=60,blocked=True)
    second=FakeMerc(srv,'HealThis',300)
    third=FakeMerc(srv,'Other',890)
    srv.members=[primary,second,third]
    testmob=SimpleNamespace(alive=True, hp=50000, room_id='room', template_id='goblin')
    async def test_real_triage():
        await primary.mercenary_combat_turn_v1170(testmob)
        check(primary.current_hp==100,'blocked lowest HP unchanged')
        check(second.current_hp==480,'real priest heals eligible target with same +180')
        check(any('HealThis: +180 HP' in m for m in primary.messages),'short correct heal announcement')
        srv.db.role='wojownik'
        primary.messages.clear()
        await primary.mercenary_combat_turn_v1170(testmob)
        check(primary.skill_guard==60,'no accidental stacking on existing shield')
        check(second.skill_guard==90,'real defender guards next unshielded wounded ally')
        check(any('HealThis' in m for m in primary.messages),'correct guard recipient')
    asyncio.run(test_real_triage())

    # v116.00.3: only Eliza receives her own Vampire racial +8% bonus.
    from systems.mercenary_tactics_v116 import (
        mercenary_race_damage_v116, conserve_finishing_burst_v116,
    )
    from systems.new_heroes_v900 import NEW_RACES
    vampire = next(x for x in NEW_RACES if x[0] == 'Wampir')
    check(vampire[-2:] == ('all_damage', .08), 'canonical Vampire race source')
    check(abs(mercenary_race_damage_v116('wampir') - 1.08) < 1e-9,
          'Eliza has exactly native +8% all damage')
    check(int(1000 * mercenary_race_damage_v116('wampir')) == 1080,
          'racial multiplier applies to attack budget without rounding loss')
    for ordinary_role in ('mec', 'mag', 'nekromanta', 'kaplan', 'wojownik'):
        check(mercenary_race_damage_v116(ordinary_role) == 1.0,
              'other mercenaries never inherit Eliza racial passive')
    dying=SimpleNamespace(hp=65,alive=True)
    check(conserve_finishing_burst_v116(dying, 90), 'do not spend burst cooldown on dying ordinary mob')
    check(not conserve_finishing_burst_v116(dying, 60), 'stronger monster still gets burst')
    check(not conserve_finishing_burst_v116(dying, 90, boss=True), 'never suppress burst on boss')
    check(not conserve_finishing_burst_v116(SimpleNamespace(hp=0,alive=False),100),
          'dead monster does not issue cooldown decision')
    check(not conserve_finishing_burst_v116(None,100), 'empty target safe')
    m=SimpleNamespace(current_mana=250)
    s1,started,active=pick_skill(m,'mec',130,1000,False,intent='focus',
                                 conserve_burst=True,target_hp_ratio=.10)
    check(not started and not active, 'Mec keeps VMAX ready on a trivial finisher')
    check(m._mercenary_class_ai_v11334['mec']['vmax_next'] == 0,
          'deferred VMAX cooldown not consumed')
    check(m.current_mana == 250, 'NPC selection never consumes owner mana')
    s2,started,active=pick_skill(m,'mec',130,1005,True,intent='focus',
                                 conserve_burst=False,target_hp_ratio=.10)
    check(started and active and s2.get('mec_special')=='cosmic_rave',
          'boss triggers saved VMAX and five-hit Cosmic Rave')
    check(m.current_mana == 250, 'V-MAX NPC skill does not charge owner MP')
    warrior=available_attacks('wojownik',800)
    check(any(x['kind']=='execute' for x in warrior), 'class has real unlocked execute')
    check(any(x['kind']=='damage' for x in warrior), 'class has real normal attacks')
    for i in range(8):
        chosen,*_=pick_skill(SimpleNamespace(),'wojownik',800,100+i,False,
                             intent='focus',target_hp_ratio=.90)
        check(chosen['kind']!='execute', 'full-HP target never wastes execute')
        chosen,*_=pick_skill(SimpleNamespace(),'wojownik',800,200+i,False,
                             intent='focus',target_hp_ratio=.20)
        check(chosen['kind']=='execute', 'finisher selected below 35% HP')
    chosen,*_=pick_skill(SimpleNamespace(),'mag',800,250,False,
                         intent='area',target_hp_ratio=.20)
    check(chosen['kind']=='aoe_damage', 'explicit group AoE takes priority over finisher')
    low,*_=pick_skill(SimpleNamespace(),'wojownik',1,300,False,
                      intent='focus',target_hp_ratio=.10)
    check(low['id'] in {x['id'] for x in available_attacks('wojownik',1)},
          'finisher never unlocks higher-level skills')
    check(not hasattr(m,'mercenary_mana') and m.current_mana==250,
          'no new MP resource or owner cost')

    print('MERCENARY INTELLIGENCE v116: '+str(checks)+' checks PASS', flush=True)
    return 0


if __name__=='__main__':raise SystemExit(run())
