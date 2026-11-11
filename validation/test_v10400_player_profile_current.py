# -*- coding: utf-8 -*-
"""v104 profile shows live data or last stored values and current Admin Live caps."""
import asyncio
import ast
import time
from pathlib import Path
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.profile_live_v10400 import current_profile_values, current_cap_label

class ProfileHelperTests(unittest.TestCase):
    def test_offline_never_changes_saved_row(self):
        stored={'name':'Ala','character_level':801,'character_xp':77,'active_title':'Zwiadowca'}
        value=current_profile_values(stored)
        self.assertEqual(value,stored)
        self.assertIsNot(value,stored)

    def test_online_uses_current_progression_not_stale_sqlite(self):
        stored={'name':'Ala','character_level':800,'character_xp':17,'soul_level':450,
                'soul_tier':45,'strength':60,'room_id':'old','active_title':'Stary tytuł'}
        live=SimpleNamespace(name='Ala',character_level=5678,character_xp=10**60,
                             soul_level=8765,soul_tier=876,strength=1000,
                             room_id='new',active_title='Nowy tytuł')
        result=current_profile_values(stored,live)
        self.assertEqual(result['character_level'],5678)
        self.assertEqual(result['character_xp'],10**60)
        self.assertEqual(result['soul_tier'],876)
        self.assertEqual(result['strength'],1000)
        self.assertEqual(result['room_id'],'new')
        self.assertEqual(result['active_title'],'Nowy tytuł')
        self.assertEqual(stored['character_level'],800)

    def test_live_does_not_overwrite_missing_fields_with_none(self):
        stored={'name':'Ala','deaths':12}
        value=current_profile_values(stored,SimpleNamespace(deaths=None))
        self.assertEqual(value['deaths'],12)

    def test_current_admin_cap_and_unlimited(self):
        with patch('systems.profile_live_v10400.cap',side_effect=lambda k: None if k=='postac' else 10000):
            self.assertEqual(current_cap_label('postac'),'bez limitu')
            self.assertEqual(current_cap_label('dusza'),'10000')


def profile_command_test_class():
    """Execute the actual profile methods without running world import-time audits."""
    source = Path(__file__).parents[1] / 'player/session_mixins/social_expansion.py'
    node = ast.parse(source.read_text(encoding='utf-8'))
    mixin = next(n for n in node.body if isinstance(n,ast.ClassDef) and n.name=='SessionSocialExpansionMixin')
    methods = [n for n in mixin.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ('whois_v03051','_profile_time_v0363')]
    test_class = ast.ClassDef(name='TestProfile', bases=[],keywords=[],body=methods,decorator_list=[])
    code=compile(ast.fix_missing_locations(ast.Module(body=[test_class],type_ignores=[])),str(source),'exec')
    namespace={
        'time':time, 'current_profile_values':current_profile_values,
        'current_cap_label':current_cap_label, 'soul_tier_title_for_class':lambda tier,name:'Testowy Tytuł Duszy',
        'SOUL_MAX_TIER':1000, 'MOB_TEMPLATES':{}, 'ROOMS':{'temple':{'name':'Świątynia'}},
        'backfill_combat_profile_records_v11341':lambda *a,**k:None,
        'combat_profile_row_v11341':lambda *a,**k:None,
        'player_item_display_name_v0335':lambda iid:str(iid),
    }
    exec(code,namespace)
    cls=namespace['TestProfile']
    cls.__test_globals__=namespace
    return cls

