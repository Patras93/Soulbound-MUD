# -*- coding: utf-8 -*-
"""Isolated EQ-level and +upgrade cap checks. No player database is read."""
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from core import live_level_caps_v5200 as caps
from systems.admin_live_level_caps_v5200 import _handle
from network import protocol_gameplay_utils as gear
from world import equipment_help as equipment
from storage.db_inventory import DatabaseInventoryMixin
from storage import db_shared


def run():
    checks=0
    def ok(v,why=''):
        nonlocal checks
        assert v,why
        checks+=1
    oldpath=caps.CAP_FILE
    oldstate=caps.current()
    oldloaded=caps._loaded
    with tempfile.TemporaryDirectory(prefix='eq_caps_') as temp:
        caps.CAP_FILE=Path(temp)/'LIVE_CONTENT'/'admin_level_caps.json'
        try:
            values=caps.load()
            ok(values['eq']==800)
            ok(values['ulepszenia_eq']==10)
            for key in ('eq','sprzet','ekwipunek','poziom_eq'):
                ok(caps.normalize_key(key)=='eq',key)
            for key in ('ulepszenia_eq','ulepsz_eq','eq_plus','ulepszanie_eq'):
                ok(caps.normalize_key(key)=='ulepszenia_eq',key)
            item={'required_character_level':1200,'required_mastery':1200,
                  'name':'Testowa zbroja','type':'armor','defense':100,'slot':'body'}
            ok(gear.v03042_equipment_level(item)==800)
            ok(gear.v03042_upgrade_stat_bonus(11)==5) # capped at +10
            ok('PLAN' in _handle('ustaw eq bezlimitu'))
            ok(not caps.CAP_FILE.exists())
            ok('ZAPISANO' in _handle('ustaw eq bezlimitu POTWIERDZAM'))
            ok(gear.v03042_equipment_level(item)==1200)
            ok(equipment.normalize_equipment_mastery_v0919(1250)==1250)
            ok('ZAPISANO' in _handle('ustaw ulepszenia_eq 100 POTWIERDZAM'))
            ok(gear.V03042_EQ_UPGRADE_MAX==100)
            ok(db_shared.V03042_EQ_UPGRADE_MAX==100)
            ok(gear.v03042_upgrade_stat_bonus(11)==5)
            ok(gear.v03042_upgrade_stat_bonus(100)==50)
            ok(gear.v03042_upgrade_defense_bonus(item,50)>gear.v03042_upgrade_defense_bonus(item,10))
            ok(gear.v03042_upgrade_material_cost(item,11)>0)
            ok(gear.v03042_upgrade_required_smithing(item,11)>0)
            ok('ZAPISANO' in _handle('ustaw ulepszenia_eq bezlimitu POTWIERDZAM'))
            ok(gear.V03042_EQ_UPGRADE_MAX==caps.TECHNICAL_CEILING)
            ok(caps.cap('ulepszenia_eq') is None)
            ok(json.loads(caps.CAP_FILE.read_text('utf-8'))['caps']['ulepszenia_eq'] is None)
            # Only specific level cap changes, never equip requirements or player stats.
            ok(item['required_character_level']==1200)
            ok(item['required_mastery']==1200)
            # The real persistence setter must preserve an existing +95 after lowering cap to +5.
            conn=sqlite3.connect(':memory:')
            conn.row_factory=sqlite3.Row
            conn.execute('CREATE TABLE equipment_upgrades_v03042(account_id INTEGER,item_id TEXT,upgrade_level INTEGER, PRIMARY KEY(account_id,item_id))')
            database=DatabaseInventoryMixin()
            database.conn=conn
            database.set_equipment_upgrade_level_v03042(1,'test_armor',95)
            ok(database.equipment_upgrade_level_v03042(1,'test_armor')==95)
            _handle('ustaw ulepszenia_eq 5 POTWIERDZAM')
            ok(gear.V03042_EQ_UPGRADE_MAX==5)
            database.set_equipment_upgrade_level_v03042(1,'test_armor',95)
            ok(database.equipment_upgrade_level_v03042(1,'test_armor')==95)
            database.set_equipment_upgrade_level_v03042(1,'other_armor',95)
            ok(database.equipment_upgrade_level_v03042(1,'other_armor')==5)
            conn.close()
            ok('5 -> 10' in _handle('reset ulepszenia_eq POTWIERDZAM'))
            ok(caps.cap('ulepszenia_eq')==10)
            ok(gear.V03042_EQ_UPGRADE_MAX==10)
            ok('RESET' in _handle('reset wszystko POTWIERDZAM'))
            ok(caps.current()==caps.DEFAULTS)
            # Import older v52 (eight-axis) settings without throwing away user overrides.
            legacy={k: caps.DEFAULTS[k] for k in caps.OLD_KEYS_V52}
            legacy['postac']=1234
            caps.CAP_FILE.write_text(json.dumps({'schema':1,'caps':legacy}),'utf-8')
            reloaded=caps.load()
            ok(reloaded['postac']==1234)
            ok(reloaded['eq']==800)
            ok(reloaded['ulepszenia_eq']==10)
            ok(len(json.loads(caps.CAP_FILE.read_text())['caps'])==8) # no automatic rewriting
            # A first write migrates forward, retaining previously configured values.
            _handle('ustaw ulepszenia_eq 20 POTWIERDZAM')
            on_disk=json.loads(caps.CAP_FILE.read_text('utf-8'))['caps']
            ok(len(on_disk)==10)
            ok(on_disk['postac']==1234)
            ok(on_disk['ulepszenia_eq']==20)
            # No loss of progress on a malformed manually edited config.
            on_disk['eq']='bad'
            caps.CAP_FILE.write_text(json.dumps({'schema':1,'caps':on_disk}),'utf-8')
            before=caps.current()
            try:caps.load()
            except ValueError:ok(True)
            else:ok(False,'invalid file accepted')
            ok(caps.current()==before)
        finally:
            caps.CAP_FILE=oldpath
            caps._state.update(oldstate)
            caps._loaded=oldloaded
            caps._apply_to_runtime()
    print(f'v52 admin live EQ caps: {checks} PASS')
    return checks

if __name__ == '__main__':run()
