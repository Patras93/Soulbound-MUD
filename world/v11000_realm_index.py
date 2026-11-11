# -*- coding: utf-8 -*-
"""v110: indeks krain, źródła danych zachowane w odrębnych modułach."""
from world.realms.delta_przyplywow import REGION as R0
from world.realms.puszcza_zarodnikow import REGION as R1
from world.realms.pustkowie_luster import REGION as R2
from world.realms.kanion_mechanizmow import REGION as R3
from world.realms.archipelag_sygnalow import REGION as R4
from world.realms.ogrod_zorz import REGION as R5
from world.realms.ziemie_nocy import REGION as R6
from world.realms.bazylika_glosow import REGION as R7
from world.realms.wulkan_popiolu import REGION as R8
from world.realms.szczeliny_swiatla import REGION as R9
from world.realms.forteca_slonc import REGION as R10
from world.realms.serce_kontynentu import REGION as R11
REGIONS = (R0,R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,)
assert len(REGIONS)==12 and len({r[0] for r in REGIONS})==12 and len({r[1] for r in REGIONS})==12
