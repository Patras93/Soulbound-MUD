# -*- coding: utf-8 -*-
"""36 indywidualnych questów tematycznych dla 4 globalnych wydarzeń."""
from world.events.registry import EVENT_SPECS

def rows(regions,prefix,mobs,npcs):
    from world.v11000_realms import _quest, EVENTS
    for slug,label,i in EVENTS:
        p=prefix(regions[i][0]);nid=p+'_npc_3';giver=npcs[nid]['name'];low=102001+i*1000
        boss='v11000_event_'+slug+'_boss'
        for j in range(1,10):
            qid=f'v11000_event_{slug}_quest_{j:02d}'
            mid=boss if j in (3,6,9) else p+f'_mob_{1+(j*2)%12}'
            opts={'requires_quest':f'v11000_event_{slug}_quest_{j-1:02d}'} if j>1 else {}
            q=_quest(p,label+f': Zadanie {j}/9',giver,'kill',mid,
                     1 if mid==boss else 3+(j%4),low,j+60,repeat=False,
                     v11000_event=slug,**opts)
            yield nid,qid,q
