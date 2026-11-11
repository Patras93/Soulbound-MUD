# -*- coding: utf-8 -*-
"""v12.00.7 resource-by-resource HOT OLC tests on isolated SQLite."""
import copy
import json
import sqlite3
import tempfile
import sys
from pathlib import Path
from types import SimpleNamespace as Obj
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run_regression():
    import server  # registered live game item catalogue
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_progression_v1206 import RESOURCE_XP_RULES, resource_rule_xp
    from systems.profession_xp_v1203 import reward_xp_v1203
    from data.items import ITEMS
    count = 0
    from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
    import inspect
    assert 'content_key=item_id' in inspect.getsource(SessionGatheringActionsMixin.fish)
    count += 1
    assert len(ITEMS) > 100000; count += 1
    known = ('iron_ore', 'copper_ore', 'gold_ore', 'brown_trout', 'salmon',
             'mint', 'oak_log')
    for key in known:
        assert key in ITEMS and ITEMS[key].get('type') == 'resource'; count += 1
    with tempfile.TemporaryDirectory() as temp:
        conn = sqlite3.connect(str(Path(temp) / 'olc.db'))
        conn.row_factory = sqlite3.Row
        world = Obj(mobs={}, _last_refresh_at=10.0, _register_runtime_spawn=lambda *_: None)
        srv = Obj(world=world, sessions=[])
        service = LiveContentV1204(Obj(conn=conn))
        try:
            assert service.active['resource_edits'] == {}; count += 1
            assert resource_rule_xp(100,'iron_ore') == 100; count += 1
            assert resource_rule_xp(0,'iron_ore') == 0; count += 1
            # Old live payloads lack resource_edits, but must still load.
            old = blank(); old.pop('resource_edits')
            assert service._compat(old)['resource_edits'] == {}; count += 1
            base = reward_xp_v1203(40,100000,50,50,content_key='iron_ore')
            base_tool = reward_xp_v1203(30,100000,50,50,tool=True,content_key='iron_ore')
            service.stage_edit('surowiec','iron_ore','prof_xp',str(base+123456))
            service.stage_edit('surowiec','iron_ore','tool_xp',str(base_tool+34567))
            service.stage_edit('surowiec','iron_ore','prof_percent','200')
            service.stage_edit('surowiec','iron_ore','tool_percent','250')
            for k in known:
                if k != 'iron_ore':
                    service.stage_edit('resource', k, 'prof_percent', '170')
                count += 1
            assert service.validate(service.draft).find('surowców') >= 0; count += 1
            assert RESOURCE_XP_RULES == {}; count += 1  # staging has NO game effect
            assert reward_xp_v1203(40,100000,50,50,content_key='iron_ore') == base; count += 1
            # Invalid attempts cannot alter the staged valid draft.
            snapshot = copy.deepcopy(service.draft)
            bad = [
                ('no_such_resource', 'prof_xp', '100'),
                ('iron_ore','prof_xp','0'),
                ('iron_ore','prof_xp','-1'),
                ('iron_ore','prof_percent','99'),
                ('iron_ore','tool_percent','1001'),
                ('iron_ore','prof_xp','1000000000001'),
                ('iron_ore','python','1'),
                ('iron_ore','prof_xp','__import__("os")'),
                ('fishing_rod','prof_xp','1000'),
                ('temple_rat','prof_xp','1000'),
                ('iron_ore','prof_percent','2.5'),
            ]
            for key, field, val in bad:
                try: service.stage_edit('surowiec',key,field,val)
                except (ValueError,TypeError):
                    assert service.draft == snapshot; count += 1
                else: raise AssertionError(f'Unsafe item rule: {(key,field,val)}')
            assert 'rewizję 1' in service.apply(srv, 'admin'); count += 1
            assert service.revision == 1 and world._last_refresh_at == 0; count += 1
            assert RESOURCE_XP_RULES['iron_ore']['prof_xp'] == base+123456; count += 1
            for key in known:
                assert reward_xp_v1203(40,100000,50,50,content_key=key) > 0
                count += 1
            after = reward_xp_v1203(40,100000,50,50,content_key='iron_ore')
            assert after >= base+123456 and after >= 2*base; count += 1
            after_tool = reward_xp_v1203(30,100000,50,50,tool=True,content_key='iron_ore')
            assert after_tool >= base_tool+34567 and after_tool >= (base_tool*250+50)//100; count += 1
            assert reward_xp_v1203(40,100000,50,50,content_key='copper_ore') > 0; count += 1
            assert reward_xp_v1203(40,100000,50,50,content_key='nonexistent') > 0; count += 1
            assert resource_rule_xp(0,'iron_ore') == 0; count += 1
            assert resource_rule_xp(77,None) == 77; count += 1
            # Rare resources inherit base settings if no exact rule.
            rare = next((name for name,item in ITEMS.items() if item.get('base_resource_id')=='salmon'),None)
            assert rare is not None; count += 1
            assert resource_rule_xp(100,rare) == 170; count += 1
            # Already published rules survive new service startup with same DB.
            saved = json.loads(conn.execute('SELECT payload FROM live_content_v1204').fetchone()['payload'])
            assert saved['resource_edits']['iron_ore']['prof_xp'] == base+123456; count += 1
            service._remove(None)
            assert not RESOURCE_XP_RULES; count += 1
            service = LiveContentV1204(Obj(conn=conn))
            assert resource_rule_xp(base,'iron_ore') == after; count += 1
            # New package import merges rules; existing local rules remain.
            incoming = {'resource_edits': {'mint': {'tool_xp': 3000},
                                           'oak_log': {'prof_percent': 180}}}
            filepath = Path(temp)/'patch.json'
            filepath.write_text(json.dumps(incoming), encoding='utf-8')
            service.stage_file(filepath)
            assert service.draft['resource_edits']['iron_ore']['prof_xp']==base+123456; count += 1
            assert service.draft['resource_edits']['mint']['tool_xp']==3000; count += 1
            file_export = Path(temp)/'export.json'
            service.export(file_export)
            assert json.loads(file_export.read_text('utf-8'))['resource_edits']['mint']['tool_xp']==3000; count += 1
            assert 'rewizję 2' in service.apply(srv,'admin'); count += 1
            assert resource_rule_xp(100,'mint',tool=True) >= 3000; count += 1
            service.stage_clear_resource('iron_ore')
            assert 'iron_ore' not in service.draft['resource_edits']; count += 1
            assert resource_rule_xp(base,'iron_ore') == after; count += 1
            assert 'rewizję 3' in service.apply(srv,'admin'); count += 1
            assert resource_rule_xp(base,'iron_ore') == base; count += 1
            assert 'rewizję 4' in service.apply(srv,'admin',rollback=True); count += 1
            assert resource_rule_xp(base,'iron_ore') == after; count += 1
            # Bulk: all authored resource IDs may be independently configured.
            choices = [key for key,v in ITEMS.items() if v.get('type')=='resource'][:200]
            for key in choices:
                service.stage_edit('surowiec',key,'prof_percent','130')
                count += 1
            assert len(choices) == 200; count += 1
            assert service.validate(service.draft); count += 1
            service.reset_draft()
            assert service.draft == service.active; count += 1
        finally:
            service._remove(None)
            conn.close()
        assert not RESOURCE_XP_RULES; count += 1
    return count


if __name__=='__main__':
    print('V12.00.7 LIVE RESOURCE EXP:', run_regression(), 'checks PASS')
