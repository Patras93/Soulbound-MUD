# -*- coding: utf-8 -*-
"""Owner-only, read-only era audit for NVDA. Does not mutate SQLite/DRAFT."""
from __future__ import annotations

from world.v10300_era_bez_granic import ERAS
from world.v10400_krainy_5001_10000 import REGIONS
from world.v10400_raids_12_25 import RAIDS
from core.progression_600 import SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS
from core.bootstrap_economy_professions import SOUL_TRIAL_QUEST_IDS

HELP = ('ADMIN LIVE ERA: krainy / krainy104 / region NAZWA / rajdy / rajdy104 / rajd NAZWA / soul TIER / audyt / lochy / exp RODZAJ PIETRO / premie / v104 pomoc / v105 pomoc. '
        'Odczyt bez zmian w grze. Próby Soul Tier u Kapłana Elora; rajdy u Mistrza krainy.')


def report(command, quests, rooms, npcs, mobs):
    """Pure dispatcher. Bounded output avoids screen-reader overload."""
    words=str(command or '').strip().split()
    if not words:return HELP
    action=words[0].casefold()
    if action in ('pomoc','help') and len(words)==1:return HELP
    if action=='v104' and len(words)==2 and words[1]=='wydarzenia':
        return 'V104: 10 odnawialnych kontraktów inwazji z siedmiodniowym czasem od ukończenia. ' \
               'Nie są jeszcze podłączone do wspólnego licznika i rotacji wydarzeń.'
    if action in ('krainy104','regiony104') and len(words)==1:
        return 'V104 KRAINY: '+ '; '.join(f'{name}, {low}–{high}, {slug}' for slug,name,low,high,*_ in REGIONS)+'.'
    if action=='rajdy104' and len(words)==1:
        return 'V104 RAJDY: '+ '; '.join(f'{n}: {name}' for n,_,_,_,name,*_ in RAIDS)+'.'
    if action=='rajd' and len(words)>=2:
        token=' '.join(words[1:]).casefold()
        match=next((r for r in RAIDS if token in (str(r[0]),r[4].casefold())),None)
        if match is not None:
            n,slug,room_no,npc_no,name,*_=match
            boss_ids=[f'v10400_raid_{n:02d}_boss_{j}' for j in (1,2,3)]
            if not all(b in mobs for b in boss_ids):return f'V104 rajd {n}: brak definicji bossa.'
            return f'V104 RAJD {n}: {name}. Wejście v10400_{slug}_{room_no:02d}, wschód. 3 etapy: '+ '; '.join(mobs[b]['name'] for b in boss_ids)+'.'
    if action=='region' and len(words)>=2:
        token=' '.join(words[1:]).casefold()
        match=next((r for r in REGIONS if token in (r[0],r[1].casefold())),None)
        if match is not None:
            slug,name,low,high,*_=match
            prefix=f'v10400_{slug}'
            return (f'V104 {name}: poziomy {low}–{high}; '+
                f'{sum(r.startswith(prefix+"_") for r in rooms)} lokacji, '+
                f'{sum(m.startswith(prefix+"_") for m in mobs)} potworów, '+
                f'{sum(q.startswith(prefix+"_") for q in quests)} questów. '+
                f'Wejście {prefix}_01. Brak twardej blokady poziomu.')
    if action in ('krainy','lista') and len(words)==1:
        return 'ERA: '+ '; '.join(f'{name}, {low}–{high}, {slug}'
                for slug,name,low,high,*_ in ERAS)+'.'
    if action=='rajdy' and len(words)==1:
        return ('ERA RAJDY (11): ' + '; '.join(f'{slug}: {name}' for slug,name,*_ in ERAS)
                + '. Szczegóły: admin live era rajd NAZWA.')
    if action=='rajd' and len(words)>=2:
        token=' '.join(words[1:]).casefold()
        choice=next(((slug,name,low,high) for slug,name,low,high,*_ in ERAS
                     if token in (slug, name.casefold())), None)
        if choice is None:
            return 'Nie ma takiego rajdu. Wpisz admin live era rajdy.'
        slug,name,low,high=choice
        prefix=f'v10300_{slug}'
        stages=[]
        for j in (1,2,3):
            qid=f'{prefix}_raid_quest_{j}'
            mid=f'{prefix}_raid_boss_{j}'
            rid=f'{prefix}_raid_{j}'
            if qid not in quests or mid not in mobs or rid not in rooms:
                return f'ERA RAJD {name}: brakuje komnaty, zadania lub bossa etapu {j}. Użyj era audyt.'
            stages.append(f'{j}/3: {mobs[mid]["name"]}')
        return (f'ERA RAJD {name}, poziomy {low}–{high}. '
                f'NPC: Mistrz {name}, lokacja {prefix}_04. '
                f'Wejście: {prefix}_09, wschód. '
                + '; '.join(stages)
                + '. Questy przyjmuj i oddawaj u Mistrza, po kolei. '
                  'Brak blokady poziomu, ale przeciwnicy mają stałą siłę.')
    if action=='region' and len(words)>=2:
        token=' '.join(words[1:]).casefold()
        chosen=next(((slug,name,low,high) for slug,name,low,high,*_ in ERAS
               if slug==token or name.casefold()==token),None)
        if chosen is None:return 'Nie ma takiej krainy. Użyj admin live era krainy.'
        slug,name,low,high=chosen; prefix=f'v10300_{slug}'
        quests_here=sum(qid.startswith(prefix+'_') for qid in quests)
        boss_here=sum(mid.startswith(prefix+'_') and ('boss' in mid) for mid in mobs)
        return (f'ERA: {name}, poziomy {low}–{high}. Wejście {prefix}_01. '
            f'Lokacje: {sum(rid.startswith(prefix+"_") for rid in rooms)}. '
            f'Bossowie: {boss_here}; zadania: {quests_here}. '
            f'Rajd od {prefix}_09 na wschód, trzy etapy. '
            'Bez blokady poziomem; questy rajdu wymagają poprzedniego etapu.')
    if action=='soul' and len(words)==2:
        try:tier=int(words[1])
        except ValueError:return f'Soul: podaj numer Tieru od 1 do {SOUL_MAX_TIER}.'
        if tier<1 or tier>SOUL_MAX_TIER:return f'Soul: dopuszczalne Tiery 1–{SOUL_MAX_TIER}. To zakres Prób, nie limit Soul Level.'
        qid=SOUL_TRIAL_QUEST_IDS.get(tier) if tier % 10 == 0 else None
        return (f'Soul Tier {tier}/{SOUL_MAX_TIER}: wymagany Soul Level '
            f'{SOUL_TIER_THRESHOLDS[tier-1]}. '
            + (f'Próba {qid}; Kapłan Elor.' if qid else 'Bez Próby.'))
    if action == 'exp' and len(words)==3:
        from systems.era_dungeon_plus_v10300 import effective_pct, DISPLAY_NAMES
        from systems.admin_live_era_settings_v10300 import ALIASES, active_bonus_pct
        kind = ALIASES.get(words[1])
        if not kind or not words[2].isascii() or not words[2].isdecimal() or len(words[2]) > 9:
            return 'ERA EXP: użyj admin live era exp deep 1000; rodzaje jak w era premie.'
        floor = int(words[2])
        if not 1 <= floor <= 999999999:
            return 'ERA EXP: piętro 1–999999999.'
        base = effective_pct(kind, floor)
        admin = active_bonus_pct(kind)
        total = effective_pct(kind, floor, admin)
        return (f'ERA EXP: {DISPLAY_NAMES[kind]}, piętro {floor}: '
                f'bazowa premia {base}%, administrator {admin}%, efektywna {total}%. '
                'Dotyczy EXP walki; nie zmienia monet, wymagań poziomu ani bankowania.')
    if action == 'lochy' and len(words)==1:
        from systems.era_dungeon_plus_v10300 import effective_pct, DISPLAY_NAMES
        from systems.admin_live_era_settings_v10300 import active_bonus_pct
        return ('ERA LOCHY 801+: ' + '; '.join(
            f'{DISPLAY_NAMES[k]}: bazowa premia {effective_pct(k, 801)}%, '
            f'Admin Live {active_bonus_pct(k)}%, wynik {effective_pct(k, 801, active_bonus_pct(k))}% '
            for k in ('deep','crypt','mythic_crypt','tower','mythic_tower'))
            + '. Premie liczone tylko od piętra 801, bez zmiany monet, CAP i skalowania.')
    if action=='audyt' and len(words)==1:
        return (f'ERA: {len(ERAS)} krain; '
            f'{sum(k.startswith("v10300_") for k in rooms)} lokacji; '
            f'{sum(k.startswith("v10300_") for k in mobs)} szablonów potworów; '
            f'{sum(k.startswith("v10300_") for k in quests)} questów; '
            f'{sum(k.startswith("v10300_") for k in npcs)} NPC. '
            f'Soul Tier {SOUL_MAX_TIER}, próg ostatniej Próby '
            f'{SOUL_TIER_THRESHOLDS[-1]}. '
            'Nie zmieniono DRAFT, SQLite ani ustawienia skalowania.')
    return HELP


