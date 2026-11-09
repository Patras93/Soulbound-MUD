# -*- coding: utf-8 -*-
"""v109: damage modules preserve the complete legacy AST and standalone tests."""
from __future__ import annotations
import ast,hashlib,math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from player.session_mixins.combat_damage import SessionCombatDamageMixin
from systems.v10900_activation import REQUIRED
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SHA256='02e3abefe2d74edbb6f0abaf57accb0cb4ddd00fc5c685cedeb8ae5690de2ea0'
PARTS={
    'combat_mastery':('CombatMasteryV109Mixin',('mec_combat_mastery_active_v1124','basic_attack_inherent_multiplier_v1124','basic_attack_build_v11196')),
    'incoming_damage':('CombatIncomingV109Mixin',('consider_enemy_expected_hit',)),
    'consider_rating':('CombatRatingV109Mixin',('consider_rating',)),
    'health_readonly':('CombatHealthReadOnlyV109Mixin',('mob_effective_max_hp_v11330',)),
}

def run():
    checks=0
    root=ROOT/'player/session_mixins/combat_damage.py'
    node=next(c for c in ast.parse(root.read_text('utf8')).body
        if isinstance(c,ast.ClassDef) and c.name=='SessionCombatDamageMixin')
    assert node.bases==[], 'historical isolated AST tests must compile without imports';checks+=1
    found={n.name:n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    extracted=set()
    for fname,(cls,expected) in PARTS.items():
        rel='player/session_mixins/combat_damage_parts_v109/'+fname+'.py'
        assert rel in REQUIRED;checks+=1
        klass=next(c for c in ast.parse((ROOT/rel).read_text('utf8')).body if isinstance(c,ast.ClassDef) and c.name==cls)
        sub={n.name:n for n in klass.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(sub)==set(expected);checks+=1
        assert not (set(sub)&set(found));checks+=1
        found.update(sub);extracted.update(sub)
    assert len(extracted)==6 and len(found)==17;checks+=1
    digest=hashlib.sha256('\n'.join(ast.dump(found[k],include_attributes=False) for k in sorted(found)).encode()).hexdigest()
    assert digest==EXPECTED_SHA256,digest;checks+=1
    for name in found:
        assert callable(getattr(SessionCombatDamageMixin,name,None)), name
        checks+=1
    assert 'player/session_mixins/combat_damage_parts_v109/__init__.py' in REQUIRED;checks+=1
    # Confirm the intentionally extracted methods are installed exactly once on
    # the actual runtime class, without changing its bases / legacy MRO.
    for name in extracted:
        assert name in SessionCombatDamageMixin.__dict__;checks+=1

    class Hero(SessionCombatDamageMixin):
        def __init__(self):
            self.character=SimpleNamespace(class_name='Mec',class_type='physical',
                soul_weapon='mec_blade',character_level=100)
            self.current_hp=100
        def job_ability_selected(self,*args):return True
        def equipment_flat_power_totals_v11187(self):return {'attack':1,'weapon_power':1}
        def effective_strength(self):return 40
        def effective_dexterity(self):return 20
        def effective_intelligence(self):return 10
        def physical_power(self):return 100
        def spell_power(self):return 80
        def defense(self):return 0
        def magic_defense(self):return 0
        def dodge_chance(self):return 0
        def consider_adaptive_preview_v11331(self,*_):
            return {'player_hit':20,'player_hits':2,'player_action':40,
                    'party_action':40,'enemy_hit':5,'current_hp':60}
    hero=Hero()
    assert hero.mec_combat_mastery_active_v1124() is True;checks+=1
    assert hero.basic_attack_inherent_multiplier_v1124()==1.2;checks+=1
    assert hero.basic_attack_build_v11196()==(100,40,'physical');checks+=1
    hero.character.soul_weapon=''
    assert hero.mec_combat_mastery_active_v1124() is False;checks+=1
    hero.character.class_type='magic'
    assert hero.basic_attack_build_v11196()==(80,10,'magic');checks+=1
    a=SimpleNamespace(template_id='goblin',adaptive_max_hp_v11330=123)
    assert hero.mob_effective_max_hp_v11330(a)==123;checks+=1
    assert hero.mob_effective_max_hp_v11330(None)==1;checks+=1
    assert hero.mob_effective_max_hp_v11330(SimpleNamespace(template_id='faux',adaptive_max_hp_v11330=0),{'max_hp':75})==75;checks+=1
    rating=hero.consider_rating(a,{})
    assert rating['label']=='bardzo słaby' and rating['turns_to_kill']==2 and rating['turns_to_die']==20;checks+=1
    class Race:
        def racial_physical_damage_reduction_percent(self):return 0
        def racial_damage_reduction_percent(self):return 0
        def class_damage_reduction_percent(self):return 0
    hero.character=Race()
    with patch('player.session_mixins.combat_damage_parts_v109.incoming_damage.elemental_expected_incoming_multiplier_v11339',return_value=1):
        assert hero.consider_enemy_expected_hit({'damage':20})==20;checks+=1
    return checks

if __name__=='__main__':print('V109 COMBAT DAMAGE MODULES:',run(),'PASS; no database/production changes')
