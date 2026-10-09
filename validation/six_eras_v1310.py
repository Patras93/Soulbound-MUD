# -*- coding: utf-8 -*-
"""Runtime integration tests for six eras and save compatibility."""
from __future__ import annotations
from systems.six_eras_v1310 import CAMPAIGNS, OCEAN_ISLANDS, ANCIENTS, ROLE_NAMES, OCEAN_NAMES, _room


def audit_six_eras_v1310(rooms,npcs,shops,mobs,spawns,quests,items):
    errors=[]; checks=0; sizes={}
    def assert_check(ok, label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    for slug,title,parent,direction,element,level,giver,boss_name,faction,loot,kind in CAMPAIGNS:
        prefix=f'v1310_{slug}_'
        expect={_room(slug,role) for role,_,_ in ROLE_NAMES}
        assert_check(rooms.get(parent,{}).get('exits',{}).get(direction)==_room(slug,'border'),f'{slug} entrance')
        seen=set();stack=[_room(slug,'border')]
        while stack:
            loc=stack.pop()
            if loc in seen:continue
            seen.add(loc)
            room=rooms.get(loc)
            assert_check(isinstance(room,dict),f'room {loc}')
            if room is None:continue
            for d,target in room.get('exits',{}).items():
                assert_check(target in rooms,f'{loc} exit {d}->{target}')
                rev={'north':'south','south':'north','east':'west','west':'east'}.get(d)
                if rev:assert_check(rooms.get(target,{}).get('exits',{}).get(rev)==loc,f'{loc} reverse exit {d}')
                if target in expect:stack.append(target)
        sizes[slug]=len(seen)
        assert_check(seen==expect,f'{slug} missing rooms')
        boss=f'v1310_{slug}_lord'
        assert_check(( _room(slug,'arena'),boss) in spawns,f'{slug} boss spawn')
        assert_check(mobs.get(boss,{}).get('boss_mechanic')=='elemental_overdrive',f'{slug} phases')
        assert_check(f'v1310_{slug}_token' in items,f'{slug} item')
        assert_check(quests.get(f'v1310_{slug}_quest',{}).get('target')==boss,f'{slug} quest')
        assert_check(quests.get(f'v1310_{slug}_triumph',{}).get('repeatable') is False,f'{slug} triumph')
        assert_check(any(n.get('name')==giver for n in npcs.values()),f'{slug} giver')
        assert_check(_room(slug,'market') in shops,f'{slug} market')
        from systems.mercenary_taverns import tavern_here
        assert_check(tavern_here(_room(slug,'tavern')),f'{slug} mercenary tavern')
        if kind=='empire':
            for role in ('gate','outpost'):
                assert_check((_room(slug,role),f'v1310_{slug}_{role}_guard') in spawns,f'{slug} garrison')
    hub='v1310_ocean_departure'
    assert_check(rooms.get('ocean_platform',{}).get('exits',{}).get('up')==hub,'ocean port')
    for slug,title,direction,element,level,giver,boss_name,loot in OCEAN_ISLANDS:
        assert_check(rooms[hub]['exits'].get(direction)==_room(slug,'shore'),f'{slug} route')
        for role,_,_ in OCEAN_NAMES:
            assert_check(_room(slug,role) in rooms,f'{slug} room {role}')
        assert_check((_room(slug,'boss'),f'v1310_{slug}_boss') in spawns,f'{slug} sea boss')
        assert_check(_room(slug,'market') in shops,f'{slug} sea shop')
        assert_check(quests.get(f'v1310_{slug}_quest',{}).get('target')==f'v1310_{slug}_boss',f'{slug} sea quest')
    for slug,name,parent,direction,element,level in ANCIENTS:
        assert_check(rooms.get(parent,{}).get('exits',{}).get(direction)==_room(slug,'sanctum'),f'{slug} route')
        assert_check((_room(slug,'sanctum'),f'v1310_{slug}_boss') in spawns,f'{slug} boss')
        assert_check(f'v1310_{slug}_heart' in items,f'{slug} drop')
        assert_check(f'v1310_{slug}_quest' in quests,f'{slug} quest')
    for i in range(1,6):
        q=quests.get(f'v1310_legacy_{i}',{})
        assert_check(bool(q),f'legacy quest {i}')
        assert_check(q.get('requires_quest')==(f'v1310_legacy_{i-1}' if i>1 else None),f'legacy chain {i}')
        assert_check(q.get('target') in mobs,f'legacy target {i}')
    from data.crafting_recipes import CRAFT_RECIPES
    for item_key in ('v1310_empire_medal','v1310_dimension_circlet',
                     'v1310_ocean_circlet','v1310_ancient_circlet'):
        recipe=CRAFT_RECIPES.get(item_key,{})
        assert_check(item_key in items,f'{item_key} artifact registered')
        assert_check(recipe.get('output')==item_key,f'{item_key} crafting output')
        for ingredient in recipe.get('ingredients',{}):
            assert_check(ingredient in items,f'{item_key} unknown ingredient {ingredient}')
    for kind,resource in (('ore','iron_ore'),('fish','salmon'),
                          ('wood','oak_log'),('herbs','chamomile')):
        quest=quests.get(f'v1310_caravan_{kind}',{})
        assert_check(quest.get('kind')=='collect_resource',f'caravan {kind} storage tracking')
        assert_check(quest.get('target')==resource and resource in items,f'caravan {kind} resource')
        assert_check(quest.get('repeat_cooldown')==21600,f'caravan {kind} cooldown')
    from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command
    from player.session import Session
    assert_check(COMMAND_REGISTRY.get('ery',('missing',))[0]=='show_six_eras_v1310','NVDA guide command')
    assert_check(resolve_session_command('wielkieery')=='ery','NVDA guide alias')
    assert_check(callable(getattr(Session,'show_six_eras_v1310',None)),'guide session method')
    assert_check('v1310_soul_legacy' in items,'legacy reward')
    assert_check(not items.get('v1310_soul_legacy',{}).get('price'),'legacy not vendor-tradeable')
    assert_check('core.generator_core' not in __import__('sys').modules,'old generator not imported')
    return {'checks':checks,'errors':errors,'error_count':len(errors),'rooms':sum(sizes.values())+len(OCEAN_ISLANDS)*len(OCEAN_NAMES)+1+len(ANCIENTS)}
