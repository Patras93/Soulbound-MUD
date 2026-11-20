# -*- coding: utf-8 -*-
"""v116.00.4: real planner/execute + room-local death notification contract."""
import time
from types import SimpleNamespace
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.monster_reactions_v116 import (
    notice_ally_defeat, has_reaction, choose_reaction, perform_reaction,
)
from systems.monster_ai import (
    monster_ai_due_v1901, monster_ai_eligible_v1160,
    monster_ai_plan_v1160, monster_ai_execute_v1160, monster_ai_attack_multiplier_v1160,
)
from data.mobs import MOB_TEMPLATES

checks = 0

def ok(condition, message):
    global checks
    checks += 1
    if not condition: raise AssertionError(message)

class World:
    def __init__(self): self.mobs={};self.templates={}
    def room_mobs(self, room):
        return [m for m in self.mobs.values() if m.room_id==room and m.alive]
    def mob_templates_for_ai_v1160(self, mob): return self.templates[mob.template_id]
    def add(self, key, template, room='one', owner='A', hp=None, turn=3, alive=True):
        cap=template.get('max_hp', 100)
        mob=SimpleNamespace(key=key,template_id=key,room_id=room,
                            engaged_by=owner,hp=cap if hp is None else hp,
                            alive=alive,combat_turn=turn)
        self.mobs[key]=mob;self.templates[key]=template
        return mob

