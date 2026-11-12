# -*- coding: utf-8 -*-
"""Keep the actual teacher help after ALL catalog/help finalizers.

No version-specific staging or legacy activator is involved. Registration is
idempotent and changes only the eight authored class help topics.
"""
from __future__ import annotations


def publish_teacher_help(runtime):
    from systems.new_heroes_v900 import NEW_CLASSES
    from systems.class_legend_paths_v900 import TEACHER_NAMES
    NPCS = runtime['NPCS']
    ROOMS = runtime['ROOMS']
    from data.current_help import get_help_catalogs
    from storage.db_shared import normalize_lookup_text

    topics, aliases = get_help_catalogs()
    from systems.content_registry import HELP_TOPICS as catalogue_topics
    from systems.content_registry import HELP_TOPIC_ALIASES as catalogue_aliases
    # The authoring registry and public session HELP are separate objects in
    # the new explicit runtime. Keep just these eight teacher pages identical.
    surfaces = ((topics,aliases),(catalogue_topics,catalogue_aliases),
                (runtime['HELP_TOPICS'],runtime['HELP_TOPIC_ALIASES']))
    updated = 0
    for row in NEW_CLASSES:
        name, _, _, _, slug, *_ = row
        teacher = NPCS.get('teacher_v900_' + slug)
        if not teacher or teacher.get('name') != TEACHER_NAMES[name]:
            raise RuntimeError('Niekompletny nauczyciel klasy ' + name + ': '+repr(teacher) + ' expected '+repr(TEACHER_NAMES[name]))
        room = ROOMS.get(teacher.get('room'))
        if not room:
            raise RuntimeError('Brak lokacji nauczyciela klasy ' + name)
        key = 'klasa_' + slug
        lines = list(topics.get(key) or ())
        line = ('Nauczyciel: ' + teacher['name'] + '. '
                'Lokacja: ' + room['name'] + '. '
                'Ma 3 zadania; quest list i przyjmij 1; learn uczy umiejętności.')
        lines = [text for text in lines if not str(text).startswith('Nauczyciel: ')]
        if not lines:
            lines.append('Klasa ' + name + ': umiejętności, rozwój i zadania nauczyciela.')
        lines.append(line)
        for surface_topics,surface_aliases in surfaces:
            surface_topics[key] = list(lines)
            surface_aliases[normalize_lookup_text(name)] = key
        updated += 1
    teacher_overview = [
        'Każda klasa ma nauczyciela skilli. Osiem klas posiada także trzy osobne zadania u imiennego nauczyciela.',
        'U nauczyciela: quest list, przyjmij 1, questy postep, oddaj quest; nauka umiejętności: learn.',
        'Próby obejmują walkę, zdobycie materiału i finał. Postęp i nagrody zapisuje SQLite.',
        'Droga Legendy (120 etapów) pozostaje u oddzielnego Mistrza Drogi Legendy.',
    ]
    for surface_topics, surface_aliases in surfaces:
        surface_topics['nauczyciele klas'] = list(teacher_overview)
        surface_aliases['nauczyciele'] = 'nauczyciele klas'
    return updated
