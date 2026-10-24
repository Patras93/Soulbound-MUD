# -*- coding: utf-8 -*-
"""v70.00.3: explain what can actually be edited; never guess quest IDs."""
from __future__ import annotations
from core.classes_skills import CLASS_SKILLS
from data.mobs import MOB_TEMPLATES
from systems.admin_live_integrity_v4900 import _effective, _issues
from systems.admin_live_v7002 import _goals
from systems.live_olc4_boss_phases import eligible_boss

HELP = ('ADMIN LIVE POMOC 28: questy automaty diagnoza QUEST_ID - szczegoly bledow, '
        'mozliwa bezpieczna naprawa licznika i sciezka recznej korekty ID; '
        'boss mechaniki ID - pola taktyki do edycji dla zwyklych bossow, '
        'ochrona skryptowanych UOSS; skill mechanika ID - typ, cooldown, '
        'sposob wlaczenia mechanicznego cooldownu w DRAFT. '
        'Brak automatycznej zamiany niejednoznacznych celow, walka UOSS nie jest 1:1. '
        'admin live centrum nowosci - skrot nowej funkcjonalnosci.')


def quest_diagnosis(service, qid):
    catalog = _effective(service)
    if qid not in catalog:
        raise ValueError('Nieznany QUEST_ID; szukaj przez admin live questy szukaj FRAZA.')
    q = catalog[qid]
    errors, hints = _issues(qid, q, catalog)
    goal = _goals(service, catalog, qid)
    current = q.get('needed')
    deterministic = goal is not None and (type(current) is not int or current != goal)
    suggestions = []
    if deterministic:
        suggestions.append(f'Bezpieczny plan: admin live questy automaty plan {qid}')
    if errors or hints:
        suggestions.append(f'Identyfikatory i cele popraw tylko jawnie: admin live questy pakiet plan pole {qid} POLE WARTOSC')
        suggestions.append('Wspomaganie ID: admin live questy ref karta '+qid)
    if not suggestions:
        suggestions.append('Brak wykrytej jednoznacznej rozbieznosci; fabule przetestuj w grze')
    return (f'QUEST DIAGNOZA {qid}, typ {q.get("kind")}: potrzebne {current}, '
            f'suma znanych celow {goal if goal is not None else "NIEJEDNOZNACZNA"}; '
            f'pewne bledy {len(errors)}: {", ".join(errors[:4]) or "brak"}; '
            f'sygnaly do sprawdzenia {len(hints)}: {", ".join(hints[:3]) or "brak"}. '
            +'. '.join(suggestions)+'. Bez zmian postepu graczy i SQLite.')


def boss_mechanics(service, bid):
    known = dict(MOB_TEMPLATES)
    known.update(service.draft.get('mobs',{}))
    if bid not in known:
        raise ValueError('Nieznany mob. admin live katalog mob FRAZA.')
    row = dict(known[bid]);row.update(service.draft.get('mob_edits',{}).get(bid,{}))
    if row.get('uoss_superboss') or row.get('uoss_superboss_id') or row.get('uoss_unique_superboss_key'):
        return (f'BOSS MECHANIKI {bid}: skryptowany UOSS, chroniony przed zwykla edycja AI. '
                'Jest osobny podglad: admin live arena uoss reguly. '
                'Nie ma bezpiecznej dowolnej edycji kodu walki.')
    if not eligible_boss(row):
        return f'BOSS MECHANIKI {bid}: brak dostepnej taktyki zwyklego bossa; sprawdz admin live pola mob {bid}.'
    names = ('olc_boss_tactic_interval','olc_boss_tactic_element','olc_boss_element_cycle',
             'olc_boss_phases','olc_boss_support_interval','olc_boss_support_duration',
             'olc_boss_support_priority','olc_boss_rally_interval','olc_boss_guard_threshold')
    state='; '.join(f'{n}={row[n]}' for n in names if n in row)
    return (f'BOSS MECHANIKI {bid}: zwykly boss, pola taktyki obslugiwane: '
            +', '.join(names)+f'. Obecne ustawienia: {state or "domyslne"}. '
            f'Komenda: admin live edytuj mob {bid} POLE | WARTOSC. '
            'Zmiana wymaga osobnej walidacji i publikacji OLC; nie kazde pole jest dozwolone dla kazdego bossa.')


def skill_mechanics(service, sid):
    known = {s['id']:s for group in CLASS_SKILLS.values() for s in group}
    known.update(service.draft.get('skills',{}))
    if sid not in known:
        raise ValueError('Nieznany skill; admin live katalog skill FRAZA.')
    row = dict(known[sid]);row.update(service.draft.get('skill_edits',{}).get(sid,{}))
    from systems.live_olc6_skill_editor import parse_existing_skill_field
    try:
        # Pure validation of the actual current definition, no edits.
        parse_existing_skill_field(row,'mechanic_cooldown',False)
        allowed=True
    except ValueError:
        allowed=False
    return (f'SKILL MECHANIKA {sid}: rodzaj {row.get("kind")}, unlock {row.get("unlock")}, '
            f'cooldown {row.get("cooldown",0)} sekund, mechaniczny '
            f'{"TAK" if row.get("mechanic_cooldown") else "NIE"}; '
            f'dostepnosc przełącznika {"TAK" if allowed and sid not in service.draft.get("skills",{}) else "NIE / nowy skill ma odrebny edytor"}. '
            'Dla zwyklego istniejacego skilla najpierw ustaw cooldown > 0, potem: '
            f'admin live edytuj skill {sid} mechanic_cooldown | true. '
            'Tylko DRAFT, bez skryptow.')


async def dispatch_v7003_diagnostics(session,group,raw):
    args=str(raw or '').strip().split()
    match=(group=='pomoc' and args==['28']) or (group in ('questy','zadania') and args[:2]==['automaty','diagnoza']) or (group=='boss' and args[:1]==['mechaniki']) or (group=='skill' and args[:1]==['mechanika']) or (group=='centrum' and args==['nowosci'])
    if not match:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':out=HELP
        elif group=='centrum':out=(
            'ADMIN LIVE CENTRUM NOWOSCI V71.00.0: 1. pomoc 29 - UOSS, questy, skill pakiet, boss fazy i limity reszta; '
            '2. pomoc 30 - rodowod istniejących ras i klas; 3. pomoc 31 - offline postacie; '
            '4. sklepy progresja dodaj/usun do 8 wariantow; stare instrukcje: pomoc 27 i 28. '
            'V70.00.3: sklepy progresja; '
            '2. pomoc 28 - diagnoza questow, bossow i skilli; '
            '3. limity eq, bieglosc, profesje, narzedzia, gildia - edytor respektuje nowe progi; '
            '4. edytuj skill ID cooldown | 5, edytuj skill ID mechanic_cooldown | true; '
            '5. sklep nowy wariant jest domyslnie WYLACZONY. Stare centrum 1-4 bez zmian.')
        elif group in ('questy','zadania') and len(args)==3:
            out=quest_diagnosis(session.server.live_content_v1204,args[2])
        elif group=='boss' and len(args)==2:
            out=boss_mechanics(session.server.live_content_v1204,args[1])
        elif group=='skill' and len(args)==2:
            out=skill_mechanics(session.server.live_content_v1204,args[1])
        else:
            raise ValueError('Uzyj: questy automaty diagnoza ID / boss mechaniki ID / skill mechanika ID.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE DIAGNOZA V70.00.3: '+str(exc)[:220]
    await session.send(out)
    return True
