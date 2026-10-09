"""Non-production regressions for v1.26.2: read-only EQ cache and auto-task cancellation.

This suite does not connect to Railway or touch player saves.
"""
from __future__ import annotations
import asyncio
from types import SimpleNamespace
from unittest.mock import patch



def audit_v1262_equipment():
    from player.session_mixins import equipment_stats as eqmod
    checks = 0
    class DB:
        def __init__(self): self.count = 0; self.rows = [{'item_id': 'test_v1262', 'slot': 'weapon'}]
        def equipment(self, _account): self.count += 1; return list(self.rows)
        def equipment_runes_v0925(self, *_): return ()
        def item_qty(self, *_): return 0
    class Fake(eqmod.SessionEquipmentStatsMixin):
        def __init__(self):
            self.server=SimpleNamespace(db=DB()); self.account_id=10
            self.character=SimpleNamespace(character_level=10)
        def active_soul_weapon_relic_v11176(self): return (None,None)
    d=Fake()
    with patch.object(eqmod, 'ITEMS', {'test_v1262': {'type':'weapon', 'properties': {'max_hp_pct':8}, 'attack':17}}):
        d._read_only_equipment_cache_v1262={}
        x=d.equipped_item_rows(); y=d.equipped_item_rows()
        assert len(x)==len(y)==1 and d.server.db.count==1
        checks+=1
        a=d.equipment_property_totals(); b=d.equipment_property_totals()
        assert a==b and a['max_hp_pct']==8
        checks+=1
        a['max_hp_pct']=12345
        assert d.equipment_property_totals()['max_hp_pct']==8  # no mutable-cache leak
        checks+=1
        fp=d.equipment_flat_power_totals_v11187()
        assert fp['attack']==17 and d.equipment_flat_power_totals_v11187()==fp
        checks+=1
        d.server.db.rows=[]
        assert d.equipped_item_rows()  # one-command snapshot
        checks+=1
        del d._read_only_equipment_cache_v1262
        assert not d.equipped_item_rows()  # next command sees latest equipment
        assert d.equipment_property_totals()['max_hp_pct']==0
        assert d.equipment_flat_power_totals_v11187()['attack']==0
        checks+=3
    return checks


async def _audit_auto_tasks():
    from player.session_mixins.gathering import SessionGatheringMixin
    from player.session_mixins.crafting_expansion import SessionCraftingExpansionV03114Mixin
    from player.session_mixins.combat_realtime import SessionCombatRealtimeMixin
    from player.session_mixins.guide_navigation import SessionGuideNavigationMixin
    checks=0
    class Dummy:
        async def send(self, text): raise AssertionError('silent shutdown must not send: '+str(text))
    def sleeping_task(): return asyncio.create_task(asyncio.sleep(3600))
    obj=Dummy();obj.auto_mining=True;obj.auto_mine_direction_v1251='east';obj.auto_mining_task=sleeping_task()
    task=obj.auto_mining_task
    await SessionGatheringMixin.stop_auto_mining(obj, announce=False)
    assert task.cancelled() and not obj.auto_mining and obj.auto_mining_task is None and obj.auto_mine_direction_v1251 is None
    checks+=1
    obj.auto_fishing=True;obj.auto_fishing_task=sleeping_task(); task=obj.auto_fishing_task
    await SessionGatheringMixin.stop_auto_fishing(obj,announce=False)
    assert task.cancelled() and not obj.auto_fishing and obj.auto_fishing_task is None
    checks+=1
    obj.smelt_task_v1124=sleeping_task();obj.smelt_interruptible_v1124=True;obj.smelt_cancel_requested_v1124=False;obj.smelt_label_v1124='test'
    task=obj.smelt_task_v1124
    await SessionCraftingExpansionV03114Mixin.stop_smelt_v1124(obj, announce=False)
    assert task.cancelled() and obj.smelt_cancel_requested_v1124
    checks+=1
    obj.combat_task=sleeping_task();task=obj.combat_task
    await SessionCombatRealtimeMixin.stop_realtime_combat(obj)
    assert task.cancelled() and obj.combat_task is None
    checks+=1
    obj.guide_task=sleeping_task();obj.guiding=True;obj.guide_choice_state=None
    task=obj.guide_task
    await SessionGuideNavigationMixin.cancel_guide(obj,announce=False)
    assert task.cancelled() and obj.guide_task is None and obj.guiding is False
    checks+=1
    return checks



def audit_v1262_superbosses():
    """Check three flagship bosses' scripted ability selectors without running combat."""
    from world.uoss_superboss_runtime import (
        SUPERBOSS_ROTATIONS_V1145, superboss_source_ability_v11162,
        superboss_source_summons_v11162,
    )
    checks=0
    for key, turn, expected in (
        ('black_rabite',2,'Summon Greater Demon'),
        ('serpentarius',12,'Gravija'),
        ('yiazmat',15,'Stone Breath'),
    ):
        template={'uoss_unique_superboss_key':key}
        mob=SimpleNamespace(combat_turn=turn, template_id=f'uoss_superboss_{key}_v11136', uoss_summon_used_v1144=False)
        assert key=="black_rabite" or key in SUPERBOSS_ROTATIONS_V1145
        checks+=1
        assert superboss_source_ability_v11162(template,mob)==expected
        checks+=1
        if key=='black_rabite':
            summons=superboss_source_summons_v11162(None,template,mob,expected)
            assert len(summons)==1 and not superboss_source_summons_v11162(None,template,mob,expected)
            checks+=1
    return checks

async def _audit_nvda_changelog():
    from player.session_mixins.help_system import SessionHelpSystemMixin
    class Dummy:
        def __init__(self): self.messages=[]
        def full_changelog_lines(self): return ['Aktualna paczka: v1.26.2'] + [f'Zapis {i}' for i in range(400)]
        async def send(self,msg): self.messages.append(msg)
    d=Dummy()
    await SessionHelpSystemMixin.show_latest_changes(d,'')
    assert len(d.messages)<=23 and 'zmiany wszystkie' in d.messages[-1]
    d.messages=[]
    await SessionHelpSystemMixin.show_latest_changes(d,'50')
    assert len(d.messages)==52
    d.messages=[]
    await SessionHelpSystemMixin.show_latest_changes(d,'wszystkie')
    assert len(d.messages)==403
    d.messages=[]
    await SessionHelpSystemMixin.show_latest_changes(d,'9'*5000)
    assert len(d.messages)<=23
    return 4


def audit_v1262():
    checks=audit_v1262_equipment()
    checks+=asyncio.run(_audit_auto_tasks())
    checks+=audit_v1262_superbosses()
    checks+=asyncio.run(_audit_nvda_changelog())
    return checks

if __name__=="__main__":
    import os, socket, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SOULBOUND_DB"]=os.path.join(tmp,"test.db")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            os.environ["SOULBOUND_PORT"]=str(sock.getsockname()[1])
        import server
        print(f"SOULBOUND v1.26.2 STABILITY: {audit_v1262()} checks PASS")
