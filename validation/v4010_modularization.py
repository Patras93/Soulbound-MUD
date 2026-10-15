# -*- coding: utf-8 -*-
"""v4.00.2 refactor stability gate: AST identity, isolated catalogs and public contracts."""
from __future__ import annotations
import ast
from pathlib import Path
from hashlib import sha256

ORIGINAL_V4000_AST = {
    "build_mountain_crafting_expansion": ("world/expansion_mountain.py", "fd369032b5fb6d29980b004ec2acde66d00a7ea1ab2531dd8fae0c467f42e661"),
    "build_world_expansion_i": ("world/expansion_frontier_north_v407.py", "3969090cfcd8dbaf358c88877459f65945f1e1cb36639e7b46650c324c77b265"),
    "build_world_expansion_ii": ("world/expansion_frontier_fields_v407.py", "6ca419e3501bcd98f486587cda10a7d711a117bb96edf4488edab3c25bb164d6"),
    "build_high_end_mob_pack": ("world/expansion_high_end.py", "dfef009cbddb58489120d44c929b439ee60e8a0c86645a801a00058c85cfb3f8"),
    "configure_profession_tool_sellers": ("world/expansion_services.py", "def7525efe8fbdfcd9cc374fad2650ddcacf3ae5a8deb5ebb799e2e83077bb2b"),
    "configure_v0800_help_info": ("world/expansion_services.py", "cfd823a3160aacbfdabe5c9c0683b2d6cbda9fa73a17d95e40bdc04bdc25b056"),
    "configure_v081_help_info": ("world/expansion_services.py", "2c534e56c62141cfdb00b561b7dcc5cbc3f83effb344b62e0665098d46f99b12"),
    "build_paid_training_guild_expansion": ("world/expansion_services.py", "f8fbf965a3f6120d75eda68cf7dd38e69e64e57d4bb9d55824bbd4f1bf6fed80"),
    "build_forest_wolves_and_quest_balance": ("world/expansion_frontier_forest_v407.py", "00ae64f05a48fc9186f842f923f29280e64e2ccf7f8f37b3ed901707b8fa328e"),
    "CLASS_SKILLS": ("core/class_skill_catalog.py", "4de60ce5016b15e826a9d231652bf7f19a90deebb1a84825644917472e8a7f6b"),
    "ENDGAME_CLASS_SKILLS": ("core/class_skill_catalog.py", "9b9e37a2fb0482d5bba9f5caf9b7997033d5cd28d82aeb60ff547fc7e9273e24"),
}

def run_regression():
    from core.bootstrap_economy_professions import VERSION
    root=Path(__file__).resolve().parents[1]
    checks=0
    for symbol,(path,expected) in ORIGINAL_V4000_AST.items():
        source=root/path
        assert source.is_file(), f"missing moved module {path}"
        tree=ast.parse(source.read_text(encoding="utf-8"),filename=str(source))
        nodes=[]
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==symbol:
                nodes.append(node)
            if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id==symbol for x in node.targets):
                nodes.append(node)
        assert len(nodes)==1, (symbol,'missing or duplicate definition')
        actual=sha256(ast.dump(nodes[0],include_attributes=False).encode()).hexdigest()
        assert actual==expected, (symbol,'original v4.00.0 authored behavior changed')
        checks+=3
    facade=(root/'world/expansions.py').read_text(encoding='utf8')
    for name in ('build_world_expansion_i','build_world_expansion_ii','build_forest_wolves_and_quest_balance'):
        part=facade.split('def '+name+'():',1)[1].split('\n\ndef ',1)[0]
        assert '_impl.EXP_AREAS = EXP_AREAS' in part and 'EXP_AREAS = _impl.EXP_AREAS' in part, name
        checks+=2
    core=(root/'core/classes_skills.py').read_text(encoding='utf8')
    assert 'CLASS_SKILLS = _deepcopy_skill_catalog_v402(_AUTHORED_CLASS_SKILLS_V402)' in core
    checks+=1
    # Every load of the compatibility facade must start from independent data,
    # because several historical audits execute the source with runpy/exec.
    from core.classes_skills import CLASS_SKILLS, ENDGAME_CLASS_SKILLS
    from core.class_skill_catalog import (
        CLASS_SKILLS as authored_skills,
        ENDGAME_CLASS_SKILLS as authored_endgame,
    )
    import runpy
    import copy
    assert CLASS_SKILLS is not authored_skills
    assert ENDGAME_CLASS_SKILLS is not authored_endgame
    assert len(CLASS_SKILLS)==(22 if VERSION == '9.00.0' else 14)
    checks+=3
    original_runtime = copy.deepcopy(CLASS_SKILLS)
    original_authored = copy.deepcopy(authored_skills)
    first_replay = None
    for iteration in (1, 2):
        replay = runpy.run_path(str(root/'core/classes_skills.py'))
        isolated = replay['CLASS_SKILLS']
        assert isolated is not CLASS_SKILLS and isolated is not authored_skills, iteration
        # Earlier test modules may legitimately adjust the live catalog. Check
        # the two fresh replays against each other, never against that live state.
        if first_replay is None:
            first_replay = copy.deepcopy(isolated)
        else:
            assert isolated == first_replay, ('fresh facade not deterministic', iteration)
        assert sum(len(rows) for rows in isolated.values()) == (5417 if VERSION == '9.00.0' else 3473 if VERSION in ('5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0') else 3445), iteration
        assert CLASS_SKILLS == original_runtime, ('replay corrupted live catalog', iteration)
        assert authored_skills == original_authored, ('replay polluted authored data', iteration)
        from world.legends_v3100 import CLASS_NAMES as _legacy_classes_v3100
        assert len(_legacy_classes_v3100)==14
        for class_name in _legacy_classes_v3100:
            skills=isolated[class_name]
            v3200 = [skill for skill in skills if str(skill['id']).startswith('v3200_')]
            assert len(v3200)==3 and {skill['unlock'] for skill in v3200}=={260,420,600}, (iteration,class_name)
        checks+=6+14
    # Checks the real game server initialized and kept 10x EXP and all additions.
    import server
    from core.bootstrap_economy_professions import VERSION
    from config.balance import ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310
    assert VERSION in ('4.00.2','4.00.3','4.00.4','4.00.5','4.00.6','4.00.7','4.10.0','4.20.0','4.21.0','4.21.1','5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0','9.00.0')
    assert ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310==10
    assert len(server.QUESTS)== (6573 if VERSION == '9.00.0' else 5605 if VERSION == '8.00.0' else 3925 if VERSION in ('7.00.0','7.10.0','7.10.1','8.00.0','9.00.0') else 3861 if VERSION == '6.00.1' else 2901 if VERSION in ('5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0','9.00.0') else 2701)
    assert len([k for k in server.NPCS if k.startswith('v4000_')])==49
    checks+=4
    return checks

if __name__=='__main__':
    print('MODULY SILNIKA v4.00.2:',run_regression(),'checks PASS')
