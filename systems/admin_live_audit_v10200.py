# -*- coding: utf-8 -*-
"""Read-only, evidence-based Admin Live diagnostics (not certification)."""
from __future__ import annotations
import ast
import copy
import importlib
from pathlib import Path
from systems import live_mechanics_v10100, uoss_ai_v10000, uoss_regeneration_v9900, uoss_tactics_v9800
from systems.admin_live_bridge_v10200 import available_port

ROOT=Path(__file__).resolve().parents[1]
# Only explicitly registered v96..v102 dispatchers, not guessed commands.
ROUTES={
 'systems.admin_live_mastery_v9600':'dispatch_v9600',
 'systems.admin_live_offline_v9700':'dispatch_v9700_offline',
 'systems.admin_live_uoss_profiles_v9700':'dispatch_v9700_uoss',
 'systems.admin_live_uoss_v9800':'dispatch_v9800_uoss',
 'systems.admin_live_quest_doctor_v9800':'dispatch_v9800_doctor',
 'systems.admin_live_advancement_v9800':'dispatch_v9800_advancement',
 'systems.admin_live_five_v9900':'dispatch_v9900',
 'systems.admin_live_ultimate_v10000':'dispatch_v10000',
 'systems.admin_live_v10100':'dispatch_v10100',
 'systems.admin_live_final_v10200':'dispatch_v10200',
}


def audit_routes():
    from player.session_mixins import admin_tools
    path=Path(admin_tools.__file__)
    tree=ast.parse(path.read_text(encoding='utf-8'))
    imported=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module:
            imported.update((node.module,alias.name) for alias in node.names)
    missing=[]
    for module,name in ROUTES.items():
        try:
            mod=importlib.import_module(module)
            if not callable(getattr(mod,name,None)) or (module,name) not in imported:
                missing.append(name)
        except (ImportError,AttributeError,ValueError,TypeError) as exc:
            missing.append(name+': '+type(exc).__name__)
    return len(ROUTES),missing


def audit_full_router_static():
    """Inspect *all* historical admin live dispatch imports without executing them."""
    from player.session_mixins import admin_tools
    tree=ast.parse(Path(admin_tools.__file__).read_text(encoding='utf-8'))
    handler=next((x for x in ast.walk(tree) if isinstance(x,ast.AsyncFunctionDef) and x.name=='admin_live_v1204'),None)
    if handler is None:return 0,['Brak admin_live_v1204']
    references=set()
    for node in ast.walk(handler):
        if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('systems.'):
            for alias in node.names:
                if alias.name.startswith('dispatch'):
                    references.add((node.module,alias.name))
    missing=[]
    for module,name in sorted(references):
        file=ROOT.joinpath(*module.split('.')).with_suffix('.py')
        if not file.is_file():
            missing.append(module+': brak pliku')
            continue
        try:
            source=ast.parse(file.read_text(encoding='utf-8-sig'))
        except (OSError,SyntaxError,UnicodeError) as exc:
            missing.append(module+': '+type(exc).__name__)
            continue
        declared=any((isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name==name)
            or isinstance(node,(ast.Import,ast.ImportFrom)) and any((a.asname or a.name)==name for a in node.names)
            for node in ast.walk(source))
        if not declared:
            missing.append(module+'.'+name+': brak definicji statycznej')
    return len(references),missing


def audit_olc(service):
    issues=[]
    for label,record in (('ACTIVE',service.active),('DRAFT',service.draft)):
        try:service.validate(record)
        except Exception as exc:issues.append(label+': '+type(exc).__name__+' '+str(exc)[:100])
    for key,runtime in (('v101_rules',live_mechanics_v10100.ACTIVE),
                        ('v100_rules',uoss_ai_v10000.ACTIVE),
                        ('v99_rules',uoss_regeneration_v9900.ACTIVE),
                        ('v98_rules',uoss_tactics_v9800.ACTIVE)):
        if copy.deepcopy(service.active[key]) != runtime:
            issues.append(key+': stan silnika inny niz ACTIVE')
    return issues


def report(session,section='raport'):
    if not session.is_admin():raise ValueError('Tylko administrator.')
    if section not in ('raport','komendy','olc','arena'):
        raise ValueError('audyt raport/komendy/olc/arena')
    output=[]
    if section in ('raport','komendy'):
        count,missing=audit_routes()
        old_count,old_missing=audit_full_router_static()
        output.append('ROUTER: '+str(count)+' najnowszych modulow; '+
                      str(old_count)+' wszystkich historycznych tras statycznych; '+
                      ('BRAKI: '+', '.join((missing+old_missing)[:8]) if missing or old_missing else 'definicje i importy OK'))
    if section in ('raport','olc'):
        issues=audit_olc(session.server.live_content_v1204)
        output.append('OLC: '+('BRAKI: '+'; '.join(issues[:6]) if issues else 'ACTIVE/DRAFT walidacja i synchronizacja 98-101 OK'))
        output.append('OLC rewizja='+str(session.server.live_content_v1204.revision))
    if section in ('raport','arena'):
        try: available_port(); status='URUCHOMIONA IZOLACJA 4900'
        except ValueError: status='STOP (wymaga arena real start POTWIERDZAM)'
        output.append('ARENA pelny silnik: '+status+'; tunel wymaga osobnego logowania na kopii')
    output.append('ZAKRES: diagnostyka tylko odczytowa, nie test end-to-end calego swiata; '
                  'Windows PREDEPLOY 60/60 PLUS i zywe testy pozostaja wymagane.')
    return 'ADMIN LIVE AUDYT v102: '+'; '.join(output)
