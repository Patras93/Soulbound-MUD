# -*- coding: utf-8 -*-
"""Validate that obsolete template-scoped forge modifiers fail BEFORE costs."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'player/session_mixins/forge_guilds.py').read_text(encoding='utf-8-sig')


def run():
    tree=ast.parse(SOURCE)
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='SessionForgeGuildsMixin')
    methods={node.name:node for node in cls.body if isinstance(node,ast.AsyncFunctionDef)}
    checks=0
    for method,unsafe in (
        ('upgrade_equipment_v03042','set_equipment_upgrade_level_v03042'),
        ('reforge_equipment_v0925','save_equipment_reforge'),
        ('handle_runes_v0925','remove_equipment_rune_v0925'),
        ('socket_rune_v0925','add_equipment_rune_v0925')):
        fn=methods[method]
        source=ast.get_source_segment(SOURCE,fn)
        assert source,method
        unsafe_pos=source.index(unsafe)
        safety_pos=source.index('_eq107_tracked(')
        assert safety_pos < unsafe_pos,method+' checks physical gear after mutation'
        assert 'await self.send(' in source[safety_pos:unsafe_pos],method+' no NVDA rejection'
        assert 'return' in source[safety_pos:unsafe_pos],method+' failed to exit before costs'
        checks+=3
    assert "'player/session_mixins/forge_guilds.py'" in (
        ROOT/'systems/v10700_activation.py').read_text(encoding='utf-8-sig')
    checks+=1
    return checks

if __name__=='__main__':print('V107 KOWALSTWO BEZ UTRATY MATERIAŁÓW:',run(),'PASS')
