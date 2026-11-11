# -*- coding: utf-8 -*-
"""Soulbound v112+: statyczny audyt zamknięcia modułów instalowanej wersji.

Ten audyt NIE uruchamia starego serwera i NIE otwiera bazy graczy.

Użycie:
    python validation/v11200_closed_runtime_gate.py --archive KANDYDAT.zip \
        --installed-list INSTALOWANE_PLIKI.txt --report RAPORT.json

Lista instalowanych plików musi pochodzić z rzeczywistego wyboru instalatora,
a nie ze zgadywania na podstawie katalogu validation czy nazwy wersji.
Każdy wiersz to jedna ścieżka względem katalogu Soulbound-MUD.

Odczyt modułów AST wykrywa importy jawne i importlib.import_module z literału.
Nie dowodzi pokrycia dynamicznych importów składanych w runtime ani LIVE.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
import zipfile
from collections import Counter

OLD_RE = re.compile(r'(?<![A-Za-z0-9])v(?:107|108|109|110|111)(?:\d+)?(?=_|\.|$)', re.I)
DYNAMIC_CALLS = {'importlib.import_module', '__import__', 'runpy.run_module'}


def norm(s: str) -> str:
    s = s.replace('\\', '/').lstrip('./')
    p = pathlib.PurePosixPath(s)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('niebezpieczna ścieżka: '+repr(s))
    return p.as_posix()


def source_files(source: pathlib.Path) -> dict[str, bytes]:
    if source.is_file():
        with zipfile.ZipFile(source) as z:
            files = [i for i in z.infolist() if not i.is_dir()]
            prefix = 'Soulbound-MUD/' if files and all(i.filename.startswith('Soulbound-MUD/') for i in files) else ''
            result = {}
            for i in files:
                name = norm(i.filename.removeprefix(prefix))
                if name in result:
                    raise ValueError('duplikat ZIP: '+name)
                result[name] = z.read(i)
            return result
    if source.is_dir():
        return {p.relative_to(source).as_posix():p.read_bytes()
                for p in source.rglob('*') if p.is_file() and not p.is_symlink()}
    raise FileNotFoundError(source)


def mod_for_path(path: str) -> str:
    if path.endswith('/__init__.py'):
        return path[:-12].replace('/', '.')
    return path[:-3].replace('/', '.')


def imports_from(tree: ast.AST, parent: str, path: str):
    """Yield (dotted_module, lineno, kind, optional imported name)."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                yield alias.name, n.lineno, 'import', None
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                pieces = parent.split('.') if parent else []
                if n.level > len(pieces):
                    yield '', n.lineno, 'invalid-relative', None
                    continue
                prefix = pieces[:len(pieces)-n.level+1]
                base = '.'.join(x for x in (*prefix, *(n.module.split('.') if n.module else [])) if x)
            else:
                base = n.module or ''
            for alias in n.names:
                yield base, n.lineno, 'from', alias.name
        elif isinstance(n, ast.Call):
            f = n.func
            call = f.id if isinstance(f, ast.Name) else f'{f.value.id}.{f.attr}' if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ''
            if call in DYNAMIC_CALLS:
                if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    yield n.args[0].value, n.lineno, 'dynamic-literal', None


