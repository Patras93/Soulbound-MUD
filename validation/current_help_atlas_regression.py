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
    # Regression of the real v113.00.20 production boot crash. The game
    # loads persisted Admin Live limits and can migrate 800 defaults to
    # None (unlimited) *before* refreshing final HELP. The isolated authoring
    # preflight used to test only the 800 baseline and missed this crash.
    from unittest.mock import patch
    from core import live_level_caps_v5200 as level_caps
    axes = ('postac', 'bieglosc', 'dusza', 'bron_duszy',
            'skille', 'profesje', 'narzedzia')
    for scenario, caps, needles in (
        ('v107_unlimited', {key: None for key in axes},
         ('postać', 'bez limitu', 'narzędzia')),
        ('custom_admin_live', {'postac': 1234, 'bieglosc': 2100, 'dusza': 1500,
                               'bron_duszy': 2000, 'skille': 2222,
                               'profesje': 3333, 'narzedzia': 4444},
         ('1234', '2100', '3333', '4444')),
        ('mixed_settings', {'postac': 800, 'bieglosc': None, 'dusza': 1500,
                            'bron_duszy': 800, 'skille': None,
                            'profesje': 800, 'narzedzia': 1200},
         ('800', '1500', '1200', 'bez limitu')),
    ):
        with patch.dict(level_caps._state, caps):
            instance_topics = make_help_topics_v405()
            instance_aliases = make_help_topic_aliases_v405()
            result = refresh_current_help_v11320(instance_topics, instance_aliases)
            assert result['classes'] == len(CLASSES), scenario; checks += 1
            progressive = ' '.join(instance_topics['progresja800'])
            for token in needles:
                assert token in progressive, (scenario, token); checks += 1
            assert instance_topics['progresja600'] == instance_topics['progresja800'], scenario; checks += 1
            assert instance_topics['multiclass'] and instance_topics['klasy']; checks += 1
            assert 'bez limitu' in progressive if scenario == 'v107_unlimited' else True; checks += 1
            assert str(caps['narzedzia']) in progressive or caps['narzedzia'] is None; checks += 1
        # No live cap files, accounts, gameplay or database are modified.
    # Invalid runtime caps must still fail explicitly, never be silently ignored.
    with patch.dict(level_caps._state, {'postac': 0}):
        try:
            refresh_current_help_v11320(make_help_topics_v405(), make_help_topic_aliases_v405())
        except RuntimeError as exc:
            assert 'niepoprawne aktywne limity' in str(exc); checks += 1
        else:
            raise AssertionError('Nie wykryto błędnych limitów w HELP')
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
