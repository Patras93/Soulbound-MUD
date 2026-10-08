# -*- coding: utf-8 -*-
"""Mercenaries 4.0: native class identities, situational moves and party combos.

All fifteen profiles are inherent, not purchased skills or a second XP track.
They inherit actual owner damage; this module only ADDS situational effects.
No database writes, background work, damage ceiling, or manual skill commands.
"""

SPECIALISTS = {
    'wojownik': ('Żelazna Awangarda', 'trzyma linię i przełamuje obronę', 'Ciężkie Cięcie', 'Rozłamanie Gardy', 'Kontratak Awangardy'),
    'berserker': ('Szał Bitewny', 'przyspiesza ofensywę pod presją', 'Szał Topora', 'Rozszalała Furia', 'Egzekucja Furii'),
    'lotrzyk': ('Cień Egzekutora', 'wykorzystuje osłabienie celu', 'Cios z Ukrycia', 'Ukłucie Cienia', 'Ostatni Sztych'),
    'lucznik': ('Znacznik Łowcy', 'wyznacza priorytetowe cele', 'Celny Strzał', 'Przeszywający Pocisk', 'Strzał w Słaby Punkt'),
    'mnich': ('Mistrz Kontry', 'odpowiada na silne uderzenia', 'Uderzenie Dłoni', 'Uderzenie Fali', 'Kontra Siedmiu Dłoni'),
    'straznik': ('Niezłomny Bastion', 'broni rannych, potem kontratakuje', 'Uderzenie Tarczy', 'Pęknięcie Pancerza', 'Mur Ostrzy'),
    'mag': ('Tkacz Żywiołów', 'splata zaklęcia z ciosami drużyny', 'Ognista Kula', 'Lodowy Rozbłysk', 'Arkaniczny Przełom'),
    'nekromanta': ('Żniwiarz Dusz', 'odzyskuje siłę życiową z ataków', 'Rozdarcie Cienia', 'Rozkaz Cieni', 'Żniwa Esencji'),
    'kaplan': ('Strażnik Świtu', 'leczy i rozprasza zagrożenia', 'Święty Promień', 'Świt Odkupienia', 'Osąd Światła'),
    'czarownik': ('Mistrz Klątw', 'wykorzystuje przełamania przeciwników', 'Klątwa Otchłani', 'Wybuch Klątwy', 'Splot Otchłani'),
    'druid': ('Żywe Korzenie', 'podtrzymuje drużynę w trakcie ataku', 'Gniew Korzeni', 'Burza Liści', 'Rozkwit Życia'),
    'psionik': ('Tarcza Umysłu', 'wyczuwa ataki i osłania słabszych', 'Impuls Umysłu', 'Pęknięcie Umysłu', 'Rezonans Myśli'),
    'mec': ('Adaptacyjny Arsenał', 'dobiera moduły do zagrożenia', 'Strzał Rdzenia', 'Salwa Modułów', 'Przeciążenie Rdzenia'),
    'inzynier': ('Mechanik Polowy', 'wzmacnia osłony i odsłania słabe punkty', 'Impuls Omni-Narzędzia', 'Ostrzał Konstruktu', 'Przeciążenie Osłon'),
    'paladyn': ('Przysięga Opiekuna', 'łączy wiarę, ochronę i ofensywę', 'Święty Cios', 'Sąd Przysięgi', 'Ostrze Odkupienia'),
}


def specialist_description_v1240(role):
    title, style, *abilities = SPECIALISTS[role]
    return f"{title}: {style}. Techniki: {', '.join(abilities)}. Dobór samodzielny, siła rośnie wraz z właścicielem bez sufitu."


def specialist_attack_v1240(mob, owner_id, role, attack_type, owner_level, now, boss=False, max_hp_hint=None):
    """Pick a true variant and optionally consume the preceding companion's imprint.

    Per-enemy, per-owner transient notes avoid cross-player damage contamination.
    Impacts expire, change with the target and do not change persistent contracts.
    """
    notes = getattr(mob, '_mercenary_specialists_v1240', None)
    if not isinstance(notes, dict):
        notes = {}
        mob._mercenary_specialists_v1240 = notes
    # Remove stale owner entries so rare persistent bosses do not accumulate notes.
    for key in list(notes):
        if float(notes[key].get('expires', 0.0)) < now:
            del notes[key]
    key = str(owner_id)
    state = notes.get(key, {})
    sequence = int(state.get('sequence', 0))
    prev_role = state.get('role')
    prev_type = state.get('attack_type')
    title, _style, ordinary, threat, finish = SPECIALISTS[role]
    hp = max(0, int(getattr(mob, 'hp', 0) or 0))
    maxhp = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or getattr(mob, 'max_hp', 0) or max_hp_hint or hp or 1))
    # Never depend solely on a monster's missing max_hp to choose a finishing move.
    exhausted = hp > 0 and hp * 100 <= maxhp * 35
    technique = finish if exhausted or boss else threat if sequence % 3 == 1 else ordinary
    # Every specialist has its own unlimited growth in addition to full owner DPS.
    factor = 1.0 + .00012 * max(0, int(owner_level) - 1)
    if boss:
        factor *= 1.08
    if exhausted and role in ('lotrzyk', 'berserker', 'lucznik', 'nekromanta'):
        factor *= 1.18
    combo = ''
    if prev_role and prev_role != role:
        if prev_type != attack_type:
            combo = 'Reakcja: przełamanie magii i stali'
            factor *= 1.16 + .00005 * max(0, int(owner_level) - 1)
        else:
            combo = 'Reakcja: wspólny nacisk'
            factor *= 1.08
    # This is not a status debuff to be applied across unrelated accounts.
    notes[key] = dict(role=role, attack_type=attack_type, sequence=sequence + 1,
                      expires=float(now) + 12.0)
    return factor, technique, combo


def specialist_support_on_strike_v1240(role, weakest, damage, major_threat, healing_blocked):
    """Low-noise, automatic secondary support that never consumes an attack turn.

    A support technique is only announced when it actually changes HP or guard.
    Healing still respects superboss restrictions and never exceeds missing HP.
    """
    if weakest is None:
        return ''
    hp_max = max(1, int(weakest.max_hp()))
    hp_now = max(0, int(weakest.current_hp))
    if role in ('nekromanta', 'kaplan', 'druid', 'paladyn') and not healing_blocked and hp_now < hp_max:
        frac = {'nekromanta': .02, 'kaplan': .04, 'druid': .035, 'paladyn': .02}[role]
        # Lifesteal uses actual DAMAGE, never the estimated potential hit.
        recovery = min(hp_max - hp_now, max(1, int(hp_max * frac)), max(0, int(damage)))
        if recovery > 0:
            weakest.current_hp += recovery
            return f"Regeneracja {weakest.character.name}: +{recovery} HP."
    if role in ('wojownik', 'straznik', 'mnich', 'psionik', 'inzynier', 'mec'):
        # For serious threats, shield a weak ally even if another hit consumed
        # their previous guard; if the guard already exists, don't overwrite it.
        if hp_now < hp_max * (.95 if major_threat else .82) and int(getattr(weakest, 'skill_guard', 0)) <= 0:
            frac = {'wojownik': .05, 'straznik': .08, 'mnich': .035,
                    'psionik': .06, 'inzynier': .06, 'mec': .035}[role]
            value = max(1, int(hp_max * frac))
            weakest.skill_guard += value
            return f"Awaryjna osłona {weakest.character.name}: {value}."
    return ''