def inspect_files(all_files: dict[str, bytes], installed: set[str],
                  required_files=()) -> dict:
    all_modules = {mod_for_path(p):p for p in all_files if p.endswith('.py')}
    runtime_modules = {mod_for_path(p):p for p in installed if p.endswith('.py') and p in all_files}
    internal_roots = {m.split('.')[0] for m in all_modules}
    # root packages (such as systems, world, player) as well as top-level .py files
    issues: list[dict] = []
    for required in sorted(required_files):
        if required not in installed or required not in all_files:
            issues.append({'file':required,'line':0,'module':'',
                           'reason':'required_entrypoint_missing_from_installed_runtime'})
    legacy: list[dict] = []
    dynamic_uncertain: list[dict] = []
    parsed_count = 0
    for path in sorted(installed):
        if not path.endswith('.py'):
            continue
        if path not in all_files:
            issues.append({'file':path,'line':0,'module':'','reason':'installed_missing_from_candidate'})
            continue
        try:
            tree = ast.parse(all_files[path].decode('utf-8-sig'), filename=path)
        except (SyntaxError, UnicodeError) as exc:
            issues.append({'file':path,'line':getattr(exc,'lineno',0) or 0,'module':'','reason':'syntax_or_encoding_error','detail':str(exc)[:300]})
            continue
        parsed_count += 1
        module = mod_for_path(path)
        parent = module if path.endswith('/__init__.py') else module.rpartition('.')[0]
        for dotted,line,kind,member in imports_from(tree,parent,path):
            if kind=='invalid-relative':
                issues.append({'file':path,'line':line,'module':dotted,'reason':'invalid_relative_import'})
                continue
            if not dotted:
                continue
            if OLD_RE.search(dotted):
                legacy.append({'file':path,'line':line,'module':dotted,'kind':kind})
            root = dotted.split('.')[0]
            if root not in internal_roots:
                continue
            # Parent module can be package or .py file. Missing external imports
            # are not checked here; this is a local-code closure audit only.
            if dotted not in runtime_modules:
                if dotted in all_modules:
                    issues.append({'file':path,'line':line,'module':dotted,'reason':'excluded_from_installed_runtime'})
                else:
                    # Unknown dotted import in our own namespace (e.g. systems.foo).
                    issues.append({'file':path,'line':line,'module':dotted,'reason':'absent_from_candidate'})
            if kind=='from' and member and member!='*':
                child = dotted + '.' + member
                # A variable like REWARD_V11134 is not a module import.
                # Only count versioned child when that child is actually a module.
                if child in all_modules and OLD_RE.search(child) and not OLD_RE.search(dotted):
                    legacy.append({'file':path,'line':line,'module':child,'kind':'from-member'})
                if child in all_modules and child not in runtime_modules:
                    issues.append({'file':path,'line':line,'module':child,'reason':'excluded_from_installed_runtime'})
            if kind=='dynamic-literal' and dotted.startswith('.'):
                dynamic_uncertain.append({'file':path,'line':line,'module':dotted})
    issues.sort(key=lambda x:(x['file'],x['line'],x['module'],x['reason']))
    legacy.sort(key=lambda x:(x['file'],x['line'],x['module']))
    return {'status':'PASS' if not issues and not legacy else 'FAIL',
            'candidate_files':len(all_files), 'installed_files':len(installed),
            'installed_python_parsed':parsed_count,
            'missing_import_count':len(issues), 'old_version_import_count':len(legacy),
            'uncertain_dynamic_relative_imports':len(dynamic_uncertain),
            'missing_imports':issues,'old_version_imports':legacy,
            'dynamic_notes':dynamic_uncertain,
            'limitations':'AST jawne importy i literalne importlib; brak pełnego śledzenia importów budowanych dynamicznie, procesów TCP i bazy SQLite.'}


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,help='ZIP z kandydatem lub rozpakowany katalog gry')
    p.add_argument('--installed-list',required=True,help='Dokładny wykaz plików wybieranych przez instalator')
    p.add_argument('--report',help='Docelowy raport JSON')
    args=p.parse_args(argv)
    raw=pathlib.Path(args.installed_list).read_text(encoding='utf-8-sig')
    install={norm(x.strip()) for x in raw.splitlines() if x.strip() and not x.lstrip().startswith('#')}
    output=inspect_files(source_files(pathlib.Path(args.archive)),install,
                         required_files={'server.py','aktualizuj_soulbound.py',
                                         'systems/v11200_activation.py'})
    if args.report:
        pathlib.Path(args.report).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SOULBOUND MODULE CLOSURE: '+output['status'])
    for key in ('installed_files','installed_python_parsed','missing_import_count','old_version_import_count'):
        print(f'{key}: {output[key]}')
    for issue in output['missing_imports'][:20]:
        print(f"MISSING {issue['file']}:{issue['line']} {issue['module']} ({issue['reason']})")
    for issue in output['old_version_imports'][:20]:
        print(f"HISTORY {issue['file']}:{issue['line']} {issue['module']}")
    return 0 if output['status']=='PASS' else 2

if __name__ == '__main__':
    raise SystemExit(main())
