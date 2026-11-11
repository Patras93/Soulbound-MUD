# -*- coding: utf-8 -*-
"""Current-only runtime smoke: previous release activators are unavailable."""
from __future__ import annotations
import os,socket,sys,tempfile,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Direct execution of validation/*.py puts that folder before the project,
# where validation/events.py shadows the real events/ package. Project root
# must always come first, even if PYTHONPATH already contains it.
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix='sb112_standalone_') as td:
        for key in list(os.environ):
            if key.startswith('SOULBOUND_') and key.endswith(('_STAGING', '_PREDEPLOY')):
                os.environ.pop(key, None)
        for key in ('SOULBOUND_DB','SOULBOUND_HOST','SOULBOUND_PORT','PORT','RAILWAY_TCP_APPLICATION_PORT'):
            os.environ.pop(key,None)
        os.environ.update(SOULBOUND_DB=str(Path(td)/'new.sqlite'),
            SOULBOUND_HOST='127.0.0.1',SOULBOUND_V112_STAGING='1')
        if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()=='112.00.0':
            os.environ['SOULBOUND_V112_STAGING']='1'
        with socket.socket() as preflight:
            preflight.bind(('127.0.0.1',0))
            localport=preflight.getsockname()[1]
        os.environ['SOULBOUND_PORT']=str(localport)
        t=time.monotonic()
        # Refuse to load earlier release activation code even if it is present
        # in the full source candidate. Only the current contract may authorize.
        import importlib.abc
        forbidden = {
            'systems.v10700_activation', 'systems.v10800_activation',
            'systems.v10900_activation', 'systems.v10900_staging_guard',
            'systems.v11000_activation', 'systems.v11100_holiday_activation',
            'systems.v10800_predeploy_isolation',
        }
        class NoPriorRelease(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname in forbidden:
                    raise ImportError('Previous release dependency: ' + fullname)
                return None
        sys.meta_path.insert(0, NoPriorRelease())
        assert not (forbidden & set(sys.modules)), forbidden & set(sys.modules)
        # Intentionally preload historical catalogue: native_runtime may reload
        # its module. All new v110 races must still be visible in character UI.
        from core.classes_skills import RACES as prebootstrap_races
        assert len(prebootstrap_races)==22
        from core.classes_skills import CLASSES as prebootstrap_classes
        assert len(prebootstrap_classes)==22
        from core.progression_resources import class_type_for_name
        from core.archetypes.chaos import CLASS_SPECS as v107_classes
        from core.archetypes.expansion import CLASS_SPECS as v110_classes
        assert class_type_for_name('Magitek')=='magic'
        assert all(class_type_for_name(spec[0])==spec[1]
                   for spec in (*v107_classes,*v110_classes))
        import server
        import core
        # Only the candidate ZIP carries release-only audits. In the
        # production subset they must not be imported or required at boot.
        if not (ROOT/'admin/audits.py').exists():
            assert 'admin.audits' not in sys.modules
            assert 'admin.audit_rules_v406' not in sys.modules
            assert 'admin.v410_release_audits' not in sys.modules
            assert 'systems.full_systems_audit_v03062' not in sys.modules
            assert 'world.runtime_gameplay_finalize' in sys.modules
        from core.classes_skills import CLASSES,RACES
        from player.session_mixins.io_auth_character import RACES as creator_races,CLASSES as creator_classes
        assert (len(server.RACES),len(server.CLASSES))==(38,38)
        assert (len(creator_races),len(creator_classes))==(38,38)
        assert core.classes_skills is sys.modules['core.classes_skills']
        assert server.RACES is RACES is creator_races
        from data.items import ITEMS
        from server.mud_server import MudServer
        assert len(CLASSES)==38 and len(RACES)==38,(len(CLASSES),len(RACES))
        from systems.equipment_crafting import (
            GUILD_CLASS_QUEST_POOLS, guild_class_quest_pool_for_mastery_v11342,
        )
        playable={c[0] for c in CLASSES}
        assert set(GUILD_CLASS_QUEST_POOLS)==playable, 'missing guild quests for a playable class'
        required_activities={'kill','boss','explore','gather','craft'}
        assert all(len(pool)==5 and {row[5] for row in pool}==required_activities
                   and len({row[0] for row in pool})==5
                   for pool in GUILD_CLASS_QUEST_POOLS.values())
        assert all(len(guild_class_quest_pool_for_mastery_v11342(name,level))==5
                   for name in playable for level in (1,100,300,600))
        # Real, generated Tier 400 pieces must distinguish every playable
        # class; names/IDs alone do not count as a distinct EQ profile.
        from world.runtime_progression import class_equipment_identity_audit_v03016
        eq_identity=class_equipment_identity_audit_v03016()
        assert eq_identity['class_count']==38 and eq_identity['error_count']==0, eq_identity
        assert eq_identity['unique_profile_signatures']==38, eq_identity
        # Class shops must work for all 38, not only old 22.  The newer
        # teachers double as vendors without creating spare NPCs or rooms.
        from systems.items_resources import CLASS_SHOP_CLASSES_BY_ROOM
        from systems.equipment_crafting import SHOPS, SHOP_SELLERS
        assert len(CLASS_SHOP_CLASSES_BY_ROOM)==38
        assert server.CLASS_SHOP_AUDIT_V03036['error_count']==0,server.CLASS_SHOP_AUDIT_V03036
        assert server.CLASS_SHOP_AUDIT_V03036['class_shops_checked']==38
        from network.protocol_gameplay_utils import normalize_lookup_text
        for name in ('Magitek',)+(tuple(spec[0] for spec in (*v107_classes,*v110_classes))):
            room=server.CLASS_SHOP_ROOM_BY_CLASS_V03036[name]
            seller_id=SHOP_SELLERS.get(room)
            seller=server.NPCS.get(seller_id,{})
            assert seller.get('teacher_class')==name and seller.get('shopkeeper'),name
            assert server.CLASS_SHOP_CLASSES_BY_ROOM[room]==[name],name
            assert SHOPS[room]==list(server.CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER[name][1]),name
            assert server.GUIDE_DESTINATION_ALIASES[normalize_lookup_text('eq '+name)]==room
        # Newly created teacher rooms must retain the terrain generator level.
        for rid,r in server.ROOMS.items():
            if r.get('npc_private_room_v03012'):
                assert int(r.get('generator_level',0))>=int(r.get('recommended_mastery',0)),rid
        # Equipment generated BEFORE server appends the successor classes must
        # still use their authored MAGIC vs PHYSICAL power channels.
        from systems.equipment_crafting import CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
        for name in ('Magitek',)+(tuple(spec[0] for spec in (*v107_classes,*v110_classes))):
            ids=CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER[name][100]
            item=next(ITEMS[item_id] for item_id in ids
                      if ITEMS[item_id].get('slot')=='hands'
                      and ITEMS[item_id].get('class_equipment_style')==2)
            if class_type_for_name(name)=='magic':
                assert item['magic_attack']>0 and item['attack']==0, name
            else:
                assert item['attack']>0 and item['magic_attack']==0, name
        # 8 new classes receive the same 9-point starting bonus as original.
        from core.archetypes.expansion import CLASS_SPECS,RACE_SPECS,PROFESSION_SPECS
        from core.classes_skills import CLASS_STARTING_STAT_BONUSES
        from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
        from core.profession_timing import TOOL_ACTION_BASE_SECONDS,TOOL_ACTION_MIN_SECONDS
        assert len(CLASS_SPECS)==len(RACE_SPECS)==len(PROFESSION_SPECS)==8
        assert all(sum(CLASS_STARTING_STAT_BONUSES[c[0]].values())==9 for c in CLASS_SPECS)
        assert all(sum(r[3])==50 for r in RACE_SPECS)
        assert len(TOOL_PROFESSION_MAP)==len(TOOL_ACTION_BASE_SECONDS)==len(TOOL_ACTION_MIN_SECONDS)==38
        assert len(server.QUESTS)==15136,len(server.QUESTS)
        assert sum(1 for q in server.QUESTS if q.startswith('v11100_holiday_'))==36
        # Do not let the frozen v104 report mask missing renewals in
        # any post-v107 quest; all explicit cooldowns must be positive.
        from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
        expected_renewals={'v10700_':1400,'v10900_':240,'v11000_':444}
        for prefix,minimum in expected_renewals.items():
            active=[q for qid,q in server.QUESTS.items()
                    if qid.startswith(prefix) and q.get('repeatable')]
            assert len(active)>=minimum,(prefix,len(active))
            assert all(q.get('repeat_cooldown') is not None
                       and int(q['repeat_cooldown'])>0 for q in active),prefix
        assert all(int(q['repeat_cooldown'])==QUEST_REPEAT_COOLDOWN_SECONDS
                   for qid,q in server.QUESTS.items()
                   if qid.startswith('v11000_realm_') and q.get('repeatable'))
        assert all('v11000_prof_tool_'+str(i) in ITEMS and 'v11000_prof_product_'+str(i) in ITEMS
                   for i in range(1,9))
        assert all('v11000_prof_tool_'+str(i) in server.SHOPS.get('market',[])
                   and ITEMS['v11000_prof_tool_'+str(i)]['price']==1200
                   and ITEMS['v11000_prof_tool_'+str(i)]['bind_on_pickup']
                   for i in range(1,9))
        # Explicit mixins must see the same final rules as the assembled game.
        # This catches a stale early import that legacy synchronization used to
        # replace after later modules loaded.
        from player.session_mixins import rest_mana, session_runtime_state, tech_crafting, milestone, quest_turnin
        comparisons = (
            (quest_turnin, ('ITEMS', 'NPCS', 'QUESTS', 'QUEST_REPEAT_COOLDOWN_SECONDS')),
            (rest_mana, ('REST_REGEN_PERCENT', 'REST_TICK_SECONDS',
                         'normalize_lookup_text', 'superboss_healing_blocked_v11179')),
            (session_runtime_state, ('HISTORY_BUFFER_LIMIT', 'V019_SAFE_INT',
                                    'double_xp_event_state', 'DEFAULT_TEXT_ENCODING')),
            (tech_crafting, ('CHARACTER_MAX_LEVEL', 'ITEMS', 'find_by_name',
                             'normalize_lookup_text', 'TECH_CRAFT_RECIPES', 'TECH_SALVAGE_RECIPES')),
            (milestone, ('ITEMS', 'TECH_SET_ITEMS_V03114', 'TECH_SET_UPGRADE_COSTS_V0320',
                         'dungeon_party_bonus_v0320', 'room_is_dungeon_v0320')),
        )
        for module, names in comparisons:
            assert server.RUNTIME_NATIVE_MODULE_INDEX[module.__name__]['dependency_mode'] == 'explicit'
            for name in names:
                actual, expected = getattr(module, name), getattr(server, name)
                assert actual is expected or actual == expected, (module.__name__, name)
        from core.runtime_manifest import RUNTIME_MODULES
        architecture = server.RUNTIME_ARCHITECTURE_STATE
        from core.runtime_manifest import EXPECTED_OVERRIDE_ORDER
        from core.runtime_rules import get_rule
        for rule_name, owners in EXPECTED_OVERRIDE_ORDER.items():
            expected_owner = owners[-1][:-3].replace('/', '.')
            assert get_rule(rule_name).__module__ == expected_owner, (rule_name, expected_owner)
        assert architecture['legacy_compat_module_count'] == 0
        assert architecture['runtime_mode'] == 'explicit-current-modules'
        assert architecture['explicit_module_count'] == len(RUNTIME_MODULES)
        assert set(architecture['modules']) == set(RUNTIME_MODULES)
        assert all(row['dependency_mode'] == 'explicit'
                   for row in server.RUNTIME_NATIVE_MODULE_INDEX.values())
        instance=MudServer()
        tables={row[0] for row in instance.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        required={'v110_event_progress','v110_event_death_receipts',
                  'v110_event_participants','v110_event_reward_receipts',
                  'v110_profession_cooldowns'}
        assert required<=tables
        assert not (forbidden & set(sys.modules)), forbidden & set(sys.modules)
        instance.db.conn.close()
        server._BOOT_SOCKET.close()
        print('CURRENT-ONLY RUNTIME PASS: 38 klas, 38 ras, 15136 questow, '
              '5 tabel SQLite, 8 narzędzi/8 wyrobów, 38 pul zadań gildyjnych, 38 unikalnych profili EQ; '
              f'{round(time.monotonic()-t,2)} sek. 127.0.0.1 tylko test',flush=True)
        # The test's server created helper threads; terminate the disposable
        # subprocess immediately after verified assertions and DB close.
        shutil.rmtree(td,ignore_errors=True)
        os._exit(0)

if __name__=='__main__':main()
