# -*- coding: utf-8 -*-
"""Frozen reference topology checks with no full game or network startup.

Reference SHA-256 values were generated from the unmodified v103 topology
function using the same synthetic rooms. The snapshot hashes cover exits,
room depth and world role, not merely room counts.
"""
import ast
import hashlib
import json
from pathlib import Path
from world import topology_generator as gen

ROOT=Path(__file__).resolve().parents[1]
REFERENCE={
    12:'24b37437cc83a32e3d3642ba21c24142ecf431ae3b674327243f93bf8142caee',
    35:'5d4d7137ae2760626eabb876a7dc2b7a55d38ada6a48c04eb87908958045397f',
    80:'a9f03f7ef9f229ef17f89fd8df18b5c87289a2c846e67f125b02587d0f0f9287',
    160:'6df362749ae806dcd2a6c32d78cdb4e0ff2ae73cc0424af7c073a1114c681ffa',
}

def optimized_function():
    path=ROOT/'world'/'v420_runtime_regions.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)
           and n.name=='_generate_zone_semantic_v03013']
    assert len(nodes)==1
    module=ast.Module(body=nodes,type_ignores=[])
    context={'world_topology_generator_v0281':gen,
             'SEMANTIC_BACKBONE_V03013':{},
             '_V03013_ORDERED_TRIAL_ZONES':set()}
    exec(compile(ast.fix_missing_locations(module),str(path),'exec'),context)
    return context[nodes[0].name]

def make_world(n):
    rooms={}
    for zone in ('Kraina Test A','Kraina Test B'):
        for i in range(n):
            rid=f'{zone.replace(" ", "_")}_{i:03}'
            rooms[rid]={'name':f'Miasto: szlak / biblioteka {i}',
                        'zone':zone,'exits':{}}
    rooms['Kraina_Test_A_000']['exits']['up']='Kraina_Test_B_000'
    rooms['Kraina_Test_B_000']['exits']['down']='Kraina_Test_A_000'
    return rooms

def run():
    fn=optimized_function()
    for n,expected in REFERENCE.items():
        rooms=make_world(n)
        for zone in ('Kraina Test A','Kraina Test B'):
            fn(rooms,zone,[k for k,v in rooms.items() if v['zone']==zone])
        payload=json.dumps({k:{'exits':r['exits'],
                               'depth':r.get('topology_zone_depth'),
                               'role':r.get('world_role')}
                            for k,r in sorted(rooms.items())},
                           sort_keys=True,ensure_ascii=False)
        got=hashlib.sha256(payload.encode('utf-8')).hexdigest()
        assert got==expected,(n,got,expected)
        print(f'TOPOLOGY SHA256 PASS: {n} rooms per zone')
    return len(REFERENCE)
if __name__=='__main__':print('TOPOLOGY',run(),'PASS')
