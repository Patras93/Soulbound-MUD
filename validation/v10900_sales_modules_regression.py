# -*- coding: utf-8 -*-
"""v109: identyczny kod 30 metod sprzedaży v108, rozdzielony na małe moduły.

Test nie zapisuje do dysku graczy i nie uruchamia produkcyjnego serwera.
"""
from __future__ import annotations
import ast
import hashlib
import inspect
from pathlib import Path
from types import SimpleNamespace
from player.session_mixins.sales import SessionSalesMixin, V11314_ARMOR_RESALE_QUEST_FRACTION
from player.session_mixins.sales_parts_v109 import (
    SalesPricingV109Mixin,SalesMarketV109Mixin,SalesProfessionExpV109Mixin,
    SalesBulkV109Mixin,SalesEquipmentV109Mixin,SalesResourcesV109Mixin)

ROOT=Path(__file__).resolve().parents[1]
PARTS=('pricing','market','profession_exp','bulk','equipment','resources')
CLASSES=(SalesPricingV109Mixin,SalesMarketV109Mixin,SalesProfessionExpV109Mixin,
         SalesBulkV109Mixin,SalesEquipmentV109Mixin,SalesResourcesV109Mixin)
V108_METHODS_SHA256='7bd35af81603e5a6faa807e8741707167ffbbd4f023a0377b0acf30e152fade3'
EXPECTED_NAMES=30


def run():
    checks=0
    source=ROOT/'player/session_mixins/sales.py'
    old_tree=ast.parse(source.read_text('utf-8'))
    facade=next(n for n in old_tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionSalesMixin')
    assert not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in facade.body)
    checks+=1
    assert SessionSalesMixin.__bases__==CLASSES
    checks+=1
    pieces=[];all_names=[]
    for part,cls in zip(PARTS,CLASSES):
        path=ROOT/'player/session_mixins/sales_parts_v109'/f'{part}.py'
        assert path.is_file() and path.stat().st_size<30000,part
        tree=ast.parse(path.read_text('utf-8'))
        declared=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        assert declared.name==cls.__name__,part
        members=[n for n in declared.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        assert set(n.name for n in members)==set(vars(cls)).intersection(n.name for n in members)
        assert len(members)>0,part
        for method in members:
            target=getattr(SessionSalesMixin,method.name)
            assert target is getattr(cls,method.name)
            assert inspect.signature(target)==inspect.signature(getattr(cls,method.name))
            all_names.append(method.name);pieces.append(method)
            checks+=2
        checks+=4
    assert len(all_names)==len(set(all_names))==EXPECTED_NAMES
    checks+=1
    digest=hashlib.sha256('\n'.join(ast.dump(m,include_attributes=False)
        for m in sorted(pieces,key=lambda m:m.name)).encode('utf-8')).hexdigest()
    assert digest==V108_METHODS_SHA256,('Zmiana kodu sprzedaży względem v108',digest)
    checks+=1
    assert V11314_ARMOR_RESALE_QUEST_FRACTION['common']==0.025
    checks+=1

    s=SessionSalesMixin()
    from systems.equipment_crafting import SHOPS
    room=sorted(SHOPS)[0]
    s.character=SimpleNamespace(room_id=room)
    assert s.generic_item_sale_allowed_here()
    checks+=1
    s.character.room_id='nieistniejacy_sklep'
    assert not s.generic_item_sale_allowed_here()
    checks+=1
    s.character.room_id='market'
    assert s.market_buyer_rejects_item('probe',{'type':'resource'})
    assert not s.market_buyer_rejects_item('probe',{'type':'armor'})
    checks+=2
    assert s.resource_sale_buyer_text('net') and s.resource_sale_location_text('bag')
    checks+=2
    assert s.profession_sale_definition('net')==('Wędkarstwo','fishing')
    assert s.profession_sale_definition('nieznany') is None
    checks+=2
    for text,expected in [('net','net'),('siatka','net'),('sakwa','bag'),
         ('drewno','woodpile'),('ziola','herbbag'),('all','inventory'),
         ('wszystkie przedmioty','inventory'),('nic','')]:
        assert (s.normalize_bulk_sell_target(text) or '')==expected,(text,expected)
        checks+=1
    for source_slot,target_slot in [('ring1','ring'),('ring2','ring'),('charm1','charm'),('helm','helm')]:
        assert s.logical_sell_equipment_slot(source_slot)==target_slot
        checks+=1
    assert s.blacksmith_crafted_sale_cap_v0341('missing',{}) is None
    checks+=1
    assert s.parse_numbered_inventory_query('helm')==(None,'helm')
    checks+=1

    print(f'V109 SALES MODULAR: {checks} PASS; {EXPECTED_NAMES} metod zgodnych AST z v108; '\
          'bez zmian zasad sprzedazy',flush=True)
    return checks

if __name__=='__main__':run()
