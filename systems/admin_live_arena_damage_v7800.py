# -*- coding: utf-8 -*-
"""v79: real basic attack AND production boss-defense on detached copies.

This deliberately does NOT claim complete fight parity.  The regular fight
still handles critical hits, full hit sequence, skills, action timing, enemy AI, rewards
and other combat effects not represented in Guardian's private rehearsal.

No real character stats, mana or global PRNG may be changed by this command.
"""
from __future__ import annotations

import copy
import hashlib
import random
from systems.admin_guardian9_v4300 import _state
from systems.admin_guardian10_v4400 import _lab_turn10

HELP=(
    'ADMIN LIVE POMOC 38: arena uoss gracz prognoza [ILE] - surowe obrazenia '
    'z PRAWDZIWEJ metody player_damage na odizolowanej kopii aktualnej postaci '
    '(1-8 autoatakow, w tym realna konsumpcja many w kopii). '
    'arena uoss gracz atak POTWIERDZAM - wykona jedna ture prywatnej areny '
    'z takim surowym ciosem, zachowujac prywatne RNG i mane postaci LAB. '
    'arena uoss gracz stan - sprawdz testowa mane, status i trafienia w obrone. '
    'Wymaga zalogowanej postaci administratora i rozpoczetej areny. '
    'Obrona bossa korzysta z apply_boss_defense produkcji NA KOPII. '
    'Krytyki, pelna sekwencja Broni Duszy, kontratak i skille NIE sa 1:1. '
    'Bez XP, pieniedzy, lootow, zmian SQLite ani prawdziwej postaci.'
)


def _number(raw):
    if not isinstance(raw,str) or not raw.isascii() or not raw.isdecimal() or len(raw)>2:
        raise ValueError('ILE: wpisz liczbe od 1 do 8.')
    value=int(raw)
    if not 1<=value<=8:raise ValueError('ILE: wpisz liczbe od 1 do 8.')
    return value


def _arena(session):
    state=_state(session)
    if '_guardian10_rng' not in state:
        raise ValueError('Najpierw: admin live arena start BOSS HP ATAK.')
    if getattr(session,'character',None) is None or not callable(getattr(session,'player_damage',None)):
        raise ValueError('Prawdziwa formula wymaga zalogowanej postaci administratora.')
    if state['finished']:
        raise ValueError('Prywatna arena zakonczona; rozpocznij nastepna.')
    return state


def _actor_copy(session, state):
    """Make a detached Session of the same *class* so method dispatch is genuine.

    The real Session has an ordinary __dict__. Shallow references to server are
    read-only input for combat power/party lookup, never a new world/session.
    Its mutable character and per-session state are deep-copied before the call.
    """
    if not hasattr(session,'__dict__'):
        raise ValueError('Nie mozna odizolowac postaci tego typu.')
    ghost=object.__new__(type(session))
    ghost.__dict__.update(session.__dict__)
    ghost.character=copy.deepcopy(session.character)
    # Production equipment getters may populate this session-local cache on
    # first lookup. Never share the mutable cache between actor and real player.
    source_cache=getattr(session,'_read_only_equipment_cache_v1262',None)
    if source_cache is not None and not isinstance(source_cache,dict):
        raise ValueError('Nieobslugiwany typ cache EQ, izolacja odrzucona.')
    ghost._read_only_equipment_cache_v1262=copy.deepcopy(source_cache) if source_cache is not None else {}
    real_mana=getattr(session,'current_mana',None)
    if type(real_mana) is not int or real_mana<0:
        raise ValueError('Brak prawidlowego stanu many postaci.')
    current=state.get('_v7800_mana',real_mana)
    if type(current) is not int or current<0:
        raise ValueError('Nieprawidlowy stan many LAB.')
    ghost.current_mana=current
    original_hp=getattr(session,'current_hp',0)
    if type(original_hp) is not int or original_hp<0:
        raise ValueError('Nieprawidlowe HP postaci dla odizolowanych efektow Broni Duszy.')
    hp=state.get('_v8100_hp',original_hp)
    if type(hp) is not int or hp<0:
        raise ValueError('Nieprawidlowe HP prywatnej kopii postaci.')
    ghost.current_hp=hp
    return ghost, real_mana


def _rng_initial(session,state):
    # Identity and current fight state seed a private sequence. Nothing relies
    # on hash() randomness, the process-wide PRNG or data from real-world combat.
    account=getattr(session,'account_id',0)
    text='\x1f'.join(map(str,('v7800',account,state['name'],state['hero_max'],state['hero_attack'])))
    seed=int.from_bytes(hashlib.sha256(text.encode('utf-8')).digest()[:16],'big')
    return random.Random(seed).getstate()


