# -*- coding: utf-8 -*-
"""Regression coverage of durable guild expansion from 600 to 800."""
import ast
from pathlib import Path
from core import balance_math
from storage.db_shared import v0926_guild_bonus_percent as db_bonus
from storage.db_shared import V0926_GUILD_MAX_LEVEL as DB_MAX

ROOT=Path(__file__).resolve().parents[1]

def _load_protocol_helpers():
    """The networking utils are a runtime-concatenated module; extract pure guild functions."""
    text=(ROOT/'network/protocol_gameplay_utils.py').read_text(encoding='utf8')
    parsed=ast.parse(text)
    wanted={'_v0926_legacy_guild_anchor_400','v0926_guild_upgrade_cost','v0926_guild_bonus_percent'}
    nodes=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
    env={'balance_math':balance_math,'V0926_GUILD_MAX_LEVEL':800,
         'V0926_GUILD_OLD_CAP':600,'V0926_GUILD_LEGACY_MAX_LEVEL':100,
         'V0926_GUILD_PREVIOUS_CAP':400}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ROOT/'network/protocol_gameplay_utils.py'),'exec'),env)
    return env['v0926_guild_bonus_percent'],env['v0926_guild_upgrade_cost']

def run_regression():
    bonus,cost=_load_protocol_helpers();checked=0
    assert DB_MAX==800;checked+=1
    # Both guild implementations must provide identical bonuses for each level.
    for level in range(1,801):
        assert bonus(level)==db_bonus(level),(level,bonus(level),db_bonus(level));checked+=1
    for level,want in ((100,11),(200,15),(300,19),(400,23),(600,29),(800,35)):
        assert bonus(level)==want,(level,bonus(level));checked+=1
    for level in range(1,800):
        assert 0<=bonus(level)<=bonus(level+1)<=35,(level,bonus(level),bonus(level+1));checked+=1
    assert cost(800)==0;checked+=1
    for level in range(400,799):
        assert cost(level)>0 and cost(level+1)>=cost(level),(level,cost(level),cost(level+1));checked+=1
    # Both 600 and 800 milestones must exist and remain achievable.
    source=(ROOT/'player/session_mixins/forge_guilds.py').read_text(encoding='utf8')
    assert '("guild600","Gildia Poziomu 600",level>=600)' in source;checked+=1
    assert '("guild800","Gildia Poziomu 800",level>=V0926_GUILD_MAX_LEVEL)' in source;checked+=1
    assert 'maksymalny poziom 800' in source;checked+=1
    return checked

if __name__=='__main__': print('GUILD 800 v1.70.10:',run_regression(),'checks PASS')
