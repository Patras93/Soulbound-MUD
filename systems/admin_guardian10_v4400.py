# -*- coding: utf-8 -*-
"""Guardian 10: locally seeded, reversible UOSS rehearsal and quest review.

All battle state is on a detached session-local lab. We temporarily borrow the
Python PRNG within *synchronous* lab operations and restore it on all paths.
The source-rule battle is not a faithful reproduction of production player AI,
equipment, timing, rewards or the full production fight loop.
"""
from __future__ import annotations

import copy
import hashlib
import random
from types import SimpleNamespace
from systems.admin_guardian7_v4100 import _number
from systems.admin_guardian8_v4200 import _start
from systems.admin_guardian9_v4300 import (
    _state, _sync_actor, _private_turn, _snapshot, _restore,
    _draft_page, _dependencies, _compare_batch,
)
from systems.admin_guardian5_v3900 import _quest_compare, _quest_rewards, _quest_diag

_MAX_RUN=20
_HELP={
    '1':('GUARDIAN10 pomoc 1/3: arena start BOSS_ID HP ATAK [HELPER]; '
         'arena atak [CEL]; arena magia ZYWIOŁ [CEL]; arena obrona; arena lecz; arena oczysc; '
         'arena seria ILE [atak/obrona/lecz]; arena prognoza ILE [atak/obrona/lecz]; '
         'arena porownaj ILE; arena ziarno LICZBA POTWIERDZAM. Wszystko LAB, zero nagrod.'),
    '2':('GUARDIAN10 pomoc 2/3: arena migawka; arena przywroc POTWIERDZAM; '
         'arena status; arena raport; arena dziennik [STRONA]; arena wyjdz. '
         'Kazda arena ma osobna losowosc. Migawka zapamietuje tez losowosc.'),
    '3':('GUARDIAN10 pomoc 3/3: questy nagrody ID; questy diagnoza ID; '
         'questy porownaj ID; questy draft [STRONA]; questy zaleznosci ID; '
         'questy seria roznice ID | POLE | WARTOSC ; ... . '
         'Bez zapisu i publikacji. Arena to model wybranych zasad UOSS, NIE pelny '
         'silnik produkcyjny, realne EQ, wszystkie skille gracza lub realne ticki.'),
}


def _seed_params(*args):
    raw='\x1f'.join(map(str,args)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')


def _local_rng(state, operation):
    """Run synchronous sourced UOSS rules on an isolated RNG state.

    No await while global state is borrowed. All changes, including failures,
    restore the production PRNG. A failed lab turn rolls back lab PRNG as well.
    """
    world_rng=random.getstate()
    prior=state['_guardian10_rng']
    random.setstate(prior)
    try:
        value=operation()
        state['_guardian10_rng']=random.getstate()
        return value
    finally:
        random.setstate(world_rng)


def _lab_start10(session, service, boss, hp, atk, helper='brak'):
    # Start effects may also consume random; keep them inside a private stream.
    seed=_seed_params(boss,hp,atk,helper)
    world_rng=random.getstate()
    random.setstate(random.Random(seed).getstate())
    try:
        out=_start(session,service,boss,hp,atk,helper)
        state=_state(session)
        state['_guardian10_rng']=random.getstate()
        state['_guardian10_seed']=seed
        _sync_actor(state)
        session.guardian9_snapshot=None
        return out.replace('ARENA8','ARENA10')+' Osobne RNG LAB, bez zmian RNG serwera.'
    finally:
        random.setstate(world_rng)


def _lab_turn10(session,action='atak',target='boss',element=None):
    state=_state(session)
    if '_guardian10_rng' not in state:raise ValueError('Uruchom nowa arene10.')
    rng_before=state['_guardian10_rng']
    try:
        return _local_rng(state, lambda:_private_turn(session,action,target,element)).replace('ARENA9','ARENA10')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError):
        session.guardian7_lab['_guardian10_rng']=rng_before
        raise


def _evaluate(session, count, action, preview=True):
    count=_number(count,1,_MAX_RUN)
    if action not in ('atak','obrona','lecz'):
        raise ValueError('Akcja: atak, obrona lub lecz.')
    source=_state(session)
    if source.get('finished') or source['round']>=250:raise ValueError('Arena zakonczona.')
    if '_guardian10_rng' not in source:raise ValueError('Uruchom arene10.')
    replica=SimpleNamespace(guardian7_lab=copy.deepcopy(source)) if preview else session
    lines=[]
    for _ in range(count):
        if replica.guardian7_lab['finished'] or replica.guardian7_lab['round']>=250:break
        lines.append(_lab_turn10(replica,action))
    state=_state(replica)
    label='PROGNOZA' if preview else 'SERIA'
    return (f'ARENA10 {label}: {len(lines)}/{count} tur {action}, '
            f'runda {state["round"]}, boss HP {state["boss"].hp}/{state["boss"].max_hp}, '
            f'postac HP {state["hero_hp"]}/{state["hero_max"]}, '
            f'obrazenia zadane {state["total_dealt"]}, otrzymane {state["total_taken"]}; '
            +('Arena oraz RNG bez zmian.' if preview else 'Zmieniono tylko symulacje.'))


