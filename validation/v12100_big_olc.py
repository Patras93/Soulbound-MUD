# -*- coding: utf-8 -*-
"""Large OLC v12.10.0 regression tests against actual registries + SQLite."""
import copy
import json
import sqlite3
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS
from data.quests import QUESTS
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_diff import describe_diff
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
from systems.live_olc4_new_skills import new_skill_definition


def run():
    count = 0
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={}, _last_refresh_at=0.0, _register_runtime_spawn=lambda *args:None)
    server = SimpleNamespace(world=world, sessions=[])
    original_skills = {key:tuple(row['id'] for row in rows) for key, rows in CLASS_SKILLS.items()}
    original_boss = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    svc = LiveContentV1204(SimpleNamespace(conn=conn))
    try:
        assert svc.validate(svc.active);count+=1
        assert 'brak przygotowanych' in describe_diff(svc.active, svc.draft);count+=1
        for kind, effect in (('heal',0.1),('group_heal',0.04),('guard',2000)):
            sid='live_wielki_'+kind
            svc.stage_new_skill(sid,'Mag','Wielka Próba '+kind,kind,20,15,1.0,'wisdom','Bezpieczny test',effect)
            definition=new_skill_definition(sid,svc.draft['skills'][sid])
            assert definition['kind']==kind;count+=1
            assert definition.get('heal_pct',definition.get('guard'))==effect;count+=1
            assert sid not in [s['id'] for s in CLASS_SKILLS['Mag']];count+=1
        svc.stage_edit('skill','live_wielki_heal','effect','0.2');count+=1
        assert svc.draft['skills']['live_wielki_heal']['effect']==0.2;count+=1
        svc.stage_edit('skill','live_wielki_guard','effect','5000');count+=1
        assert svc.draft['skills']['live_wielki_guard']['effect']==5000;count+=1
        for invalid in (-1,0,1.01, float('nan')):
            old=copy.deepcopy(svc.draft)
            try:svc.stage_edit('skill','live_wielki_heal','effect',str(invalid))
            except ValueError: count+=1
            else:raise AssertionError('invalid healing effect accepted')
            assert svc.draft==old;count+=1
        try:svc.stage_new_skill('live_invalid_attack','Mag','Atak Effect','damage',1,1,1,'wisdom','Nie ma',5)
        except ValueError:count+=1
        else:raise AssertionError('attack with effect accepted')
        # Compare read-only and confirm correct nested field diff.
        before=copy.deepcopy(svc.draft); rev=svc.revision
        summary=describe_diff(svc.active,svc.draft,50)
        assert 'skills/live_wielki_heal' in summary and '0.2' in summary;count+=1
        assert before==svc.draft and rev==svc.revision;count+=1
        # Four/five ordinary boss phases with unchanged stock AI for others.
        phase=[dict(hp_percent=hp,attack_multiplier=round(1.2+i*0.1,2),duration_seconds=10+i,message='Faza '+str(i))
               for i,hp in enumerate((90,70,50,30,10),1)]
        svc.stage_edit('mob','bandit_captain','olc_boss_phases',json.dumps(phase,ensure_ascii=False));count+=1
        svc.stage_new_quest('live_olc4_pogrom','Wielki pogrom','Rybak Borys','kill','temple_rat',20,500,'Pokonaj szczury.');count+=1
        assert svc.draft['quests']['live_olc4_pogrom']['needed']==20;count+=1
        assert 'quest' not in QUESTS.get('live_olc4_pogrom',{});count+=1
        svc.stage_new_item('live_big_helm','armor','Testowy Hełm','Pancerz', 'head',120,600);count+=1
        svc.stage_new_item('live_big_potion','consumable','Mikstura Testowa','Leczy', 'heal',250,50);count+=1
        svc.stage_new_item('live_big_material','craft_material','Materiał Testowy','Do rzemiosła', '-',0,5);count+=1
        for bad_kind,bad_variant in (('armor','unknown'), ('consumable','python'), ('equipment','-')):
            old_draft=copy.deepcopy(svc.draft)
            try:svc.stage_new_item('live_invalid_item',bad_kind,'Test','Opis',bad_variant,200,50)
            except ValueError:count+=1
            else:raise AssertionError('invalid item kind accepted')
            assert old_draft==svc.draft;count+=1
        original=copy.deepcopy(svc.active)
        svc.apply(server,'admin');count+=1
        assert 'live_olc4_pogrom' in QUESTS and QUESTS['live_olc4_pogrom']['reward_silver']==500;count+=1
        assert ITEMS['live_big_helm']['defense']==120;count+=1
        assert ITEMS['live_big_potion']['heal']==250;count+=1
        assert ITEMS['live_big_material']['type']=='craft_material';count+=1
        assert len(CLASS_SKILLS['Mag'])==len(original_skills['Mag'])+3;count+=1
        assert next(s for s in CLASS_SKILLS['Mag'] if s['id']=='live_wielki_heal')['heal_pct']==0.2;count+=1
        assert next(s for s in CLASS_SKILLS['Mag'] if s['id']=='live_wielki_guard')['guard']==5000;count+=1
        mob=SimpleNamespace(alive=True,hp=9,adaptive_max_hp_v11330=100,v1230_boss_phase=0)
        assert 'FAZA 5/5' in boss_tactics_phase_v1230(mob,MOB_TEMPLATES['bandit_captain'],now=100);count+=1
        assert svc.revision==1;count+=1
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn));count+=1
        assert reopened.active['skills']['live_wielki_group_heal']['effect']==0.04;count+=1
        assert '0.2' in describe_current_edit(reopened,'skill','live_wielki_heal','effect');count+=1
        assert '5000' in describe_current_edit(reopened,'skill','live_wielki_guard','effect');count+=1
        assert reopened.active['mob_edits']['bandit_captain']['olc_boss_phases']==phase;count+=1
        # Published persistent IDs cannot disappear on rollback.
        try:reopened.apply(server,'admin',rollback=True)
        except ValueError as exc:
            assert any(section in str(exc) for section in ('items','skills','quests'));count+=1
        else: raise AssertionError('removed published quest/skill')
        assert reopened.revision==1;count+=1
        # Invalid scripting/injection and invalid quest references rejected.
        for bad in ('No such NPC', 'Wojownik'):
            snapshot=copy.deepcopy(reopened.draft)
            try:reopened.stage_new_quest('live_test_bad', 'Błędny',bad,'kill','temple_rat',10,2,'Opis')
            except ValueError:count+=1
            else:raise AssertionError('invalid NPC accepted')
            assert reopened.draft==snapshot;count+=1
        for bad in ('__import__','python'):
            snapshot=copy.deepcopy(reopened.draft)
            try:reopened.stage_new_quest('live_test_bad','Błędny','Rybak Borys',bad,'temple_rat',10,2,'Opis')
            except ValueError:count+=1
            else:raise AssertionError('invalid kind accepted')
            assert reopened.draft==snapshot;count+=1
        try:describe_diff(reopened.active,reopened.draft,500)
        except ValueError:count+=1
        else:raise AssertionError('invalid diff limit')
    finally:
        svc._remove(world) if svc._undo else None
        # A reopened service may be the current owner of installed definitions.
        if 'reopened' in locals() and reopened._undo: reopened._remove(world)
        MOB_TEMPLATES['bandit_captain']=original_boss
        for key, original_ids in original_skills.items():
            CLASS_SKILLS[key][:]=[row for row in CLASS_SKILLS[key] if row['id'] in original_ids]
        conn.close()
    return count + test_real_admin_commands()


