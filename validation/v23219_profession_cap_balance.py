# -*- coding: utf-8 -*-
"""v2.32.19: real profession/action/sale XP integration and progression pacing.

Uses in-memory SQLite; never touches live player accounts or stored experience.
"""
import sqlite3
from types import SimpleNamespace

from core.progression_resources import v0190_requirement
from core.profession_timing import profession_action_seconds
from config.balance import profession_xp_requirement_v1401, tool_xp_requirement_v1402, PROFESSION_XP_REQUIREMENT_MULTIPLIERS
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
import server as _runtime_ready_v23219  # authored catalog imports need ordered bootstrap
from player.session_mixins.profession_storage import SessionProfessionStorageMixin
from player.session_mixins.sales import SessionSalesMixin


class DummyDB(DatabaseExperienceBankV2011Mixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT INTO accounts VALUES(1)')
        self.conn.commit()
        self.create_experience_bank_schema_v2011()
        self.professions = {name: {'level':400,'xp':0,'actions':0} for name in ('Górnictwo', 'Wędkarstwo')}
        self.tools = {'mining':{'level':400,'xp':0,'uses':0}, 'fishing':{'level':400,'xp':0,'uses':0}}
    def multi_cap_v23215(self, account):
        return 5000
    def profession(self, account, name):
        return self.professions[name]
    def tool(self, account, name):
        return self.tools[name]
    def save_profession(self, account, name, level, xp, actions):
        self.professions[name] = {'level':level, 'xp':xp, 'actions':actions}
    def save_tool(self, account, name, level, xp, uses):
        self.tools[name] = {'level':level, 'xp':xp, 'uses':uses}
    def save_character(self, character):
        pass
    def increment_profession_action_quests_v0700(self, *args):
        return []


class Tester(SessionProfessionStorageMixin, SessionSalesMixin):
    def __init__(self):
        self.account_id = 1
        self.server = SimpleNamespace(db=DummyDB())
        self.character = SimpleNamespace()
    def guild_bonus_percent_v0926(self): return 0
    def mentor_bonus_percent_v03050(self): return 0
    def v0260_profession_xp_bonus_percent(self, *args): return 0
    def apply_double_xp(self, xp): return xp
    def session_summary_add(self, *args): pass
    def add_character_xp_with_event(self, *args, **kwargs): return []


def run_regression():
    checks=0
    tester=Tester()
    messages,_,_=tester.grant_profession_progress(
        'Górnictwo', 10_000_000, 'mining', 10_000_000, content_level=400)
    earned=tester._last_profession_progress_gain_v11343
    assert earned['profession_xp']==5000 and earned['tool_xp']==5000,earned
    assert tester.server.db.professions['Górnictwo']['xp']==5000
    assert tester.server.db.tools['mining']['xp']==5000
    assert any('+5000 XP' in x for x in messages),messages
    bank={(kind,key):value for kind,key,value in tester.server.db.experience_bank_rows_v2011(1)}
    assert bank[('profession','Górnictwo')]>0 and bank[('tool','mining')]>0
    checks+=5
    # A single very large batch sale does not multiply the Multi Cap per item.
    sale_messages=tester.grant_profession_sale_xp('net', 1_000_000, content_level=400)
    assert tester.server.db.professions['Wędkarstwo']['xp']==5000
    assert any('sprzedaż +5000 XP' in x for x in sale_messages)
    bank2={(kind,key):value for kind,key,value in tester.server.db.experience_bank_rows_v2011(1)}
    assert bank2[('profession','Wędkarstwo')]>0
    assert bank2[('profession','Górnictwo')]==bank[('profession','Górnictwo')]
    checks+=4
    # Bank release cannot turn a 1-XP source into a massive reward.
    db=tester.server.db
    assert db.allocate_experience_bank_v2011(1,500_000,'skill','fire',5000)==5000
    before=dict(((kind,key),value) for kind,key,value in db.experience_bank_rows_v2011(1))[('skill','fire')]
    assert db.allocate_experience_bank_v2011(1,1,'skill','fire',5000)==2
    after=dict(((kind,key),value) for kind,key,value in db.experience_bank_rows_v2011(1))[('skill','fire')]
    assert after==before-1
    checks+=3
    # Requirement-only balancing: all materials still pay their authored XP.
    # Most time-critical professions at high levels must not level in minutes.
    from core.bootstrap_economy_professions import PROFESSION_XP_GAIN_MULTIPLIER
    assert PROFESSION_XP_GAIN_MULTIPLIER==4
    checks+=1
    for lv in (1,10,20,30,49,50,75,100,150,200,300,400,500,600,700,799):
        for kind,name in [('herbalism','Zielarstwo'),('fishing','Wędkarstwo'),('mining','Górnictwo'),('crafting','Kowalstwo')]:
            req=profession_xp_requirement_v1401(v0190_requirement('profession',lv),name,lv)
            assert req>0
            original=max(1,int(round(v0190_requirement('profession',lv)*PROFESSION_XP_REQUIREMENT_MULTIPLIERS[name])))
            if lv<50:
                assert req==original, (name,lv,req,original)
            elif lv>=50:
                assert req>original, (name,lv,req,original)
            if lv>=100:
                assert req>=profession_xp_requirement_v1401(v0190_requirement('profession',50),name,50)
            checks+=2
    tester.server.db.conn.close()
    return checks

if __name__=='__main__':
    print('BALANS PROFESJI MULTI CAP v2.32.19:',run_regression(),'checks PASS')
