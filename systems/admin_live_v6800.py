# -*- coding: utf-8 -*-
"""v68 UOSS production helper target selection + party support on detached actors.

Do NOT call production Session combat coroutine, inventory, XP, SQL, world, or I/O.
Use exact production target-selection logic; apply only verified support math from
player/session_methods_v4200/combatrealtime_part01.py to detached party snapshots.
Offensive effects remain unspecified (no guessed damage). Never mutate live arena
except explicitly requested TEST member HP/MP state, which is session-local.
"""
from __future__ import annotations
from types import SimpleNamespace
from systems.admin_live_v6500 import _replica
from systems.admin_live_ultimate_v4600 import _int
from systems.admin_guardian9_v4300 import _state
from world.uoss_superboss_runtime import (
    superboss_helper_profile_v11137, superboss_helper_action_v1146,
    superboss_healing_blocked_v11179, superboss_helper_passives_v11174,
    superboss_helper_exact_utility_v11183,
)

HELP=('ADMIN LIVE POMOC 23: arena uoss druzyna wsparcie [TURY] [HP_LIDERA MANA_LIDERA] '
      '- zrodłowy wybor celu oraz reguly wsparcia UOSS na kopii calej druzyny (1-12 tur). '
      'arena uoss druzyna stan NUMER HP MANA POTWIERDZAM - ustawia RANY I MANA '
      'wylacznie testowego czlonka druzyny, NUMER 1-4 (najpierw arena druzyna dodaj). '
      'Limit pomocnika UOSS: lider plus maksymalnie 2 czlonkow testowych. '
      'Cure 23 procent, MP 20/25/8 procent, Bubble +50 procent max HP u calej '
      'druzyny, Power Breakdown tylko boss. Bez prawdziwego EXP, RNG i DB. '
      'Ofensywne obrazenia NIEOBLICZONE, brak parity 1:1 calej walki.')


def _party_actors(state, leader_hp=None, leader_mp=None):
    leader=state['actor8']; boss=state['boss']
    spec=state.get('_guardian11_build',{})
    if not isinstance(spec,dict):spec={}
    if spec.get('class'):
        mana_max=int(spec.get('max_mana',0))
        mana_now=int(spec.get('mana',0))
    else:
        mana_max=int(leader.max_mana());mana_now=int(leader.current_mana)
    base_hp=int(state['hero_max'])
    if not (1<=base_hp<=10**12 and 0<=mana_now<=mana_max<=10**12):
        raise ValueError('Nieprawidlowy stan lidera w LAB.')
    leader._max_hp=base_hp
    leader._max_mana=mana_max
    leader.current_hp=(int(state['hero_hp']) if leader_hp is None else _int(leader_hp,1,base_hp,'HP lidera'))
    leader.current_mana=(mana_now if leader_mp is None else _int(leader_mp,0,mana_max,'MP lidera'))
    members=[leader]
    leader.character.name='Lider'
    for index, data in enumerate(state.get('_adminlive46_party',[]),1):
        hp_max=int(data['hp']); mp_max=int(data.get('max_mana',data['mana']))
        hp=int(data.get('_v6800_current_hp',hp_max))
        mp=int(data.get('_v6800_current_mana',data['mana']))
        if not (1<=hp<=hp_max<=10**12 and 0<=mp<=mp_max<=10**12):
            raise ValueError('Nieprawidlowy stan postaci LAB numer '+str(index))
        actor=SimpleNamespace(
            current_hp=hp, current_mana=mp, _max_hp=hp_max, _max_mana=mp_max,
            account_id=123456+index, closed=False,
            character=SimpleNamespace(room_id='__guardian8_private__', name=f'Postac {index}'))
        members.append(actor)
    if len(members)>3:
        raise ValueError('UOSS pozwala korzystac z pomocnika przy najwyzej 3 graczach; usun nadmiarowe testowe postacie.')
    # Production helpers check the source's local-party size, lowest HP/MP,
    # and per-mob marker. The fake server is owned ONLY by our replica.
    server=leader.server
    server.party_sessions=lambda *_a,**_kw:members
    for item in members:
        item.server=server
        # Make max HP reflect source Bubble marker on isolated actor INSTANCE.
        item.max_hp=lambda x=item: (x._max_hp*3)//2 if getattr(x,'uoss_helper_bubble_v1146',False) else x._max_hp
        item.max_mana=lambda x=item: x._max_mana
    boss.room_id='__guardian8_private__'
    return leader,members


