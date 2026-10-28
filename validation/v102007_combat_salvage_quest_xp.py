# -*- coding: utf-8 -*-
"""v102.00.7: real Haldor quest IDs, OLC persistence and reward payout gates."""
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

from systems.quest_combat_salvage_v102007 import (
    is_combat_salvage_quest, class_xp_at_turnin, soul_xp_at_turnin,
)
from systems.live_quest_olc_v1209 import validate_quest_edit
from systems.content_registry import QUESTS

# The actual quest registrations live in two different parts of the engine.
import world.dynamic_content  # noqa: F401
import network.protocol_gameplay_utils  # noqa: F401

_TARGET_QUESTS = {
    'haldor_steel_recycling': ('Zlecenie Haldora: Stal do Przetopu', 'salvaged_steel_plate', 4),
    'haldor_broken_blades_v0929': ('Złamane ostrza', 'damaged_weapon_v0929', 6),
    'haldor_armor_recycling_v0929': ('Pancerz do przetopu', 'heavy_armor_fragment_v0929', 6),
}


def run():
    count = 0
    def ok(result, msg):
        nonlocal count
        assert result, msg
        count += 1

    original = {qid: copy.deepcopy(QUESTS[qid]) for qid in _TARGET_QUESTS}
    for qid, (title, target, needed) in _TARGET_QUESTS.items():
        q = original[qid]
        ok(q['name'] == title and q['kind'] == 'collect', 'real quest name/kind: '+qid)
        ok(q['target'] == target and q['needed'] == needed, 'real quest objective: '+qid)
        ok(is_combat_salvage_quest(q,qid), 'real-ID match: '+qid)
        ok(class_xp_at_turnin(q,1234,qid) == 0, 'no implicit class XP: '+qid)
        ok(soul_xp_at_turnin(q,5678,qid) == 0, 'no implicit soul XP: '+qid)
        edited = validate_quest_edit(qid,q,{'olc_reward_class_xp':1200,'olc_reward_soul_xp':600}, {}, {}, {}, {}, {})
        ok(class_xp_at_turnin(edited,1234,qid)==1200, 'Mastery payout: '+qid)
        ok(soul_xp_at_turnin(edited,5678,qid)==600, 'Soul payout: '+qid)
        for field in ('kind','target','needed','reward_silver','reward_gold','reward_mithril','repeatable','repeat_cooldown'):
            ok(edited.get(field)==q.get(field), 'preserved '+field+': '+qid)
        ok(class_xp_at_turnin({**edited,'olc_reward_class_xp':0},1234,qid)==0,'manual zero Mastery: '+qid)
        ok(soul_xp_at_turnin({**edited,'olc_reward_soul_xp':0},5678,qid)==0,'manual zero Soul: '+qid)

    # An arbitrary newly authored quest that copies a title is not privileged.
    fake={'name':'Pancerz do przetopu','kind':'collect','target':'other','reward_profession_xp':30}
    ok(not is_combat_salvage_quest(fake,'live_fake'), 'display-name spoof is not a listed ID')
    try:
        validate_quest_edit('live_fake',fake,{'olc_reward_class_xp':25}, {}, {}, {}, {}, {})
    except ValueError as exc:
        ok('EXP biegłości' in str(exc),'ordinary collection denied')
    else:
        raise AssertionError('ordinary collect cannot pay Class EXP')
    ok(soul_xp_at_turnin({**fake, 'olc_reward_soul_xp':500},100,'live_fake') == 0,
       'ordinary profession remains Soul XP zero')
    ok(not is_combat_salvage_quest({'kind':'craft_set'},'haldor_steel_recycling'),
       'changing objective kind does not bypass guard')
    ok(class_xp_at_turnin({'kind':'kill','olc_reward_class_xp':500},100,'bandit_patrol')==500,
       'ordinary kill quest remains unchanged')
    ok(soul_xp_at_turnin({'kind':'collect'},300,'nonprof_quest')==300,
       'ordinary nonprofession quest remains unchanged')

    # Real persisted, atomic admin-live path. Uses isolated in-memory SQLite only.
    from systems.live_content_v1204 import LiveContentV1204
    with tempfile.TemporaryDirectory(prefix='sb-haldor-') as tempdir:
        conn = sqlite3.connect(str(Path(tempdir)/'test.db'))
        conn.row_factory = sqlite3.Row
        conn.execute('CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,PRIMARY KEY(account_id,quest_id))')
        for index,qid in enumerate(_TARGET_QUESTS,1):
            conn.execute('INSERT INTO quests VALUES(?,?,?,?)',(index,qid,'active',index))
        conn.commit()
        db = SimpleNamespace(conn=conn)
        world = SimpleNamespace(mobs={}, _last_refresh_at=1., _register_runtime_spawn=lambda *a: None)
        server = SimpleNamespace(world=world,sessions=[])
        service = LiveContentV1204(db)
        try:
            for qid in _TARGET_QUESTS:
                service.stage_edit('quest',qid,'xp_bieglosci','7000')
                service.stage_edit('quest',qid,'xp_duszy','9000')
                ok(QUESTS[qid] == original[qid],'draft does not edit quest: '+qid)
            outcome = service.apply(server,'test-admin')
            ok('rewizję 1' in outcome, 'one atomic publish')
            for qid in _TARGET_QUESTS:
                current=QUESTS[qid]
                ok(class_xp_at_turnin(current,111,qid)==7000,'published mastery: '+qid)
                ok(soul_xp_at_turnin(current,222,qid)==9000,'published soul: '+qid)
                for field in ('target','needed','reward_gold','reward_silver','repeat_cooldown'):
                    ok(current.get(field)==original[qid].get(field),'published preserves '+field+': '+qid)
            ok([x[0] for x in conn.execute('SELECT progress FROM quests ORDER BY account_id')] == [1,2,3],
               'active-player quest progress preserved')
            service._remove(world)
            service=LiveContentV1204(db)
            for qid in _TARGET_QUESTS:
                ok(class_xp_at_turnin(QUESTS[qid],0,qid)==7000, 'reload mastery: '+qid)
                ok(soul_xp_at_turnin(QUESTS[qid],0,qid)==9000, 'reload soul: '+qid)
        finally:
            service._remove(world)
            conn.close()
        for qid in _TARGET_QUESTS:
            ok(QUESTS[qid]==original[qid], 'no catalog residue: '+qid)

    source=Path(__file__).resolve().parents[1]
    for filename, needle in (
        # v102.00.12: both UI and payout use the same effective quest plan;
        # the plan must call the exact Haldor-aware gates, not bypass them.
        ('player/session_mixins/quest_commands.py','reward_plan = quest_xp_plan(quest_id, q)'),
        ('player/session_mixins/quest_offers.py','reward_plan = quest_xp_plan(quest_id, quest)'),
        ('systems/quest_reward_floor_v1020012.py','original_class = class_xp_at_turnin('),
        ('systems/quest_reward_floor_v1020012.py','original_soul = soul_xp_at_turnin('),
        ('player/session_mixins/admin_tools.py','auto_soul = soul_xp_at_turnin('),
    ):
        ok(needle in (source/filename).read_text('utf-8'), 'actual runtime integration: '+filename)
    return count

if __name__=='__main__':
    print(f'COMBAT SALVAGE v102.00.7: {run()} checks PASS', flush=True)
