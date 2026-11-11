# -*- coding: utf-8 -*-
"""Czysty katalog ośmiu profesji — bez zależności od serwera i SQLite."""
from core.archetypes.expansion import PROFESSION_SPECS


def tools():
    return {'v11000_prof_tool_'+str(i+1):
            {'name':label,'type':'tool','tool_type':tool,'price':1200,
             'currency':'silver','bind_on_pickup':True,
             'desc':'Narzędzie profesji '+name+'; do kupienia na targu za 1200 srebra, tylko raz na postać.','v11000':True}
            for i,(name,tool,label,_) in enumerate(PROFESSION_SPECS)}


def products():
    return {'v11000_prof_product_'+str(i+1):
            {'name':'Wyrób '+name,'type':'craft_material','price':None,
             'sell_silver':40,'desc':'Produkt profesji '+name+'.','v11000':True}
            for i,(name,_,_,_) in enumerate(PROFESSION_SPECS)}
