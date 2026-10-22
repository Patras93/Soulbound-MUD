# -*- coding: utf-8 -*-
"""OLC36–43: atomic authored workflows using the existing validated engine.

No dynamic Python execution. Each operation is draft-only until explicit publish.
"""
import copy
import json


def profession_package(service, raw):
    """Create registered profession, real tool and its first recipe atomically."""
    parts = [part.strip() for part in raw.split('|')]
    if len(parts) != 16:
        raise ValueError('pakietfach: 8 pól nowafach + 8 pól fachreceptura oddzielonych |.')
    if parts[10] != parts[0]:
        raise ValueError('Receptura musi odnosić się do tej samej nowej profesji.')
    previous = copy.deepcopy(service.draft)
    try:
        service.stage_new_profession_and_tool_v2400(*parts[:8])
        service.stage_new_profession_recipe_v2400(*parts[8:])
    except Exception:
        service.draft = previous
        raise
    return 'DRAFT: nowa profesja, narzędzie i receptura. Użyj sprawdz, potem aktywuj POTWIERDZAM.'


def batch(service, category, raw):
    """Atomic changes of <=24 existing or new skills / rooms / recipes."""
    categories = {'skille':'skill', 'pokoje':'pokoj', 'receptury':'receptura',
                  'questy':'quest','przedmioty':'przedmiot', 'npcs':'npc'}
    if category not in categories:
        raise ValueError('pakietzmian: skille/pokoje/receptury/questy/przedmioty/npcs.')
    try:
        changes = json.loads(raw)
    except (TypeError,ValueError) as exc:
        raise ValueError('pakietzmian: słownik JSON ID -> {pole: wartosc}.') from exc
    if type(changes) is not dict or not 1 <= len(changes) <= 24:
        raise ValueError('pakietzmian: 1–24 istniejących ID.')
    if sum(len(v) if type(v) is dict else 999 for v in changes.values()) > 64:
        raise ValueError('pakietzmian: maksymalnie 64 pola.')
    previous = copy.deepcopy(service.draft)
    try:
        for ident, fields in changes.items():
            if type(fields) is not dict or not fields:
                raise ValueError('pakietzmian: każde ID wymaga słownika pól.')
            for field, value in fields.items():
                if type(field) is not str:
                    raise ValueError('Nazwa pola musi być tekstem.')
                if type(value) is str:
                    raw_value = value
                else:
                    raw_value = json.dumps(value,ensure_ascii=False)
                service.stage_edit(categories[category], ident, field, raw_value)
    except Exception:
        service.draft = previous
        raise
    return f'DRAFT: {len(changes)} obiektów, {sum(len(x) for x in changes.values())} pól, wszystkie zwalidowane. Publikacja: admin live aktywuj POTWIERDZAM.'


def summary(service):
    active=service.active['v24_rules']
    draft=service.draft['v24_rules']
    summary=[]
    for name in ('professions','uoss','summons','cap','events','story','world'):
        summary.append(f'{name}: aktywne {len(active[name])}, projekt {len(draft[name])}')
    return ('OLC 36–43. '+ '; '.join(summary)+'. Zmiany tylko przez DRAFT; '+
            'sprawdz, porownaj, aktywuj POTWIERDZAM. Cofnij pojedyncze pole: auto. '+
            'pakietfach: nowafach(8 pól) | fachreceptura(8 pól); '+
            'pakietzmian skille/pokoje/receptury/questy/przedmioty/npcs | JSON.')


def bundle_new_skills(service, raw):
    """OLC47: 1-12 genuine new abilities with existing status/element mechanics.

    JSON records: id,class,name,kind,unlock,mana,mult,scale,desc,
    optional element/status. All modifications remain one unpublished draft.
    """
    from systems.live_olc24_revolution import stage_skill_combo
    try:
        rows=json.loads(raw)
    except (ValueError,TypeError) as exc:
        raise ValueError('pakietskilli: lista JSON obiektów.') from exc
    if type(rows) is not list or not 1<=len(rows)<=12:
        raise ValueError('pakietskilli: 1–12 obiektów.')
    required={'id','class','name','kind','unlock','mana','mult','scale','desc'}
    snapshot=copy.deepcopy(service.draft)
    try:
        for row in rows:
            if type(row) is not dict or not required<=set(row) or not set(row)<=required|{'element','status'}:
                raise ValueError('pakietskilli: zła definicja skilla.')
            if row['id'] in service.draft['skills']:
                raise ValueError('pakietskilli: ID już występuje w projekcie.')
            service.stage_new_skill(row['id'],row['class'],row['name'],row['kind'],
                row['unlock'],row['mana'],row['mult'],row['scale'],row['desc'])
            if 'status' in row or 'element' in row:
                if 'status' in row and 'element' in row:
                    stage_skill_combo(service,row['id'],row['element'],
                        json.dumps(row['status'],ensure_ascii=False))
                elif 'element' in row:
                    service.stage_edit('skill',row['id'],'element',row['element'])
                else:
                    service.stage_edit('skill',row['id'],'olc_status',
                        json.dumps(row['status'],ensure_ascii=False))
    except Exception:
        service.draft=snapshot
        raise
    return f'OLC47: przygotowano {len(rows)} nowych skilli w DRAFT. sprawdz, aktywuj POTWIERDZAM.'
