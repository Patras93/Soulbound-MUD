# -*- coding: utf-8 -*-
"""Admin Live v52. One entry point, short NVDA-oriented messages."""
from core import live_level_caps_v5200 as caps

_HELP = (
    'ADMIN LIVE LIMITY: limity / limity NAZWA; '
    'limity ustaw NAZWA LICZBA POTWIERDZAM; '
    'limity ustaw NAZWA bezlimitu POTWIERDZAM; '
    'limity wszystkie LICZBA lub bezlimitu POTWIERDZAM; '
    'limity reset NAZWA POTWIERDZAM; limity reset wszystko POTWIERDZAM; '
    'limity wczytaj POTWIERDZAM. '
    'EQ: wymagania 800; ulepszenia_eq: +10. '
    'Zalozenie EQ nadal wymaga poziomu i klasy. Soul Tier, rangi profesji i budynki gildii to osobne progi. '
    'Opcja bezlimitu ma techniczny prog awaryjny 1 miliarda poziomow. '
    'v53: limity audyt; limity eq prognoza krypta 901; limity progi 801.'
)



def _v53_equipment_forecast(parts):
    from systems.infinite_equipment import infinite_source_profile, infinite_equipment_power_multiplier
    from core.equipment_growth_v5300 import stage_report
    if len(parts)!=4 or parts[0:2]!=['eq','prognoza']:
        raise ValueError('Uzyj: admin live limity eq prognoza krypta 901.')
    source=parts[2].lower()
    source_keys={'krypta':'crypt_floor','mit_krypta':'mythic_crypt_floor',
        'wieza':'astral_floor','mit_wieza':'mythic_astral_floor','magitek':'magitek_floor'}
    if source not in source_keys:raise ValueError('Zrodlo: krypta / mit_krypta / wieza / mit_wieza / magitek.')
    raw=parts[3]
    if not raw.isdecimal() or len(raw)>10 or not 1<=int(raw)<=100000000:
        raise ValueError('Pietro: 1..100000000.')
    template={source_keys[source]:int(raw)}
    if source=='magitek':template['magitek_infinite']=True
    profile=infinite_source_profile(template)
    if profile is None:
        return 'EQ PROGNOZA: na tym pietrze nie powstaje wariant Rezonans Glebi. Nic nie zmieniono.'
    stats=stage_report(profile['effective_stage'])
    mult=infinite_equipment_power_multiplier(profile['rank'],profile['grade'])
    return (f'EQ PROGNOZA: {source} pietro {raw}. Etap {stats["stage"]}; '
            f'wymagana bieglosc {stats["required_mastery"]}; ranga glebi {profile["rank"]}; '
            f'mnoznik mocy x{mult:.3f}. '
            + ('; '.join(stats['notes'])+'. ' if stats['notes'] else '')
            +'Tylko podglad, bez generowania przedmiotu i bez zmian w grze.')


def _v53_exp_thresholds(level):
    from core import progression_resources as progress
    try:level=int(level)
    except (TypeError,ValueError):raise ValueError('Poziom: podaj liczbe 1..100000.')
    if not 1<=level<=100000:raise ValueError('Poziom: podaj liczbe 1..100000.')
    entries=(('postac',progress.character_xp_to_next),
             ('bieglosc',progress.class_mastery_xp_to_next),
             ('dusza',progress.soul_xp_to_next),
             ('bron_duszy',progress.soul_weapon_mastery_xp_to_next),
             ('skille',progress.skill_xp_to_next))
    parts=[]
    for key,func in entries:
        try:
            req=func(level)
            if not isinstance(req,int) or req<0 or req>9223372036854775807:
                value='UWAGA przekroczony bezpieczny zakres SQLite int64'
            else:value=str(req)
        except (OverflowError,ValueError,ArithmeticError):
            value='UWAGA: obliczenie poza zakresem'
        parts.append(f'{key} {value}')
    return (f'EXP PROGI poziom {level}: '+'; '.join(parts)+
            '. Zero oznacza blokade limitu. Podglad nie nadaje EXP. '
            'Obliczenia wysokich poziomow wymagaja kontroli SQLite int64.')