async def handle(session, tail):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    if str(tail or '').strip().casefold().split(maxsplit=1)[0:1] in (['v104'], ['v105']):
        use_v105 = str(tail or '').strip().casefold().split(maxsplit=1)[0] == 'v105'
        if use_v105:
            from systems.admin_live_era_v10500 import command as command_v104
        else:
            from systems.admin_live_era_v10400 import command as command_v104
        from core.classes_skills import ROOMS
        from systems.content_registry import QUESTS, NPCS, MOB_TEMPLATES
        from data.items import ITEMS
        from data.crafting_recipes import CRAFT_RECIPES
        rest=str(tail or '').strip().split(maxsplit=1)
        await session.send(command_v104(rest[1] if len(rest)>1 else '',{
            'rooms':ROOMS,'mobs':MOB_TEMPLATES,'quests':QUESTS,'items':ITEMS,
            'recipes':CRAFT_RECIPES}, connection=session.server.db.conn))
        return True
    # Scoped DRAFT: only the five high-floor XP multipliers, never arbitrary code.
    if str(tail or '').strip().casefold().startswith('premie'):
        from systems.admin_live_era_settings_v10300 import command
        pieces = str(tail or '').split(maxsplit=1)
        await session.send(command(pieces[1] if len(pieces) > 1 else ''))
        return True
    # These are the same live world registries used by the MUD server.
    from core.classes_skills import ROOMS
    from systems.content_registry import QUESTS, NPCS, MOB_TEMPLATES
    await session.send(report(tail, QUESTS, ROOMS, NPCS, MOB_TEMPLATES))
    return True