def test_real_admin_commands():
    """Exercise actual owner-facing async command handler and single NEWS."""
    import ast
    import asyncio
    from pathlib import Path
    src=(Path(__file__).resolve().parents[1]/"player/session_mixins/admin_tools.py").read_text("utf8")
    tree=ast.parse(src)
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and any(getattr(m,"name",None)=="admin_live_v1204" for m in n.body))
    method=next(n for n in owner.body if getattr(n,"name",None)=="admin_live_v1204")
    compiled=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name="Mini",bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
    scope={}
    exec(compile(compiled,"<olc-admin>","exec"),scope)
    mini=scope["Mini"]()
    conn=sqlite3.connect(":memory:");conn.row_factory=sqlite3.Row
    conn.execute("CREATE TABLE quests (quest_id TEXT, status TEXT)")
    db=SimpleNamespace(conn=conn,account_name=lambda *a:"admin",record_admin_action_v1224=lambda *a:None)
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(sessions=[],world=world,db=db)
    svc=LiveContentV1204(db);server.live_content_v1204=svc
    mini.server=server;mini.master_account_id=1;mini.is_admin=lambda:True
    messages=[];news=[]
    async def send(line):messages.append(line)
    async def news_send(line):news.append(line)
    mini.send=send;mini.news_channel_v1204=news_send
    async def check():
        count=0
        try:
            await mini.admin_live_v1204("nowyskill live_proba_admin_heal | Mag | Test Healer OLC | heal | 20 | 15 | 1.0 | wisdom | Opis | 0.2")
            assert "przygotowano" in messages[-1];count+=1
            await mini.admin_live_v1204("nowyprzedmiot live_proba_admin_zbroja | armor | Testowa Zbroja | Opis | body | 50 | 200")
            assert "przygotowano" in messages[-1];count+=1
            await mini.admin_live_v1204("nowyquest live_proba_admin_quest | Zadanie Testowe | Rybak Borys | kill | temple_rat | 5 | 100 | Opis zadania")
            assert "przygotowano" in messages[-1];count+=1
            await mini.admin_live_v1204("porownaj 10")
            assert "było" in messages[-1] and not news;count+=1
            await mini.admin_live_v1204("sprawdz")
            assert "Przygotowane" in messages[-1] and not news;count+=1
            await mini.admin_live_v1204("aktywuj POTWIERDZAM")
            assert "Aktywowano" in messages[-1];count+=1
            assert len(news)==1;count+=1
            assert svc.revision==1;count+=1
        finally:
            svc._remove(world);conn.close()
        return count
    return asyncio.run(check())


if __name__=='__main__':
    print('V12.10.0 BIG OLC:',run(),'checks PASS')
