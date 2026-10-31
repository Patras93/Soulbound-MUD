# -*- coding: utf-8 -*-
"""Isolated check of Era admin live read-only vocabulary and permission gate."""
from __future__ import annotations
import asyncio
from types import SimpleNamespace

def run():
    from systems.admin_live_era_v10300 import report,handle
    from world.v10300_era_bez_granic import install as era_install
    from world.v10300_era_raids import install as raids_install
    n=0
    def ok(flag,label):
        nonlocal n
        assert flag,label;n+=1
    rooms={'v3000_eternal_6':{'exits':{}}};mobs={};spawns=[];npcs={};quests={};items={};recipes={};areas=[]
    era_install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    raids_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    for t in ('','pomoc','krainy','region swit','region tron','region brak',
              'rajdy','rajd swit','rajd gwiazdy','rajd brak','soul 1','soul 80','soul 81','soul 500','soul 501','soul x','audyt','zly_arg'):
        reply=report(t,quests,rooms,npcs,mobs)
        ok(isinstance(reply,str) and bool(reply),'reply '+t)
        ok(len(reply)<1800,'NVDA size '+t)
    ok('165 lokacji' in report('audyt',quests,rooms,npcs,mobs),'room count')
    ok('385 questów' in report('audyt',quests,rooms,npcs,mobs),'quest count')
    ok('Soul Level 810' in report('soul 81',quests,rooms,npcs,mobs),'tier81')
    ok('etapy' in report('region swit',quests,rooms,npcs,mobs),'raid directions')
    ok('Władca Rajdu' in report('rajd swit', quests, rooms, npcs, mobs), 'raid boss info')
    ok('11' in report('rajdy', quests, rooms, npcs, mobs), 'raid list')
    class Session:
        def __init__(self,admin):self.admin=admin;self.messages=[]
        def is_admin(self):return self.admin
        async def send(self,text):self.messages.append(text)
    guest=Session(False)
    asyncio.run(handle(guest,'audyt'))
    ok(guest.messages==['Nieznana komenda. Wpisz help.'],'guest access')
    return n
if __name__=='__main__':print(f'ERA ADMIN READ-ONLY: {run()} checks PASS',flush=True)
