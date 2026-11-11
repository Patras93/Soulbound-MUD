"""Compare all33 canonical gameplay catalogs to the pre-migration baseline.
The worker uses a disposable current staging environment and fixed world seed.
No database, production authorization or prior-release Python code is needed.
"""
from __future__ import annotations
import dataclasses, enum, hashlib, json, math, os, random, socket, subprocess, sys, tempfile, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=Path(__file__).with_name('current_catalog_baseline.json')
def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'), allow_nan=False)


def normalize(value, stack=None):
    if value is None or isinstance(value,(str,bool,int)):
        return value
    if isinstance(value,float):
        return value if math.isfinite(value) else {'@float':str(value)}
    if isinstance(value,enum.Enum):
        return {'@enum':type(value).__qualname__, 'value':normalize(value.value)}
    if isinstance(value,types.FunctionType) or isinstance(value,types.BuiltinFunctionType):
        # Module/file locations intentionally change in a native refactor;
        # retain the callable's declared identity and argument defaults.
        return {'@callable':value.__qualname__, 'defaults':normalize(getattr(value,'__defaults__',None)),
                'kwdefaults':normalize(getattr(value,'__kwdefaults__',None))}
    if isinstance(value,bytes):
        return {'@bytes':value.hex()}
    stack=set() if stack is None else stack
    if id(value) in stack:
        raise TypeError('Circular catalog value: '+type(value).__qualname__)
    nested=stack|{id(value)}
    if isinstance(value,dict):
        if all(isinstance(k,str) for k in value):
            return {k:normalize(v,nested) for k,v in sorted(value.items())}
        pairs=[(normalize(k,nested),normalize(v,nested)) for k,v in value.items()]
        return {'@dict':sorted(pairs,key=lambda pair:encoded(pair[0]))}
    if isinstance(value,list):
        return [normalize(v,nested) for v in value]
    if isinstance(value,tuple):
        return {'@tuple':[normalize(v,nested) for v in value]}
    if isinstance(value,(set,frozenset)):
        return {'@set':sorted((normalize(v,nested) for v in value),key=encoded)}
    if dataclasses.is_dataclass(value):
        return {'@dataclass':type(value).__qualname__, 'fields':normalize(dataclasses.asdict(value),nested)}
    raise TypeError('Unsupported catalog value: '+type(value).__module__+'.'+type(value).__qualname__)


def worker():
    sys.path.insert(0,str(ROOT))
    expected=json.loads(FIXTURE.read_text('utf8'))
    for key in list(os.environ):
        if key.startswith(('SOULBOUND_','RAILWAY_')) or key=='PORT':os.environ.pop(key,None)
    with tempfile.TemporaryDirectory(prefix='sb112_catalog_contract_') as directory:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        os.environ.update(SOULBOUND_V112_STAGING='1',SOULBOUND_HOST='127.0.0.1',SOULBOUND_PORT=str(port),
            SOULBOUND_DB=str(Path(directory)/'catalog.sqlite'),SOULBOUND_WORLD_SEED=expected['seed'],
            SOULBOUND_WORLD_SEED_FILE=str(Path(directory)/'seed.txt'))
        random.seed(expected['random_seed'])
        import server
        try:
            for name,reference in expected['catalogs'].items():
                value=getattr(server,name)
                actual=hashlib.sha256(encoded(normalize(value)).encode('utf8')).hexdigest()
                assert len(value)==reference['entries'], (name,'catalog size changed')
                assert actual==reference['sha256'], (name,'catalog content changed',actual,reference['sha256'])
            print('CURRENT CATALOG EQUIVALENCE: 33/33 PASS; authored gameplay, HELP, exploration, spawns and shops preserved',flush=True)
        finally:server._BOOT_SOCKET.close()
    return 0

def main():
    if '--worker' in sys.argv:return worker()
    env=dict(os.environ,PYTHONHASHSEED='0',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',
             PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,
                          stdin=subprocess.DEVNULL,timeout=300).returncode

if __name__=='__main__':raise SystemExit(main())