class ProfileCommandIntegration(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        commands=[
            "CREATE TABLE characters(account_id INTEGER, name TEXT, race TEXT, class_name TEXT, active_title TEXT, character_level INTEGER, character_xp INTEGER, soul_weapon TEXT, soul_level INTEGER, soul_tier INTEGER, soul_weapon_mastery_level INTEGER, strength INTEGER, dexterity INTEGER, constitution INTEGER, intelligence INTEGER, willpower INTEGER, charisma INTEGER, deaths INTEGER, room_id TEXT)",
            "CREATE TABLE player_clan_members(account_id INTEGER,clan_id INTEGER,rank TEXT)",
            "CREATE TABLE player_clans(id INTEGER,name TEXT,level INTEGER)",
            "CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER,xp INTEGER,active_slot INTEGER)",
            "CREATE TABLE professions(account_id INTEGER,profession TEXT,level INTEGER,xp INTEGER)",
            "CREATE TABLE tools(account_id INTEGER,tool_type TEXT,level INTEGER,xp INTEGER)",
            "CREATE TABLE world_tier_settings_v021(account_id INTEGER,tier INTEGER)",
            "CREATE TABLE ascension_progress_v021(account_id INTEGER,track TEXT,rank INTEGER)",
            "CREATE TABLE achievements(account_id INTEGER)",
            "CREATE TABLE unlocked_titles(account_id INTEGER)",
            "CREATE TABLE quests(account_id INTEGER,status TEXT)",
            "CREATE TABLE bestiary_stats(account_id INTEGER,kills INTEGER)",
            "CREATE TABLE boss_floor_clears(account_id INTEGER,floor INTEGER)",
            "CREATE TABLE mine_progress(account_id INTEGER,max_floor_unlocked INTEGER)",
            "CREATE TABLE endless_gauntlet_progress_v021(account_id INTEGER,best_round INTEGER)",
            "CREATE TABLE player_records_v03051(account_id INTEGER, record_key TEXT,value INTEGER,text_value TEXT)",
            "CREATE TABLE fish_journal(account_id INTEGER,best_weight_g INTEGER)",
            "CREATE TABLE player_profile_privacy_v03051(account_id INTEGER,inspect_enabled INTEGER)",
            "CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT)",
        ]
        for cmd in commands:self.conn.execute(cmd)
        self.conn.execute('INSERT INTO characters VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (1,'Ala','Człowiek','Mag','Stary tytuł',800,7,'Laska',400,40,400,4,5,6,7,8,9,2,'temple'))
        self.conn.execute('INSERT INTO class_progress VALUES (1,\'Mag\',800,10,1)')
        self.conn.commit()

    def tearDown(self):self.conn.close()

    def _session(self,online=True):
        TestSession = profile_command_test_class()
        live=SimpleNamespace(account_id=1,closed=False,character=SimpleNamespace(
            name='Ala',race='Człowiek',class_name='Mag',active_title='Aktualny tytuł',
            character_level=4321,character_xp=10**50,soul_level=9000,soul_tier=900,
            soul_weapon='Laska',soul_weapon_mastery_level=9000,
            strength=5555,dexterity=5,constitution=6,intelligence=7,willpower=8,charisma=9,
            room_id='temple',deaths=3)) if online else None
        db=SimpleNamespace(conn=self.conn,player_presence_v0363=lambda aid:None)
        server=SimpleNamespace(db=db,find_character_session=lambda name:live)
        sess=TestSession()
        sess.server=server
        self._profile_globals=TestSession.__test_globals__
        sess.account_id=1
        sess.send=lambda msg: sess.messages.append(str(msg)) or asyncio.sleep(0)
        sess.messages=[]
        sess._social_target_id_v03051=lambda name:1
        return sess

    def test_profile_online_uses_live_progress_and_cap(self):
        s=self._session(True)
        with patch.dict(self._profile_globals, {'current_cap_label':lambda k:'bez limitu' if k=='postac' else '10000'}):
            asyncio.run(s.whois_v03051('Ala'))
        data='\n'.join(s.messages)
        self.assertIn('bieżący stan sesji',data)
        self.assertIn('Level postaci: 4321/bez limitu',data)
        self.assertIn('Soul Level 9000/10000',data)
        self.assertIn('Aktualny tytuł',data)
        self.assertIn('Siła 5555',data)
        self.assertNotIn('Level postaci: 800/800',data)
        self.assertIn('Profil nie ujawnia loginu',data)
        self.assertEqual(self.conn.execute('SELECT character_level FROM characters').fetchone()[0],800)

    def test_profile_offline_uses_saved_progress(self):
        s=self._session(False)
        with patch.dict(self._profile_globals, {'current_cap_label':lambda k:'10000'}):
            asyncio.run(s.whois_v03051('Ala'))
        data='\n'.join(s.messages)
        self.assertIn('ostatni zapis SQLite',data)
        self.assertIn('Level postaci: 800/10000',data)
        self.assertIn('Stary tytuł',data)
        self.assertNotIn('Aktualny tytuł',data)

if __name__=='__main__': unittest.main()
