# -*- coding: utf-8 -*-
"""v70.00.2: three safe operator workflows: UOSS source trace, EQ-source coverage,
and atomic obvious quest-count repairs. No production combat, XP, SQL or awards.
"""
from __future__ import annotations

import copy
from systems.admin_live_v6500 import _replica
from systems.admin_live_integrity_v4900 import _effective, _issues
from systems.admin_live_v6400 import count_preview
from systems.live_olc18_multi_objective import validate_objectives
from systems.live_quest_olc_v1209 import parse_quest_edit
from systems.admin_live_quest_refs_v6100 import _npc_catalog
from systems.infinite_equipment import (
    infinite_source_profile, infinite_equipment_variant_id,
    infinite_equipment_power_multiplier, parse_infinite_equipment_variant,
)
from systems.endless_loot_v5600 import eligible_normal_equipment_drop_v5600
from systems.quest_equipment_v6200 import quest_gear_profile_v6200
from systems.endless_chest_equipment_v5800 import chest_equipment_profile_v5800, _BASE_ITEMS
from systems.admin_live_ultimate_v4600 import _int
from core.equipment_growth_v5300 import infinite_equipment_requirement
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from world.uoss_superboss_runtime import (
    superboss_source_ability_v11162, superboss_source_status_v11162,
    superboss_exact_ability_effect_v11160, superboss_source_round_event_v11160,
    superboss_source_attack_multiplier_v11162, superboss_phase_v11137,
)

HELP = ('ADMIN LIVE POMOC 26: arena uoss reguly [TURY] [OD_TURY] - prawdziwe '
        'wybory zrodlowych umiejetnosci i znane efekty UOSS bez zgadywania damage; '
        'eq pokrycie ID_EQ [ETAP] - 8 zrodel, 4 typy skrzyn, wykrywanie luk; '
        'questy automaty skan [STRONA] / karta ID / plan [ID ...] / '
        'zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj / status. '
        'Automat poprawia TYLKO needed, gdy mozna go obliczyc z istniejacych '
        'celow multi_objective lub collect_resource_set. Maksymalnie 8 questow '
        'w planie, DRAFT, bez automatycznej publikacji i zmian SQLite. '
        'To NIE jest walka produkcyjna 1:1 ani pokrycie dowolnego bledu questa.')


def _number(value, lo, hi, name):
    raw=str(value)
    if not raw.isascii() or not raw.isdecimal() or len(raw)>11:
        raise ValueError(name+': wpisz dodatnia liczbe dziesietna.')
    v=int(raw)
    if not lo<=v<=hi:raise ValueError(f'{name}: zakres {lo}..{hi}.')
    return v


def uoss_source_trace(session, turns='6', start='1'):
    """Trace real source functions on an isolated copy; intentionally not live AI."""
    count=_number(turns,1,12,'TURY')
    first=_number(start,1,250,'OD_TURY')
    if first+count-1>250:raise ValueError('Koniec przekracza 250 tur laboratorium.')
    state=_replica(session)
    boss=state['boss'];template=state['template'];actor=state['actor8']
    reports=[];unknown=0
    # Reconstruct source one-shot flags from the first round even for a
    # mid-fight query; otherwise Odin would re-summon on every requested turn.
    for turn in range(1,first+count):
        boss.combat_turn=turn
        phase=superboss_phase_v11137(template,boss)
        ability=superboss_source_ability_v11162(template,boss)
        if ability:
            # The source emitter marks one-off summons on successful dispatch.
            # There is NO real spawn here: record only the verified one-shot flag,
            # so Odin/ Emerald do not endlessly choose their opening summon.
            if ability in ('Gungnir','Open Eye','Emerald Torpedo'):
                boss.uoss_summon_used_v1144=True
                boss.uoss_last_summon_turn_v1144=turn
            effect=superboss_exact_ability_effect_v11160(actor,template,boss,ability)
            status=superboss_source_status_v11162(template,ability)
            multiplier=superboss_source_attack_multiplier_v11162(template,ability)
            # No random summon spawning, no damage application, no production tick.
            effects=[]
            if isinstance(effect,dict):
                for key in ('damage','current_hp_fraction','countdown_rounds'):
                    if key in effect:effects.append(key+'='+str(effect[key]))
            if status:effects.append('status='+str(status))
            if multiplier!=1.0:effects.append('mnoznik_ataku='+str(multiplier))
            if not effects:
                effects.append('liczby_nieokreslone')
                if turn>=first:unknown+=1
            label=str(ability)+' ['+', '.join(effects)+']'
        else:label='atak bazowy / brak zdolnosci specjalnej'
        event=superboss_source_round_event_v11160(actor,template,boss)
        if event:label+='; '+str(event.get('name','zdarzenie'))
        if turn>=first:reports.append(f'{turn}: faza {phase}; {label}')
    return (f'ARENA UOSS REGULY: {state["name"]}, tury {first}-{first+count-1}; '
            +'; '.join(reports)+f'. Bez liczb dla {unknown} umiejetnosci. '
            'Prawdziwe reguly z kodu Soulbound na kopii. NIE: pelny damage, '
            'AI, kolejka akcji, przywolania losowe, walka 1:1. '
            'Biezaca arena, SQLite, EXP, RNG bez zmian.')


