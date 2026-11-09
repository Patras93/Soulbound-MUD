# -*- coding: utf-8 -*-
"""v109: pomoc i historia postaci, metody identyczne AST, stare komendy zachowane."""
from __future__ import annotations
import ast,hashlib
from pathlib import Path
from systems.v10900_activation import REQUIRED
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST='2c86b5b8432f05d10d6946f9713aaaf9a335b3aaed481d4d44cd786d736ac2eb'
PARTS={'history':('HelpHistoryV109Mixin',{'show_lifetime_statistics','full_changelog_lines'}),
       'skills':('HelpSkillsV109Mixin',{'all_skill_help_entries','skill_help_query_text','find_global_skill_help_matches','skill_help_kind_label','skill_help_scale_label','skill_help_effect_details','show_skill_help'})}
RETAINED={'show_where','help_commands','show_latest_changes','show_help'}

def run():
    base=ROOT/'player/session_mixins/help_system.py'
    original=next(c for c in ast.parse(base.read_text('utf8')).body if isinstance(c,ast.ClassDef) and c.name=='SessionHelpSystemMixin')
    found={n.name:n for n in original.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert set(found)==RETAINED
    checks=len(found)
    for file,(cls,names) in PARTS.items():
        path=f'player/session_mixins/help_parts_v109/{file}.py'
        assert path in REQUIRED
        node=next(n for n in ast.parse((ROOT/path).read_text('utf8')).body if isinstance(n,ast.ClassDef) and n.name==cls)
        sub={n.name:n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(sub)==names
        assert not (set(sub)&set(found))
        found.update(sub)
        checks+=len(sub)+2
    digest=hashlib.sha256('\n'.join(ast.dump(found[k],include_attributes=False) for k in sorted(found)).encode()).hexdigest()
    assert digest==EXPECTED_AST,digest
    bases={ast.unparse(n) for n in original.bases}
    assert bases=={item[0] for item in PARTS.values()}
    assert all('from .help_parts_v109 import ' in base.read_text('utf8') for _ in [0])
    assert len(found)==13
    checks+=3
    return checks
if __name__=='__main__':print('V109 HELP:',run(),'PASS')
