# -*- coding: utf-8 -*-
"""Isolated v106 Admin Live 3.0 regression; no production journal or accounts."""
from __future__ import annotations
from pathlib import Path
import os,sys,json,tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import admin_live_era_v10400 as native
from systems.admin_live_era_v10600 import command,HELP
from world.v10600_soul_trials import quest_definitions
from world.v10600_raids_26_35 import RAID_ROWS
from world.v10400_raids_12_25 import _boss_phases


def run():
    checks=0
    def ck(condition,explain):
        nonlocal checks
        assert condition,explain
        checks+=1
    key='v10600_raid_26_boss_1'
    first_trial='soul_tier_3010_trial'
    final_trial='soul_tier_6000_trial'
    quest_defs=quest_definitions()
    catalog={'rooms': {'v10600_test_01':{'generator_level':30001,'recommended_mastery':30001}},
             'mobs':{key: {'name':'Strażnik Bramy', 'boss':True,
                    'max_hp':123456789, 'damage':1234567,
                    'olc_boss_phases':_boss_phases('Brama',1)},
                    'v10500_test_boss':{'max_hp':12345}},
             'quests':{first_trial:quest_defs[first_trial].copy(),
                       final_trial:quest_defs[final_trial].copy(),
                       'v10600_test_quest':{'needed':1,'reward_gold':20}},
             'items': {'v10600_test_item':{'defense':20,'affix_amount':55}},
             'recipes': {'v10600_test_recipe':{'min_profession_level':30001,'quantity':1}}}
    old_path=native.PATH
    old_env=os.environ.get('SOULBOUND_V106_STAGING')
    with tempfile.TemporaryDirectory(prefix='sb_v106_admin3_') as dirname:
        try:
            native.PATH=Path(dirname)/'LIVE_CONTENT'/'era_v10400_overrides.json'
            native.reset_for_tests()
            os.environ.pop('SOULBOUND_V106_STAGING',None)
            ck('nieaktywny' in command('status',catalog),'staging off blocked')
            ck('nieaktywny' in command('ustaw mob '+key+' max_hp 900000000',catalog),
               'writes blocked outside staging')
            for kind,ident,field in [('mob',key,'max_hp'),
                      ('soul_trial',first_trial,'needed'),
                      ('raid_phase',key,'p1_attack_pct')]:
                try:native._parse_key('|'.join((kind,ident,field)))
                except ValueError:checks+=1
                else:raise AssertionError('v106 key accepted without staging: '+kind)
            ck(not native.PATH.exists(),'staging off writes nothing')
            os.environ['SOULBOUND_V106_STAGING']='1'
            ck('v10600' in HELP.casefold(),'help references v106')
            ck('1/6' in command('regiony',catalog),'regions paginated 30/5')
            ck('6/6' in command('regiony 6',catalog),'last regions page')
            ck('strony' in command('regiony 7',catalog).casefold(),'bad page refused')
            ck('1/2' in command('rajdy',catalog),'raids paginated 10/5')
            ck('2/2' in command('rajdy 2',catalog),'last raids page')
            ck('niekompletny' in command('rajd 26',catalog),'no fake complete raid')
            ck('3010' in command('soul 3010',catalog),'first trial inspect')
            ck('6000' in command('soul 6000',catalog),'last trial inspect')
            ck('co 10' in command('soul 3011',catalog).casefold() or 'wielokrotność 10' in command('soul 3011',catalog),
               'non ten-multiple refused')
            ck('krain 30' in command('audyt',catalog),'audit exposes counts')
            from core.live_level_caps_v5200 import _state as cap_state
            soul_cap_before=cap_state['dusza']
            try:
                cap_state['dusza']=800
                ck('BLOKADA PROGRESJI' in command('audyt',catalog),'audit warns about 800 cap')
                cap_state['dusza']=60000
                ck('zgodny z Tierem 6000' in command('audyt',catalog),'audit sees full Soul cap')
                cap_state['dusza']=None
                ck('zgodny z Tierem 6000' in command('audyt',catalog),'audit supports unlimited')
            finally:
                cap_state['dusza']=soul_cap_before
            ck('rewizja 0' in command('status',catalog),'journal status')
            ck('123456789' in command('podglad mob '+key+' max_hp',catalog), 'read original HP')
            ck('DRAFT' in command('ustaw mob '+key+' max_hp 900000000',catalog),'stage boss HP')
            ck('DRAFT' in command('ustaw soul_trial '+first_trial+' needed 2',catalog),'stage trial count')
            ck('DRAFT' in command('ustaw quest v10600_test_quest reward_gold 50',catalog), 'stage quest reward')
            ck('DRAFT' in command('ustaw recipe v10600_test_recipe quantity 2',catalog), 'stage recipe qty')
            ck('DRAFT' in command('ustaw item v10600_test_item defense 25',catalog), 'stage item')
            ck('DRAFT' in command('ustaw room v10600_test_01 generator_level 31000',catalog), 'stage room')
            ck('DRAFT' in command('ustaw raid_phase '+key+' p1_attack_pct 150',catalog),'stage raid phase')
            ck('DRAFT' in command('sprawdz',catalog),'shared draft check')
            ck(not native.PATH.exists(),'draft only no journal disk')
            ck(catalog['mobs'][key]['max_hp']==123456789,'draft not hot-published')
            ck('Zakres pola' in command('ustaw mob '+key+' max_hp 0',catalog), 'reject zero HP')
            ck('Nieobsługiwane pole' in command('ustaw soul_trial '+first_trial+' required_soul_level 1',catalog),
               'deny unsafe tier threshold edits')
            ck('Nieobsługiwane pole' in command('ustaw mob v10600_not_real__hack max_hp 10',catalog)
               or 'Nie istnieje' in command('ustaw mob v10600_not_real__hack max_hp 10',catalog),
               'no arbitrary forged object')
            ck('rewizję 1' in command('aktywuj POTWIERDZAM',catalog),'publish one shared revision')
            saved=json.loads(native.PATH.read_text(encoding='utf8'))
            ck(saved['schema']==1 and saved['rev']==1 and len(saved['active'])==7,
               'single journal with 7 v106 keys')
            ck(catalog['mobs'][key]['max_hp']==900000000,'published HP is used')
            ck(catalog['quests'][first_trial]['needed']==2,'published trial needed')
            ck(catalog['quests'][first_trial]['required_soul_level']==30100,
               'trial threshold immutable')
            ck(catalog['quests'][first_trial]['target']==quest_defs[first_trial]['target'],
               'trial boss immutable')
            ck(catalog['quests']['v10600_test_quest']['reward_gold']==50,'published quest reward')
            ck(catalog['recipes']['v10600_test_recipe']['quantity']==2,'published recipe')
            ck(catalog['items']['v10600_test_item']['defense']==25,'published item')
            ck(catalog['rooms']['v10600_test_01']['generator_level']==31000,'published room')
            ck(round(catalog['mobs'][key]['olc_boss_phases'][0]['attack_multiplier'],2)==1.5,
               'published boss phase')
            ck('rewizja 1' in command('status',catalog),'revision tracked after publish')
            ck('rewizja 2' in command('cofnij POTWIERDZAM',catalog),'rollback uses same journal')
            ck(catalog['mobs'][key]['max_hp']==123456789, 'rollback HP')
            ck(catalog['quests'][first_trial]['needed']==1, 'rollback trial')
            ck(catalog['quests']['v10600_test_quest']['reward_gold']==20, 'rollback quest')
            ck(native.PATH.exists(),'journal retained with history')
            # CAS conflicts: an external writer advances shared journal before publication.
            ck('DRAFT' in command('ustaw mob '+key+' max_hp 777777777',catalog),'new draft')
            state=json.loads(native.PATH.read_text(encoding='utf8'));state['rev']+=1
            native.PATH.write_text(json.dumps(state),encoding='utf8')
            ck('konflikt rewizji' in command('aktywuj POTWIERDZAM',catalog),
               'external CAS revision blocks publication')
            ck(catalog['mobs'][key]['max_hp']==123456789,'no write on CAS conflict')
            ck('anulowany' in command('anuluj',catalog),'abandon draft')
        finally:
            native.PATH=old_path
            native.reset_for_tests()
            if old_env is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
            else:os.environ['SOULBOUND_V106_STAGING']=old_env
    return checks

if __name__=='__main__':print('V106 ADMIN LIVE 3 STAGING:',run(),'PASS',flush=True)