def _v53_audit():
    state=caps.current()
    unlimited=[key for key in caps.KEYS if state[key] is None]
    from core.equipment_growth_v5300 import infinite_equipment_requirement
    checks=[f'etap EQ 900: biegłość {infinite_equipment_requirement(900)}',
            f'etap EQ 1200: biegłość {infinite_equipment_requirement(1200)}']
    return ('ADMIN LIVE AUDYT ROZWOJU: 10 dziedzin; bez limitu: '+
            (', '.join(unlimited) if unlimited else 'brak')+'. '+
            '; '.join(checks)+'. '
            'UWAGA: Soul Tier, receptury i budynki gildii nie sa automatycznie rozszerzane. '
            'Limit techniczny 1 mld; SQLite int64 i koszt obliczen EXP moga byc wezszym ograniczeniem. '
            'Tylko odczyt; baz i poziomow graczy nie zmieniono.')

def _handle(args):
    parts=str(args or '').strip().split()
    if not parts or parts in (['lista'],['status']):
        return caps.describe()+' Pomoc: admin live limity pomoc.'
    if parts == ['pomoc']:
        return _HELP
    if parts == ['audyt']:
        return _v53_audit()
    if parts[:2]==['eq','prognoza']:
        return _v53_equipment_forecast(parts)
    if len(parts)==2 and parts[0]=='progi':
        return _v53_exp_thresholds(parts[1])
    if len(parts)==1:
        return caps.describe(parts[0])
    confirmed=bool(parts and parts[-1]=='POTWIERDZAM')
    body=parts[:-1] if confirmed else parts
    if body[0]=='wczytaj' and len(body)==1:
        if not confirmed:return 'Zatwierdz: admin live limity wczytaj POTWIERDZAM.'
        vals=caps.load()
        return 'LIMITY WCZYTANE z pliku; '+caps.describe()
    if body[0]=='reset' and len(body)==2:
        if body[1]=='wszystko':
            if not confirmed:return 'PLAN: 10 limitow -> domyslne; EQ 800, ulepszenia EQ +10. Bez zmian. Dodaj POTWIERDZAM.'
            _,_,changed=caps.reset_all()
            return 'LIMITY RESET: domyslne (EQ 800, ulepszenia EQ +10). '+('Zapisano.' if changed else 'Bez zmian.')
        key=caps.normalize_key(body[1])
        old=caps.cap(key)
        if not confirmed:
            return f'LIMITY PLAN: {caps.LABELS[key]} {caps.display(old)} -> {caps.DEFAULTS[key]}. Bez zmian. Dodaj POTWIERDZAM.'
        _,old,new,changed=caps.reset(key)
        return f'LIMITY ZAPISANO: {caps.LABELS[key]} {caps.display(old)} -> {caps.display(new)}. '+('Trwaly zapis.' if changed else 'Bez zmian.')
    if body[0]=='ustaw' and len(body)==3:
        key=caps.normalize_key(body[1]); value=caps.parse_limit(body[2])
        old=caps.cap(key)
        if not confirmed:
            return (f'LIMITY PLAN: {caps.LABELS[key]} {caps.display(old)} -> '
                    f'{caps.display(value)}. Bez zmian. Powtorz z POTWIERDZAM.')
        _,old,new,changed=caps.change(key,body[2])
        return (f'LIMITY ZAPISANO: {caps.LABELS[key]} {caps.display(old)} -> '
                f'{caps.display(new)}. '+('Dziala teraz; zapis trwaly.' if changed else 'Bez zmian.')+
                ' Nie obnizamy uzyskanych poziomow.')
    if body[0]=='wszystkie' and len(body)==2:
        value=caps.parse_limit(body[1]); previous=caps.current()
        if not confirmed:
            return ('LIMITY PLAN: wszystkie 10 kategorii na '+caps.display(value)+
                    '. Bez zmian. Zatwierdz POTWIERDZAM.')
        _,_,changed=caps.change_all(body[1])
        return ('LIMITY ZAPISANO: wszystkie 10 kategorii '+caps.display(value)+
                '. '+('Dziala teraz i po restarcie.' if changed else 'Bez zmian.')+
                ' Nie cofamy uzyskanych poziomow.')
    raise ValueError('Nieznana skladnia. Wpisz admin live limity pomoc.')


async def dispatch_v52_caps(session,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return
    try:
        result=_handle(raw)
    except (ValueError,TypeError,OSError,OverflowError) as exc:
        result='ADMIN LIVE LIMITY: '+str(exc)[:250]
    await session.send(result)