_SOURCES = (
    ('krypta','crypt',lambda v:{'crypt_floor':v}),
    ('mityczna_krypta','mythiccrypt',lambda v:{'mythic_crypt_floor':max(1,(v-200)+1)}),
    ('wieza_astralna','tower',lambda v:{'astral_floor':v}),
    ('mityczna_wieza','mythictower',lambda v:{'mythic_astral_floor':max(1,(v-200)+1)}),
    ('magitek','magitek',lambda v:{'magitek_floor':max(1,(v-110+6)//7)}),
    ('swiat','world',lambda v:{'level':v}),
)


def equipment_coverage(item_id,level='900'):
    if not isinstance(item_id,str) or not 1<=len(item_id)<=100 or not all(c.isascii() and (c.isalnum() or c in '_-') for c in item_id):
        raise ValueError('Wpisz poprawne ID przedmiotu (litery, cyfry, _ i -).')
    lvl=_number(level,801,1_000_000,'ETAP')
    if not eligible_normal_equipment_drop_v5600(item_id,{'level':lvl}):
        raise ValueError('Nieznane zwykle EQ lub przedmiot wykluczony (unikat, material, waluta).')
    # Check actual generator mathematics without item registration or any roll.
    rows=[]
    for title,expected,maker in _SOURCES:
        seed=maker(lvl)
        profile=infinite_source_profile(seed)
        if profile is None or profile['source']!=expected:
            rows.append(f'{title}: BRAK etapu ponad 600')
            continue
        rank=int(profile['rank'])
        variant=infinite_equipment_variant_id(item_id,profile['source'],profile['grade'],rank)
        if parse_infinite_equipment_variant(variant)['base_id']!=item_id:
            raise ValueError('Blad identyfikatora wariantu: '+title)
        rows.append(f'{title}: etap {profile["effective_stage"]}, moc x{infinite_equipment_power_multiplier(rank,profile["grade"]):.3f}, bieg {infinite_equipment_requirement(profile["effective_stage"])}')
    # Crafting requires real profession/tool level AND the operator-defined EQ cap.
    from systems.endless_crafting_v5500 import craft_stage_v5500
    forge=craft_stage_v5500(lvl,lvl)
    rows.append('rzemioslo: '+(f'etap {forge}' if forge else 'WYLACZONE lub limit EQ nie zezwala na ten etap'))
    qp=quest_gear_profile_v6200(item_id,{'recommended_level':lvl})
    rows.append('quest: '+(f'etap {qp["effective_stage"]}, Rezonans {qp["rank"]}' if qp else 'BRAK: nagroda wykluczona'))
    chests=[]
    for name,kind,fl in (('krypta','crypt',lvl),('mityczna_krypta','mythic_crypt',max(1,(lvl-200)+1)),
                         ('wieza','astral',lvl),('mityczna_wieza','mythic_astral',max(1,(lvl-200)+1))):
        info=chest_equipment_profile_v5800(kind,fl)
        chests.append(f'{name} '+('25% losowania 1 dodatkowego EQ' if info else 'BRAK bonusu na tym pietrze'))
    chest_note=('Ten konkretny ID jest w puli' if item_id in _BASE_ITEMS else
                'Ten konkretny ID NIE jest w puli bonusowej skrzyni')
    return (f'EQ POKRYCIE {item_id} / etap probny {lvl}: '+ '; '.join(rows)
            +'. Skrzynie: '+'; '.join(chests)+'. '+chest_note
            +'. Sklepy nie maja automatycznej skali EQ: uzywaja katalogu ofert. '
             'To audyt reguly, NIE test losowania ani gwarancja kazdego dropu. '
             'Brak rejestracji przedmiotow, brak zmian bazy.')


def _goals(service,catalog,qid):
    q=catalog[qid]
    if q.get('kind')=='collect_resource_set':
        group=q.get('resource_targets')
        if not isinstance(group,dict) or not group or any(type(v) is not int or v<1 for v in group.values()):
            return None
        return sum(group.values())
    if q.get('kind')=='multi_objective':
        mobs=set(MOB_TEMPLATES)|set(service.draft.get('mobs',{}))|set(service.active.get('mobs',{}))
        items=set(ITEMS)|set(service.draft.get('items',{}))|set(service.active.get('items',{}))
        try:
            _,goal=validate_objectives(q.get('objectives'),mobs,items,set(_npc_catalog(service)))
            return int(goal)
        except (ValueError,TypeError,KeyError,AttributeError):return None
    return None


def _scan(service):
    catalog=_effective(service)
    repairable={};needs_review=[]
    for qid,q in sorted(catalog.items()):
        if q.get('kind') not in ('multi_objective','collect_resource_set'):continue
        count=_goals(service,catalog,qid)
        if count is None:
            needs_review.append(qid)
        elif type(q.get('needed')) is not int or q['needed']!=count:
            repairable[qid]=count
    return catalog,repairable,needs_review


def quest_scan(service,page='1'):
    p=_number(page,1,10000,'STRONA')
    _,repairable,review=_scan(service)
    pages=max(1,(len(repairable)+7)//8)
    if p>pages:raise ValueError(f'Dostepne strony: 1-{pages}.')
    displayed=list(repairable.items())[(p-1)*8:p*8]
    return (f'QUEST AUTOMAT SKAN: naprawialne {len(repairable)}, wymagaja recznego sprawdzenia {len(review)}, '
            f'strona {p}/{pages}. '+('; '.join(f'{qid} -> needed {num}' for qid,num in displayed) or 'brak rozbieznosci')+
            '. Tylko jednoznaczne sumy celow; pozostale bledy: questy bledy. Bez zmian.')


def quest_card(service,qid):
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Nieznany quest; uzyj questy szukaj.')
    num=_goals(service,catalog,qid)
    err,hint=_issues(qid,catalog[qid],catalog)
    return (f'QUEST AUTOMAT KARTA {qid}: needed {catalog[qid].get("needed")}; '
            f'wyliczony licznik {num if num is not None else "BRAK JEDNOZNACZNEGO WYNIKU"}; '
            f'pewne problemy {len(err)}; ostrzezenia {len(hint)}. '
            'Poprawialny automatycznie tylko istniejący licznik celu, nie ID, nie nagrody.')


def quest_plan(session,service,ids=()):
    session.adminlive7002_plan=None
    catalog,repairable,review=_scan(service)
    if ids:
        if len(ids)>8 or len(set(ids))!=len(ids):raise ValueError('Podaj 1-8 roznych ID questow.')
        for qid in ids:
            if qid not in repairable:raise ValueError(qid+': brak jednoznacznej poprawki needed.')
        chosen=tuple(ids)
    else:
        chosen=tuple(list(repairable)[:8])
    if not chosen:
        raise ValueError('Brak bezpiecznych automatycznych napraw. Pozostale bledy wymagaja decyzji administratora.')
    before=copy.deepcopy(service.draft);active=copy.deepcopy(service.active);candidate=copy.deepcopy(before)
    for qid in chosen:
        key,value=parse_quest_edit('needed',repairable[qid])
        # Newly authored OLC quests are validated *as definitions* before
        # field overrides; fix the staged definition too when it exists.
        if qid in candidate.get('quests',{}):
            candidate['quests'][qid][key]=value
            if key in candidate.get('quest_edits',{}).get(qid,{}):
                candidate['quest_edits'][qid][key]=value
        else:
            candidate.setdefault('quest_edits',{}).setdefault(qid,{})[key]=value
    service.validate(candidate)
    session.adminlive7002_plan=(before,active,copy.deepcopy(candidate),chosen)
    return (f'QUEST AUTOMAT PLAN {len(chosen)}: '+
            '; '.join(f'{qid} needed {catalog[qid].get("needed")} -> {repairable[qid]}' for qid in chosen)+
            '. Bez zapisu. questy automaty zatwierdz POTWIERDZAM (tylko DRAFT).')


def quest_commit(session,service):
    plan=getattr(session,'adminlive7002_plan',None)
    if not plan:raise ValueError('Brak planu, uzyj questy automaty plan.')
    before,active,candidate,ids=plan
    if service.active!=active or service.draft!=before:
        session.adminlive7002_plan=None
        raise ValueError('OLC zmienione od planu: trzeba przeliczyc ponownie.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive7002_undo=(before,copy.deepcopy(candidate),active)
    session.adminlive7002_plan=None
    return f'QUEST AUTOMAT DRAFT: {len(ids)} licznikow. Nie opublikowano; gracze, SQLite i nagrody bez zmian.'


def quest_undo(session,service):
    data=getattr(session,'adminlive7002_undo',None)
    if not data:raise ValueError('Brak poprawki do cofniecia.')
    before,after,active=data
    if service.active!=active or service.draft!=after:
        raise ValueError('OLC zmienione pozniej; cofniecie zablokowane.')
    service.draft=copy.deepcopy(before)
    session.adminlive7002_undo=None
    session.adminlive7002_plan=None
    return 'QUEST AUTOMAT COFNIETO: tylko DRAFT; bez zmian postepow graczy.'


async def dispatch_v7002(session,group,raw):
    args=str(raw or '').strip().split()
    matched=(group=='pomoc' and args==['26']) or (group=='arena' and args[:2]==['uoss','reguly']) or (group=='eq' and args[:1]==['pokrycie'] and len(args)>1) or (group in ('questy','zadania') and args[:1]==['automaty'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':output=HELP
        elif group=='arena':
            if len(args)>4:raise ValueError('arena uoss reguly [TURY] [OD_TURY].')
            output=uoss_source_trace(session,args[2] if len(args)>2 else '6',args[3] if len(args)>3 else '1')
        elif group=='eq':
            if len(args) not in (2,3):raise ValueError('eq pokrycie ID_PRZEDMIOTU [ETAP]')
            output=equipment_coverage(args[1],args[2] if len(args)==3 else '900')
        else:
            service=session.server.live_content_v1204
            if len(args) in (2,3) and args[1]=='skan':output=quest_scan(service,args[2] if len(args)==3 else '1')
            elif len(args)==3 and args[1]=='karta':output=quest_card(service,args[2])
            elif args[1:2]==['plan']:output=quest_plan(session,service,args[2:])
            elif args==['automaty','zatwierdz','POTWIERDZAM']:output=quest_commit(session,service)
            elif args==['automaty','cofnij','POTWIERDZAM']:output=quest_undo(session,service)
            elif args==['automaty','anuluj']:
                session.adminlive7002_plan=None;output='QUEST AUTOMAT: plan anulowany.'
            elif args==['automaty','status']:
                output=('QUEST AUTOMAT: plan '+('gotowy' if getattr(session,'adminlive7002_plan',None) else 'brak')+
                        '; cofanie '+('dostepne' if getattr(session,'adminlive7002_undo',None) else 'brak')+'.')
            else:raise ValueError('questy automaty skan/karta/plan/zatwierdz/cofnij/anuluj/status.')
    except (ValueError,TypeError,AttributeError,KeyError,OverflowError,AssertionError) as exc:
        output='ADMIN LIVE V70.00.2: '+str(exc)[:300]
    await session.send(output)
    return True
