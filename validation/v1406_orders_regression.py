# -*- coding: utf-8 -*-
"""v1.40.6: deterministic reward, market-floor and offer regressions."""
from types import SimpleNamespace


def run_orders_regression_v1406():
    from systems.profession_order_rewards_v1406 import balanced_order_reward_v1406
    from core.progression_resources import v0190_quest_currency_reward
    from systems import economy4_v1360 as eco
    from player.session_mixins.crafting_orders import (
        SessionCraftingOrdersV0600Mixin, CRAFTING_ORDER_NPCS_V0600,
    )
    checks=0
    def verify(condition, message):
        nonlocal checks
        checks+=1
        if not condition:raise AssertionError(message)
    # Fixed non-regressive samples: no single-step fast XP adjustment.
    for stage in (1,100,200,400,600,799):
        for tier in (1,2,3):
            for kind in ('gather','action'):
                recipe={'order_kind':kind,'order_tier':tier,'order_reward_level':stage,
                        'profession_xp':max(20,stage*3),'tool_xp':max(15,stage*2)}
                item={'order_kind':kind,'order_tier':tier}
                qty=5+tier*5
                coins,pxp,txp=balanced_order_reward_v1406(recipe,qty,item,stage)
                old=max(50,v0190_quest_currency_reward({'min_profession_level':stage,'needed':qty,'repeatable':True}))
                verify(coins >= old*3, f'no wage premium {stage} {kind} {tier}')
                verify(coins>=qty*(300+stage//2 if kind=='gather' else 500+stage),'too low per-unit premium')
                verify(pxp>=max(25,recipe['profession_xp']*qty//2)*2,'low profession XP')
                verify(txp>=max(15,recipe['tool_xp']*qty//3)*2,'low tool XP')
                verify(coins < 1_000_000_000_001,'contract bounded')
    # Product market floor: seller earns at least double authored product sale,
    # and material cost per output counts batch yield correctly.
    catalog={'ore':{'sell_silver':400},'gem':{'sell_gold':300}}
    rec={'min_profession_level':100,'ingredients':{'ore':5},'quantity':2,'profession_xp':100,'tool_xp':90}
    high=balanced_order_reward_v1406(rec,8,{'sell_gold':500},100,item_catalog=catalog)
    verify(high[0]>=8*500*100*2,'product selling is better than an order')
    crafted=balanced_order_reward_v1406(rec,8,{},100,item_catalog=catalog)
    verify(crafted[0]>=8*5*400,'ingredients not covered')
    verify(balanced_order_reward_v1406(rec,9,{},100,item_catalog=catalog)[0]>=crafted[0],'quantity reduces price')
    verify(balanced_order_reward_v1406(rec,8,{},100,item_catalog=catalog)==crafted,'not deterministic')
    # Every guild/kingdom quote exactly matches its settlement formula.
    now=12345678
    for code,name,ingredients,quoted in eco.order_quotes(now=now):
        cost=sum(q*eco._item_value(item) for item,q in ingredients.items())
        verify(quoted==eco.order_reward_v1406(code,now=now),f'quote mismatch {code}')
        verify(quoted>=min(eco.demand(code,now=now),125)*cost*3//100,f'underpaid trade order {code}')
    # All 14 job categories produce three meaningful offers, not just smithing.
    class FakeDB:
        def profession(self,account_id,profession):return {'level':600}
        @staticmethod
        def crafting_order_completion_key_v0700(cycle,npc,output,qty):return f'{cycle}:{npc}:{output}:{qty}'
    class FakeSession(SessionCraftingOrdersV0600Mixin):
        def __init__(self):
            self.account_id=1
            self.server=SimpleNamespace(db=FakeDB())
        def crafting_order_cycle_v0600(self):return 55555
    test=FakeSession()
    verify(len(CRAFTING_ORDER_NPCS_V0600)==14,'not all 14 professions covered')
    for npc_id,spec in CRAFTING_ORDER_NPCS_V0600.items():
        offers=test.crafting_order_offers_v0600(npc_id)
        verify(bool(offers),f'no offers for {npc_id}')
        verify(len(offers)<=3,f'too many {npc_id}')
        verify(all(x['reward_coins']>=150 for x in offers),f'poor reward {npc_id}')
        verify(all(x['reward_profession_xp']>0 and x['reward_tool_xp']>0 for x in offers),f'poor XP {npc_id}')
        verify(all(x['profession']==spec['profession'] for x in offers),f'wrong profession {npc_id}')
        verify(len({x['item_id'] for x in offers})==len(offers),f'duplicated offers {npc_id}')
    return {'checks':checks,'professions':len(CRAFTING_ORDER_NPCS_V0600)}