def _calculate(session,state,count):
    actor,original_mana=_actor_copy(session,state)
    rng=copy.deepcopy(state.get('_v7800_rng',_rng_initial(session,state)))
    external_rng=random.getstate()
    damages=[]
    try:
        random.setstate(rng)
        for _ in range(count):
            value=actor.player_damage()  # production Session method, on a clone
            if type(value) is not int or value<1:
                raise ValueError('player_damage zwrocil nieprawidlowy wynik.')
            damages.append(value)
        next_rng=random.getstate()
    finally:
        random.setstate(external_rng)
    if getattr(session,'current_mana',None)!=original_mana:
        raise AssertionError('Naruszono prawdziwa mane postaci.')
    return damages, actor.current_mana, next_rng


async def _calculate_defended(session, state, count):
    """Execute production damage and boss defense on two disconnected copies.

    Real source: player_damage + SessionSkillLearningMixin.apply_boss_defense.
    The source defense may await `send_combat`; our sink coroutine performs
    zero awaits and cannot yield to the server while the private RNG is borrowed.
    """
    from player.session_mixins.skill_learning import SessionSkillLearningMixin
    from data.mobs import MOB_TEMPLATES
    actor, original_mana = _actor_copy(session, state)
    boss = copy.deepcopy(state['boss'])
    if boss.template_id not in MOB_TEMPLATES:
        raise ValueError('Brak produkcyjnego szablonu bossa. Obrona 1:1 niedostepna.')
    boss.player_hits = int(getattr(boss, 'player_hits', 0) or 0)
    if boss.player_hits < 0:
        raise ValueError('Nieprawidlowy licznik trafien bossa w LAB.')
    rng=copy.deepcopy(state.get('_v7800_rng',_rng_initial(session,state)))
    public_rng=random.getstate()
    raw_hits=[]
    defended_hits=[]
    notes=[]
    async def private_combat_message(message,*args,**kwargs):
        notes.append(str(message)[:160])
    actor.send_combat=private_combat_message
    try:
        random.setstate(rng)
        for _ in range(count):
            raw = actor.player_damage()
            if type(raw) is not int or raw<1:
                raise ValueError('player_damage zwrocil nieprawidlowy wynik.')
            defended = await SessionSkillLearningMixin.apply_boss_defense(actor,boss,raw)
            if type(defended) is not int or defended<0:
                raise ValueError('apply_boss_defense zwrocil nieprawidlowy wynik.')
            raw_hits.append(raw)
            defended_hits.append(defended)
        next_rng=random.getstate()
    finally:
        random.setstate(public_rng)
    if getattr(session,'current_mana',None)!=original_mana:
        raise AssertionError('Naruszono prawdziwa mane postaci.')
    return raw_hits,defended_hits,actor.current_mana,next_rng,boss.player_hits,notes


async def preview(session,count='1'):
    size=_number(count)
    state=_arena(session)
    raw,defended,mana,_rng,_hits,notes=await _calculate_defended(session,state,size)
    details=('; obrona: '+', '.join(notes[:3])) if notes else ''
    return (f'ARENA UOSS GRACZ PROGNOZA {len(raw)}: '
            f'ciosy surowe {", ".join(map(str,raw))}; '
            f'po prawdziwej obronie bossa {", ".join(map(str,defended))}; '
            f'mana kopii po {len(raw)} ciosach {mana}; '
            f'prywatna tura {state["round"]}{details}. '
            'player_damage i apply_boss_defense pochodza z produkcji. '
            'Krytyki, sekwencja dodatkowych trafien i kontratak bossa '
            'nie zostaly odtworzone 1:1. '
            'Zero zmian areny, prawdziwej many i RNG serwera.')


async def strike(session):
    state=_arena(session)
    before=copy.deepcopy(state)
    try:
        raw,defended,mana,rng,hits,notes=await _calculate_defended(session,state,1)
        previous=state['hero_attack']
        state['hero_attack']=defended[0]
        message=_lab_turn10(session,'atak')
        result=_state(session)
        result['hero_attack']=previous
        result['boss'].player_hits=hits
        result['_v7800_rng']=rng
        result['_v7800_mana']=mana
        summary=('; obrona: '+', '.join(notes[:2])) if notes else ''
        return (f'ARENA UOSS GRACZ ATAK: surowe {raw[0]}, '
                f'po produkcyjnej obronie {defended[0]}, '
                f'mana kopii {mana}{summary}. '+message+' '
                'Tylko prywatne LAB. Pozostale fazy tury nadal nie sa 1:1.')
    except Exception:
        session.guardian7_lab=before
        raise


