# -*- coding: utf-8 -*-
"""Tests for actual v115 material registration, acquisition and recipe usability."""
import asyncio
import inspect
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from core.classes_skills import ROOMS
from systems.v115.high_level_world import REGIONS
from systems.v115.profession_sites import has_site
from systems.v115.playable_regions import WIDTH, HEIGHT, room_id
from systems.v115.regional_crafting import MATERIALS, material_for, grant_after_native_gather, register_items, register_recipes
from systems.equipment_crafting import CRAFT_RECIPES,COOK_RECIPES,ALCHEMY_RECIPES
from data.items import ITEMS


def site_room(index,kind):
    region=REGIONS[index-1]
    return next(room_id(region.key,x,y) for y in range(HEIGHT) for x in range(WIDTH)
                if has_site(room_id(region.key,x,y),ROOMS[room_id(region.key,x,y)],kind))

class RegionalCrafting(unittest.TestCase):
    def test_materials_all_four_professions_in_30_realms(self):
        self.assertEqual(len(MATERIALS),4)
        for idx in range(1,31):
            for kind in MATERIALS:
                rid=site_room(idx,kind)
                row=ROOMS[rid]
                tier=0 if idx<=15 else 1
                req=800 if tier==0 else 1600
                self.assertEqual(material_for(rid,row,kind,req,0),MATERIALS[kind][tier])
                self.assertIsNone(material_for(rid,row,kind,req-1,0))
                self.assertIsNone(material_for(rid,row,kind,req,0.25))
                self.assertIsNone(material_for(rid,row,'invalid',req,0))
        self.assertIsNone(material_for('graveyard',ROOMS['graveyard'],'mining',2000,0))

    def test_all_items_and_recipe_ingredients_existing(self):
        ids={v for variants in MATERIALS.values() for v in variants}
        self.assertEqual(len(ids),8)
        for ident in ids:
            self.assertEqual(ITEMS[ident]['type'],'craft_material')
        seen=set()
        for catalog in (CRAFT_RECIPES,COOK_RECIPES,ALCHEMY_RECIPES):
            for key, recipe in catalog.items():
                if not key.startswith('v115_'): continue
                seen.add(key)
                self.assertIn(recipe['output'],ITEMS)
                self.assertTrue(recipe['stations'])
                for station in recipe['stations']: self.assertIn(station,ROOMS)
                for ingredient in recipe['ingredients']: self.assertIn(ingredient,ITEMS)
                self.assertIn(recipe['min_profession_level'],(800,1600))
        self.assertEqual(len(seen),8)
        self.assertEqual(set(ITEMS[i]['type'] for i in seen),{'armor','consumable','craft_material'})

    def test_registration_idempotent_and_no_mutation_of_old(self):
        before={key:ITEMS[key].copy() for key in ('iron_ore','fishing_rod','herbalist_sickle')}
        size=len(ITEMS)
        register_items(ITEMS)
        register_recipes(CRAFT_RECIPES,COOK_RECIPES,ALCHEMY_RECIPES)
        self.assertEqual(size,len(ITEMS))
        self.assertEqual(before,{key:ITEMS[key] for key in before})

    def test_successful_gather_uses_real_craftbox_without_audio(self):
        from storage.database import Database
        rid=site_room(1,'mining')
        with tempfile.TemporaryDirectory(prefix='soulbound_v115_craft_') as td:
            db=Database(str(Path(td)/'test.sqlite'))
            try:
                account=db.create_account('TestV115Materials','LongPasswordForSafeTest115!')
                sent=[]
                async def send(s): sent.append(s)
                actor=SimpleNamespace(character=SimpleNamespace(room_id=rid),account_id=account,
                    server=SimpleNamespace(db=db),send=send,profession_level_for_tool=lambda kind:800)
                with patch('systems.v115.regional_crafting.random.random',return_value=0):
                    self.assertEqual(asyncio.run(grant_after_native_gather(actor,'mining')),'v115_aether_ore')
                self.assertEqual(db.storage_qty(account,'craftbox','v115_aether_ore'),1)
                self.assertEqual(db.item_qty(account,'v115_aether_ore'),0)
                self.assertEqual(len(sent),1)
                with patch('systems.v115.regional_crafting.random.random',return_value=.99):
                    self.assertIsNone(asyncio.run(grant_after_native_gather(actor,'mining')))
                self.assertEqual(db.storage_qty(account,'craftbox','v115_aether_ore'),1)
                db.conn.close()
                db=Database(str(Path(td)/'test.sqlite'))
                self.assertEqual(db.storage_qty(account,'craftbox','v115_aether_ore'),1)
                self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:
                db.conn.close()

    def test_real_recipe_consumes_craftbox_ingredients(self):
        from storage.database import Database
        from player.session_mixins.crafting import SessionCraftingMixin
        from player.session_mixins.sales_parts_v109.resources import SalesResourcesV109Mixin
        class Actor(SessionCraftingMixin, SalesResourcesV109Mixin):
            pass
        with tempfile.TemporaryDirectory(prefix='soulbound_v115_recipe_') as td:
            db=Database(str(Path(td)/'craft.sqlite'))
            try:
                acc=db.create_account('TestV115Ingredients','LongPasswordForSafeTest115!')
                actor=Actor()
                actor.account_id=acc
                actor.server=SimpleNamespace(db=db)
                recipe=CRAFT_RECIPES['v115_soul_plank']
                self.assertEqual(recipe['ingredients'],{'v115_soulwood':2})
                db.add_item(acc,'v115_soulwood',3)
                self.assertEqual(actor.recipe_container_for_item('v115_soulwood'),'craftbox')
                self.assertEqual(actor.available_recipe_item('v115_soulwood'),3)
                self.assertTrue(actor.consume_recipe_item('v115_soulwood',2))
                self.assertEqual(actor.available_recipe_item('v115_soulwood'),1)
                self.assertEqual(db.storage_qty(acc,'craftbox','v115_soulwood'),1)
                db.add_item(acc,recipe['output'],1)
                self.assertEqual(db.storage_qty(acc,'craftbox','v115_soul_plank'),1)
                db.conn.close()
                db=Database(str(Path(td)/'craft.sqlite'))
                self.assertEqual(db.storage_qty(acc,'craftbox','v115_soul_plank'),1)
                self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:
                db.conn.close()

    def test_existing_tools_only_and_no_sound_import(self):
        from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
        from systems.v115 import regional_crafting
        src=inspect.getsource(regional_crafting)
        self.assertNotIn('sound_events',src)
        for name,kind in [('fish','fishing'),('mine','mining'),('woodcut','woodcutting'),('gather_herb','herbalism')]:
            body=inspect.getsource(getattr(SessionGatheringActionsMixin,name))
            self.assertIn(f'_v115_regional_material(self, "{kind}")',body)
            self.assertIn(f'_v115_has_site(self.character.room_id, ROOMS.get(self.character.room_id), "{kind}")',body)
        # Source of equipment/recipes does not invent a tool item.
        self.assertNotIn('"type":"tool"',src)

if __name__=='__main__': unittest.main()
