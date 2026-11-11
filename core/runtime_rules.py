"""Explicit composition slots for the thirteen authored gameplay rule overrides.

Only these named rule functions are replaceable. Catalogues, constants, classes
and arbitrary module namespaces never enter this API. Rule owners register the
next implementation as the current world is built; consumers ask for the active
rule when handling a request. This preserves bootstrap order without injecting
symbols into another module or cloning a function's globals.
"""
from __future__ import annotations
from collections.abc import Callable

RULE_NAMES=frozenset({
    '_boss_floor_chest_spec','boss_floor_identity','boss_key_for_template',
    'create_infinite_astral_floor_definition','create_infinite_crypt_floor_definition',
    'create_infinite_magitek_floor_definition','normalize_profession_name',
    'v0100_instance_spec','v0150_environment_bonus','v0190_apply_combat_template',
    'v0190_combat_reward','v0927_guild_building_upgrade_cost',
    'v0927_guild_hall_upgrade_cost',
})
_rules:dict[str,Callable]={}

def register_rule(name:str,implementation:Callable)->None:
    """Publish an authored rule implementation at its explicit composition step."""
    if name not in RULE_NAMES:raise ValueError('Undeclared gameplay rule: '+str(name))
    if not callable(implementation):raise TypeError('Gameplay rule must be callable: '+name)
    _rules[name]=implementation

def get_rule(name:str)->Callable:
    """Return the active implementation of one declared gameplay rule."""
    if name not in RULE_NAMES:raise ValueError('Undeclared gameplay rule: '+str(name))
    try:return _rules[name]
    except KeyError as exc:raise RuntimeError('Gameplay rule used before composition: '+name) from exc

def rule_owners()->dict[str,str]:
    """Read-only diagnostics; callers cannot mutate the composed slots."""
    return {name:fn.__module__+'.'+fn.__qualname__ for name,fn in sorted(_rules.items())}
