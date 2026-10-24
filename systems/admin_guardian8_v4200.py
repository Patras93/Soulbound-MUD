# -*- coding: utf-8 -*-
"""Guardian 8: strictly private encounter rehearsal + all-or-nothing OLC batch.

This reuses vetted UOSS *rules* on detached memory objects; it must not call
live combat, world spawning, reward, database or network routines. It is not
an exact replay of player build / realtime scheduling / complete monster AI.
"""
from __future__ import annotations
import copy
from types import SimpleNamespace
from data.mobs import MOB_TEMPLATES
from systems.admin_guardian7_v4100 import (
    _lab_start, _lab_status, _lab_log, _lab_report, _lab_target,
    _known_element_effect, _number, _undo, _audit_one, _audit_all,
    _olc_guard, _id, _MAX_TURNS, _MAX_ADDS,
)
from systems.admin_guardian2_v3600 import _audit
from world.uoss_superboss_runtime import (
    SUPERBOSS_HELPER_ROLES_V11330, superboss_combat_start_effects_v11176,
    superboss_phase_event_v11138, superboss_source_ability_v11162,
    superboss_source_summons_v11162, superboss_source_round_event_v11160,
    superboss_exact_ability_effect_v11160, superboss_counterattack_multiplier_v11137,
    superboss_source_attack_multiplier_v11162, superboss_apply_source_status_v11173,
    superboss_source_timed_effect_v11179, superboss_advance_timed_effects_v11179,
    superboss_healing_blocked_v11179, superboss_add_round_event_v11176,
)
from systems.monster_ai import monster_ai_plan_v1160

_HELP={
 '1':('GUARDIAN8 1/3: arena start ID HP ATAK [HELPER]; arena atak [CEL]; '
      'arena magia ZYWIOŁ [CEL]; arena obrona; arena lecz; arena oczysc; '
      'arena status [STRONA]; arena dziennik [STRONA]; arena wynik; arena wyjdz. '
      'Tury UOSS sa odizolowane, a leczenie/obrona to model testowy.'),
 '2':('GUARDIAN8 2/3: questy seria plan ID | POLE | WARTOSC ; ID | POLE | WARTOSC; '
      'questy seria zmien ID | POLE | WARTOSC ; ID | POLE | WARTOSC | POTWIERDZAM; '
      'questy cofnij POTWIERDZAM; questy audyt ID; questy skan. '
      'Maksymalnie 8 roznych questow, tylko DRAFT. Nie publikuje automatycznie.'),
 '3':('GUARDIAN8 3/3: olc kontrola; status; pomoc 1/2/3. '
      'Arena korzysta z rzeczywistych funkcji UOSS faz, umiejetnosci, przywolan, '
      'statusow i efektow czasowych na KOPIACH. Prawdziwe HP/EXP/EQ/SQLite/questy '
      'nie zmieniaja sie. To nie jest identyczna walka produkcyjna ani pelne AI.'),
}

class _LabActor:
    """Only detached attributes used by selected pure/snapshot UOSS functions."""
    def __init__(self, hp, helper, mana=100):
        self.current_hp=hp
        self._max_hp=hp
        self.current_mana=mana
        self._max_mana=mana
        self.account_id=123456
        self.character=SimpleNamespace(room_id='__guardian8_private__', gravityproof=False)
        self.gravityproof=False
        self.closed=False
        self.uoss_source_statuses_v11173=set()
        self.uoss_nullify_healing_rounds_v11179=0
        self.uoss_necrotic_energy_rounds_v11179=0
        self.server=SimpleNamespace(_uoss_helper_choice_123456=helper)
        self.server.party_sessions=lambda *_a, **_kw:[self]
    def party_key(self):return None
    def max_hp(self):return self._max_hp
    def max_mana(self):return self._max_mana
    def equipped_item_rows(self):
        # v65: isolated *laboratory* equipment only. Production sourced UOSS
        # status protection reads these item_ids from the canonical ITEMS list.
        # These never resolve real player equipment, inventory or database.
        return getattr(self,'_lab_equipped_rows_v6500',())

def _start(session,service,boss,hp,attack,helper='brak'):
    msg=_lab_start(session,service,boss,hp,attack,helper)
    a=session.guardian7_lab
    actor=_LabActor(a['hero_hp'],a['helper'])
    a['actor8']=actor
    a['heal_count8']=0
    a['model8']='UOSS source-rule rehearsal; no real build, items, EXP or persistence'
    a['boss'].room_id='__guardian8_private__'
    initial=superboss_combat_start_effects_v11176(actor,a['template'],a['boss'])
    a['notes'].extend('ARENA8: '+str(x) for x in initial)
    return msg.replace('ARENA7','ARENA8')+(' Efekty startowe: '+', '.join(initial)+'.' if initial else '')

