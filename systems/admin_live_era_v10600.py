# -*- coding: utf-8 -*-
"""v106: guarded Admin Live 3.0 facade for existing v104/v105 DRAFT/CAS.

All writes require the opt-in v106 staging flag; numbers only, author-generated
IDs only, staged in the SAME historic journal and rollback. No new SQLite or
source-code execution; ordinary v105 server never sees these commands.
"""
from __future__ import annotations
from systems.runtime_activation import enabled as _sb107_runtime_enabled

import os
from world.v10600_region_index import REGIONS
from world.v10600_raids_26_35 import RAID_ROWS
from world.v10600_soul_trials import trial_ids
from systems import admin_live_era_v10400 as native

HELP=(
    'ADMIN LIVE V106 3.0, tylko na kopii testowej: '
    'regiony [strona], region SLUG, rajdy [strona], rajd 26..35, '
    'soul TIER, audyt, status, podglad TYP ID POLE, '
    'ustaw TYP ID POLE LICZBA, sprawdz, porownaj, '
    'aktywuj POTWIERDZAM, anuluj, cofnij POTWIERDZAM. '
    'Typy liczbowe: mob, quest, room, recipe, item, raid_phase, soul_trial. '
    'Przykłady: ustaw mob v10600_raid_26_boss_1 max_hp 5000000000; '
    'ustaw soul_trial soul_tier_3010_trial needed 2; '
    'ustaw raid_phase v10600_raid_26_boss_1 p1_attack_pct 150. '
    'Ten sam dziennik DRAFT/CAS co v104/v105; żadnych osobnych ustawień ani resetu graczy.'
)


def _page(rows, raw='1', page_size=5):
    if not isinstance(raw,str) or not raw.isascii() or not raw.isdecimal() or len(raw)>4:
        return 'Podaj numer strony 1..9999.'
    page=int(raw); pages=max(1,(len(rows)+page_size-1)//page_size)
    if not 1<=page<=pages:return f'Dostępne strony: 1..{pages}.'
    return page,pages,rows[(page-1)*page_size:page*page_size]


def command(tail, registries, *, connection=None):
    if (os.environ.get('SOULBOUND_V106_STAGING') != '1' and
            not _sb107_runtime_enabled()):
        return 'Admin Live v106 nieaktywny. Produkcyjne v105 pozostaje bez zmian.'
    args=str(tail or '').strip().split()
    if not args or args[0].casefold() in ('pomoc','help'):
        if _sb107_runtime_enabled():
            return 'V106: regiony, region, soul, audyt. Rajdy wycofane w v107.'
        return HELP
    action=args[0].casefold()
    if _sb107_runtime_enabled() and action in ('rajd','rajdy'):
        return 'V107: rajdy 26–35 są wycofane. Ich zadania zastąpiły zwykłe polowania.'
    if action in ('regiony','krainy') and len(args)<=2:
        result=_page(REGIONS,args[1] if len(args)>1 else '1')
        if isinstance(result,str):return result
        page,pages,rows=result
        return ('V106 KRAINY '+f'{page}/{pages}: '+'; '.join(
             f'{x[0]} {x[2]}–{x[3]}' for x in rows)+'.')
    if action=='region' and len(args)>=2:
        token=' '.join(args[1:]).casefold()
        found=next((x for x in REGIONS if token in (x[0],x[1].casefold())),None)
        if not found:return 'V106: nieznana kraina. Użyj regiony.'
        slug,name,low,high,*_=found
        prefix=f'v10600_{slug}_'
        return (f'V106 {name}, poziomy {low}–{high}. '
            f'Pomieszczenia {sum(k.startswith(prefix) for k in registries["rooms"])}; '
            f'potwory {sum(k.startswith(prefix) for k in registries["mobs"])}; '
            f'questy {sum(k.startswith(prefix) for k in registries["quests"])}. '
            f'Wejście: {prefix}01; brak twardej blokady poziomu.')
    if action=='rajdy' and len(args)<=2:
        result=_page(RAID_ROWS,args[1] if len(args)>1 else '1')
        if isinstance(result,str):return result
        page,pages,rows=result
        return (f'V106 RAJDY {page}/{pages}: '+'; '.join(f'{r[0]}: {r[2]}' for r in rows)+'.')
    if action=='rajd' and len(args)==2:
        if not args[1].isascii() or not args[1].isdecimal():return 'Podaj numer rajdu 26..35.'
        number=int(args[1]); selected=next((r for r in RAID_ROWS if r[0]==number),None)
        if selected is None:return 'Podaj numer rajdu 26..35.'
        no,idx,name,*_=selected
        mid=[f'v10600_raid_{no}_boss_{i}' for i in (1,2,3)]
        qid=[f'v10600_raid_{no}_quest_{i}' for i in (1,2,3)]
        if not all(k in registries['mobs'] for k in mid) or not all(k in registries['quests'] for k in qid):
            return 'V106: rajd niekompletny; nie edytuj, sprawdź katalog.'
        return (f'V106 rajd {no}: {name}. Trzy etapy; '+
                '; '.join(f'{i}: {registries["mobs"][m]["name"]}' for i,m in enumerate(mid,1))+
                '. Nagrody zadań i fazy bossa edytuj przez podglad/ustaw.')
    if action=='soul' and len(args)==2:
        if not args[1].isascii() or not args[1].isdecimal() or len(args[1])>4:
            return 'Podaj Soul Tier 3010..6000, wielokrotność 10.'
        tier=int(args[1]); ids=trial_ids()
        if tier not in ids:return 'Podaj Soul Tier 3010..6000, wielokrotność 10.'
        qid=ids[tier]; quest=registries['quests'].get(qid)
        if not isinstance(quest,dict) or quest.get('unlocks_soul_tier')!=tier:
            return 'Brak prawidłowej Próby Duszy w świecie. Nie edytuj.'
        return (f'V106 Soul Tier {tier}: próba {qid}, wymagany Soul Level '
            f'{quest["required_soul_level"]}, cel {quest["target"]}, '
            f'wymagane zabicia {quest["needed"]}. Historia postaci bez zmian.')
    if action=='audyt' and len(args)==1:
        from core.live_level_caps_v5200 import cap, display
        soul_cap=cap('dusza')
        required=60000
        soul_ready=(soul_cap is None or int(soul_cap)>=required)
        limit_info=(f'Limit Soul Level {display(soul_cap)}: '
            + ('zgodny z Tierem 6000' if soul_ready else
               f'BLOKADA PROGRESJI, wymagane co najmniej {required}; '
               f'zmiana wyłącznie przez administratora: admin live limity ustaw dusza {required} POTWIERDZAM'))
        trial_set=set(trial_ids().values())
        quest_count=sum(k.startswith('v10600_') or k in trial_set
                        for k in registries['quests'])
        _legacy_raids = (0 if _sb107_runtime_enabled() else len(RAID_ROWS))
        return (f'V106 ADMIN LIVE AUDYT: krain {len(REGIONS)}; aktywnych rajdów {_legacy_raids}; '
            f'nowych prób {len(trial_set)}; '
            f'pokoi {sum(k.startswith("v10600_") for k in registries["rooms"])}; '
            f'questów {quest_count}. '
            f'{limit_info}. '
            'Odczyt bez zmian SQLite i DRAFT. Wynik nie zastępuje testów TCP.')
    if action in ('podglad','ustaw','sprawdz','porownaj','aktywuj','cofnij','anuluj','status'):
        # One DRAFT/journal/revision/undo across all three eras; no v106 shadow state.
        return native.command(tail,registries,connection=connection).replace('V104','V106')
    return HELP
