# -*- coding: utf-8 -*-
"""v1.27: deterministic lore, gradual discoveries and characterful bosses.

No player power caps, save migrations or duplicate item catalogs.
"""

BOSS_PHASE_LINES = {
    'black rabite': ('zamienia cień w wir', 'przyzywa mroczne echo', 'wpada w czarną furię'),
    'serpentarius': ('splata gwiezdne zaklęcia', 'otwiera wężowe wrota', 'uwalnia astralną burzę'),
    'yiazmat': ('budzi pradawny oddech', 'łamie rytm drużyny', 'wstrząsa areną'),
    'dragon': ('rozpościera ogniste skrzydła', 'przywołuje płomienie', 'uderza smoczym gniewem'),
    'lich': ('unosi księgę klątw', 'wznawia mroczny rytuał', 'rzuca ostatnią klątwę'),
}

def boss_phase_identity_v1270(template, stage):
    name = str(template.get('name') or '').casefold()
    for term, lines in BOSS_PHASE_LINES.items():
        if term in name:
            return lines[max(1, min(3, int(stage))) - 1]
    element = (template.get('attack_elements_v11339') or ())
    if element:
        element = str(element[0]) if not isinstance(element, str) else element
        return ('gromadzi ' + element + ' i zmienia taktykę',
                'przeplata ataki żywiołowe z kontrami',
                'uwalnia ostateczny atak żywiołowy')[max(1,min(3,int(stage)))-1]
    return ''


def bestiary_knowledge_v1270(template, kills):
    kills = max(0, int(kills))
    lines = []
    if kills >= 3:
        affinities = template.get('attack_elements_v11339') or ()
        if isinstance(affinities, str): affinities=(affinities,)
        if affinities:
            lines.append('Poznane żywioły ataków: ' + ', '.join(map(str, affinities)) + '.')
        else:
            lines.append('Brak potwierdzonych specjalnych żywiołów ataku.')
    else:
        lines.append('Poznaj żywioły po 3 pokonaniach tego gatunku.')
    if kills >= 8:
        abilities = template.get('boss_mechanic_text') or template.get('monster_magic') or template.get('special_attacks')
        if abilities:
            lines.append('Poznane techniki: ' + str(abilities)[:240] + '.')
        else:
            lines.append('Nie odkryto dodatkowych technik w opisie tego gatunku.')
    else:
        lines.append('Poznaj techniki po 8 pokonaniach tego gatunku.')
    if kills >= 20:
        lines.append('Mistrzostwo obserwacji: rozpoznajesz zwyczaje tego gatunku.')
    return lines


def dungeon_floor_event_v1270(floor, dungeon='krypta'):
    """Meaningful deterministic features for endless floors; no traps or loot dupes."""
    floor = int(floor)
    if floor <= 0: return ''
    if floor % 50 == 0: return 'Sala Kronikarzy: kamienne kroniki dawnych wypraw.'
    if floor % 25 == 0: return 'Zapomniane Sanktuarium: na ścianach wyryto historię tego piętra.'
    if floor % 10 == 0: return 'Komnata Strażnika: tu odczujesz potęgę dalszych pięter.'
    return ''