def _snapshot_status(a):
    actor=a['actor8'];return (f'HP {a["hero_hp"]}/{a["hero_max"]}, '
        f'blokada leczenia {actor.uoss_nullify_healing_rounds_v11179}, '
        f'oslabienie {actor.uoss_necrotic_energy_rounds_v11179}, '
        f'statusy {", ".join(sorted(actor.uoss_source_statuses_v11173)) or "brak"}')

def _turn(session, action='atak', element=None, target='boss'):
    a=getattr(session,'guardian7_lab',None)
    if not a or 'actor8' not in a:raise ValueError('Brak aktywnej areny8.')
    if a['finished']:raise ValueError('Walka zakonczona, wpisz arena wynik lub arena wyjdz.')
    if a['round']>=_MAX_TURNS:
        a['finished']=True
        return 'ARENA8: limit 250 tur w LABORATORIUM, nie limit prawdziwej walki.'
    actor=a['actor8'];boss=a['boss'];t=a['template'];lines=[]
    defending=action=='obrona'
    if action in ('atak','magia'):
        mob,add=_lab_target(a,target)
        hit=a['hero_attack']
        if action=='magia':
            mult,note=_known_element_effect(t,element) if mob else (1.0,'')
            if note:lines.append(note)
            if mult<0 and mob:
                healed=min(boss.max_hp-boss.hp,hit)
                boss.hp+=healed;hit=0
                lines.append(f'Absorpcja {element}: +{healed} HP bossa')
            else:hit=max(0,int(hit*mult))
        if mob:
            hit=min(hit,boss.hp);boss.hp-=hit
        else:
            hit=min(hit,add['hp']);add['hp']-=hit
            add['mob'].hp=add['hp'];add['mob'].alive=add['hp']>0
        a['total_dealt']+=hit
        lines.append(f'Atak w {"bossa" if mob else "pomocnika"}: {hit}')
    elif action=='lecz':
        if superboss_healing_blocked_v11179(actor):
            lines.append('Leczenie zablokowane: Nullify Healing')
        else:
            heal=max(1,a['hero_max']//4)  # explicit hypothetical lab-only heal
            recovered=min(heal,a['hero_max']-a['hero_hp'])
            a['hero_hp']+=recovered;lines.append(f'Leczenie MODELOWE +{recovered} HP')
            a['heal_count8']+=1
    elif action=='oczysc':
        actor.uoss_source_statuses_v11173.clear()
        a['statuses'].clear()
        lines.append('Modelowe oczyszczenie nazwanych statusow (nie skrocono efektow UOSS)')
    elif defending:lines.append('Obrona MODELOWA: 50% otrzymanych obrazen')
    else:raise ValueError('Nieznana akcja testowa.')
    a['round']+=1; boss.combat_turn=a['round']
    if boss.hp<=0:
        boss.alive=False;a['finished']=True
        outcome=f'ARENA8 tura {a["round"]}: '+', '.join(lines)+'; boss pokonany. 0 EXP, 0 zlota, 0 dropow.'
        a['notes'].append(outcome);a['notes']=a['notes'][-24:]
        return outcome
    phase=superboss_phase_event_v11138(None,t,boss)
    if phase:lines.append(f'Faza {phase[0]}: {str(phase[1])[:90]}')
    ability=superboss_source_ability_v11162(t,boss)
    if ability:lines.append('Zdolnosc '+str(ability)[:60])
    summoned=superboss_source_summons_v11162(None,t,boss,ability) if ability else ()
    for sid in summoned:
        if len(a['adds'])>=_MAX_ADDS:
            lines.append('Limit symulatora 24 pomocnikow, bez limitowania mobow w normalnej grze')
            break
        temp=MOB_TEMPLATES.get(sid)
        if not temp:
            lines.append('Niezdefiniowany pomocnik: '+sid);continue
        mh=_number(temp.get('max_hp',0)); dmg=_number(temp.get('damage',0),0)
        m=SimpleNamespace(key='lab_'+str(len(a['adds'])+1),template_id=sid,
                room_id='__guardian8_private__',engaged_by=actor.account_id,
                hp=mh,alive=True,combat_turn=0)
        a['adds'].append({'id':sid,'name':str(temp.get('name',sid)),'hp':mh,'max':mh,
                          'damage':dmg,'mob':m,'template':copy.deepcopy(temp)})
        lines.append('Przywolano '+str(temp.get('name',sid))[:60])
    ended=superboss_advance_timed_effects_v11179(actor)
    if ended:lines.append('Wygaslo: '+', '.join(ended))
    effect=superboss_exact_ability_effect_v11160(actor,t,boss,ability)
    timed=superboss_source_timed_effect_v11179(actor,t,ability)
    if timed:lines.append(f'Efekt {timed["effect"]} ({timed["rounds"]} rund)')
    applied=superboss_apply_source_status_v11173(actor,t,ability)
    if applied:
        if not applied.get('blocked'):
            a['statuses'].add(str(applied['status'])); lines.append('Status '+str(applied['status']))
        else:lines.append('Status odporny: '+str(applied['status']))
    event=superboss_source_round_event_v11160(None,t,boss)
    if event and event.get('instant_death'):
        a['hero_hp']=0;a['finished']=True
        lines.append(f'{event["name"]}: modelowa porazka, prawdziwa postac nie ucierpiala')
    else:
        phase_mult,_=superboss_counterattack_multiplier_v11137(t,boss)
        dmg=int(int(t.get('damage',0))*phase_mult)
        if ability:dmg=int(dmg*superboss_source_attack_multiplier_v11162(t,ability))
        if effect:
            if 'damage' in effect:dmg=int(effect['damage'])
            elif 'current_hp_fraction' in effect:dmg=int(a['hero_hp']*effect['current_hp_fraction'])
            if 'countdown_rounds' in effect:lines.append('Odliczanie '+str(effect['countdown_rounds']))
        if defending:dmg//=2
        if a['helper']:
            dmg=max(0,int(dmg*(1-SUPERBOSS_HELPER_ROLES_V11330[a['helper']]['damage_reduction'])))
        add_damage=0
        for entry in a['adds']:
            if entry['hp']<=0:continue
            entry['mob'].combat_turn+=1
            event_add=superboss_add_round_event_v11176(entry['template'],entry['mob'])
            if event_add and event_add.get('despawn'):
                entry['hp']=0
                lines.append(str(event_add.get('text','Pomocnik znika'))[:70])
                continue
            # AI plan is read-only on isolated enemy objects; never execute on real world.
            plan=monster_ai_plan_v1160(entry['mob'],entry['template'],
                  [entry['mob']],(),now=a['round']*30.0)
            if plan and plan.get('kind')=='heal':
                amount=min(entry['max']-entry['hp'], max(1,entry['max']*18//100))
                entry['hp']+=amount;entry['mob'].hp=entry['hp']
                lines.append(f'AI pomocnika: leczenie {amount} HP')
            if plan and plan.get('kind') not in (None,'heal'):
                lines.append('AI pomocnika sugeruje '+str(plan['kind'])+' (bez spawn/efektu produkcyjnego)')
            add_damage+=entry['damage']
        if defending:add_damage//=2
        total=max(0,dmg)+add_damage
        a['hero_hp']=max(0,a['hero_hp']-total)
        a['total_taken']+=total
        lines.append(f'Boss {dmg}, pomocnicy {add_damage}, postac HP {a["hero_hp"]}')
        if a['hero_hp']<=0:a['finished']=True;lines.append('Porazka w laboratorium')
    # An effect applied this round keeps its full sourced duration.
    outcome=f'ARENA8 tura {a["round"]}: '+'. '.join(lines)[:480]
    a['notes'].append(outcome);a['notes']=a['notes'][-24:]
    return outcome


def _batch_preview(service,payload):
    specs=[p.strip() for p in payload.split(';')]
    if not (1<=len(specs)<=8) or any(not s for s in specs):
        raise ValueError('Od 1 do 8 niepustych operacji rozdzielonych srednikiem.')
    current=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(current)
    ids=[];notes=[]
    # Stage all changes on a detached snapshot, then validate only the finished bundle.
    from systems.admin_guardian7_v4100 import _repair_parse
    from systems.admin_guardian6_v4000 import _combined
    available=_combined(service)
    for spec in specs:
        qid,changes=_repair_parse(spec)
        if qid not in available:raise ValueError('Nie ma questa: '+qid)
        if qid in ids:raise ValueError('Powtorzony quest: '+qid)
        ids.append(qid)
        candidate['quest_edits'].setdefault(qid,{}).update(changes)
        notes.append(f'{qid} ({", ".join(changes)})')
    service.validate(candidate)
    return current,candidate,ids,notes


def _batch(session,service,payload,confirm):
    before,after,ids,notes=_batch_preview(service,payload)
    if not confirm:
        return f'QUEST8 SERIA PLAN: {len(ids)} questow: '+ '; '.join(notes)+'. Nic nie zmieniono.'
    service.draft=after
    history=getattr(session,'guardian7_undo',[])
    history.append((copy.deepcopy(before),copy.deepcopy(after), ','.join(ids)))
    session.guardian7_undo=history[-8:]
    return f'QUEST8 SERIA DRAFT: {len(ids)} questow: '+ '; '.join(notes)+'. Bez publikacji. admin live sprawdz / porownaj / aktywuj POTWIERDZAM.'


async def handle_guardian8(session,raw):
    fields=str(raw or '').strip().split(maxsplit=1)
    if not fields or fields[0].casefold()!='guardian8':return False
    if not session.is_admin():
        await session.send('GUARDIAN8: tylko administrator-wlasciciel.');return True
    service=session.server.live_content_v1204
    rest=fields[1].strip() if len(fields)>1 else 'pomoc 1'
    bits=rest.split();group=bits[0].casefold() if bits else 'pomoc'
    try:
        if group=='pomoc':
            page=bits[1] if len(bits)>1 else '1'
            if len(bits)>2 or page not in _HELP:raise ValueError('Pomoc: strony 1, 2 lub 3.')
            msg=_HELP[page]
        elif group=='status':
            a=getattr(session,'guardian7_lab',None)
            msg='GUARDIAN8: arena8 '+('aktywna; '+_snapshot_status(a) if a and 'actor8' in a else 'nieaktywna')+'; zmiany questow tylko DRAFT.'
        elif group=='arena':
            op=bits[1].casefold() if len(bits)>1 else ''
            if op=='start' and len(bits) in (5,6):
                msg=_start(session,service,bits[2],bits[3],bits[4],bits[5] if len(bits)==6 else 'brak')
            elif op in ('atak','obrona','lecz','oczysc') and len(bits)==(3 if op=='atak' and len(bits)==3 else 2):
                msg=_turn(session,action=op,target=bits[2] if len(bits)==3 else 'boss')
            elif op=='magia' and len(bits) in (3,4):
                msg=_turn(session,action='magia',element=bits[2],target=bits[3] if len(bits)==4 else 'boss')
            elif op=='status' and len(bits) in (2,3):
                a=getattr(session,'guardian7_lab',None)
                msg=_lab_status(session,bits[2] if len(bits)==3 else '1')
                if a and 'actor8' in a:msg=msg.replace('ARENA7','ARENA8')+' '+_snapshot_status(a)
            elif op=='dziennik' and len(bits) in (2,3):msg=_lab_log(session,bits[2] if len(bits)==3 else '1').replace('ARENA7','ARENA8')
            elif op=='wynik' and len(bits)==2:msg=_lab_report(session).replace('ARENA7','ARENA8')
            elif op=='wyjdz' and len(bits)==2:
                session.guardian7_lab=None
                msg='ARENA8: test zakonczony, usunieto prywatne dane; brak nagrod, brak zmian postaci.'
            else:raise ValueError(_HELP['1'])
        elif group=='questy':
            op=bits[1].casefold() if len(bits)>1 else ''
            if op=='seria':
                sub=rest.split(None,3)
                if len(sub)!=4 or sub[2].casefold() not in ('plan','zmien'):raise ValueError(_HELP['2'])
                payload=sub[3];yes=sub[2].casefold()=='zmien'
                if yes:
                    segments=payload.rsplit('|',1)
                    if len(segments)<2 or segments[-1].strip()!='POTWIERDZAM':
                        raise ValueError('Zatwierdz na koncu przez | POTWIERDZAM.')
                    payload=segments[0].strip()
                msg=_batch(session,service,payload,yes)
                if yes:_audit(session,'guardian8_quest_draft','seria')
            elif op=='cofnij' and len(bits)==3 and bits[2]=='POTWIERDZAM':
                msg=_undo(session,service)
                _audit(session,'guardian8_quest_undo','seria')
            elif op=='audyt' and len(bits)==3:msg=_audit_one(service,_id(bits[2]))
            elif op=='skan' and len(bits)==2:msg=_audit_all(service)
            else:raise ValueError(_HELP['2'])
        elif group=='olc' and len(bits)==2 and bits[1].casefold()=='kontrola':msg=_olc_guard(service)
        else:raise ValueError('Wpisz admin guardian8 pomoc 1/2/3.')
        await session.send(msg)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        await session.send('GUARDIAN8: '+str(exc)[:360])
    return True