def status(session):
    state=_arena(session)
    mana=state.get('_v7800_mana',getattr(session,'current_mana',None))
    return (f'ARENA UOSS GRACZ STAN: tura {state["round"]}, '
            f'mana kopii {mana}, HP kopii {state.get("_v8100_hp",getattr(session,"current_hp",0))}, HP bossa {state["boss"].hp}/{state["boss"].max_hp}, '
            f'licznik trafien w obrone {getattr(state["boss"],"player_hits",0)}. '
            'Prawdziwa postac i boss swiata nie sa zmieniane.')


HELP_41=(
    'ADMIN LIVE POMOC 41: arena uoss bron prognoza [1-8], '
    'arena uoss bron atak POTWIERDZAM, arena uoss bron stan. '
    'Wspolne z realna walka: autoatak, krytyk, wielotrafienia, obrona, Echo Broni Duszy, '
    'wysysanie zycia i regeneracja many. Efekty tylko na kopii; '
    'HP arenowego bohatera oraz odpowiedz bossa nadal sa modelem. '
    'Kolejka skilli i pelne AI 1:1 NIE sa obslugiwane.'
)

HELP_40=(
    'ADMIN LIVE POMOC 40: arena uoss bron prognoza [1-8] - prywatny atak Broni Duszy, '
    'z PRODUKCYJNYM przygotowaniem obrazen, krytykiem, obrona bossa i seria hitow od Speed/Haste. '
    'arena uoss bron atak POTWIERDZAM - jeden rzeczywisty cios gracza przeciw kopii bossa; '
    'pozostala odpowiedz bossa jest MODELOWA. arena uoss bron stan - stan kopii. '
    'Brak skilli z kolejki, echo, lifesteal, nagrod, XP, lootow, pelnego AI i walki 1:1.'
)

async def _calculate_weapon(session, state, count):
    """Identical attack boost/crit and hit loop as production, on detached objects."""
    from systems.uoss_basic_weapon_shared_v8000 import weapon_attack_boost, apply_weapon_hit_series, weapon_after_hit
    from player.session_mixins.skill_learning import SessionSkillLearningMixin
    from world.machine_expansion import v0314_adjust_damage_vs_template
    from data.mobs import MOB_TEMPLATES
    actor, real_mana = _actor_copy(session,state)
    required=('active_soul_weapon_relic_v11176','mob_effective_max_hp_v11330',
              'critical_chance','critical_multiplier','v0210_adjust_player_damage',
              'class_damage_multiplier_v1700','basic_attack_hit_count_v11196')
    if any(not callable(getattr(actor,x,None)) for x in required):
        raise ValueError('Brak pelnej mechaniki Broni Duszy dla tej postaci.')
    if not hasattr(actor.character,'soul_weapon_mastery_level') or not hasattr(actor.character,'soul_tier'):
        raise ValueError('Brak biegłości Broni Duszy lub Soul Tier postaci.')
    boss=copy.deepcopy(state['boss'])
    template=MOB_TEMPLATES.get(boss.template_id)
    if not template:raise ValueError('Nie znaleziono produkcyjnego szablonu bossa.')
    boss.player_hits=int(getattr(boss,'player_hits',0) or 0)
    if boss.player_hits<0:raise ValueError('Uszkodzony licznik trafien bossa.')
    rng=copy.deepcopy(state.get('_v7800_rng',_rng_initial(session,state)))
    public_rng=random.getstate()
    notes=[]; results=[]
    async def private_combat_message(message,*args,**kwargs):
        notes.append(str(message)[:160])
    actor.send_combat=private_combat_message
    try:
        random.setstate(rng)
        for _ in range(count):
            if boss.hp<=0:break
            relic_id,_relic=actor.active_soul_weapon_relic_v11176()
            disabled=(relic_id=='uoss_odin_unique_2' and actor.character.class_type=='physical')
            basic=0 if disabled else actor.player_damage()
            if type(basic) is not int or basic<0:raise ValueError('Nieprawidlowy autoatak produkcji.')
            powered,critical,chance,traits,mastery=weapon_attack_boost(
                actor,boss,template,basic,zantetsuken=disabled
            )
            defended=await SessionSkillLearningMixin.apply_boss_defense(actor,boss,powered)
            if disabled:defended=0
            defended=actor.v0210_adjust_player_damage(defended)
            kind='physical' if actor.character.class_type=='physical' else 'magic'
            defended,machine_note=v0314_adjust_damage_vs_template(template,defended,kind,'')
            hit_count=1 if disabled else actor.basic_attack_hit_count_v11196()
            # Production invokes class multiplier after machine resistance.
            per_hit=max(0,int(defended*actor.class_damage_multiplier_v1700()))
            total,actual,per=apply_weapon_hit_series(boss,per_hit,hit_count)
            echo,heal,mp=weapon_after_hit(actor,boss,total,traits,mastery,disabled=disabled)
            results.append({'basic':basic,'critical':critical,'chance':chance,
                            'hits':actual,'potential':hit_count,'per':per,'total':total+echo,
                            'weapon_total':total,'echo':echo,'heal':heal,'mana_restore':mp,
                            'copy_hp':actor.current_hp,'copy_mana':actor.current_mana,
                            'machine':machine_note})
        next_rng=random.getstate()
    finally:
        random.setstate(public_rng)
    if session.current_mana!=real_mana:
        raise AssertionError('Naruszono prawdziwa mane gracza.')
    return results,actor.current_mana,next_rng,boss.player_hits,notes


