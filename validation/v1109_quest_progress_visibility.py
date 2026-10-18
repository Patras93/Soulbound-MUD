# -*- coding: utf-8 -*-
"""v11.00.9: all 18 canonical quest kinds report progress under NVDA."""
from __future__ import annotations
import asyncio
import inspect
from collections import Counter
from types import SimpleNamespace

import server
from player.session_mixins.quest_progress import SessionQuestProgressMixin
from player.session_mixins.quest_turnin import SessionQuestTurninMixin
from player.session_mixins.quest_commands import SessionQuestCommandsMixin
from player.session_mixins.quest_npc import SessionQuestNpcMixin


class FakeDb:
    def __init__(self, rows):
        self.rows=rows
    def quest(self, aid, quest_id):
        return self.rows.get(quest_id)
    def quest_rows(self, aid):
        return [dict(row, quest_id=qid) for qid, row in self.rows.items()]
    def resource_set_progress_v0929(self, aid, qid, requirements):
        progress = int(self.rows[qid]['progress'])
        remaining = progress
        counts={}
        for key, qty in requirements.items():
            counts[key]=min(remaining,int(qty))
            remaining -= counts[key]
        return counts
    def distinct_category_items_v023(self, aid, qid):
        return ['demo_species'] * int(self.rows[qid]['progress'])


class Probe(SessionQuestProgressMixin, SessionQuestTurninMixin, SessionQuestCommandsMixin):
    def __init__(self, rows):
        self.rows=rows
        self.server=SimpleNamespace(db=FakeDb(rows))
        self.account_id=9
        self.messages=[]
        self.quest_list_context=None
    async def send(self, txt='', **kw):
        self.messages.append((str(txt), kw))
    def quest_progress_for_turnin(self, quest_id):
        row=self.rows[quest_id]
        quest=server.QUESTS[quest_id]
        return min(int(row['progress']),int(quest['needed'])), int(row['progress'])>=int(quest['needed'])
    def quest_crafted_item_have_v0333(self, item):
        return 999
    def resource_quest_have(self, item):
        return 999
    def quest_turnin_stock_status(self, qid):
        return None
    def normalize_description_query(self, value):
        return str(value or '').casefold().strip()


def run_regression():
    checks=0
    def ck(condition, why):
        nonlocal checks
        checks+=1
        if not condition:
            raise AssertionError('QUEST PROGRESS v11.00.9: '+why)
    quests=server.QUESTS
    ck(server.VERSION in ('11.00.9','11.00.10','11.00.11','11.00.12'), 'canonical release')
    counts=Counter(str(q.get('kind')) for q in quests.values())
    ck(len(counts)==18, f'18 canonical quest kinds: {counts}')
    from validation.v1100_release_counts import expected_quest_total_v1100
    ck(len(quests)==expected_quest_total_v1100(),'preserved quest catalogue plus authored teacher quests')
    # Validate ALL definitions have a meaningful, numeric denominator and id.
    for qid,q in quests.items():
        ck(int(q.get('needed',0))>=1 and bool(q.get('name')),
           f'{qid}: missing real progress denominator/name')
    representative={}
    for qid,q in quests.items():
        representative.setdefault(str(q['kind']),qid)
    for kind,qid in sorted(representative.items()):
        needed=int(quests[qid]['needed'])
        for progress in (0,1,needed):
            rows={qid:{'status':'active','progress':min(needed,progress)}}
            obj=Probe(rows)
            asyncio.run(obj.announce_active_quest_progress(qid))
            ck(bool(obj.messages),f'{kind}: no message at {progress}/{needed}')
            ck(all(message and kw.get('combat_detail')=='essential' and kw.get('history_category')=='quest'
                   for message,kw in obj.messages),f'{kind}: nonessential/uncategorized progress')
            ck(any(quests[qid]['name'] in message for message,kw in obj.messages),f'{kind}: missing quest name')
    # For all 22 classes test the actual saga announcer after *each* win at a
    # stage whose denominator is >= 6 (old interval throttling hid 1/6).
    class_quests={}
    for qid,q in quests.items():
        if q.get('v800_class_saga') and int(q['needed'])>=6:
            class_quests.setdefault(q['required_class'],qid)
    ck(len(class_quests)==22, f'all 22 active class saga chains: {len(class_quests)}')
    for klass,qid in class_quests.items():
        needed=int(quests[qid]['needed'])
        for progress in (1,2,3,needed):
            obj=Probe({qid:{'status':'active','progress':progress}})
            asyncio.run(obj.announce_active_quest_progress(qid))
            ck(len(obj.messages)==1 and f'Postęp {progress} z {needed}' in obj.messages[0][0],
               f'{klass}: every victory must be spoken: {progress}/{needed}')
            ck(obj.messages[0][1].get('combat_detail')=='essential',f'{klass}: essential')
    # Every canonical kind is visible in the active journal, even if it has
    # its own physical-stock readiness rule or unusual objective shape.
    rows={qid:{'status':'active','progress':1} for qid in representative.values()}
    obj=Probe(rows)
    asyncio.run(obj.show_active_quests())
    text='\n'.join(m for m,k in obj.messages)
    ck(text.count('Postęp ')==18,'active quest journal shows 18 distinct progress counters')
    for qid in representative.values():
        ck(quests[qid]['name'] in text,f'{qid}: missing on active quest list')
    for alias in ('postep','postęp','progress','status'):
        obj=Probe(rows)
        asyncio.run(obj.quests(alias))
        ck(any('AKTYWNE ZADANIA: 18.' in m for m,k in obj.messages),
           f'questy {alias} not routed to journal')
    # During actual progression, non-combat quests MUST call the essential
    # announcer, not self.send() with no combat priority.
    from player.session_mixins import museum_bounty, exploration_professions, profesje6
    for meth,source in (
        ('world exploration',inspect.getsource(museum_bounty.SessionMuseumBountyMixin.advance_v0140_quest_progress)),
        ('new profession',inspect.getsource(exploration_professions.SessionExplorationProfessionsV1100Mixin.v1100_profession_quest_progress)),
        ('eight profession works',inspect.getsource(profesje6.SessionProfesje6Mixin.profesje6_command))
    ):
        ck('await self.announce_active_quest_progress(' in source,
           meth+' must use canonical progress announcer')
    # Collection, hourly combat loot, profession resources and crafting now
    # announce progress through the one essential, stock-aware reporter.
    for label, source in (
        ('normal item collection', inspect.getsource(museum_bounty.SessionMuseumBountyMixin.announce_item_collect_quest_progress)),
        ('hourly item collection', inspect.getsource(museum_bounty.SessionMuseumBountyMixin.grant_hourly_quest_kill_drop_v0929)),
        ('resource collection', inspect.getsource(SessionQuestProgressMixin.announce_resource_quest_progress)),
        ('crafting', inspect.getsource(SessionQuestProgressMixin.announce_craft_quest_progress)),
    ):
        ck('await self.announce_active_quest_progress(' in source,
           label+' must not use hidden normal combat messages')
    # The master NPC displays both completed stages and live progress.
    code=inspect.getsource(SessionQuestNpcMixin.show_specialist_quest_progression)
    ck(code.count('await self.announce_active_quest_progress(active_stage)')==2,
       'master NPCs show active step for both saga paths')
    print(f'POSTEP QUESTOW v11.00.9: {checks} checks PASS; kinds={len(counts)} quests={len(quests)} saga_classes={len(class_quests)}')
    return checks

if __name__=='__main__':
    run_regression()
