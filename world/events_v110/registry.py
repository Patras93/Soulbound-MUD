# -*- coding: utf-8 -*-
"""4 definicje osobnych bossów wydarzeń; używa ich świat i harmonogram."""
from world.events_v110.przebudzenie_kontynentu import EVENT as E1
from world.events_v110.zanik_pradow import EVENT as E2
from world.events_v110.echo_imion import EVENT as E3
from world.events_v110.wielka_migracja import EVENT as E4
EVENT_SPECS={r['slug']:r for r in (E1,E2,E3,E4)}
BOSSES={r['slug']:{'name':r['boss'],'damage_type':r['damage_type']} for r in EVENT_SPECS.values()}
assert len(EVENT_SPECS)==len(BOSSES)==4