async def weapon_preview(session,count='1'):
    state=_arena(session); size=_number(count)
    values,mana,rng,hits,notes=await _calculate_weapon(session,state,size)
    summary='; '.join(f'{x["total"]} obrazen (Echo {x["echo"]}), {x["hits"]}/{x["potential"]} trafien, '
                      +('krytyk' if x['critical'] else 'bez krytyka') for x in values)
    return (f'ARENA UOSS BRON PROGNOZA: {summary}; mana kopii {mana}; '
            f'licznik obron {hits}; HP kopii {values[-1]["copy_hp"] if values else "brak"}. '
            f'Wspolne formuly produkcyjne, brak zmian w LAB/SQLite. '
            'Odpowiedz bossa i kolejka skilli wciaz sa modelem lub nieobslugiwane; AI bossa 1:1 niedostepne.')


async def weapon_strike(session):
    state=_arena(session); before=copy.deepcopy(state)
    try:
        values,mana,rng,hits,notes=await _calculate_weapon(session,state,1)
        if len(values)!=1:raise ValueError('Boss pokonany, nie ma kolejnego ataku.')
        previous=state['hero_attack']
        state['hero_attack']=values[0]['total']
        message=_lab_turn10(session,'atak')
        result=_state(session)
        result['hero_attack']=previous
        result['boss'].player_hits=hits
        result['_v7800_rng']=rng
        result['_v7800_mana']=mana
        result['_v8100_hp']=values[0]['copy_hp']
        return (f'ARENA UOSS BRON ATAK: {values[0]["total"]} obrazen, '
                f'{values[0]["hits"]} trafien, '
                +('krytyk' if values[0]['critical'] else 'bez krytyka')
                +f', Echo {values[0]["echo"]}, leczenie {values[0]["heal"]}, odzysk MP {values[0]["mana_restore"]}, 'f'HP kopii {values[0]["copy_hp"]}, mana kopii {mana}. '+message+' Pozostaly kontratak jest modelem.')
    except BaseException:
        session.guardian7_lab=before
        raise


async def dispatch_v7800(session,group,raw):
    parts=str(raw or '').strip().split()
    matched=(group=='pomoc' and parts in (['38'],['39'],['40'],['41'],['42'],['43'])) or (
        group=='arena' and len(parts)>=2 and parts[:2] in (['uoss','gracz'],['uoss','bron'],['uoss','kolejka']))
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc' and parts==['43']:
            from systems.admin_live_plain_skill_v8300 import HELP as out
        elif group=='pomoc' and parts==['42']:
            from systems.admin_live_queue_v8200 import HELP as out
        elif group=='pomoc':out=HELP_41 if parts==['41'] else (HELP_40 if parts==['40'] else (HELP.replace('POMOC 38','POMOC 39') if parts==['39'] else HELP))
        elif parts==['uoss','kolejka','prosty','prognoza']:
            from systems.admin_live_plain_skill_v8300 import preview as _skill_preview
            out=await _skill_preview(session)
        elif parts==['uoss','kolejka','prosty','rzuc','POTWIERDZAM']:
            from systems.admin_live_plain_skill_v8300 import cast as _skill_cast
            out=await _skill_cast(session)
        elif parts==['uoss','kolejka','nastepny']:
            from systems.admin_live_queue_v8200 import inspect_queue
            out=inspect_queue(session)
        elif parts==['uoss','bron','prognoza']:out=await weapon_preview(session)
        elif len(parts)==4 and parts[:3]==['uoss','bron','prognoza']:
            out=await weapon_preview(session,parts[3])
        elif parts==['uoss','bron','atak','POTWIERDZAM']:out=await weapon_strike(session)
        elif parts==['uoss','bron','stan']:out=status(session)
        elif parts==['uoss','gracz','prognoza']:out=await preview(session)
        elif len(parts)==4 and parts[:3]==['uoss','gracz','prognoza']:
            out=await preview(session,parts[3])
        elif parts==['uoss','gracz','atak','POTWIERDZAM']:out=await strike(session)
        elif parts==['uoss','gracz','stan']:out=status(session)
        else:raise ValueError('arena uoss bron: prognoza [1-8], atak POTWIERDZAM, stan. Pomoc 41.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,AssertionError) as exc:
        out='ADMIN LIVE V78: '+str(exc)[:280]
    await session.send(out)
    return True
