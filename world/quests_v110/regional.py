# -*- coding: utf-8 -*-
"""600 prawdziwych zadań regionalnych: 12 x 50."""
from world.v10300_era_bez_granic import PROFESSION_SPECS as OLD_PROFS
from core.v11000_archetypes import PROFESSION_SPECS as NEW_PROFS


def produce_regional(index,slug,name,low,p,enemies,bosses,materials,npcs):
    from world.v11000_realms import _quest
    npc=lambda n:p+f'_npc_{n}'
    giver=lambda n:npcs[npc(n)]['name']
    # Primary story always one-off and ordered. Each step references a real object.
    stages=(('talk_npc',2),('kill',1),('collect',1),('kill',6),
            ('talk_npc',3),('collect',3),('kill',13),('kill',12),
            ('kill',14),('kill',15))
    for j,(kind,target_index) in enumerate(stages,1):
        nid=npc(1)
        mid=(p+f'_mob_{target_index}' if target_index<=12
             else p+f'_boss_{target_index-12}')
        target=(npc(target_index) if kind=='talk_npc' else
                materials[target_index-1] if kind=='collect' else mid)
        qid=p+f'_story_{j:02d}'
        args={'requires_quest':p+f'_story_{j-1:02d}'} if j>1 else {}
        q=_quest(p,f'{name}: Opowieść {j}/10',giver(1),kind,target,
                 (1 if kind=='talk_npc' or target_index>12 else 4),low,j,repeat=False,**args)
        yield nid,qid,q
    for j in range(1,21):
        mid=p+(f'_mob_{1+(j-1)%12}' if j<=17 else f'_boss_{j-17}')
        nid=npc(2)
        qid=p+f'_hunt_{j:02d}'
        yield nid,qid,_quest(p,f'{name}: Polowanie {j}/20',giver(2),'kill',mid,
                   3+(j%5) if j<=17 else 1,low,j+10,repeat=(j<=17))
    for j in range(1,11):
        nid=npc(3);qid=p+f'_collect_{j:02d}'
        yield nid,qid,_quest(p,f'{name}: Zbiory {j}/10',giver(3),'collect',
                   materials[(j-1)%4],5+j,low,j+30)
    professions=NEW_PROFS+OLD_PROFS
    for j in range(1,11):
        nid=npc(4);qid=p+f'_prof_{j:02d}'
        prof,tool,*_=professions[((index*10)+(j-1))%len(professions)]
        yield nid,qid,_quest(p,f'{name}: Rzemiosło {prof} {j}/10',giver(4),
                   'profession_action',prof,3+j,low,j+40,
                   required_profession=prof,specialist_tool_type=tool,
                   reward_profession=prof,reward_profession_xp=low*2300,
                   reward_tool_type=tool,reward_tool_xp=low*1900)
