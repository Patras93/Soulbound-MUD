# -*- coding: utf-8 -*-
"""40 zadań: 5 na każdą nową klasę, tylko rzeczywiste cele mobów."""
from core.archetypes.expansion import CLASS_SPECS

def rows(regions,prefix,mobs,npcs):
    from world.v11000_realms import _quest
    for i,(cl,*_) in enumerate(CLASS_SPECS):
        p=prefix(regions[i][0]);nid=p+'_npc_1';giver=npcs[nid]['name'];low=102001+i*1000
        tag=cl.casefold().replace(' ','_')
        for j in range(1,6):
            qid='v11000_class_'+tag+f'_{j:02d}'
            mid=p+f'_mob_{1+(j*2)%12}' if j<5 else p+'_boss_3'
            opts={'requires_quest':'v11000_class_'+tag+f'_{j-1:02d}'} if j>1 else {}
            q=_quest(p,cl+f': Próba {j}/5',giver,'kill',mid,2+j if j<5 else 1,low,j+140,
                     repeat=False,required_class=cl,**opts)
            yield nid,qid,q
