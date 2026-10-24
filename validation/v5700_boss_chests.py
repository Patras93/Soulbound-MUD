# -*- coding: utf-8 -*-
"""v57: real post-roll boss chest payout, no item/RNG/SQLite mutations."""
import asyncio
import random
from pathlib import Path
from systems.endless_chests_v5700 import (
    chest_extension_v5700, extend_boss_chest_reward_v5700,
    preview_chest_extension_v5700, _SAFE_REWARD_GOLD,
)
from validation.v3600_admin_guardian2 import Fake

async def suite():
    n=0
    def ok(cond,why=''):
        nonlocal n
        assert cond,why
        n+=1
    owner=Fake();guest=Fake(False,owner.server.db)
    rng=random.getstate()
    root=Path(__file__).resolve().parents[1]
    before_draft=repr(owner.server.live_content_v1204.draft)
    before_tables=list(owner.server.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    # Genuine high-end supported floor types.
    for kind,floor in (('crypt',901),('mythic_crypt',901),('magitek',150)):
        meta=chest_extension_v5700(kind,floor)
        ok(meta is not None,(kind,floor))
        ok(meta['stage']>800,(kind,meta))
        ok(meta['numerator']>100)
        original={'gold':1000,'items':['soul_shard','healing_potion'],'unique':'do_not_touch'}
        converted=extend_boss_chest_reward_v5700(kind,floor,original)
        ok(converted['gold']>original['gold'])
        ok(converted['gold']==1000*meta['numerator']//100)
        ok(converted['items'] is original['items'])
        ok(converted['unique']==original['unique'])
        ok(original['gold']==1000)
        ok(converted is not original)
        ok(extend_boss_chest_reward_v5700(kind,floor,converted)['gold']>=converted['gold'])
    # No changed historical early floors, other finite chests or authored UOSS.
    for kind,floor in (('crypt',100),('mythic_crypt',100),('magitek',50),
                       ('giant',99999),('astral',99999),('mythic_astral',99999),
                       ('uoss',99999),('',900)):
        original={'gold':123,'items':['soul_shard']}
        ok(chest_extension_v5700(kind,floor) is None,(kind,floor))
        ok(extend_boss_chest_reward_v5700(kind,floor,original) is original)
    # Stable inputs, overflow guards, no extra RNG consumption.
    for bad in (0,-1,None,True,'abc',1000001,'1.4',object()):
        ok(chest_extension_v5700('crypt',bad) is None,str(bad))
    ok(extend_boss_chest_reward_v5700('crypt',901,{'gold':-1,'items':[]})['gold']==-1)
    ok(extend_boss_chest_reward_v5700('crypt',901,{'gold':'NaN'})['gold']=='NaN')
    ok(extend_boss_chest_reward_v5700('crypt',901,None) is None)
    huge=extend_boss_chest_reward_v5700('crypt',999999,{'gold':10**14,'items':[]})
    ok(huge['gold']<=_SAFE_REWARD_GOLD)
    ok(huge['gold']>=10**14)
    report=preview_chest_extension_v5700('krypta',901,1000)
    ok('etap 910' in report)
    ok('bonus +' in report)
    ok('Tylko podglad' in report)
    ok('Brak premii' in preview_chest_extension_v5700('krypta',700,1000))
    for bad in (('bad',901,1000),('krypta',0,1000),('krypta','abc',1000),
                ('krypta',901,'abc'),('krypta',901,-1),('krypta',1000001,10)):
        try:preview_chest_extension_v5700(*bad)
        except ValueError:ok(True)
        else:ok(False,'bad accepted '+str(bad))
    # Owner-only routing through the actual `admin live` dispatcher.
    async def cmd(line,who=owner):
        await who.admin_command('live '+line)
        return who.messages[-1]
    ok('POMOC 12' in await cmd('pomoc 12'))
    ok('etap 910' in await cmd('skrzynie krypta 901 1000'))
    ok('etap ' in await cmd('skrzynie mityczna_krypta 901 1000'))
    ok('etap ' in await cmd('skrzynie magitek 150 1000'))
    ok('POMOC 12' in await cmd('skrzynie pomoc'))
    ok('ADMIN LIVE SKRZYNIA:' in await cmd('skrzynie nieznane 901 1000'))
    ok('ADMIN LIVE SKRZYNIA:' in await cmd('skrzynie abc'))
    ok('Nieznana komenda' in await cmd('skrzynie krypta 901 1000',guest))
    ok('Nieznana komenda' in await cmd('pomoc 12',guest))
    ok(random.getstate()==rng,'RNG used by helper/preview')
    ok(repr(owner.server.live_content_v1204.draft)==before_draft,'quest DRAFT mutated')
    ok(list(owner.server.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))==before_tables,'SQLite modified')
    # Gameplay integration exactly after authored roll, before assignment in per-member loop.
    source=(root/'player/session_mixins/admin_tools.py').read_text('utf8')
    segment=source[source.index('            rewarded = []'):source.index('            if len(rewarded) > 1:',source.index('            rewarded = []'))]
    ok('reward = boss_chest_reward_roll(kind, floor, power)' in segment)
    ok('reward = extend_boss_chest_reward_v5700(kind, floor, reward)' in segment)
    ok(segment.index('reward = boss_chest_reward_roll')<segment.index('reward = extend_boss_chest_reward_v5700')<segment.index('member.character.gold +='))
    ok(segment.count('reward = boss_chest_reward_roll')==1)
    ok('self.server.db.add_item(member.account_id, item_id, 1)' in segment)
    ok('self.server.db.add_collection_entry(' in segment)
    ok('for member in recipients:' in segment)
    ok('consumed_member_key' in segment)
    ok('boss_floor_chest_state_id(kind, floor)' in segment)
    return n

def run():
    count=asyncio.run(suite());print(f'V57 BOSS CHESTS: {count} PASS');return count
if __name__=='__main__':run()
