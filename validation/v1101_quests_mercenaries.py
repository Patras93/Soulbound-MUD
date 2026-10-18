# -*- coding: utf-8 -*-
"""v11.00.1: 22 class guild offers, legend stage 2 and 22 real hireable roles.

Uses only an isolated SQLite database and genuine runtime quest definitions.
No production account, character, save or contract is altered.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from core.classes_skills import CLASSES
    from systems.equipment_crafting import (GUILD_CLASS_QUEST_POOLS,
        GUILD_CLASS_QUEST_AUDIT_V1120, guild_class_quest_pool_for_mastery_v11342)
    from systems.mercenary_taverns import MERCENARIES, mercenary_role
    from systems.mercenary_specialists_v1240 import SPECIALISTS, specialist_attack_v1240
    from systems.class_legend_paths_v800 import QUEST_IDS as EARLIER
    from systems.class_legend_paths_v900 import QUEST_IDS as LATER
    from storage.db_quests import DatabaseQuestMixin
    import storage.db_quests as quest_module
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from types import SimpleNamespace
    import ast
    from core.progression_resources import v0190_mob_stage

    count = 0
    def ck(expr, what):
        nonlocal count
        assert expr, 'v11.00.1: ' + what
        count += 1

    playable={row[0] for row in CLASSES}
    ck(len(playable)==22, '22 real playable classes')
    ck(set(GUILD_CLASS_QUEST_POOLS)==playable, 'guild offers for all 22')
    ck(GUILD_CLASS_QUEST_AUDIT_V1120['error_count']==0, 'complete guild quest audit')
    ck(len(MERCENARIES)==22, '22 hireable roles')
    ck({row['class'] for row in MERCENARIES.values()}==playable, 'all playable classes matched')
    ck(set(SPECIALISTS)==set(MERCENARIES), 'each mercenary has a real AI profile')
    from systems.companion_tactics_v4000 import FINISHERS, BREAKERS, GUARDIANS, tactical_response
    ck(not (FINISHERS & BREAKERS or FINISHERS & GUARDIANS or BREAKERS & GUARDIANS), 'no conflicting tactics')
    ck(set(SPECIALISTS)==set(FINISHERS|BREAKERS|GUARDIANS), 'all 22 roles have tactical category')
    for role in SPECIALISTS:
        ck(sum(role in group for group in (FINISHERS,BREAKERS,GUARDIANS))==1, 'exactly one tactic per hireable: '+role)
        ck(tactical_response(role, True, 100, 1000, 2)[0] >= 1.0, 'all tactics remain additive: '+role)
    ck(MERCENARIES['paladyn']['name']=='Seren', 'old Paladin remains Seren')
    ck(MERCENARIES['lucznik']['name']=='Riven', 'old Łowca contract remains Riven')
    for klass in playable:
        pool=GUILD_CLASS_QUEST_POOLS[klass]
        ck(len(pool)==5, 'five guild offers: '+klass)
        ck({entry[5] for entry in pool}=={'kill','boss','explore','gather','craft'},'all activities '+klass)
        ck(len(guild_class_quest_pool_for_mastery_v11342(klass,800))==5,'high mastery guild '+klass)
        role=mercenary_role(klass)
        ck(role in MERCENARIES and MERCENARIES[role]['class']==klass,'hire by class '+klass)
        spec=MERCENARIES[role]
        ck(mercenary_role(spec['name'])==role,'hire by NPC name '+klass)
        ck(bool(SPECIALISTS[role]) and len(SPECIALISTS[role])==5,'distinct class attacks '+klass)
        ck(float(spec['power'])>0 and spec['attack_type'] in ('magic','physical'),'valid attack '+klass)
    ck(mercenary_role('Łucznik')=='lucznik','historical hire alias')
    ck(mercenary_role('Kapłanka')=='kaplan','historical priest alias')

    # Actual current runtime quest objects, not a synthetic duplicate catalogue.
    quests=dict(EARLIER,**LATER)
    ck(len(quests)==22,'22 complete legend paths')
    ck(quest_module.QUESTS is runtime.QUESTS, 'SQLite quest handlers use active catalogue')
    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.execute('''CREATE TABLE quests (
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0, completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (account_id, quest_id))''')
            self.conn.execute('''CREATE TABLE quest_resource_progress_v0929 (
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL)''')
    db=DB()
    for index,(klass,ids) in enumerate(quests.items()):
        ck(len(ids)==120,'120 class legend stages '+klass)
        first,second=ids[0],ids[1]
        q=runtime.QUESTS[second]
        ck(q.get('requires_quest')==first,'second stage prereq '+klass)
        ck(q.get('v800_class_saga') and q.get('v800_stage')==2 and q.get('kind')=='kill','real second stage '+klass)
        account=100+index
        db.conn.execute("INSERT INTO quests VALUES(?,?,?,0,0,1)",(account,first,'completed'))
        db.start_quest(account,second)
        ck(not db.increment_class_legend_kill_v800(account,'Nieistniejąca',800,True,True),'foreign class no credit '+klass)
        minimum=int(q.get('v800_min_enemy_level',1))
        ck(not db.increment_class_legend_kill_v800(account,klass,max(0,minimum-1)) if minimum>0 else True,'too weak enemy no credit '+klass)
        events=db.increment_class_legend_kill_v800(account,klass,max(1,minimum),elite=False,boss=False)
        ck(events==[(second,1)],'stage 2 real kill awards exactly once '+klass)
        ck(db.quest(account,second)['progress']==1,'second stage persisted '+klass)
        class Player(SessionQuestProgressMixin):
            def __init__(self, acc):
                self.server=SimpleNamespace(db=db);self.account_id=acc
            def active_class_names(self):return [klass]
        npc=next((npc for npc in runtime.NPCS.values() if npc.get('v800_class_mentor') and npc.get('v800_required_class')==klass),None)
        ck(npc is not None, 'mentor for class '+klass)
        player=Player(account)
        ck(player.quest_ids_for_npc('mentor',npc)==[second],'mentor offers stage 2 '+klass)
        db.conn.execute('UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?',(int(q['needed']),account,second))
        ck(not db.increment_class_legend_kill_v800(account,klass,800,True,True),'completed progress never exceeds goal '+klass)
    # Regression: a real MobState lacks `level`, and the enemy catalog uses
    # generator_level/v019_stage rather than a non-existent `template["level"]`.
    # The former runtime hook treated all of these as level 1 and rejected
    # every stage 2 kill, although in-memory DB unit tests looked green.
    mob_source = (Path(__file__).resolve().parents[1] / 'world/world_state.py').read_text(encoding='utf8')
    mob_tree = ast.parse(mob_source)
    mob_defs = [node for node in mob_tree.body if isinstance(node, ast.ClassDef) and node.name == 'MobState']
    ck(len(mob_defs) == 1, 'real MobState declaration found')
    ck(not any(isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'level' for node in mob_defs[0].body), 'real MobState does not store a `level` field')
    ck(v0190_mob_stage({'generator_level': 3, 'max_hp': 100}) == 3,
       'actual generated monster stage three')
    ck(v0190_mob_stage({'generator_level': 2, 'max_hp': 100}) == 2,
       'actual monster stage two is below quest minimum')
    ck(v0190_mob_stage({'v019_stage': 9, 'generator_level': 3}) == 9,
       'canonical combat level honours final v019 stage')
    reward_tree = ast.parse((Path(__file__).resolve().parents[1] /
        'player/session_mixins/combat_rewards.py').read_text(encoding='utf8'))
    level_assignments = [node for node in ast.walk(reward_tree)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == '_v800_mob_level'
            for target in node.targets)]
    ck(len(level_assignments) == 1, 'exactly one live saga enemy-level hook')
    ck(isinstance(level_assignments[0].value, ast.Call) and
       isinstance(level_assignments[0].value.func, ast.Name) and
       level_assignments[0].value.func.id == 'v0190_mob_stage',
       'live combat hook uses canonical opponent level, not nonexistent MobState.level')
    # SQLite: both real stage-2 quests, ordinary rank, one eligible kill = one
    # step, below minimum = zero; credits are stored per account independently.
    for idx, class_name in enumerate(quests):
        qid = quests[class_name][1]
        required = runtime.QUESTS[qid]['v800_min_enemy_level']
        acc = 2001 + idx
        db.start_quest(acc, qid)
        ck(required == 3, 'stage two requires a level-three enemy: '+class_name)
        too_weak = v0190_mob_stage({'generator_level': required-1})
        eligible = v0190_mob_stage({'generator_level': required})
        ck(db.increment_class_legend_kill_v800(acc,class_name,too_weak) == [],
           'level-two kill is rejected: '+class_name)
        ck(db.increment_class_legend_kill_v800(acc,class_name,eligible) == [(qid,1)],
           'level-three kill gets credited: '+class_name)
        ck(db.increment_class_legend_kill_v800(acc,class_name,eligible) == [(qid,2)],
           'second genuine kill gets credited: '+class_name)
        ck(db.increment_class_legend_kill_v800(acc,class_name,eligible) == [(qid,3)],
           'third genuine kill finishes quest: '+class_name)
        ck(db.increment_class_legend_kill_v800(acc,class_name,eligible) == [],
           'extra kills do not overcredit: '+class_name)
        ck(db.quest(acc,qid)['progress']==3,'three of three persisted in SQLite: '+class_name)

    # Soul Weapon Tier 2 is a different quest from Legend stage 2. Exercise both.
    trial=runtime.QUESTS['soul_tier_02_trial']
    ck(trial['kind']=='kill' and trial.get('target') and int(trial['needed'])>=1,'Soul Tier 2 real kill target')
    db.start_quest(991,'soul_tier_02_trial')
    for progress in range(1, int(trial['needed'])+1):
        ck(db.increment_quest(991,trial['target'])==[('soul_tier_02_trial',progress)],'Soul Tier 2 real kill credit')
    ck(not db.increment_quest(991,trial['target']),'Tier 2 no duplicate after reaching quota')
    ck(db.quest(991,'soul_tier_02_trial')['progress']==int(trial['needed']),'Soul Tier 2 survives SQLite commit')
    ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    db.conn.close()
    source=(Path(__file__).resolve().parents[1]/'player/session_mixins/combat_rewards.py').read_text(encoding='utf8')
    ck('for _v800_class in _v800_active_classes:' in source, 'actual combat awards every active class')
    return count


if __name__=='__main__':
    print('QUESTY 22 KLAS I 22 NAJEMNIKOW:',run_regression(),'kontroli PASS')
