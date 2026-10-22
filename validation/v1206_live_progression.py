# -*- coding: utf-8 -*-
"""No-restart OLC regression for existing profession/tool and skill rewards."""
import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace


def run_regression():
    import server
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_progression_v1206 import PROFESSION_XP_PERCENT, TOOL_XP_PERCENT, xp_with_live_bonus
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
    from core.classes_skills import CLASS_SKILLS
    from systems.profession_xp_v1203 import reward_xp_v1203
    count=0
    assert len(PROFESSION_RANK_NAMES)==22 and len(TOOL_PROFESSION_MAP)==22
    count+=2
    assert len(CLASS_SKILLS)==22 and sum(map(len,CLASS_SKILLS.values()))==5461
    count+=2
    all_skills={x['id']:x for ls in CLASS_SKILLS.values() for x in ls}
    original=copy.deepcopy(all_skills['warrior_power_slash'])
    with tempfile.TemporaryDirectory() as tmp:
        conn=sqlite3.connect(str(Path(tmp)/'live.sqlite'))
        conn.row_factory=sqlite3.Row
        db=SimpleNamespace(conn=conn)
        world=SimpleNamespace(mobs={},_last_refresh_at=4.0)
        world._register_runtime_spawn=lambda rid,mid:None
        svr=SimpleNamespace(world=world,sessions=[])
        service=LiveContentV1204(db)
        assert service.revision==0 and not PROFESSION_XP_PERCENT and not TOOL_XP_PERCENT
        count+=3
        # Each of 22 professions can get a separate live EXP override.
        for prof in PROFESSION_RANK_NAMES:
            before=service.validate(service.draft)
            assert 'profesji' in before
            service.stage_edit('profesja',prof,'xp_percent','180')
            count+=2
        # Every existing tool has its own XP setting.
        for tool in TOOL_PROFESSION_MAP:
            service.stage_edit('narzedzie',tool,'xp_percent','200')
            count+=1
        service.stage_edit('skill','warrior_power_slash','mana','11')
        service.stage_edit('skill','warrior_power_slash','mult','1.75')
        count+=2
        for section,key,field,value in (
            ('profesja','NieMa','xp_percent','120'),
            ('narzedzie','NieMa','xp_percent','150'),
            ('profesja','Jubilerstwo','xp_percent','5'),
            ('profesja','Jubilerstwo','xp_percent','1001'),
            ('skill','warrior_power_slash','code','print(1)'),
            ('skill','warrior_power_slash','mana','-1'),
            ('skill','warrior_power_slash','mult','1000'),
            ('skill','warrior_power_slash','nonexistent','100'),
        ):
            try:
                service.stage_edit(section,key,field,value)
            except (ValueError, TypeError):
                count+=1
            else:
                raise AssertionError('Unsafe live change accepted '+str((section,key,field)))
        before=reward_xp_v1203(500,20000,50,50,content_key='iron_ore')
        assert xp_with_live_bonus(before,'Jubilerstwo')==before
        count+=1
        # Block a skill hot-publish while an enemy is actively engaged.
        fake=SimpleNamespace(engaged_by='player',aoe_engaged_by=None,home_room_id='temple_basement',room_id='temple_basement',template_id='temple_rat')
        world.mobs['fight']=fake
        try:
            service.apply(svr,'admin')
        except ValueError as exc:
            assert 'walk' in str(exc)
            count+=1
        else:raise AssertionError('Changed skill was published mid-combat')
        world.mobs.clear()
        msg=service.apply(svr,'admin')
        assert 'rewizję 1' in msg and service.revision==1
        count+=2
        assert PROFESSION_XP_PERCENT['Jubilerstwo']==180 and TOOL_XP_PERCENT['jewelcrafting']==200
        assert xp_with_live_bonus(before,'Jubilerstwo')==round(before*1.8)
        assert xp_with_live_bonus(before,'jewelcrafting',tool=True)==before*2
        assert xp_with_live_bonus(0,'Jubilerstwo')==0
        assert xp_with_live_bonus(before,'Inny')==before
        count+=6
        assert all(PROFESSION_XP_PERCENT[name]==180 for name in PROFESSION_RANK_NAMES)
        assert all(TOOL_XP_PERCENT[name]==200 for name in TOOL_PROFESSION_MAP)
        count+=44
        edited=next(row for row in CLASS_SKILLS['Wojownik'] if row['id']=='warrior_power_slash')
        assert edited['mana']==11 and edited['mult']==1.75
        count+=2
        saved=conn.execute('SELECT payload FROM live_content_v1204 WHERE id=1').fetchone()
        assert json.loads(saved['payload'])['skill_edits']['warrior_power_slash']['mana']==11
        count+=1
        # Persistence survives service recreation using the same sqlite DB.
        service._remove(None)
        service=LiveContentV1204(db)
        assert service.revision==1 and PROFESSION_XP_PERCENT['Jubilerstwo']==180
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']=='warrior_power_slash')['mana']==11
        count+=3
        # Rollback restores previous XP, skill params, and retains accounts.
        msg=service.apply(svr,'admin',rollback=True)
        assert 'rewizję 2' in msg and not PROFESSION_XP_PERCENT and not TOOL_XP_PERCENT
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']=='warrior_power_slash')==original
        assert xp_with_live_bonus(before,'Jubilerstwo')==before
        count+=4
        # Round trip for publication packages.
        service.stage_edit('profesja','Górnictwo','xp_percent','150')
        path=Path(tmp)/'publish.json';service.export(path)
        service.reset_draft();service.stage_file(path)
        assert service.draft['profession_edits']['Górnictwo']=={'xp_percent':150}
        count+=3
        service._remove(None)
        conn.close()
    return count


if __name__=='__main__':
    print(f'V12.00.6 OLC PROFESJE NARZEDZIA SKILLE: {run_regression()} checks PASS')