def _compare(session,count):
    count=_number(count,1,_MAX_RUN)
    original=_state(session)
    original_state=copy.deepcopy(original)
    results=[]
    for action in ('atak','obrona','lecz'):
        clone=SimpleNamespace(guardian7_lab=copy.deepcopy(original_state))
        # Compare exactly the same starting state and local RNG stream.
        _evaluate(clone,count,action,False)
        end=clone.guardian7_lab
        results.append(f'{action}: tur {end["round"]-original["round"]}, '
                       f'HP gracza {end["hero_hp"]}, boss HP {end["boss"].hp}, '
                       f'zadane +{end["total_dealt"]-original["total_dealt"]}, '
                       f'otrzymane +{end["total_taken"]-original["total_taken"]}')
    return ('ARENA10 POROWNAJ '+str(count)+' tur: '+'; '.join(results)+'. '
            'Trzy warianty z jednakowego stanu RNG; bez modyfikacji areny i serwera. '
            'Leczenie i obrona sa modelowe, nie rzeczywistymi skillami postaci.')


def _seed_change(session,seed):
    seed=_number(seed,0,4294967295)
    state=_state(session)
    state['_guardian10_seed']=seed
    state['_guardian10_rng']=random.Random(seed).getstate()
    return f'ARENA10 ZIARNO {seed}: zmieniono tylko RNG prywatnej areny. Nie ruszono serwera.'


async def handle_guardian10(session, raw):
    parts=str(raw or '').strip().split(maxsplit=1)
    if not parts or parts[0].casefold()!='guardian10':return False
    if not session.is_admin():
        await session.send('GUARDIAN10: tylko administrator-wlasciciel.');return True
    service=session.server.live_content_v1204
    rest=parts[1].strip() if len(parts)>1 else 'pomoc 1'
    args=rest.split()
    try:
        mode=args[0].casefold() if args else 'pomoc'
        if mode=='pomoc':
            page=args[1] if len(args)>1 else '1'
            if len(args)>2 or page not in _HELP:raise ValueError('Pomoc strony 1, 2, 3.')
            output=_HELP[page]
        elif mode=='status' and len(args)==1:
            output='GUARDIAN10: '+('arena aktywna' if getattr(session,'guardian7_lab',None) and '_guardian10_rng' in session.guardian7_lab else 'arena nieaktywna')+'; RNG tylko LAB, nagrody 0.'
        elif mode=='arena':
            op=args[1].casefold() if len(args)>1 else ''
            if op=='start' and len(args) in (5,6):
                output=_lab_start10(session,service,args[2],args[3],args[4],args[5] if len(args)==6 else 'brak')
            elif op in ('atak','obrona','lecz','oczysc') and (len(args)==2 or (len(args)==3 and op=='atak')):
                output=_lab_turn10(session,op,args[2] if len(args)==3 else 'boss')
            elif op=='magia' and len(args) in (3,4):
                output=_lab_turn10(session,'magia',args[3] if len(args)==4 else 'boss',args[2])
            elif op in ('seria','prognoza') and len(args) in (3,4):
                output=_evaluate(session,args[2],args[3].casefold() if len(args)==4 else 'atak',op=='prognoza')
            elif op=='porownaj' and len(args)==3:output=_compare(session,args[2])
            elif op=='ziarno' and len(args)==4 and args[3]=='POTWIERDZAM':output=_seed_change(session,args[2])
            elif op=='migawka' and len(args)==2:
                _state(session);output=_snapshot(session).replace('ARENA9','ARENA10')
            elif op=='przywroc' and len(args)==3 and args[2]=='POTWIERDZAM':
                output=_restore(session).replace('ARENA9','ARENA10')
            elif op=='status' and len(args)==2:
                s=_state(session);output=(f'ARENA10 runda {s["round"]}; boss {s["name"]} '
                    f'HP {s["boss"].hp}/{s["boss"].max_hp}; postac HP {s["hero_hp"]}/{s["hero_max"]}; '
                    f'pomocnicy {sum(e["hp"]>0 for e in s["adds"])}; '
                    f'seed {s.get("_guardian10_seed", "brak")}; '
                    f'{"KONIEC" if s["finished"] else "TRWA"}. Bez prawdziwych nagrod.')
            elif op=='raport' and len(args)==2:
                s=_state(session);output=(f'ARENA10 RAPORT {s["name"]}: rund {s["round"]}, '
                    f'zadane {s["total_dealt"]}, otrzymane {s["total_taken"]}, '
                    f'HP bossa {s["boss"].hp}, HP postaci {s["hero_hp"]}; '
                    'brak dropu i zapisow, AI/szkody/obrona sa tylko czesciowym modelem.')
            elif op=='dziennik' and len(args) in (2,3):
                from systems.admin_guardian7_v4100 import _lab_log
                _state(session)
                output=_lab_log(session,args[2] if len(args)==3 else '1').replace('ARENA7','ARENA10')
            elif op=='wyjdz' and len(args)==2:
                session.guardian7_lab=None;session.guardian9_snapshot=None
                output='ARENA10: usunieto testowe stany i migawke. Bez zmian postaci.'
            else:raise ValueError(_HELP['1'])
        elif mode=='questy':
            sub=args[1].casefold() if len(args)>1 else ''
            if sub in ('nagrody','diagnoza','porownaj','zaleznosci') and len(args)==3:
                if sub=='nagrody':output=_quest_rewards(service,args[2])
                elif sub=='diagnoza':output=_quest_diag(service,args[2])
                elif sub=='porownaj':output=_quest_compare(service,args[2])
                else:output=_dependencies(service,args[2])
            elif sub=='draft' and len(args) in (2,3):output=_draft_page(service,args[2] if len(args)==3 else '1')
            elif sub=='seria' and len(args)>3:
                sections=rest.split(None,3)
                if len(sections)!=4 or sections[2].casefold()!='roznice':raise ValueError(_HELP['3'])
                output=_compare_batch(service,sections[3])
            else:raise ValueError(_HELP['3'])
        else:raise ValueError('Wpisz admin guardian10 pomoc 1, 2, 3.')
        await session.send(output)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        await session.send('GUARDIAN10: '+str(exc)[:320])
    return True
