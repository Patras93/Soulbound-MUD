# -*- coding: utf-8 -*-
"""v65: real UOSS source status-proof and helper-passive rules, on detached LAB copies.

Only canonical catalog statuses/passives, never a guessed UOSS rotation.
NEVER calls live combat, world or database methods. No production fight parity claim.
"""
from __future__ import annotations
import copy
from types import SimpleNamespace
from data.items import ITEMS
from systems.admin_guardian9_v4300 import _state,_sync_actor
from world.uoss_superboss_runtime import (
    superboss_source_status_v11162, superboss_apply_source_status_v11173,
    superboss_helper_passives_v11174, superboss_helper_profile_v11137,
)

HELP=('ADMIN LIVE POMOC 20: arena uoss ekwipunek - nazwy ochron statusowych z '
      'testowego EQ; arena uoss status NAZWA UMIEJETNOSCI - sprawdz rzeczywista '
      'funkcje odpornosci UOSS na kopii; arena uoss pasywy - sprawdz pasywne '
      'reguly pomocnika z UOSS, bez zmian areny. Najpierw arena start, '
      'opcjonalnie arena zaloz ID POTWIERDZAM. Statusy i pasywy pochodza '
      'z kodu silnika UOSS; pozostala walka nadal modelowa, nie 1:1.')


def _replica(session):
    current=_state(session)
    if '_guardian10_rng' not in current:raise ValueError('Najpierw: admin live arena start BOSS HP ATAK.')
    clone=copy.deepcopy(current)
    _sync_actor(clone)
    return clone


def _gear_proofs(state):
    rows=state['actor8'].equipped_item_rows()
    selected=state.get('_guardian11_build',{}).get('items',{})
    parts=[]
    all_proofs=set()
    for slot,ident in sorted(selected.items()):
        item=ITEMS.get(ident,{})
        normalized=tuple(sorted(str(v).lower().replace("'",'').replace(' ','_')
                                for v in item.get('status_proof',())))
        all_proofs.update(normalized)
        parts.append(f'{slot}: {ident} [{",".join(normalized) or "bez odpornosci"}]')
    # Sanity guard: never report an immunity from a non-equipped item.
    assert len(rows)==len(parts), 'Niekompletna lista testowego EQ.'
    return parts,all_proofs


def _equipment(session):
    state=_replica(session)
    entries,proofs=_gear_proofs(state)
    return ('ARENA UOSS EQ: '+('; '.join(entries) if entries else 'brak testowego EQ')+
            f'; odpornosci [{", ".join(sorted(proofs)) or "brak"}]. '
            'To tylko sprzet LAB, bez odczytu ekwipunku gracza i bez zapisow.')


def _status(session,ability):
    if not ability or len(ability)>90:raise ValueError('Podaj nazwe zdolnosci UOSS (do 90 znakow).')
    state=_replica(session)
    template=state['template']
    status=superboss_source_status_v11162(template,ability)
    if status is None:
        raise ValueError('Ten boss nie ma zdefiniowanego w UOSS statusu dla zdolnosci: '+ability[:50])
    result=superboss_apply_source_status_v11173(state['actor8'],template,ability)
    if not isinstance(result,dict):raise ValueError('Brak danych o statusie ze zrodla UOSS.')
    _,proofs=_gear_proofs(state)
    decision=('NIEPEWNE (nie mozna zweryfikowac EQ)' if result.get('verification_failed')
              else 'ZABLOKOWANY PRZEZ EQ' if result.get('blocked')
              else 'NALOZONY NA KOPIE')
    return (f'ARENA UOSS STATUS: {ability} -> {status}, {decision}; '
            f'odpornosc EQ [{", ".join(sorted(proofs)) or "brak"}]. '
            'Wynik z funkcji produkcyjnej UOSS; bez tury, zmiany areny, RNG i postaci.')


def _passives(session):
    state=_replica(session)
    actor=state['actor8']; mob=state['boss']; template=state['template']
    profile=superboss_helper_profile_v11137(actor,template)
    events=superboss_helper_passives_v11174(actor,template,mob)
    helper=profile['name'] if profile else 'brak aktywnego pomocnika'
    effects=[]
    if getattr(mob,'uoss_power_breakdown_target_scope_v11196',None)=='enemy_only':
        effects.append('Power Breakdown na bossie, nie na postaci')
    if getattr(mob,'uoss_ignore_helper_target_v11174',False):
        effects.append('boss ignoruje pomocnika jako cel')
    return (f'ARENA UOSS PASYWY: boss {state["name"]}, pomocnik {helper}; '
            f'{"; ".join(events) if events else "brak aktywowanych zdarzen"}; '
            f'{"; ".join(effects) if effects else "brak dodatkowych flag"}. '
            'Odczyt tylko z funkcji UOSS na kopii; nie symuluje niepodanych obrazen.')


async def dispatch_v65(session,group,raw):
    bits=str(raw or '').strip().split()
    if not ((group=='pomoc' and bits==['20']) or
            (group=='arena' and len(bits)>=2 and bits[0]=='uoss')):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':message=HELP
        elif len(bits)==2 and bits[1]=='ekwipunek':message=_equipment(session)
        elif len(bits)>=3 and bits[1]=='status':message=_status(session,' '.join(bits[2:]))
        elif len(bits)==2 and bits[1]=='pasywy':message=_passives(session)
        else:raise ValueError('arena uoss ekwipunek / status NAZWA UMIEJETNOSCI / pasywy.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,AssertionError) as exc:
        message='ADMIN LIVE V65: '+str(exc)[:300]
    await session.send(message)
    return True
