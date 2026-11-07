# -*- coding: utf-8 -*-
"""Opt-in v106: real trainer registry, player command, shared weapon attack.

All DB writes use :memory: SQLite. No game server, no production data, no
claim of ordinary-boss time-to-kill or Windows PREDEPLOY coverage.
"""
from __future__ import annotations
import asyncio
import ast
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def worker():
    from core.classes_skills import CLASS_SKILLS,CLASSES,V10600_CLASS_SKILLS_ADDED
    from core.class_skills_v10600 import is_authored_unlock_v106
    from core.catalog_validation import validate_catalog
    enabled=os.environ.get('SOULBOUND_V106_STAGING')=='1'
    checks=0
    def ck(cond,message):
        nonlocal checks
        if not cond:raise AssertionError(message)
        checks+=1
    ck(len(CLASSES)==22,'all existing classes')
    ids={name:tuple(str(s['id']) for s in rows) for name,rows in CLASS_SKILLS.items()}
    all_ids=[sid for group in ids.values() for sid in group]
    ck(len(all_ids)==len(set(all_ids)),'IDs unique globally')
    ck(validate_catalog({'CLASS_SKILLS':CLASS_SKILLS})['error_count']==0,'canonical validation')
    if enabled:
        ck(V10600_CLASS_SKILLS_ADDED==44,'44 real skills installed')
        for i,(name,*_) in enumerate(CLASSES,1):
            rows=[s for s in CLASS_SKILLS[name] if str(s['id']).startswith('v10600_skill_')]
            ck(len(rows)==2,'two skills '+name)
            for j,s in enumerate(rows,1):
                ck(s['id']==f'v10600_skill_{i:02d}_{j}','stable authored ID '+name)
                ck(is_authored_unlock_v106(s,name),'whitelist for '+name)
                ck(int(s['unlock'])==[15000,30000][j-1],'unlock requires proper class mastery')
                ck(s['kind'] in {'damage','aoe_damage','boost','guard','heal','group_heal'},'real mechanic kind')
                ck(s['name'].casefold() in s['aliases'],'Polish spell alias')
                ck(s['cooldown']>0,'cooldown')
        ck(not is_authored_unlock_v106({'id':'v10600_skill_01_1','unlock':15000,'kind':'damage','name':'x'},'Wojownik'),'fake skill denied')
        ck(not is_authored_unlock_v106({'id':'v10600_skill_01_1','unlock':15000,'kind':'damage','name':'Cios Astralnego Żelaza'},'Mag'),'wrong class denied')
    else:
        ck(V10600_CLASS_SKILLS_ADDED==0,'no 106 skills in historical mode')
        ck(not any(sid.startswith('v10600_skill_') for sid in all_ids),'no leaked skills')

    # Compile the verbatim player command from production source. Full mixin
    # imports have world-wide side effects and cannot run outside server bootstrap.
    from systems.soul_weapon_elements_v10500 import (
        MIN_TIER, PREFERRED, normalize_element, selected_element,
        choose_element, activate_impulse, tuning)
    fn=ROOT/'player/session_mixins/equipment_stats.py'
    tree=ast.parse(fn.read_text(encoding='utf8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionEquipmentStatsMixin')
    method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef)
                and n.name=='soul_weapon_command_v10500')
    method.decorator_list=[]
    scope={'MIN_TIER':MIN_TIER,'PREFERRED':PREFERRED,'normalize_element':normalize_element,
           'selected_element':selected_element,'choose_element':choose_element,
           'activate_impulse':activate_impulse,'tuning':tuning}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(fn),'exec'),scope)
    cmd=scope['soul_weapon_command_v10500']
    from systems.soul_weapon_astral_v10600 import SECONDARY_KEY
    from systems.soul_weapon_elements_v10500 import COOLDOWN_KEY, SELECT_KEY
    import systems.uoss_basic_weapon_shared_v8000 as attacks

    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE player_records_v03051(account_id INTEGER NOT NULL, '
                 'record_key TEXT NOT NULL, value INTEGER NOT NULL DEFAULT 0, '
                 'text_value TEXT NOT NULL DEFAULT "", updated_at TEXT DEFAULT CURRENT_TIMESTAMP, '
                 'PRIMARY KEY(account_id,record_key))')
    conn.execute('INSERT INTO player_records_v03051 (account_id,record_key,text_value) VALUES(?,?,?)',
                 (7, SELECT_KEY, 'lightning'))
    conn.execute('INSERT INTO player_records_v03051 (account_id,record_key,value) VALUES(?,?,?)',
                 (7, COOLDOWN_KEY, 555555))
    class Actor:
        account_id=7
        server=SimpleNamespace(db=SimpleNamespace(conn=conn))
        character=SimpleNamespace(soul_tier=3100,soul_weapon_mastery_level=1,class_name='Wojownik')
        _v105_impulse_charged=False
        def __init__(self):self.messages=[]
        async def send(self,msg):self.messages.append(str(msg))
        def critical_chance(self):return 0.0
        def critical_multiplier(self):return 1.5
        def mob_effective_max_hp_v11330(self,mob,template):return 10000
    actor=Actor()
    asyncio.run(cmd(actor,'status'))
    ck(any('Tier 3100' in msg for msg in actor.messages),'real session status')
    if enabled:
        ck(any('Żywioł pomocniczy:' in msg for msg in actor.messages),'new real NVDA status')
        asyncio.run(cmd(actor,'drugi próżnia'))
        ck(any('Próżnia' in msg for msg in actor.messages),'new real select command')
        ck(conn.execute('SELECT text_value FROM player_records_v03051 '
                        'WHERE account_id=? AND record_key=?',(7,SECONDARY_KEY)).fetchone()[0]=='void',
           'new element persisted through real command')
        actor.character.soul_tier=3099
        asyncio.run(cmd(actor,'drugi astral'))
        ck(any('3100' in msg for msg in actor.messages),'tier guard actual command')
        actor.character.soul_tier=3100
        ck(conn.execute('SELECT text_value FROM player_records_v03051 WHERE account_id=7 AND record_key=?',
                        (SECONDARY_KEY,)).fetchone()[0]=='void','tier guard retains old valid choice')
    else:
        asyncio.run(cmd(actor,'drugi próżnia'))
        ck(not conn.execute('SELECT 1 FROM player_records_v03051 WHERE record_key=?',
                            (SECONDARY_KEY,)).fetchone(),'historical command has no new write')
        ck(not any('Żywioł pomocniczy:' in msg for msg in actor.messages),'v105 speech unchanged')

    # Check REAL shared production attack, isolating fixed historic weapon
    # factors so the only change is the new secondary damage multiplier.
    mob=SimpleNamespace(hp=10000)
    mastery={'damage_percent':0,'boss_damage_percent':0,'crit_chance':0,'crit_damage_percent':0}
    traits={'damage_percent':0,'execute_damage_percent':0,'boss_damage_percent':0,
            'crit_chance':0,'crit_damage_percent':0}
    with (patch.object(attacks,'soul_weapon_mastery_bonuses',return_value=mastery),
          patch.object(attacks,'weapon_resonance_percent',return_value=0),
          patch.object(attacks,'soul_weapon_trait_totals_v11193',return_value=traits),
          patch('systems.soul_weapon_elements_v10500.weapon_multiplier',return_value=1.0),
          patch('systems.soul_weapon_elements_v10500.consume_impulse',return_value=1.0),
          patch.object(attacks.random,'random',return_value=0.999)):
        ordinary=attacks.weapon_attack_boost(actor,mob,{},1000)[0]
        boss=attacks.weapon_attack_boost(actor,mob,{'world_boss':True},1000)[0]
        if enabled:
            ck(ordinary==950,'void deliberately weaker against normal mobs')
            ck(boss==1080,'void stronger against boss')
        else:
            ck(ordinary==1000 and boss==1000,'v105 attack unchanged')
    ck(conn.execute('SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
                    (7,COOLDOWN_KEY)).fetchone()[0]==555555,'v105 cooldown preserved')
    ck(conn.execute('SELECT text_value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
                    (7,SELECT_KEY)).fetchone()[0]=='lightning','v105 chosen element preserved')
    conn.close()
    print('RESULT_JSON='+json.dumps({'enabled':enabled,'checks':checks,'skills':sum(len(v) for v in ids.values()),
                                     'ids':ids},ensure_ascii=False))


def run():
    result=[]
    for enabled in (False,True):
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','SOULBOUND_V106_STAGING':'1' if enabled else ''}
        proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],
                            env=env,cwd=ROOT,timeout=120,text=True,capture_output=True)
        if proc.returncode:
            raise AssertionError(f'v106 worker stage={enabled}:\n{proc.stdout}\n{proc.stderr}')
        line=next((x[12:] for x in proc.stdout.splitlines() if x.startswith('RESULT_JSON=')),None)
        if not line:raise AssertionError('missing result in '+str(enabled)+': '+proc.stdout)
        result.append(json.loads(line))
    old,new=result
    assert old['enabled'] is False and new['enabled'] is True
    assert new['skills']==old['skills']+44
    for klass,old_ids in old['ids'].items():
        assert set(old_ids)<=set(new['ids'][klass]),'missing historical skills '+klass
        assert len(new['ids'][klass])==len(old_ids)+2,'wrong class delta '+klass
    return sum(x['checks'] for x in result)+22+3


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker()
    else:print('V106 SKILLS/SECONDARY REAL ENGINE:',run(),'PASS',flush=True)
