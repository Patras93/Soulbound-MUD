# -*- coding: utf-8 -*-
"""v110: physical profession tool purchase-path contract without live DB."""
from __future__ import annotations
import os,sys,tempfile,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))

def main():
    from core.v11000_archetypes import PROFESSION_SPECS
    from systems.v10700_activation import enabled as v107_enabled
    with tempfile.TemporaryDirectory(prefix='sb110_profession_tools_') as directory:
        os.environ.update(SOULBOUND_V107_STAGING='1', SOULBOUND_V109_STAGING='1',
                          SOULBOUND_V110_STAGING='1', SOULBOUND_HOST='127.0.0.1',
                          SOULBOUND_DB=str(Path(directory)/'test.sqlite'))
        with socket.socket() as s:
            s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        os.environ['SOULBOUND_PORT']=str(port)
        assert v107_enabled(), 'historical v107 tool progression not enabled in staging'
        from systems.v11000_activation import enabled
        assert enabled(), 'v110 tooling must only be installed in authorised test context'
        from systems.v11000_profession_work import tool_item_id, product_id
        from data.items import ITEMS
        from data.shops import SHOPS
        from core.mines_threat import is_character_bound_item
        from systems.new_professions import PROFESSIONS
        assert len(PROFESSION_SPECS)==8
        assert len(PROFESSIONS)==8
        assert len(set(SHOPS['market']))==len(SHOPS['market'])
        for index,(name,kind,label,ingredient) in enumerate(PROFESSION_SPECS):
            item=tool_item_id(index)
            assert item in ITEMS and item in SHOPS['market'], (name,item)
            obj=ITEMS[item]
            assert obj['type']=='tool' and obj['tool_type']==kind, name
            assert obj['name']==label and obj['currency']=='silver' and obj['price']==1200,name
            assert is_character_bound_item(item),name
            assert product_id(index) not in SHOPS['market'],name
        for name,(kind,item_id,label) in PROFESSIONS.items():
            assert item_id in ITEMS and ITEMS[item_id]['type']=='tool' and is_character_bound_item(item_id),name
        # Historical v107 tool XP is virtual, not a physical new purchase:
        # preserve those profiles and existing player progress on v109 -> v110.
        from core.v10700_new_archetypes import PROFESSION_SPECS as V107
        assert len(V107)==8 and len({row[1] for row in V107})==8
        print('V110 PROFESSION TOOLS PASS: 8/8 new named, purchasable, bound items; '
              '8/8 v6 physical tools; 8/8 v107 virtual profiles preserved',flush=True)

if __name__=='__main__': main()
