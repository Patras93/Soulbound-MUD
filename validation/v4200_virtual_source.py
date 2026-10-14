# -*- coding: utf-8 -*-
"""Verified textual view of refactored sources for historical source contracts.

Hash validates the ACTUAL shipped Python AST before a historical source check
is presented with a reconstructed layout. Nothing is skipped or suppressed.
"""
import ast
from hashlib import sha256
from functools import lru_cache
from pathlib import Path
from validation.v4200_modularization import LEDGER
from validation.v4100_virtual_source import read_factored_legacy_source_v410

@lru_cache(maxsize=96)
def read_actual_refactored_source_v4200(file):
    file=Path(file).resolve()
    code=read_factored_legacy_source_v410(file)
    relevant={sym:desc for sym,desc in LEDGER.items() if str(file).replace('\\','/').endswith('/'+desc[0])}
    if not relevant:return code
    lines=code.splitlines(keepends=True)
    tree=ast.parse(code)
    replacements=[]
    actual=set()
    for symbol,(oldrel,newrel,digest,_) in relevant.items():
        origin=file.parents[len(oldrel.split('/'))-1]
        moved=(origin/newrel).read_text(encoding='utf8')
        node=next((n for n in ast.parse(moved).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==symbol.rsplit('.',1)[-1]),None)
        if node is None or sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()!=digest:
            raise AssertionError(('module body not identical',symbol))
        frag='\n'.join(moved.splitlines()[node.lineno-1:node.end_lineno])+'\n'
        if '.' in symbol:
            cls_name,name=symbol.split('.',1)
            cls=next((c for c in tree.body if isinstance(c,ast.ClassDef) and c.name==cls_name),None)
            if cls is None:raise AssertionError(('missing class',cls_name))
            stub=next((m for m in cls.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef)) and m.name==name),None)
            if stub is None:raise AssertionError(('missing class method',symbol))
            if f'{cls_name}.{name} = _sb420_bind(' not in code:raise AssertionError(('missing live method binding',symbol))
            replacements.append((stub.lineno,stub.end_lineno,''.join('    '+line if line.strip() else line for line in frag.splitlines(keepends=True))))
        else:
            stub=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==symbol),None)
            if stub is None:raise AssertionError(('missing source function',symbol))
            if f'{symbol} = _sb420_topbind(' not in code:raise AssertionError(('missing live function binding',symbol))
            replacements.append((stub.lineno,stub.end_lineno,frag))
        actual.add(symbol)
    if actual!=set(relevant):raise AssertionError(('missing audited extractions',relevant.keys()-actual))
    for start,end,text in sorted(replacements,reverse=True):lines[start-1:end]=[text]
    return ''.join(lines)