def _preview(session,turns='1',hp=None,mana=None):
    count=_int(turns,1,12,'liczba tur')
    state=_replica(session)
    leader,party=_party_actors(state,hp,mana)
    boss=state['boss'];template=state['template']
    profile=superboss_helper_profile_v11137(leader,template)
    if not profile:
        return ('ARENA UOSS DRUZYNA: brak pomocnika dla tego bossa/skladu. '
                'Sprawdz wybranego pomocnika, jego limit i arena start.')
    first=max(1,int(state['round']))
    if first+count-1>250:raise ValueError('Maksymalnie 250 tur prywatnego laboratorium.')
    passives=superboss_helper_passives_v11174(leader,template,boss)
    passive_state=('Power Breakdown aktywny na bossie. ' if getattr(boss,'uoss_power_breakdown_v11174',False) else '')
    results=[]; heal_total=mp_total=unresolved=0
    for turn in range(first,first+count):
        boss.combat_turn=turn
        action=superboss_helper_action_v1146(leader,template,boss)
        if action is None:
            results.append(f'{turn}: bez akcji');continue
        ability=str(action['ability']);name=str(action['name']);target=action.get('target')
        if target is not None and target not in party:
            raise AssertionError('UOSS wskazal obcy cel poza druzyna testowa.')
        description=''
        if ability in ('Cure Water','Cure') and target is not None:
            if superboss_healing_blocked_v11179(target):
                description='leczenie zablokowane przez Nullify Healing'
            else:
                amount=min(max(0,target.max_hp()-target.current_hp),max(1,int(target.max_hp()*.23)))
                target.current_hp+=amount;heal_total+=amount
                description=f'{target.character.name} +{amount} HP'
        elif ability in ('Faerie Walnut','X-Ether') and target is not None:
            before=target.current_mana
            # Production apply_uoss_helper_turn_v1146 uses the chosen party target,
            # not the leader, and applies 20% / 25% based on ability.
            rate=.20 if ability=='Faerie Walnut' else .25
            target.current_mana=min(target.max_mana(),before+max(1,int(target.max_mana()*rate)))
            gained=target.current_mana-before
            mp_total+=gained
            description=f'{target.character.name} +{gained} MP'
        elif ability=='Bubble':
            selected=[]
            for member in party:
                if not getattr(member,'uoss_helper_bubble_v1146',False):
                    member.uoss_helper_bubble_v1146=True
                    selected.append(f'{member.character.name} {member.max_hp()} max HP')
            description='Bubble: '+(', '.join(selected) if selected else 'juz aktywny')
        elif ability=='Dryad Preach':
            total=0
            for member in party:
                gain=min(max(0,member.max_mana()-member.current_mana),max(1,int(member.max_mana()*.08)))
                member.current_mana+=gain;total+=gain
            mp_total+=total
            description=f'odnowienie calej druzyny +{total} MP'
        elif ability=='Power Breakdown':
            boss.uoss_power_breakdown_v11174=True
            boss.uoss_power_breakdown_target_scope_v11196='enemy_only'
            description='oslabienie tylko na bossie'
        else:
            unresolved+=1
            description='atak: obrazenia NIEOBLICZONE'
        # The production selector marks the mob before any awaited action.
        if superboss_helper_action_v1146(leader,template,boss) is not None:
            raise AssertionError('Pomocnik wykonal 2 akcje podczas jednej tury.')
        results.append(f'{turn}: {name} {ability} -> {description}')
    summary=', '.join(f'{m.character.name}: HP {m.current_hp}/{m.max_hp()}, MP {m.current_mana}/{m.max_mana()}' for m in party)
    return (f'ARENA UOSS DRUZYNA {len(party)} graczy, pomocnik {profile["name"]}, '
            f'tury {first}-{first+count-1}; leczenie {heal_total} HP, mana {mp_total} MP, '
            f'ataki bez liczb {unresolved}. '+passive_state+(' '.join(passives)+' ' if passives else '')+summary+'. '+'; '.join(results)+
            '. Zrodlo wybiera akcje i cel, skutki wsparcia z rzeczywistego Soulbound. '
            'Biezaca arena, EXP, RNG, SQLite i prawdziwi gracze BEZ ZMIAN. Nie 1:1.')


def _set_member(session,index,hp,mp):
    state=_state(session)
    if '_guardian10_rng' not in state:
        raise ValueError('Najpierw rozpocznij arene UOSS.')
    members=state.get('_adminlive46_party',[])
    number=_int(index,1,len(members),'numer testowego czlonka')
    entry=members[number-1]
    current_hp=_int(hp,1,int(entry['hp']),'HP')
    current_mp=_int(mp,0,int(entry.get('max_mana',entry['mana'])),'MP')
    entry['_v6800_current_hp']=current_hp
    entry['_v6800_current_mana']=current_mp
    return f'ARENA UOSS DRUZYNA TEST {number}: HP {current_hp}/{entry["hp"]}, MP {current_mp}/{entry.get("max_mana",entry["mana"])}. Tylko prywatny stan LAB.'


async def dispatch_v68(session,group,raw):
    bits=str(raw or '').strip().split()
    matches=(group=='pomoc' and bits==['23']) or (group=='arena' and len(bits)>=3 and bits[:2]==['uoss','druzyna'])
    if not matches:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':message=HELP
        elif bits[2]=='wsparcie' and len(bits)==3:message=_preview(session)
        elif bits[2]=='wsparcie' and len(bits)==4:message=_preview(session,bits[3])
        elif bits[2]=='wsparcie' and len(bits)==6:message=_preview(session,bits[3],bits[4],bits[5])
        elif bits[2]=='stan' and len(bits)==7 and bits[6]=='POTWIERDZAM':
            message=_set_member(session,bits[3],bits[4],bits[5])
        else:raise ValueError('arena uoss druzyna wsparcie [TURY] [HP MANA] / stan NUMER HP MANA POTWIERDZAM')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,AssertionError) as exc:
        message='ADMIN LIVE V68: '+str(exc)[:280]
    await session.send(message)
    return True
