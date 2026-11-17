# -*- coding: utf-8 -*-
"""Current HELP/Atlas contract: real registries, no static 14/22 caps."""
from __future__ import annotations
import ast
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
from data.help_base_catalog_v405 import make_help_topics_v405, make_help_topic_aliases_v405
from systems.help_atlas_v1602 import refresh_current_help_v11320
from systems.new_professions import PROFESSIONS, BASE_ACTIONS
from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
from core.classes_skills import CLASSES


def run():
    checks=0
    topics=make_help_topics_v405()
    aliases=make_help_topic_aliases_v405()
    summary=refresh_current_help_v11320(topics, aliases)
    assert summary['classes'] == len(CLASSES); checks += 1
    assert summary['professions'] == len(set(TOOL_PROFESSION_MAP.values())); checks += 1
    assert str(len(CLASSES)) in topics['klasy'][0]; checks += 1
    assert 'JEDNĄ' in topics['multiclass'][0] and 'wyłączone' in ' '.join(topics['multiclass']); checks += 1
    assert all('Multiclass działa' not in line for line in topics['sklepy_klasowe']); checks += 1
    for topic in ('atlas','profesje','druzyny','krypta','nawigacja','teleport_to_leader','ziemia'):
        assert topics[topic] and isinstance(topics[topic][0], str), topic
        checks += 1
    assert aliases['tp lider']=='teleport_to_leader'; checks += 1
    assert aliases['podnies']=='ziemia'; checks += 1
    # Method bodies are audited for current registries without importing the
    # full Session / 14-specialist dynamic NPC bootstrap in this cheap preflight.
    source=(ROOT/'player/session.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    session=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Session')
    names={n.name for n in session.body if isinstance(n,ast.AsyncFunctionDef)}
    assert {'show_atlas','show_profession_atlas_v1602'}.issubset(names); checks += 1
    assert 'TOOL_PROFESSION_MAP.values()' in source; checks += 1
    assert 'BASE_ACTIONS' in source and 'PROFESSIONS' in source; checks += 1
    assert 'SessionAtlasCodexMixin.show_atlas(self, query)' in source; checks += 1
    assert 'SessionAtlasCodexMixin.show_profession_atlas_v1602(self, query)' in source; checks += 1
    assert 'name not in historical' in source; checks += 1
    assert len(PROFESSIONS)==8 and len(BASE_ACTIONS)>=8; checks += 1
    # Test the current immutable development policy on every progression axis.
    from core import live_level_caps_v5200 as level_caps
    assert all(level_caps.cap(key) is None for key in level_caps.PROGRESSION_KEYS); checks += 1
    assert level_caps.cap('ulepszenia_eq') == 10; checks += 1
    dynamic_topics = make_help_topics_v405()
    current = refresh_current_help_v11320(dynamic_topics, make_help_topic_aliases_v405())
    assert current['classes'] == len(CLASSES); checks += 1
    active = ' '.join(dynamic_topics['progresja800'])
    assert 'bez limitu' in active; checks += 1
    assert dynamic_topics['progresja600'] == dynamic_topics['progresja800']; checks += 1
    for key in level_caps.PROGRESSION_KEYS:
        assert level_caps.can_grow(key, 800) and level_caps.can_grow(key, 60000)
        checks += 1
    # The fast PREDEPLOY must validate real dynamic HELP, not the retired
    # literal 14-tool wording, and must still detect missing public HELP links.
    from admin.fast_predeploy_audit_v0571 import _current_profession_help_contract_errors_v11320
    active_help=(ROOT/'player/session_mixins/help_system.py').read_text(encoding='utf-8')
    current_truth=(ROOT/'admin/help_truth_current.py').read_text(encoding='utf-8')
    audit=_current_profession_help_contract_errors_v11320
    assert audit(active_help, current_truth)==[]; checks += 1
    assert 'wszystkich 14 narzędzi' not in active_help; checks += 1
    assert audit(active_help.replace('HELP_TOPICS = _current_help_catalogs()[0]', 'HELP_TOPICS = {}'), current_truth); checks += 1
    assert audit(active_help, current_truth.replace('f"Soulbound ma {profession_count} profesji', '"14 profesji')); checks += 1
    assert audit(active_help, current_truth.replace('Eksploracja: Archeologia i Kartografia.', 'Eksploracja: [brak]')); checks += 1
    assert audit(active_help, current_truth.replace('COMMAND_CATALOG.bind_help(HELP_TOPICS, HELP_TOPIC_ALIASES)', '# brak finalnego wiązania')); checks += 1
    print(f'CURRENT HELP/ATLAS: {checks}/{checks} PASS', flush=True)
    return checks


if __name__=='__main__': run()
