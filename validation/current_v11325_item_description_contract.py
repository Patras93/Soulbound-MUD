# -*- coding: utf-8 -*-
"""Kontrola nowego tekstu opisów i dokładnego kontraktu AST metody."""
from pathlib import Path
from validation.current_native_v420_contract import verify_native_method
from player.session_mixins.atlas_codex import SessionAtlasCodexMixin


def run():
    root=Path(__file__).resolve().parents[1]
    assert verify_native_method(root / 'player/session_mixins/atlas_codex.py',
                                'SessionAtlasCodexMixin.format_item_description')
    class Fake(SessionAtlasCodexMixin):
        def shop_item_base_value_silver(self, item):
            return 0
    fake=Fake()
    for name, tool in [('Szczypce Jubilerskie', 'jewelcrafting'),
                       ('Kilof', 'mining'), ('Siekiera', 'woodcutting')]:
        result=fake.format_item_description('test', {
            'name':name,'type':'tool','tool_type':tool, 'price':None,
        })
        assert 'Typ: narzędzie.' in result, result
        assert 'Tier i XP' in result, result
        assert '1-600' not in result, result
        assert 'Kilof' not in result or name=='Kilof', result
    return 4


if __name__=='__main__':
    print('OPISY NARZEDZI / KONTRAKT AST: '+str(run())+'/4 PASS')
