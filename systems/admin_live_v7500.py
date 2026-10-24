# -*- coding: utf-8 -*-
"""v75: atomic native UOSS mechanics editor.

This stages *existing, executed* OLC24/32/33/34 runtime policies together.
It neither simulates combat nor executes user code; active rules remain intact
until the owner uses the established OLC publish command.
"""
from __future__ import annotations

import copy
import re

from systems.admin_live_v7100 import _plan, _commit, _undo
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

_IDS = re.compile(r'[a-z0-9_]{1,90}\Z', re.ASCII)
_NUM = re.compile(r'[0-9]{1,8}\Z', re.ASCII)
SLOT='adminlive7500_uoss_plan'
UNDO='adminlive7500_uoss_undo'
HELP = (
    'ADMIN LIVE POMOC 35: boss uoss mechaniki karta ID; '
    'boss uoss mechaniki plan ID | fazy=75:2:160,40:3:220;leczenie=35:4:3;'
    'furia=3:115:4;skala=150:130; '
    'boss uoss mechaniki zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'BRAK po rownosci usuwa wybrana regule. '
    'Fazy: procent_HP:co_ile_atakow:procent_obrazen (1-5); '
    'leczenie: ponizej_HP:co_ile_atakow:procent_HP; '
    'furia: co_ile_atakow:procent_na_stos:liczba_stosow; '
    'skala: procent_HP:procent_obrazen. '
    'DRAFT, bez EXP, dropow, SQLite i prawdziwej walki w edytorze. '
    'Aktywacja OLC wymaga osobnej komendy admin live sprawdz i aktywuj POTWIERDZAM.'
)


def _boss(key):
    if not _IDS.fullmatch(key) or key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
        raise ValueError('Nieznany ID skryptowanego superbossa (boss uoss lista).')
    return key


def _integers(text, count, label):
    parts = text.split(':')
    if len(parts) != count or any(not _NUM.fullmatch(v) for v in parts):
        raise ValueError(f'{label}: wymagane {count} liczby rozdzielone dwukropkiem.')
    return [int(v) for v in parts]


def card(service, key):
    _boss(key)
    result=[]
    for section,label in (('v24_rules','skala'),('v32_rules','fazy'),
                          ('v33_rules','leczenie'),('v34_rules','furia')):
        active=service.active[section]['uoss'].get(key)
        draft=service.draft[section]['uoss'].get(key)
        # Bounded one-line NVDA text. Explicitly show active and draft status.
        result.append(f'{label}: aktywne={str(active)[:220] if active else "AUTO"}, '
                      f'DRAFT={str(draft)[:220] if draft else "AUTO"}')
    return (f'BOSS UOSS MECHANIKI {key}: '+'; '.join(result)+
            '. Reguly egzekwowane przez silnik walki po osobnej publikacji OLC. Bez zmian.')


def plan(session,service,raw):
    setattr(session,SLOT,None)
    if raw.count('|')!=1 or not 1<=len(raw)<=1150:
        raise ValueError('Format: boss uoss mechaniki plan ID | fazy=...;leczenie=...;furia=...;skala=...')
    key, args=(part.strip() for part in raw.split('|',1))
    _boss(key)
    operations=args.split(';')
    if not 1<=len(operations)<=4 or any(not op.strip() for op in operations):
        raise ValueError('1-4 niepuste ustawienia oddzielone srednikiem.')
    before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before)
    sections={'fazy':'v32_rules','leczenie':'v33_rules',
              'furia':'v34_rules','skala':'v24_rules'}
    seen=set()
    descriptions=[]
    for op in operations:
        if op.count('=')!=1:
            raise ValueError('Wpisz pole=wartosc, np. leczenie=35:4:3.')
        label,value=(v.strip() for v in op.split('=',1))
        if label not in sections or label in seen:
            raise ValueError('Pole nieznane lub powtorzone: fazy, leczenie, furia, skala.')
        seen.add(label)
        dest=candidate[sections[label]]['uoss']
        if value.upper()=='BRAK':
            if label=='skala':
                row=copy.deepcopy(dest.get(key,{}))
                row.pop('max_hp_percent',None)
                row.pop('damage_percent',None)
                if row:dest[key]=row
                else:dest.pop(key,None)
            else:
                dest.pop(key,None)
            descriptions.append(label+'=AUTO')
            continue
        if label=='fazy':
            specs=value.split(',')
            if not 1<=len(specs)<=5:
                raise ValueError('Fazy: od 1 do 5 wpisow.')
            phases=[]
            for spec in specs:
                hp,every,power=_integers(spec.strip(),3,'fazy')
                phases.append({'below_hp':hp,'interval':every,'damage_percent':power})
            dest[key]={'phases':phases}
            descriptions.append('fazy='+str(len(phases)))
        elif label=='leczenie':
            hp,every,restore=_integers(value,3,'leczenie')
            dest[key]={'below_hp':hp,'every':every,'restore_percent':restore}
            descriptions.append(f'leczenie={hp}:{every}:{restore}')
        elif label=='furia':
            every,power,stacks=_integers(value,3,'furia')
            dest[key]={'every':every,'stack_percent':power,'max_stacks':stacks}
            descriptions.append(f'furia={every}:{power}:{stacks}')
        else:
            hp,attack=_integers(value,2,'skala')
            row=copy.deepcopy(dest.get(key,{}))
            row.update(max_hp_percent=hp,damage_percent=attack)
            dest[key]=row
            descriptions.append(f'skala={hp}:{attack}')
    # These are the real production validators of four executable subsystems.
    service.validate(candidate)
    if candidate==before:
        raise ValueError('Brak zmian wzgledem DRAFT.')
    _plan(session,SLOT,before,service.active,candidate,'BOSS UOSS MECHANIKI')
    return (f'BOSS UOSS MECHANIKI PLAN {key}: '+', '.join(descriptions)+
            '. Zweryfikowano komplet czterech regul. Bez zapisu; '
            'boss uoss mechaniki zatwierdz POTWIERDZAM.')


async def dispatch_v7500(session,group,raw):
    parts=str(raw or '').strip().split()
    is_help=group=='pomoc' and parts==['35']
    matched=is_help or (group=='boss' and parts[:2]==['uoss','mechaniki'])
    if not matched:
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if is_help:
            answer=HELP
        elif len(parts)==4 and parts[2]=='karta':
            answer=card(service,parts[3])
        elif len(parts)>=5 and parts[2]=='plan':
            answer=plan(session,service,raw.partition('plan')[2].strip())
        elif parts==['uoss','mechaniki','zatwierdz','POTWIERDZAM']:
            answer=_commit(session,service,SLOT,UNDO)
        elif parts==['uoss','mechaniki','cofnij','POTWIERDZAM']:
            answer=_undo(session,service,SLOT,UNDO)
        elif parts==['uoss','mechaniki','anuluj']:
            setattr(session,SLOT,None)
            answer='BOSS UOSS MECHANIKI: anulowano plan.'
        else:
            raise ValueError('boss uoss mechaniki karta/plan/zatwierdz/cofnij/anuluj. Pomoc 35.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        answer='ADMIN LIVE V75: '+str(exc)[:250]
    await session.send(answer)
    return True
