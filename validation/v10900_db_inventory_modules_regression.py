# -*- coding: utf-8 -*-
"""v109: mocna zgodnosc historii SQLite po rozdzieleniu. Bez produkcyjnej bazy."""
from __future__ import annotations
import ast
import hashlib
import inspect
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256='c022c843ef0e31fdeeddb0b6db2779b26dbfdeba2e850f100af596ca10de0e11'
# Metody w starym pliku musza pozostac ze wzgledu na historyczne kontrole zrodel.
RETAINED={"save_profession","save_tool","equip","add_item","total_items_across_storage_and_inventory","add_drop_history"}
MODULES={'bank_currency': ('ensure_bank',
                   'bank_balance',
                   'change_bank_currency',
                   'transfer_shared_currency',
                   'transfer_bank_v1225',
                   'bank_transfer_history_v1225'),
 'bank_items': ('bank_items',
                'bank_item_qty',
                'move_bank_equipment_v106',
                'add_bank_item',
                'remove_bank_item'),
 'crafting': ('_v104_crafting_ids',
              '_v104_crafting_quantity',
              'craft_item_atomic_v106',
              'consume_items_across_storage_and_inventory'),
 'enchant': ('equipment_enchant_v03053', 'set_equipment_enchant_v03053', 'equipment_enchants_v03053'),
 'equipment': ('equipment', 'equipped_item', 'unequip'),
 'forge': ('equipment_reforge',
           'save_equipment_reforge',
           'equipment_runes_v0925',
           'add_equipment_rune_v0925',
           'remove_equipment_rune_v0925',
           'equipment_upgrade_level_v03042',
           'set_equipment_upgrade_level_v03042',
           'clear_equipment_crafting_v0925',
           'transfer_equipment_crafting_v0925',
           'crafting_mastery_v03054',
           'add_crafting_mastery_action_v03054',
           'crafting_masteries_v03054'),
 'gems': ('socketed_gems', 'add_socketed_gem', 'clear_socketed_gems'),
 'hunters': ('hunter_state_v1225', 'hunter_accept_v1225', 'hunter_kill_v1225', 'hunter_claim_v1225'),
 'inventory': ('_persisted_dynamic_item_ids',
               'persisted_crafting_quality_item_ids_v0332',
               'persisted_infinite_equipment_item_ids_v11330',
               'inventory',
               'item_qty',
               'drop_history_rows',
               'remove_item',
               'transfer_inventory_item'),
 'mail': ('send_mail_attachment_v0614', 'claim_mail_attachment_v0614'),
 'professions': ('ensure_profession', 'profession'),
 'protection': ('inventory_is_protected_v1280', 'inventory_set_protected_v1280'),
 'shop_lots': ('record_shop_purchase_v1175',
               'shop_resale_total_v1175',
               '_consume_shop_purchase_lots_v1175',
               'bank_purchase_lot_key_v1175',
               'move_shop_purchase_basis_v1175'),
 'storage': ('storage_rows',
             'storage_qty',
             'move_storage_equipment_v106',
             'add_storage_item',
             'remove_storage_item'),
 'tools': ('ensure_tool', 'tool')}

def run():
    checks=0
    f=ROOT/'storage/db_inventory.py'
    t=ast.parse(f.read_text('utf8'))
    c=next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name=='DatabaseInventoryMixin')
    found={x.name:x for x in c.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert set(found)==RETAINED, ('historyczne metody do zachowania',set(found))
    checks+=len(found)
    for group,names in MODULES.items():
        t=ast.parse((ROOT/f'storage/db_inventory_parts_v109/{group}.py').read_text('utf8'))
        c=next(x for x in t.body if isinstance(x,ast.ClassDef))
        methods={x.name:x for x in c.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(methods)==set(names),(group,set(methods)^set(names))
        assert not set(methods)&set(found),group
        found.update(methods)
        checks+=len(methods)+1
    assert len(found)==72
    raw='\n'.join(n+'='+ast.dump(found[n],include_attributes=False) for n in sorted(found))
    assert hashlib.sha256(raw.encode()).hexdigest()==EXPECTED_AST_SHA256
    checks+=72
    from storage.db_inventory import DatabaseInventoryMixin, is_craft_material_storage_item
    from storage.database import Database
    assert issubclass(Database,DatabaseInventoryMixin);checks+=1
    assert DatabaseInventoryMixin.__module__=='storage.db_inventory';checks+=1
    assert callable(is_craft_material_storage_item);checks+=1
    assert all(callable(getattr(DatabaseInventoryMixin,n,None)) for n in found);checks+=72
    assert DatabaseInventoryMixin._v104_crafting_ids(['a','a','b'])==('a','b');checks+=1
    assert DatabaseInventoryMixin._v104_crafting_quantity(3)==3;checks+=1
    assert len([n for n in DatabaseInventoryMixin.__mro__ if n.__name__.endswith('V109Mixin')])==len(MODULES);checks+=1
    src=(ROOT/'storage/db_inventory.py').read_text('utf8')
    for token in ('def add_item(self, account_id, item_id, qty=1, commit=True):',
                  'def equip(self, account_id, slot, item_id, commit=True):',
                  'def save_profession(', 'def save_tool(', 'record_activity_v0560', '"drop"'):
        assert token in src,token
        checks+=1
    # Izolowane transakcje na bazie pamieciowej: brak zapisu danych graczy.
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER)')
    class DBTest(DatabaseInventoryMixin):
        def __init__(self,conn):self.conn=conn
        def master_account_for_character(self,account_id):return account_id
    db=DBTest(conn)
    assert db.ensure_bank(42)==42;checks+=1
    assert dict(db.bank_balance(42))=={'silver':0,'gold':0,'mithril':0};checks+=1
    assert db.change_bank_currency(42,'silver',50) is True;checks+=1
    assert db.bank_balance(42)['silver']==50;checks+=1
    assert db.change_bank_currency(42,'silver',-51) is False;checks+=1
    assert db.bank_balance(42)['silver']==50;checks+=1
    conn.execute('BEGIN')
    assert db.change_bank_currency(42,'silver',20) is True;checks+=1
    assert conn.in_transaction;checks+=1
    assert db.bank_balance(42)['silver']==70;checks+=1
    conn.rollback()
    assert db.bank_balance(42)['silver']==50;checks+=1
    conn.execute('BEGIN')
    db.ensure_bank(77)
    assert conn.in_transaction;checks+=1
    conn.rollback()
    assert conn.execute('SELECT 1 FROM bank_balances WHERE account_id=77').fetchone() is None;checks+=1
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
    conn.close()
    print(f'V109 SQLITE INVENTORY MODULAR: {checks} PASS; 72 AST=v108; SQLite rollback in memory')
    return checks

if __name__=='__main__': run()
