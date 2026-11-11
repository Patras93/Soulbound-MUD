"""Current runtime composition through ordinary imports and declared exports.

No module is seeded with another module's globals. Initialization is explicit
in the manifest; thirteen replaceable gameplay rules have their own narrow API.
Historical source-contract audits execute offline, never as part of game boot.
"""
from __future__ import annotations
import ast
import importlib
import os
import time
from pathlib import Path
from typing import MutableMapping
from core.runtime_manifest import RUNTIME_MODULES, EXPLICIT_RUNTIME_EXPORTS, FULL_AUDIT_ONLY_MODULES, RUNTIME_INITIALIZERS


def module_name_for_path(relative_path: str) -> str:
    path=str(relative_path).replace('\\','/')
    if not path.endswith('.py'):raise ValueError('Runtime path must be Python source: '+path)
    return path[:-3].replace('/','.').removesuffix('.__init__')


def _source_definition_index(source: str, filename: str):
    tree=ast.parse(source,filename=filename)
    top=[];functions=set();methods=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):top.append(node.name)
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):functions.add(node.name)
        if isinstance(node,ast.ClassDef):
            for child in node.body:
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    methods.append({'class':node.name,'method':child.name,'line':child.lineno})
    return top,methods,functions


def load_native_runtime(root: Path, namespace: MutableMapping[str,object])->dict:
    root=Path(root).resolve()
    active_modules=tuple(RUNTIME_MODULES)
    missing=[rel for rel in active_modules if not (root/rel).is_file()]
    undeclared=[rel for rel in active_modules if rel not in EXPLICIT_RUNTIME_EXPORTS]
    if missing or undeclared:raise RuntimeError(f'Incomplete explicit runtime: missing={missing}; undeclared={undeclared}')
    trace=os.environ.get('SOULBOUND_BOOT_TRACE','').strip().lower() in ('1','true','yes','on')
    full_audit=os.environ.get('SOULBOUND_FULL_AUDIT','').strip().lower() in ('1','true','yes','on')
    started=time.monotonic()
    published={};source_index={};method_index={};module_index={};owners={};method_owners={}
    for relative in active_modules:
        name=module_name_for_path(relative)
        if trace:print('[CURRENT BOOT] START '+relative,flush=True)
        module=importlib.import_module(name)
        initializer = RUNTIME_INITIALIZERS.get(relative)
        if initializer is not None:
            getattr(module, initializer)()
        # Normal imports use the one canonical module instance even when a
        # dependency was imported earlier by another owner.
        if Path(module.__file__).resolve()!=(root/relative).resolve():
            raise ImportError('Runtime module came from another installation: '+name)
        exports=EXPLICIT_RUNTIME_EXPORTS[relative]
        absent=[key for key in exports if not hasattr(module,key)]
        if absent:raise RuntimeError(f'Missing declared exports in {name}: {absent}')
        for key in exports:published[key]=getattr(module,key)
        definitions,methods,_=_source_definition_index((root/relative).read_text('utf-8-sig'),str(root/relative))
        for symbol in definitions:
            owners.setdefault(symbol,[]).append(relative)
            source_index[symbol]={'file':relative,'module':name}
        for method in methods:
            row={'file':relative,'module':name,**method}
            method_index.setdefault(method['method'],[]).append(row)
            if method['class'].startswith('Session') and method['class'].endswith('Mixin'):
                method_owners.setdefault(method['method'],[]).append(relative+':'+method['class'])
        module_index[name]={'file':relative,'authored_symbol_count':len(exports),
                            'dependency_mode':'explicit','declared_exports':tuple(exports)}
    from core.runtime_rules import rule_owners
    rules=rule_owners()
    if len(rules)!=13:raise RuntimeError('Incomplete current gameplay rules: '+repr(rules))
    state={'version':'112-current','module_count':len(active_modules),'modules':active_modules,
           'native_module_names':tuple(module_name_for_path(p) for p in active_modules),
           'override_symbol_count':sum(len(v)>1 for v in owners.values()),
           'session_method_collision_count':sum(len(v)>1 for v in method_owners.values()),
           'indexed_method_count':sum(map(len,method_index.values())),
           'override_order':{k:v for k,v in owners.items() if len(v)>1},
           'direct_exec_locations':(),'runtime_mode':'explicit-current-modules',
           'explicit_module_count':len(active_modules),'legacy_compat_module_count':0,
           'explicit_modules':active_modules,'full_audit_enabled':full_audit,
           'full_audit_only_module_count':len(FULL_AUDIT_ONLY_MODULES),
           'full_audit_only_modules':tuple(sorted(FULL_AUDIT_ONLY_MODULES)),
           'current_rule_owners':rules,'historical_audits_enabled':False}
    published.update(RUNTIME_SYMBOL_SOURCE_INDEX=source_index,RUNTIME_METHOD_SOURCE_INDEX=method_index,
                     RUNTIME_NATIVE_MODULE_INDEX=module_index,RUNTIME_ARCHITECTURE_STATE=state)
    namespace.update(published)
    if trace:print(f'[CURRENT BOOT] {len(active_modules)} explicit modules ({time.monotonic()-started:.3f}s)',flush=True)
    return state
