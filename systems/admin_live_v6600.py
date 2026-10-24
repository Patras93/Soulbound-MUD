# -*- coding: utf-8 -*-
"""Source UOSS helper action selection on a private, detached laboratory copy.

The source routine chooses one action per boss round; this inspection does not
execute actual damage/healing/world effects. Only source-defined, exact Popoi
mana restoration and Primm Bubble multiplier are modelled on the private actor.
No real Session, DB, world, rewards, tick loop or other player are accessed.
"""
from __future__ import annotations
from systems.admin_live_v6500 import _replica
from systems.admin_guardian7_v4100 import _number
from world.uoss_superboss_runtime import (
    superboss_helper_action_v1146, superboss_helper_exact_utility_v11183,
    superboss_helper_profile_v11137,
)

HELP=('ADMIN LIVE POMOC 21: arena uoss pomocnik - wybor akcji pomocnika UOSS '
      'w obecnej turze (bez skutkow walki); arena uoss pomocnik tura N - wybor '
      'w podanej turze; arena uoss pomocnik prognoza HP MANA [TURA] - podglad '
      'decyzji pomocnika dla podanego testowego HP i many; arena uoss pomocnik '
      'seria N [OD_TURY] - do 12 kolejnych wyborow na prywatnej kopii. '
      'Pomocnicy: Primm, Popoi, Byblos, Montblanc, Seifer. Zrodlo UOSS wybiera '
      'akcje; tylko scisle zdefiniowane efekty Popoi/Primm otrzymuja liczby. '
      'To nie jest produkcyjna walka 1:1. Nie ma prawdziwych nagrod ani zapisow.')


def _preview(session, turns=1, start=None, hp=None, mana=None):
    # _replica deep-copies all lab state and binds actor's party to the replica.
    state=_replica(session)
    actor=state['actor8']
    mob=state['boss']
    template=state['template']
    profile=superboss_helper_profile_v11137(actor,template)
    if not profile:
        return ('ARENA UOSS POMOCNIK: brak pomocnika dopuszczonego dla tego bossa. '
                'Uruchom arena start BOSS HP ATAK POMOCNIK. Arena bez zmian.')
    build=state.get('_guardian11_build',{})
    if not isinstance(build,dict): build={}
    # A fresh LAB encounter has no class build: use the detached actor's
    # baseline mana pool. Explicitly selected class/mana (even zero) wins.
    if build.get('class'):
        max_mp=int(build.get('max_mana',0))
        cur_mp=int(build.get('mana',0))
    else:
        max_mp=int(actor.max_mana())
        cur_mp=int(actor.current_mana)
    if max_mp<0 or max_mp>10**12 or cur_mp<0 or cur_mp>max_mp:
        raise ValueError('Nieprawidlowa testowa pula many.')
    actor._max_mana=max_mp
    actor.current_mana=cur_mp
    if hp is not None: actor.current_hp=_number(hp,1,state['hero_max'])
    if mana is not None: actor.current_mana=_number(mana,0,max_mp) if max_mp else (0 if str(mana)=='0' else _reject_mana())
    # A preview of a fresh encounter has round 0; source helper decisions start at 1.
    first=_number(start,1,250) if start is not None else max(1,int(state['round']))
    turns=_number(turns,1,12)
    if first+turns-1>250:raise ValueError('Zakres przekracza 250 tur bezpiecznego LAB.')
    results=[]
    for number in range(first,first+turns):
        mob.combat_turn=number
        action=superboss_helper_action_v1146(actor,template,mob)
        if action is None:
            results.append(f'{number}: brak akcji');continue
        ability=str(action['ability'])
        note='wybor, brak symulacji jego skutkow'
        if ability in ('Faerie Walnut','Bubble'):
            exact=superboss_helper_exact_utility_v11183(actor,template,ability)
            if exact:
                if 'mana_restored' in exact:
                    note=f'odnowiono na kopii {exact["mana_restored"]} many'
                elif 'max_hp_multiplier' in exact:
                    # As in the live Soulbound helper caller, Bubble sets
                    # its active marker; ONLY on our detached LAB actor.
                    actor.uoss_helper_bubble_v1146=True
                    note=f'znacznik zrodla mnoznika max HP x{exact["max_hp_multiplier"]:.2f}'
        # Source guarantees at most one action per boss action cycle.
        if superboss_helper_action_v1146(actor,template,mob) is not None:
            raise AssertionError('Zrodlo UOSS wybralo dwie akcje pomocnika w jednej turze.')
        results.append(f'{number}: {action["name"]} - {ability} ({note})')
    return (f'ARENA UOSS POMOCNIK {profile["name"]}; HP {actor.current_hp}/{actor.max_hp()}, '
            f'mana {actor.current_mana}/{actor.max_mana()}, tury {first}-{first+turns-1}: '
            +'; '.join(results)
            +'. Wybory ze zrodla UOSS na kopii; nie symuluja pelnej walki. '
             'Biezaca arena, RNG, gracze i SQLite bez zmian.')


def _reject_mana():
    raise ValueError('Postac bez maksymalnej many: dozwolone tylko 0.')


async def dispatch_v66(session,group,raw):
    bits=str(raw or '').strip().split()
    if not ((group=='pomoc' and bits==['21']) or
            (group=='arena' and len(bits)>=2 and bits[:2]==['uoss','pomocnik'])):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':msg=HELP
        elif len(bits)==2:msg=_preview(session)
        elif len(bits)==4 and bits[2]=='tura':msg=_preview(session,start=bits[3])
        elif len(bits) in (5,6) and bits[2]=='prognoza':
            msg=_preview(session,hp=bits[3],mana=bits[4],start=bits[5] if len(bits)==6 else None)
        elif len(bits) in (4,5) and bits[2]=='seria':
            msg=_preview(session,turns=bits[3],start=bits[4] if len(bits)==5 else None)
        else:raise ValueError('arena uoss pomocnik / tura N / prognoza HP MANA [TURA] / seria N [OD_TURY].')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,AssertionError) as exc:
        msg='ADMIN LIVE V66: '+str(exc)[:300]
    await session.send(msg)
    return True
