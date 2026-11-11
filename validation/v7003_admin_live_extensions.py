# -*- coding: utf-8 -*-
"""v70.00.3: isolated proof for shop opt-in, OLC >800 and safe diagnostics."""
from __future__ import annotations
import asyncio
import copy
import random
import tempfile
from pathlib import Path
from types import SimpleNamespace

from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from core import live_level_caps_v5200 as caps
from systems import admin_live_shop_progression_v7003 as shop
from systems.live_olc4_new_skills import validate_new_skills
from systems.live_olc6_skill_editor import parse_existing_skill_field, stage_existing_skill
from systems.live_olc4_fields import validate_extra
from systems.live_olc32_finale import validate as validate32, CATEGORIES
from systems.admin_live_diagnostics_v7003 import quest_diagnosis, skill_mechanics, boss_mechanics
from data.items import ITEMS
from data.crafting_recipes import CRAFT_RECIPES
from core.classes_skills import CLASS_SKILLS
from systems.infinite_equipment import parse_infinite_equipment_variant, shop_variant_price_v7003

async def checks():
    ok=0
    def check(value, label=''):
        nonlocal ok
        assert value,label
        ok+=1
    owner=Fake();db=owner.server.db
    guest=Fake(False,db)
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest.server.live_content_v1204=service
    original_caps=copy.deepcopy(caps.current())
    original_draft=copy.deepcopy(service.draft)
    original_active=copy.deepcopy(service.active)
    before_db=db.conn.total_changes
    before_rng=random.getstate()
    async def cmd(value,who=owner):
        await who.admin_command('live '+value)
        return who.messages[-1]
    old_shop_path=shop.CONFIG_PATH
    old_shop_cache=shop._settings
    with tempfile.TemporaryDirectory() as td:
        shop.CONFIG_PATH=Path(td)/'shop_progression_v7003.json'
        shop._settings=None
        try:
            check('POMOC 27' in await cmd('pomoc 27'))
            check('POMOC 28' in await cmd('pomoc 28'))
            for value in ('sklepy progresja','sklepy progresja status market',
                          'sklepy progresja ustaw market leather_vest 900 POTWIERDZAM',
                          'questy automaty diagnoza temple_rats', 'skill mechanika warrior_power_slash',
                          'boss mechaniki temple_rat'):
                check('Nieznana komenda' in await cmd(value,guest),value)
            check('ustawionych 0' in await cmd('sklepy progresja status'))
            check('WYLACZONA' in await cmd('sklepy progresja status market'))
            check('limity pozwalaja NIE' in await cmd('sklepy progresja prognoza market leather_vest 900'))
            check('Najpierw podnies' in await cmd('sklepy progresja ustaw market leather_vest 900 POTWIERDZAM'))
            check(not shop.CONFIG_PATH.exists())
            for error in ('sklepy progresja prognoza market healing_potion 900',
                          'sklepy progresja prognoza market uoss_black_rabite_unique_1 900',
                          'sklepy progresja prognoza forged_room leather_vest 900',
                          'sklepy progresja prognoza market leather_vest 0',
                          'sklepy progresja prognoza market leather_vest -1',
                          'sklepy progresja prognoza market ../evil 900',
                          'sklepy progresja ustaw market leather_vest 900',
                          'sklepy progresja wylacz market'):
                check('ADMIN LIVE SKLEPY' in await cmd(error),error)
            # Editor truly respects owner caps, while DEFAULT 800 remains enforced.
            case={'class_name':next(iter(CLASS_SKILLS)),'name':'Test skill v7003 proof',
                  'desc':'Test', 'kind':'damage', 'unlock':900,'mana':0,
                  'cooldown':0,'scale':'strength','mult':1.0,'aliases':[]}
            try:validate_new_skills({'live_v7003_probe':case}, {})
            except ValueError:check(True)
            else:raise AssertionError('Default 800 incorrectly accepted 900')
            for axis in ('eq','bieglosc','profesje','narzedzia','gildia'):
                caps._state[axis]=1200
            check('limity pozwalaja TAK' in await cmd('sklepy progresja prognoza market leather_vest 900'))
            check(validate_new_skills({'live_v7003_probe':case}, {}) == 1)
            check(parse_existing_skill_field({'unlock':1,'kind':'damage','cooldown':2},'unlock','900')==900)
            check(parse_existing_skill_field({'kind':'damage','cooldown':2},'mechanic_cooldown','true') is True)
            check(parse_existing_skill_field({'kind':'damage','cooldown':2},'mechanic_cooldown','false') is False)
            for blocked in ({'kind':'damage','cooldown':0}, {'kind':'heal','cooldown':4},
                            {'kind':'damage','cooldown':4,'mec_authored':True}):
                try:parse_existing_skill_field(blocked,'mechanic_cooldown','true')
                except ValueError:check(True)
                else:raise AssertionError('Unsafe skill cooldown allowed')
            skill_draft=copy.deepcopy(service.draft)
            stage_existing_skill(skill_draft,'warrior_power_slash','cooldown','5')
            stage_existing_skill(skill_draft,'warrior_power_slash','mechanic_cooldown','true')
            check(skill_draft['skill_edits']['warrior_power_slash']['mechanic_cooldown'] is True)
            check('1 edycji skilli' in service.validate(skill_draft))
            valid_item=next(k for k,v in ITEMS.items() if 'required_level' in v)
            check(validate_extra('item_edits',valid_item,'required_level',950,service.draft,set(),set()) is True)
            temp_draft=copy.deepcopy(service.draft)
            temp_draft['recipes']['live_v7003_recipe']={'min_tool_level':1}
            check(validate_extra('recipe_edits','live_v7003_recipe','min_tool_level',950,temp_draft,set(),set()) is True)
            guild_payload={key:{} for key in CATEGORIES}
            guild_payload['guilds']={'global':{'milestones':[{'level':999,'bonus_percent':2}]}}
            check(validate32(guild_payload,payload=service.draft) is True)
            check('SKLEP ZAPISANO' in await cmd('sklepy progresja ustaw market leather_vest 900 POTWIERDZAM'))
            check(shop.CONFIG_PATH.exists())
            check(shop.current()['market']=={'item':'leather_vest','stage':900})
            offer=shop.append_progression_offer('market',['healing_potion','leather_vest'])
            check(len(offer)==3)
            extra=offer[-1]
            check(extra=='deepq_shop_r_r30_leather_vest')
            check(extra in ITEMS and ITEMS[extra].get('shop_tier_v7003') is True)
            check(ITEMS[extra].get('price')>ITEMS['leather_vest'].get('price'))
            check(ITEMS[extra]['currency']=='silver')
            check(ITEMS[extra]['price']==shop_variant_price_v7003('leather_vest',30))
            from player.session_mixins.shops_teachers import SessionShopsTeachersMixin
            active=SessionShopsTeachersMixin.current_shop_offers(SimpleNamespace(
                character=SimpleNamespace(room_id='market')))
            check(active[-1]==extra and 'leather_vest' in active)
            check(parse_infinite_equipment_variant(extra)['source']=='shop')
            check(shop.append_progression_offer('market',offer)==offer)
            check(shop.append_progression_offer('inn',['healing_potion'])==['healing_potion'])
            shop._settings=None
            check(shop.current()['market']['stage']==900) # restart-like fresh config read
            caps._state['eq']=800
            check(shop.append_progression_offer('market',['leather_vest'])==['leather_vest'])
            check('widoczna NIE' in shop.describe('market'))
            caps._state['eq']=1200
            check(shop.append_progression_offer('market',['leather_vest'])[-1]==extra)
            check('wylaczono' in await cmd('sklepy progresja wylacz market POTWIERDZAM'))
            check(shop.append_progression_offer('market',['leather_vest'])==['leather_vest'])
            check(shop.current()=={})
            check('nie ma' not in (await cmd('questy automaty diagnoza toren_ore_samples_v0929')).lower())
            check('QUEST DIAGNOZA' in quest_diagnosis(service,'toren_ore_samples_v0929'))
            check('SKILL MECHANIKA' in skill_mechanics(service,'warrior_power_slash'))
            check('BOSS MECHANIKI' in boss_mechanics(service,'temple_rat'))
            check('QUEST DIAGNOZA' in await cmd('questy automaty diagnoza toren_ore_samples_v0929'))
            check('SKILL MECHANIKA' in await cmd('skill mechanika warrior_power_slash'))
            check('BOSS MECHANIKI' in await cmd('boss mechaniki temple_rat'))
            for bad in ('questy automaty diagnoza missing_v7003',
                        'skill mechanika missing_v7003',
                        'boss mechaniki missing_v7003'):
                check('ADMIN LIVE DIAGNOZA V70.00.3:' in await cmd(bad))
            # World/character data strictly untouched by the operator tools.
            check(service.draft==original_draft)
            check(service.active==original_active)
            check(db.conn.total_changes==before_db)
            check(random.getstate()==before_rng)
            check(not db.logged)
        finally:
            caps._state.clear();caps._state.update(original_caps)
            shop.CONFIG_PATH=old_shop_path
            shop._settings=old_shop_cache
            db.conn.close()
    return ok

if __name__=='__main__':
    print('V70.00.3 ADMIN LIVE:',asyncio.run(checks()),'PASS')
