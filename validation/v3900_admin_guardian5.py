# -*- coding: utf-8 -*-
"""Soulbound v39 regression. No real player DB. Tests rewards, OLC rollback and owner gate."""
import asyncio
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from data.quests import QUESTS
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.live_quest_olc_v1209 import (parse_quest_edit,STAT_XP_FIELDS_V3900)
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.admin_guardian5_v3900 import (_quest_rewards,_quest_diag,_quest_compare,_boss_metadata)

async def checks():
    c=0
    original=copy.deepcopy(QUESTS['bandit_patrol'])
    f=Fake();live=f.server.live_content_v1204
    for section in ('quests','quest_edits','npcs','mob_edits'):
        live.draft.setdefault(section,{})
        live.active.setdefault(section,{})
    stranger=Fake(False,f.server.db)
    await stranger.admin_command('guardian5 status')
    assert 'tylko wlasciciel' in stranger.messages[-1];c+=1
    stranger_before=len(f.server.db.logged)
    async def command(value):
        await f.admin_command('guardian5 '+value)
        return f.messages[-1]
    assert 'GUARDIAN5' in await command('pomoc');c+=1
    assert 'v39' in await command('status');c+=1
    assert 'bandit_patrol' in await command('questy szukaj bandit_patrol');c+=1
    assert 'Patrol' in await command('questy szukaj Patrol');c+=1
    assert 'nagrody' in (await command('questy szukaj snkjuns')).lower() or 'Brak wyników' in f.messages[-1];c+=1
    assert 'QUEST NAGRODY' in await command('questy nagrody bandit_patrol');c+=1
    assert 'EXP indywidualne' in f.messages[-1];c+=1
    assert 'reward_stat_xp' in f.messages[-1] and 'reward_stat_strength' in f.messages[-1];c+=1
    assert 'QUEST DIAGNOZA' in await command('questy diagnoza bandit_patrol');c+=1
    assert 'QUEST POROWNAJ' in await command('questy porownaj bandit_patrol');c+=1
    assert 'Nieznany' in await command('questy nagrody id_nie_ma');c+=1
    assert 'GUARDIAN5' in await command('arena boss id_nie_ma');c+=1
    assert 'OLC GUARDIAN5' in await command('olc status');c+=1
    assert 'Nie ma takiej krainy' in await command('kraina audyt nieistnieje');c+=1
    assert len(f.server.db.logged)==stranger_before;c+=1
    for name,field in STAT_XP_FIELDS_V3900.items():
        alias='reward_stat_'+name
        assert parse_quest_edit(alias,'100000')==(field,100000);c+=1
        assert parse_quest_edit(field,'0')==(field,0);c+=1
        for invalid in ('-1','abc',str(10**16)):
            try:parse_quest_edit(alias,invalid)
            except ValueError:c+=1
            else:raise AssertionError('Accepted wrong stat reward')
    assert parse_quest_edit('reward_stat_xp','1000')==('olc_reward_stat_xp',1000);c+=1
    # Import code unchanged from older versions and exercise the real OLC atomic pipeline.
    with tempfile.TemporaryDirectory() as t:
        con=sqlite3.connect(str(Path(t)/'clone.db'))
        con.row_factory=sqlite3.Row
        con.execute('CREATE TABLE quests (account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,PRIMARY KEY(account_id,quest_id))')
        db=SimpleNamespace(conn=con)
        svc=LiveContentV1204(db)
        original_draft=copy.deepcopy(svc.draft)
        try:
            svc.stage_edit('quest','bandit_patrol','reward_stat_xp','100000');c+=1
            assert svc.draft['quest_edits']['bandit_patrol']['olc_reward_stat_xp']==100000;c+=1
            for i,(stat,field) in enumerate(STAT_XP_FIELDS_V3900.items()):
                svc.stage_edit('quest','bandit_patrol','reward_stat_'+stat,str(20000+i*10000));c+=1
                assert svc.draft['quest_edits']['bandit_patrol'][field]==20000+i*10000;c+=1
            assert QUESTS['bandit_patrol']==original;c+=1
            assert 'brak zmian' not in _quest_compare(svc,'bandit_patrol').lower();c+=1
            assert 'przygotowane' in describe_current_edit(svc,'quest','bandit_patrol','reward_stat_strength');c+=1
            old=copy.deepcopy(svc.draft)
            try:svc.stage_edit('quest','bandit_patrol','reward_stat_strength','-100')
            except ValueError as exc:
                assert str(exc), 'Invalid quest edit must explain the error'
            else:raise AssertionError('Invalid update was accepted')
            assert old==svc.draft;c+=1
            con.execute('INSERT INTO quests VALUES(1,?,?,?)',('bandit_patrol','active',5))
            con.commit()
            world=SimpleNamespace(mobs={},_last_refresh_at=1,_register_runtime_spawn=lambda *_:None)
            srv=SimpleNamespace(world=world,sessions=[])
            result=svc.apply(srv,'tester')
            assert 'rewizj' in result;c+=1
            assert QUESTS['bandit_patrol']['olc_reward_stat_xp']==100000;c+=1
            for i,field in enumerate(STAT_XP_FIELDS_V3900.values()):
                assert QUESTS['bandit_patrol'][field]==20000+i*10000;c+=1
            assert con.execute('SELECT progress FROM quests WHERE account_id=1').fetchone()[0]==5;c+=1
            assert 'wspolny' in _quest_rewards(svc,'bandit_patrol').lower();c+=1
            assert 'osobny' in _quest_rewards(svc,'bandit_patrol');c+=1
            assert 'ręczna' in describe_current_edit(svc,'quest','bandit_patrol','reward_stat_strength');c+=1
            # Reset one statistic, preserve global override and all others.
            svc.stage_edit('quest','bandit_patrol','reward_stat_strength','auto');c+=1
            svc.apply(srv,'tester');c+=1
            assert 'olc_reward_stat_strength' not in QUESTS['bandit_patrol'];c+=1
            assert QUESTS['bandit_patrol']['olc_reward_stat_xp']==100000;c+=1
            assert 'wspólny' in describe_current_edit(svc,'quest','bandit_patrol','reward_stat_strength');c+=1
            assert con.execute('SELECT progress FROM quests WHERE account_id=1').fetchone()[0]==5;c+=1
            # Reset common override, leave other individual overrides untouched.
            svc.stage_edit('quest','bandit_patrol','reward_stat_xp','auto');c+=1
            svc.apply(srv,'tester');c+=1
            assert 'olc_reward_stat_xp' not in QUESTS['bandit_patrol'];c+=1
            assert 'olc_reward_stat_dexterity' in QUESTS['bandit_patrol'];c+=1
            assert 'automatycznie' in describe_current_edit(svc,'quest','bandit_patrol','reward_stat_strength');c+=1
            # Revert individually, ensure native base returns and content in catalog survives.
            for stat in STAT_XP_FIELDS_V3900:
                svc.stage_edit('quest','bandit_patrol','reward_stat_'+stat,'auto');c+=1
            svc.apply(srv,'tester');c+=1
            assert QUESTS['bandit_patrol']==original;c+=1
            assert con.execute('SELECT progress FROM quests WHERE account_id=1').fetchone()[0]==5;c+=1
        finally:
            svc._remove(world if 'world' in locals() else None)
            con.close()
    assert QUESTS['bandit_patrol']==original;c+=1
    # Real reward handler used by quest turn-in, including zero and independent XP bank keys.
    import player.session_methods_v4200.dungeonprogression_part02 as reward_module
    import systems.experience_bank_v2011 as bank_module
    old_base=getattr(reward_module,'v0874_quest_stat_progress_base_grant',None)
    old_bank=bank_module.banked_experience_v2011
    rewards=[];bank_keys=[]
    reward_module.v0874_quest_stat_progress_base_grant=lambda char,name,base,rep:base
    bank_module.banked_experience_v2011=lambda db,acc,amount,typ,level,source_key=None: (bank_keys.append(source_key) or amount)
    class Character:
        STAT_PROGRESS_FIELDS={name:(name,name,name+'_progress') for name in STAT_XP_FIELDS_V3900}
        character_level=55
        def add_stat_progress(self,value,targets):
            rewards.append((targets[0],value))
            return []
    class Session:
        character=Character();server=SimpleNamespace(db=None);account_id=123;messages=[]
        def scale_progression_xp_v11342(self,base,*a,**kw):return base*3
        def apply_double_xp(self,amount):return amount*2
        async def send(self,msg):self.messages.append(msg)
    try:
        obj=Session()
        raw=dict(strength=100,dexterity=0,constitution=200,intelligence=300,willpower=400,charisma=500)
        output=await reward_module.grant_combat_quest_stat_xp(obj,raw,False,content_level=50,content_scaled=True)
        assert output==[600,0,1200,1800,2400,3000];c+=1
        assert len(rewards)==5 and 'dexterity' not in bank_keys;c+=1
        assert bank_keys==[key for key in raw if raw[key]];c+=1
        assert all(target!='dexterity' for target,_ in rewards);c+=1
        assert 'strength' in obj.messages[-1] and 'charisma' in obj.messages[-1];c+=1
        rewards.clear();bank_keys.clear()
        applied=await reward_module.grant_combat_quest_stat_xp(obj,100,False,content_level=50,content_scaled=True)
        assert applied==[600]*6 and len(bank_keys)==6;c+=1
        assert await reward_module.grant_combat_quest_stat_xp(obj,0,content_level=50,content_scaled=True)==[];c+=1
    finally:
        if old_base is None:delattr(reward_module,'v0874_quest_stat_progress_base_grant')
        else:reward_module.v0874_quest_stat_progress_base_grant=old_base
        bank_module.banked_experience_v2011=old_bank
    return c


def run():return asyncio.run(checks())
if __name__=='__main__':print('SOULBOUND GUARDIAN5 v39:',run(),'checks PASS')