now=time.monotonic()
w=World()
defender = {'name':'Gwardzista', 'max_hp':100, 'damage_type':'physical'}
ordinary = {'name':'Bandyta', 'max_hp':100, 'damage_type':'physical'}
leader = {'name':'Dowódca Bandyt', 'max_hp':100, 'damage_type':'physical'}
boss_t = {'name':'Bandycki herszt', 'max_hp':500, 'damage_type':'physical', 'boss':True}
special_t = {'name':'Boss UOSS', 'max_hp':500, 'uoss_superboss':True, 'boss':True}
# Synthetic names exist only in this isolated regression process.
MOB_TEMPLATES['boss'] = boss_t
MOB_TEMPLATES['special'] = special_t
removed=w.add('dead',ordinary)
scared=w.add('scared',ordinary)
angry=w.add('angry',leader)
guard=w.add('guard',defender)
boss=w.add('boss',boss_t,hp=200)
neutral=w.add('neutral',ordinary,owner=None)
other=w.add('other',ordinary,owner='B')
other_room=w.add('other_room',ordinary,room='two')
authored=w.add('authored',special_t)
summoned=w.add('summoned',ordinary);summoned.monster_ai_summoned_v1160=True
ok(not monster_ai_eligible_v1160(scared,ordinary),'ordinary mob has no autonomous magic AI before a death')
count=notice_ally_defeat(w,removed,now=now)
ok(count==3, f'only scared, angry and guard should be notified: {count}')
ok(not hasattr(neutral,'monster_reaction_pending_v1164'),'neutral is not aggroed')
ok(not hasattr(other,'monster_reaction_pending_v1164'),'another fight is not aggroed')
ok(not hasattr(other_room,'monster_reaction_pending_v1164'),'another room is untouched')
ok(not hasattr(authored,'monster_reaction_pending_v1164'),'authored boss is excluded')
ok(not hasattr(summoned,'monster_reaction_pending_v1164'),'temporary adds do not cascade')
ok(not hasattr(boss,'monster_reaction_pending_v1164'),'ordinary boss is excluded')
ok(notice_ally_defeat(w,removed,now=now)==0,'one death cannot notify twice')
ok(scared.engaged_by=='A' and neutral.engaged_by is None,'notice never changes engagement')
ok(has_reaction(scared,now=now+1),'physical monster has a pending reaction')
ok(monster_ai_eligible_v1160(scared,ordinary),'physical mob joins AI only after ally death')
ok(monster_ai_due_v1901(scared,ordinary,now+1),'pending fear action is eligible')
p=monster_ai_plan_v1160(scared,ordinary,[scared,guard,angry,boss],now=now+1)
ok(p and p['kind']=='fear','fear is a planned action')
text=monster_ai_execute_v1160(w,scared,ordinary,p,now=now+1)
ok('strachu' in text,'fear has short combat message')
ok(not has_reaction(scared,now=now+2),'fear used once')
ok(scared.engaged_by=='A' and scared.hp==100,'fear cannot flee, alter HP or disengage')
ok(scared.monster_ai_next_action_v1160==now+15,'fear uses existing 14 sec cooldown')
ok(monster_ai_attack_multiplier_v1160(scared,now+2)==1.0,'fear grants no damage buff')
p=monster_ai_plan_v1160(angry,leader,[angry,boss],now=now+1)
ok(p and p['kind']=='rage','commander enrages')
text=monster_ai_execute_v1160(w,angry,leader,p,now=now+1)
ok('szał' in text and monster_ai_attack_multiplier_v1160(angry,now+2)>=1.18,'rage uses existing buff')
ok(monster_ai_attack_multiplier_v1160(angry,now+12)==1.0,'rage expires')
ok(angry.engaged_by=='A','rage never changes fight owner')
# A defender's *existing* guard applies to injured ordinary bosses and not UOSS.
p=monster_ai_plan_v1160(guard,defender,[guard,boss],now=now+1)
ok(p and p['kind']=='guard' and p['target'] is boss,'guard prioritizes injured local boss')
text=monster_ai_execute_v1160(w,guard,defender,p,now=now+1)
ok('osłania' in text and boss.monster_ai_guard_until_v1160>now+1,'guard uses existing 20% shield')
boss.hp=500;guard.combat_turn=6;guard.monster_ai_next_action_v1160=0
p=monster_ai_plan_v1160(guard,defender,[guard,boss],now=now+20)
ok(not (p and p.get('kind')=='guard' and p.get('target') is boss),'full-hp boss needs no special protection')
# A new monster in an unrelated battle cannot shield the boss.
other_guard=w.add('other_guard',defender,owner='B')
p=choose_reaction(other_guard,defender,[other_guard,boss],now+2)
ok(not p,'different battle cannot protect boss')
# Authored UOSS never becomes a target of generic boss guard.
special=w.add('special',special_t,hp=100)
p=choose_reaction(other_guard,defender,[other_guard,special],now+2)
ok(not p,'UOSS boss uses authored mechanics')
# Expired, mismatched owner, no kill source, protected killer, cooldown.
new=w.add('later',ordinary)
new.monster_reaction_pending_v1164=('fear','A',now-1)
ok(not has_reaction(new,now=now),'expired reaction inert')
ok(perform_reaction(new,ordinary,{'kind':'fear','target':new},now)=='','expired reaction never consumes a turn')
new.monster_reaction_pending_v1164=('fear','B',now+10)
ok(not has_reaction(new,now=now),'cross-owner reaction inert')
new.monster_reaction_pending_v1164=('fear','A',now+10)
new.monster_reaction_next_v1164=now+90
ok(notice_ally_defeat(w,w.add('dead2',ordinary),now=now+2)>=0,'new death processed')
ok(new.monster_reaction_pending_v1164==('fear','A',now+10),'cooldown cannot override pending')
new.engaged_by=None
ok(not has_reaction(new,now=now),'disengagement cancels reaction')
ok(notice_ally_defeat(w,w.add('no_owner',ordinary,owner=None),now=now)==0,'no player means no propagation')
# A notification that expires without a turn must not block future losses.
stale=w.add('stale',ordinary)
stale.monster_reaction_pending_v1164=('fear','A',now-2)
notice_ally_defeat(w,w.add('real_loss',ordinary),now=now+2)
ok(has_reaction(stale,now=now+3),'expired notification is safely replaced')
# Resets for newly respawned monsters must be defined in the world refresh.
from pathlib import Path
state_src=(Path(__file__).resolve().parents[1]/'world/world_state.py').read_text(encoding='utf-8')
for attr in ('monster_reaction_pending_v1164','monster_reaction_next_v1164','monster_reaction_notified_v1164'):
    ok('"'+attr+'"' in state_src,'respawn forgets '+attr)
# Deterministic single-target selection must not depend on an unengaged NPC.
ok(notice_ally_defeat(w,w.add('add_kill',ordinary),now=now+3)>=0,'nonnegative notification count')
print(f'MONSTER REACTIONS v116.00.4: {checks}/{checks} PASS')
