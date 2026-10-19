# -*- coding: utf-8 -*-
"""v11.00.12: real teacher quests, NVDA help, crate supply and durable SQLite."""
import asyncio
import tempfile
from pathlib import Path
from types import SimpleNamespace


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.class_legend_paths_v900 import (
        NEW_CLASSES, TEACHER_NAMES, TEACHER_TRIALS, TEACHER_QUEST_IDS,
    )
    from core.bootstrap_economy_professions import VERSION
    from storage.database import Database
    from core.classes_skills import RACES, CLASSES
    from world.legends_v3200 import _reachable
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from player.session_mixins.quest_offers import SessionQuestOffersMixin
    from player.session_mixins.help_system import SessionHelpSystemMixin
    from validation.v1111_skill_help_dispatch import _Probe as _HelpProbe
    from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES
    from storage.db_shared import normalize_lookup_text
    checks = 0
    def ck(value, label):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError('V1112 NAUCZYCIELE: ' + label)

    ck(VERSION == runtime.VERSION and VERSION in ('11.00.12', '11.00.13', '11.00.14', '11.00.15', '11.00.16','11.00.17','11.00.18'), 'version')
    ck(len(runtime.QUESTS) == 6769, 'old 6745 quests + exactly 24 teacher quests')
    ck(len(TEACHER_QUEST_IDS) == 24 and TEACHER_QUEST_IDS <= set(runtime.QUESTS), 'all teacher quests in world')
    ck(len(TEACHER_NAMES) == len(TEACHER_TRIALS) == 8, 'eight independent teachers')
    ck(len(set(TEACHER_NAMES.values())) == 8, 'eight unique personal names')
    reachable = _reachable(runtime.ROOMS)
    existing_rooms = [npc['room'] for npc in runtime.NPCS.values()]
    for row in NEW_CLASSES:
        klass,_,_,_,slug,*_ = row
        npc_id=f'teacher_v900_{slug}'
        npc=runtime.NPCS[npc_id]
        ck(npc['name']==TEACHER_NAMES[klass] and npc['teacher_class']==klass, 'named real teacher '+klass)
        ck(npc['room'] in reachable and existing_rooms.count(npc['room']) == 1, 'reachable solo classroom '+klass)
        ck(npc.get('v1112_teacher_quests') is True, 'teacher quest flag '+klass)
        ids=tuple(npc['quest_chain'])
        ck(ids==tuple(f'v1112_teacher_{slug}_{i:02d}' for i in (1,2,3)), 'ordered teacher quests '+klass)
        for i, qid in enumerate(ids):
            q=runtime.QUESTS[qid]
            ck(q['giver']==npc['name'] and q['required_class']==klass, 'giver and class '+qid)
            ck(q['required_npc_id']==npc_id and q['repeatable'] is False, 'local turn-in and no farm '+qid)
            ck(q.get('requires_quest') == (ids[i-1] if i else None), 'strict sequence '+qid)
            ck(q['kind']==('kill','collect','kill')[i] and q['needed']==(5,3,8)[i], 'stage mechanics '+qid)
            ck(q['reward_silver']>0 and q['reward_gold']==0 and q['reward_mithril']==0, 'reward '+qid)
            ck(str(i+1)+'/3' in q['description'] and q['name'].startswith(klass+': '), 'NVDA readable '+qid)
            if i==1:ck(q['target'] in runtime.ITEMS,'existing collectible '+qid)
            else:ck(q['target'] in ('bandit','goblin','skeleton','shadow_wolf'),'real target '+qid)
        # `help mag`, `help paladyn` should directly resolve to class description.
        alias=normalize_lookup_text(klass)
        key=HELP_TOPIC_ALIASES.get(alias)
        ck(bool(key and key in HELP_TOPICS and 'Nauczyciel: '+npc['name'] in '\n'.join(HELP_TOPICS[key])), 'class help '+klass)
        helper=_HelpProbe()
        asyncio.run(helper.show_help(klass))
        ck(any(npc['name'] in t for t in helper.sent) and not helper.lookups,
           'direct help <class> describes teacher, never skill usage '+klass)
    ck('nauczyciele klas' in HELP_TOPICS,'teacher quest help topic')
    # Normal mission list dispatch + class lock; real SQLite client account.
    class _QuestProbe(SessionQuestProgressMixin,SessionQuestOffersMixin):
        def __init__(self,db,aid,klass,room):
            self.server=SimpleNamespace(db=db)
            self.account_id=aid
            self.character=SimpleNamespace(room_id=room)
            self.klass=klass
            self.sent=[]
            self.quest_list_context=None
        def active_class_names(self):return (self.klass,)
        async def send(self,text,*args,**kwargs):self.sent.append(str(text))
        def quest_completed(self,qid):
            row=self.server.db.quest(self.account_id,qid)
            return bool(row and row['status']=='completed')
    with tempfile.TemporaryDirectory(prefix='sb1112_teacher_') as temp:
        path=Path(temp)/'teacher.db';db=Database(str(path))
        master=db.create_account('NauczycieleQuest112','PasswordSafe_v1112_123456')
        inflect={key:'Wędrowiec' for key in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'UczenJedenaDwanascie',RACES[0],next(r for r in CLASSES if r[0]=='Paladyn'),inflect)
        other,_=db.create_character_for_master(master,'MagJedenaDwanascie',RACES[0],next(r for r in CLASSES if r[0]=='Mag'),inflect)
        npc=runtime.NPCS['teacher_v900_paladyn']; ids=npc['quest_chain']
        probe=_QuestProbe(db,aid,'Paladyn',npc['room'])
        ck(probe.quest_ids_for_npc('teacher_v900_paladyn',npc)==[ids[0]],'only first visible before accepting')
        asyncio.run(probe.show_npc_quest_offers('teacher_v900_paladyn',npc))
        ck(any('LISTA ZADAŃ' in t and npc['name'] in t for t in probe.sent), 'quest list NPC displayed')
        ck(probe.quest_list_context['quest_ids']==[ids[0]],'przyjmij 1 context for first quest')
        blocked=_QuestProbe(db,other,'Mag',npc['room'])
        ck(not blocked.quest_ids_for_npc('teacher_v900_paladyn',npc),'wrong class cannot obtain quest')
        ck(not probe.quest_lock_reasons(ids[0]),'available by class at teacher')
        ck(any('wymaga aktywnej klasy' in t for t in blocked.quest_lock_reasons(ids[0])),'wrong class cannot accept')
        db.start_quest(aid,ids[0])
        changes=db.increment_quest(aid,runtime.QUESTS[ids[0]]['target'])
        ck(changes and changes[0][0]==ids[0] and db.quest(aid,ids[0])['progress']==1,'real kill event recorded')
        db.conn.close();db=Database(str(path));probe.server.db=db
        ck(db.quest(aid,ids[0])['progress']==1 and db.quest(other,ids[0]) is None,'SQLite restart preserves one character only')
        for _ in range(4):db.increment_quest(aid,runtime.QUESTS[ids[0]]['target'])
        ck(db.quest(aid,ids[0])['progress']==5,'kill cap exact')
        db.complete_quest(aid,ids[0])
        ck(probe.quest_ids_for_npc('teacher_v900_paladyn',npc)==[ids[1]],'after first only collect offered')
        db.start_quest(aid,ids[1])
        item=runtime.QUESTS[ids[1]]['target']
        changes=db.increment_item_collect_quest(aid,item,3)
        ck(changes and changes[0][1]==3,'genuine collect event counted')
        db.complete_quest(aid,ids[1])
        ck(probe.quest_ids_for_npc('teacher_v900_paladyn',npc)==[ids[2]],'final teacher trial unlocked')
        db.start_quest(aid,ids[2]); db.increment_quest(aid,runtime.QUESTS[ids[2]]['target'])
        ck(db.quest(aid,ids[2])['progress']==1,'final real combat progression')
        db.complete_quest(aid,ids[2])
        ck(not probe.quest_ids_for_npc('teacher_v900_paladyn',npc),'completed school stops offering quests')
        ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        db.conn.close()
    # Chest chances are improved; quest contract and boss guaranteed loot retained.
    regular=runtime.MOB_TEMPLATES['mountain_troll']['drops']['stolen_mountain_ore']
    rare=runtime.MOB_TEMPLATES['albino_troll']['drops']['stolen_mountain_ore']
    king=runtime.MOB_TEMPLATES['troll_king']['drops']['stolen_mountain_ore']
    ck((regular,rare,king)==(.55,.70,1.0),'increased chest loot rates')
    ck(runtime.QUESTS['stolen_mountain_ores']['needed']==10 and runtime.QUESTS['stolen_mountain_ores']['target']=='stolen_mountain_ore','unchanged Borin quest')
    print(f'NAUCZYCIELE 8 / QUESTY 24 / HELP KLAS / SKRZYNIE v11.00.12: {checks} checks PASS')
    return checks

if __name__=='__main__':run_regression()
