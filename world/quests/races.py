# -*- coding: utf-8 -*-
"""24 zadania: po 3 dla każdej nowej rasy, z prawdziwym sprawdzeniem rasy."""
from core.archetypes.expansion import RACE_SPECS

def rows(regions,prefix,mobs,npcs):
    from world.v11000_realms import _quest
    for i,(race,*_) in enumerate(RACE_SPECS):
        p=prefix(regions[(i+4)%12][0]);nid=p+'_npc_2'
        low=102001+((i+4)%12)*1000;giver=npcs[nid]['name']
        tag=race.casefold().replace(' ','_')
        for j in range(1,4):
            qid='v11000_race_'+tag+f'_{j:02d}'
            mid=p+f'_mob_{j+7}'
            options={'requires_quest':'v11000_race_'+tag+f'_{j-1:02d}'} if j>1 else {}
            q=_quest(p,race+f': Dziedzictwo {j}/3',giver,'kill',mid,3+j,low,j+130,
                     repeat=False,required_race=race,**options)
            yield nid,qid,q
