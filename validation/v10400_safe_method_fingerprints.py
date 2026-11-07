# -*- coding: utf-8 -*-
"""Test fingerprintów metod v4.20 bez importu serwera, socketow i baz."""
import ast
import hashlib
from pathlib import Path
from validation.v4200_modularization import expected_moved_ast_digest_v4200


def run():
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'validation/v4200_modularization.py').read_text('utf-8'))
    ledger=next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LEDGER' for t in n.targets))
    count=0
    version=(root/'VERSION').read_text(encoding='utf-8').strip()
    for name,(host,src,old_hash,_) in ledger.items():
        symbol=name.rsplit('.',1)[-1]
        code=ast.parse((root/src).read_text('utf-8'))
        found=[n for n in code.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==symbol]
        if len(found)!=1:
            raise AssertionError('Brak metody: '+name)
        sha=hashlib.sha256(ast.dump(found[0],include_attributes=False).encode()).hexdigest()
        # Same audited version-aware AST fingerprints as the v4.20 runtime
        # binder. v105/v106/v107 make specific, explicitly pinned changes;
        # new code must never be blessed by simply ignoring the fingerprint.
        expected_hash=expected_moved_ast_digest_v4200(root,name,old_hash,found[0])
        if sha!=expected_hash:
            raise AssertionError('Zmiana metody bez aktualizacji audytu: '+name)
        hosttext=(root/host).read_text('utf-8')
        expected=('.'+symbol+' = _sb420_bind(') if '.' in name else symbol+' = _sb420_topbind('
        if expected not in hosttext:
            raise AssertionError('Brak podlaczenia metody: '+name)
        count+=3
    return count

if __name__=='__main__':
    print('BEZPIECZNA KONTROLA MODULOW v4200:',run(),'PASS')
