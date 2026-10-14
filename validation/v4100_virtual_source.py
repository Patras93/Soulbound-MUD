# -*- coding: utf-8 -*-
"""Static audit view of factored legacy files.

Old safety checks use exact snippets from specific historical source files.
We reconstitute the authored function bodies at their original positions
ONLY after hash-verifying each actual helper module AST. The gate thus still
checks the true shipped code, and fails if helpers were changed or missing.
"""
import ast
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from validation.v4100_large_modularization import SPLIT_SYMBOLS

@lru_cache(maxsize=32)
def read_factored_legacy_source_v410(file):
    file = Path(file)
    source = file.read_text(encoding='utf-8')
    path = str(file.resolve()).replace('\\','/')
    fragments = {}
    for symbol, (oldrel, newrel, required_hash, _) in SPLIT_SYMBOLS.items():
        if not path.endswith('/' + oldrel):
            continue
        helper = file.resolve().parents[len(oldrel.split('/'))-1] / newrel
        helper_src = helper.read_text(encoding='utf-8')
        tree = ast.parse(helper_src)
        match = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name==symbol]
        if len(match)!=1:
            raise AssertionError(('missing actual function body',symbol))
        authored = match[0]
        if sha256(ast.dump(authored,include_attributes=False).encode()).hexdigest()!=required_hash:
            raise AssertionError(('function AST changed',symbol))
        fragments[symbol] = '\n'.join(helper_src.splitlines()[authored.lineno-1:authored.end_lineno])+'\n'
    if not fragments:
        return source
    tree = ast.parse(source)
    lines=source.splitlines(keepends=True)
    replacements=[]
    for i,node in enumerate(tree.body):
        if not isinstance(node,ast.FunctionDef) or node.name not in fragments:
            continue
        nxt=tree.body[i+1]
        if not isinstance(nxt,ast.Assign) or not any(isinstance(t,ast.Name) and t.id==node.name for t in nxt.targets):
            raise AssertionError(('missing proper binding',node.name))
        if '_sb410_bind(' not in '\n'.join(lines[nxt.lineno-1:nxt.end_lineno]):
            raise AssertionError(('binding altered',node.name))
        replacements.append((node.lineno,nxt.end_lineno,fragments[node.name]))
    if len(replacements)!=len(fragments):
        raise AssertionError(('missing functions in source facade', len(replacements),len(fragments)))
    for start,end,body in sorted(replacements,reverse=True):
        lines[start-1:end]=[body]
    return ''.join(lines)
