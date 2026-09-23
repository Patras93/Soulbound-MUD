# -*- coding: utf-8 -*-
"""Soulbound v0.30.53 - Extended Crafting Professions.
Adds Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie and Jubilerstwo 2.0.
"""
from data import catalog_mutations as _catalog_mut

V03053_PROFESSIONS = {
    "Krawiectwo": {"tool_type":"tailoring","tool_item_id":"tailor_kit","tool_name":"Zestaw Krawiecki","station":"tailor_workshop"},
    "Garbarstwo": {"tool_type":"leatherworking","tool_item_id":"tanning_knife","tool_name":"Nóż Garbarski","station":"leatherworker_workshop"},
    "Stolarstwo": {"tool_type":"carpentry","tool_item_id":"carpenter_tools","tool_name":"Narzędzia Ciesielskie","station":"carpenter_workshop"},
    "Zaklinanie": {"tool_type":"enchanting","tool_item_id":"runic_focus","tool_name":"Fokus Runiczny","station":"guild_arcane_chamber"},
}

# Rangi 1-600. Pierwsze 13 są opisowe, ostatnie 10 zgodne z progresją 201-600.
def _profession_rank_names(label, master):
    base=(f"Uczeń {label}",f"Adept {label}",f"Czeladnik {label}",f"Specjalista {label}",f"Ekspert {label}",f"Mistrz {label}",f"Arcymistrz {label}",f"Legenda {label}",f"Runiczny {master}",f"Smoczy {master}",f"Astralny {master}",f"{master} Pustki",f"Wieczny {master}")
    return base + tuple(f"{suffix} {label}" for suffix in (_PROFESSION_400_RANK_SUFFIXES + _PROFESSION_600_RANK_SUFFIXES))

PROFESSION_RANK_NAMES["Krawiectwo"] = _profession_rank_names("Krawiectwa", "Krawiec")
PROFESSION_RANK_NAMES["Garbarstwo"] = _profession_rank_names("Garbarstwa", "Garbownik")
PROFESSION_RANK_NAMES["Stolarstwo"] = _profession_rank_names("Stolarstwa", "Stolarz")
PROFESSION_RANK_NAMES["Zaklinanie"] = _profession_rank_names("Zaklinania", "Zaklinacz")
TOOL_PROFESSION_MAP.update({
    "tailoring":"Krawiectwo", "leatherworking":"Garbarstwo",
    "carpentry":"Stolarstwo", "enchanting":"Zaklinanie",
})

_old_normalize_profession_name_v03053 = normalize_profession_name
def normalize_profession_name(profession):
    raw=str(profession or '').strip().casefold()
    aliases={
      'krawiectwo':'Krawiectwo','tailoring':'Krawiectwo','krawiec':'Krawiectwo',
      'garbarstwo':'Garbarstwo','leatherworking':'Garbarstwo','garbarz':'Garbarstwo','kaletnictwo':'Garbarstwo',
      'stolarstwo':'Stolarstwo','carpentry':'Stolarstwo','stolarz':'Stolarstwo','ciesielstwo':'Stolarstwo',
      'zaklinanie':'Zaklinanie','enchanting':'Zaklinanie','enchant':'Zaklinanie','enchanting':'Zaklinanie',
    }
    return aliases.get(raw) or _old_normalize_profession_name_v03053(profession)

# Czterdzieści nazw Tierów na profesję; poziomy i progi pozostają wspólne 1-600.
def _tool_names(prefix):
    stages=("Ucznia","Miedzi","Żelaza","Srebra","Złota","Hartowany","Precyzji","Kryształu","Kobaltu","Mistrza","Runiczny","Smoczy","Obsydianu","Astralny","Gwiezdny","Pustki","Otchłani","Eternium","Mityczny","Wieczny")
    extra=("Przebudzenia","Transcendencji","Horyzontu","Niebiański","Pierwotny","Echa","Korony","Serca Świata","Nieskończony","Pradawny","Zorzy","Smoczej Mocy","Tajemnicy","Gwiezdnego Rdzenia","Wieczności","Korony Świata","Przeznaczenia","Ponadczasowy","Końca","Absolutu")
    extended=("Ponadprzestrzeni","Gwiezdnego Tronu","Wiecznego Echa","Serca Otchłani","Korony Gwiazd","Sądu Horyzontu","Nieskończonego Pulsu","Kosmicznej Pieczęci","Pradawnego Rezonansu","Świtu Absolutu","Drogi Wybranych","Oka Wszechświata","Wiecznej Iskry","Transcendentnego Znaku","Głosu Nieskończoności","Ostatecznego Horyzontu","Duszy Kosmosu","Korony Wieczności","Apogeum","Absolutnej Pełni")
    return tuple(f"{prefix} {x}" for x in stages+extra+extended)
TOOL_TIER_NAMES["tailoring"]=_tool_names("Zestaw Krawiecki")
TOOL_TIER_NAMES["leatherworking"]=_tool_names("Nóż Garbarski")
TOOL_TIER_NAMES["carpentry"]=_tool_names("Narzędzia Ciesielskie")
TOOL_TIER_NAMES["enchanting"]=_tool_names("Fokus Runiczny")

# Narzędzia - brak trwałości, jak we wszystkich profesjach Soulbound.
_catalog_mut.catalog_update_path('ITEMS', ITEMS, (), {
 "tailor_kit":{"name":"Zestaw Krawiecki","type":"tool","tool_type":"tailoring","price":1200,"currency":"silver","desc":"Igły, nici i nożyce do Krawiectwa. Level 1-600, 60 Tierów, bez trwałości."},
 "tanning_knife":{"name":"Nóż Garbarski","type":"tool","tool_type":"leatherworking","price":1200,"currency":"silver","desc":"Narzędzie Garbarstwa. Level 1-600, 60 Tierów, bez trwałości."},
 "carpenter_tools":{"name":"Narzędzia Ciesielskie","type":"tool","tool_type":"carpentry","price":1200,"currency":"silver","desc":"Dłuta, piła precyzyjna i hebel do Stolarstwa. Level 1-600, 60 Tierów, bez trwałości."},
 "runic_focus":{"name":"Fokus Runiczny","type":"tool","tool_type":"enchanting","price":1200,"currency":"silver","desc":"Fokus do trwałego zaklinania wyposażenia. Level 1-600, 60 Tierów, bez trwałości."},
 "beast_hide":{"name":"Surowa Skóra Bestii","type":"resource","price":None,"sell_silver":20,"desc":"Skóra pozyskiwana z bestii. Podstawowy materiał Garbarstwa."},
 "tanned_hide":{"name":"Garbowana Skóra","type":"resource","price":None,"sell_silver":35,"desc":"Oczyszczona skóra do pancerzy, pasów i naramienników."},
 "woven_cloth":{"name":"Tkana Tkanina","type":"resource","price":None,"sell_silver":30,"desc":"Tkanina utkana z włókien roślinnych."},
 "treated_plank":{"name":"Obrobiona Deska","type":"resource","price":None,"sell_silver":30,"desc":"Precyzyjnie obrobiona deska do Stolarstwa i housingu."},
 "runic_essence":{"name":"Esencja Runiczna","type":"resource","price":None,"sell_silver":50,"desc":"Skondensowana esencja używana przez Zaklinaczy."},
})

# Przykładowe pełne linie EQ 1-600. Każdy wynik ma inną tożsamość/statystyki.
def _armor(iid,name,slot,defense,affix,amount,level,profession):
    _catalog_mut.catalog_assign({"name":name,"type":"armor","slot":slot,"defense":defense,"price":None,"rarity":"crafted","rarity_name":profession,"affix":affix,"affix_amount":amount,"generator_level":level,"desc":f"{profession} level {level}. Obrona +{defense}; {affix} +{amount}."}, 'ITEMS', ITEMS, (iid,))

_tailor=[
 (1,"cloak","Płaszcz Wędrowca","dexterity"),(30,"body","Szata Wzmocnionych Włókien","willpower"),(60,"cloak","Płaszcz Srebrnej Nici","intelligence"),(100,"body","Runiczna Szata Tkacza","mana"),(160,"cloak","Astralny Płaszcz","dexterity"),(220,"body","Szata Przebudzenia","intelligence"),(300,"cloak","Płaszcz Gwiezdnego Rdzenia","willpower"),(400,"body","Szata Absolutnego Krawca","mana")]
_leather=[
 (1,"belt","Pas Garbowanej Skóry","constitution"),(30,"bracers","Karwasze Łowcy","dexterity"),(60,"shoulders","Naramienniki Twardej Skóry","constitution"),(100,"belt","Runiczny Pas Bestii","strength"),(160,"bracers","Karwasze Astralnej Skóry","dexterity"),(220,"shoulders","Naramienniki Przebudzenia","constitution"),(300,"belt","Pas Gwiezdnej Bestii","strength"),(400,"bracers","Karwasze Absolutnego Garbarza","dexterity")]
_carp=[
 (1,"charm","Drewniany Talizman Rzemieślnika","willpower"),(30,"charm","Dębowy Totem Straży","constitution"),(60,"charm","Jesionowy Totem Mocy","strength"),(100,"charm","Runiczny Totem","intelligence"),(160,"charm","Astralny Totem","mana"),(220,"charm","Totem Przebudzenia","willpower"),(300,"charm","Totem Gwiezdnego Serca","hp"),(400,"charm","Totem Absolutnego Stolarza","constitution")]
for prefix,rows,prof in (("tailor",_tailor,"Krawiectwo"),("leather",_leather,"Garbarstwo"),("carp",_carp,"Stolarstwo")):
    for idx,(lvl,slot,name,affix) in enumerate(rows):
        amount=max(1,1+lvl//55) if affix not in ('hp','mana') else 20+lvl//2
        _armor(f"v03053_{prefix}_{lvl}",name,slot,1+lvl//35,affix,amount,lvl,prof)

# Jubilerstwo 2.0 - nowe wyroby zamiast duplikowania starych nazw.
_jewel=[
 (30,'earring','Kolczyk Srebrnego Echa','dexterity',2,'silver_ingot'),
 (60,'necklace','Naszyjnik Złotej Gwiazdy','intelligence',3,'gold_ingot'),
 (100,'ring','Runiczny Pierścień Harmonii','willpower',4,'runestone_ingot'),
 (160,'earring','Astralny Kolczyk Precyzji','dexterity',5,'astral_ingot'),
 (220,'necklace','Naszyjnik Przebudzenia','mana',130,'ingot_400_220'),
 (300,'ring','Pierścień Gwiezdnego Rdzenia','strength',7,'ingot_400_300'),
 (400,'necklace','Korona Klejnotów Absolutu','intelligence',9,'ingot_400_400'),
]
for lvl,slot,name,affix,amt,mat in _jewel:
    iid=f"v03053_jewel_{lvl}"
    _armor(iid,name,slot,2+lvl//55,affix,amt,lvl,"Jubilerstwo")


# v0.36.0: pełna treść 420-600 dla rozszerzonych profesji rzemieślniczych.
# Każdy próg co 20 leveli ma własny przedmiot i recepturę; ID są stabilne i
# nazwy nie są numerowanymi kopiami dla gracza.
V0360_EXTENDED_PROFESSION_LEVELS = tuple(range(420, 601, 20))
V0360_EXTENDED_SUFFIXES = {
    420:"Przekroczenia", 440:"Gwiezdnego Tronu", 460:"Wiecznego Echa",
    480:"Serca Otchłani", 500:"Korony Gwiazd", 520:"Sądu Horyzontu",
    540:"Kosmicznego Szlaku", 560:"Wieczności", 580:"Apogeum", 600:"Absolutu Duszy",
}
for _i,_lvl in enumerate(V0360_EXTENDED_PROFESSION_LEVELS):
    _suffix=V0360_EXTENDED_SUFFIXES[_lvl]
    _tail_slot=("cloak","body")[_i%2]
    _tail_aff=("dexterity","intelligence","willpower","mana")[_i%4]
    _tail_name=("Płaszcz" if _tail_slot=="cloak" else "Szata")+f" {_suffix}"
    _armor(f"v03053_tailor_{_lvl}",_tail_name,_tail_slot,1+_lvl//35,_tail_aff,(2+_lvl//55 if _tail_aff!='mana' else 20+_lvl//2),_lvl,"Krawiectwo")
    _tailor.append((_lvl,_tail_slot,_tail_name,_tail_aff))

    _leath_slot=("belt","bracers","shoulders")[_i%3]
    _leath_aff=("constitution","dexterity","strength")[_i%3]
    _leath_label={"belt":"Pas","bracers":"Karwasze","shoulders":"Naramienniki"}[_leath_slot]
    _leath_name=f"{_leath_label} {_suffix}"
    _armor(f"v03053_leather_{_lvl}",_leath_name,_leath_slot,1+_lvl//35,_leath_aff,2+_lvl//55,_lvl,"Garbarstwo")
    _leather.append((_lvl,_leath_slot,_leath_name,_leath_aff))

    _carp_aff=("willpower","constitution","strength","intelligence","hp")[_i%5]
    _carp_name=f"Totem {_suffix}"
    _armor(f"v03053_carp_{_lvl}",_carp_name,"charm",1+_lvl//35,_carp_aff,(2+_lvl//55 if _carp_aff!='hp' else 20+_lvl//2),_lvl,"Stolarstwo")
    _carp.append((_lvl,"charm",_carp_name,_carp_aff))

    _j_slot=("ring","necklace","earring")[_i%3]
    _j_aff=("strength","intelligence","willpower","dexterity","constitution")[_i%5]
    _j_label={"ring":"Pierścień","necklace":"Naszyjnik","earring":"Kolczyk"}[_j_slot]
    _j_name=f"{_j_label} {_suffix}"
    _j_amt=7+(_lvl-400)//40
    _armor(f"v03053_jewel_{_lvl}",_j_name,_j_slot,2+_lvl//55,_j_aff,_j_amt,_lvl,"Jubilerstwo")
    _jewel.append((_lvl,_j_slot,_j_name,_j_aff,_j_amt,f"ingot_400_{_lvl}"))

# Skóry dropią z realnych bestii, bez osobnego generatora zasobów.
for _mid,_mob in MOB_TEMPLATES.items():
    _name=str(_mob.get('name','')).casefold()
    if any(k in _name for k in ('wilk','niedźw','dzik','bestia','pająk','stalker','bear','wolf','boar')):
        _mob.setdefault('drops',{})
        _mob['drops'].setdefault('beast_hide',0.18)

# Warsztaty i sprzedawcy.
for _room,_item,_seller in (
 ('tailor_workshop','tailor_kit','tailor_lysa'),('leatherworker_workshop','tanning_knife','leatherworker_soren'),('carpenter_workshop','carpenter_tools','carpenter_edric'),('guild_arcane_chamber','runic_focus','guild_quartermaster_arcane')):
    _catalog_mut.catalog_setdefault_path('SHOPS', SHOPS, (), _room,[])
    if _item not in SHOPS[_room]: SHOPS[_room].append(_item)
    SHOP_SELLERS[_room]=_seller
TOOL_SHOP_ROOMS.update({'tailor_kit':'tailor_workshop','tanning_knife':'leatherworker_workshop','carpenter_tools':'carpenter_workshop','runic_focus':'guild_arcane_chamber'})

# v0.31.7: wszystkie 12 profesji używa tej samej zasady: dokładnie jedno narzędzie na postać.
CHARACTER_BOUND_TOOL_IDS.update({'tailor_kit','tanning_knife','carpenter_tools','runic_focus'})
TOOL_BUY_ALIASES.update({
 'zestaw krawiecki':'tailor_kit','tailor kit':'tailor_kit','sewing kit':'tailor_kit',
 'noz garbarski':'tanning_knife','tanning knife':'tanning_knife','leatherworking knife':'tanning_knife',
 'narzedzia ciesielskie':'carpenter_tools','carpenter tools':'carpenter_tools','carpentry tools':'carpenter_tools',
 'fokus runiczny':'runic_focus','runic focus':'runic_focus','enchanting focus':'runic_focus',
})

# Receptury wspólnego silnika perform_recipe.
V03053_CRAFT_RECIPES={}
def _recipe(key,name,profession,tool_type,tool_item,station,level,ingredients,output,quantity=1,xp=None):
    V03053_CRAFT_RECIPES[key]={"name":name,"profession":profession,"tool_type":tool_type,"tool_item_id":tool_item,"tool_name":ITEMS[tool_item]['name'],"stations":(station,),"min_profession_level":level,"ingredients":ingredients,"output":output,"quantity":quantity,"profession_xp":xp or max(20,level*3),"tool_xp":max(15,level*2),"generator_level":level,"desc":f"Receptura profesji {profession}."}

_recipe('cloth','Tkana Tkanina','Krawiectwo','tailoring','tailor_kit','tailor_workshop',1,{'nettle':2,'chamomile':1},'woven_cloth')
for lvl,slot,name,affix in _tailor:
    mat={'woven_cloth':max(2,2+lvl//80)}
    if lvl>=420: mat[f'herb_400_{lvl}']=2
    elif lvl>=100: mat['runestone_ore']=1
    _recipe(f'tailor_{lvl}',name,'Krawiectwo','tailoring','tailor_kit','tailor_workshop',lvl,mat,f'v03053_tailor_{lvl}')
_recipe('tan_hide','Garbowana Skóra','Garbarstwo','leatherworking','tanning_knife','leatherworker_workshop',1,{'beast_hide':2,'sage':1},'tanned_hide')
for lvl,slot,name,affix in _leather:
    mat={'tanned_hide':max(2,2+lvl//80)}
    if lvl>=420: mat[f'ore_400_{lvl}']=1
    elif lvl>=100: mat['runestone_ore']=1
    _recipe(f'leather_{lvl}',name,'Garbarstwo','leatherworking','tanning_knife','leatherworker_workshop',lvl,mat,f'v03053_leather_{lvl}')
_recipe('plank','Obrobiona Deska','Stolarstwo','carpentry','carpenter_tools','carpenter_workshop',1,{'birch_log':2},'treated_plank')
_carp_mats={1:'treated_plank',30:'oak_log',60:'ash_log',100:'runewood_log',160:'astralwood_log',220:'wood_400_220',300:'wood_400_300',400:'wood_400_400', **{lvl:f'wood_400_{lvl}' for lvl in V0360_EXTENDED_PROFESSION_LEVELS}}
for lvl,slot,name,affix in _carp:
    _recipe(f'carp_{lvl}',name,'Stolarstwo','carpentry','carpenter_tools','carpenter_workshop',lvl,{_carp_mats[lvl]:2},f'v03053_carp_{lvl}')

# Jubilerstwo 2.0 w istniejącym systemie receptur.
for lvl,slot,name,affix,amt,mat in _jewel:
    iid=f'v03053_jewel_{lvl}'
    JEWELCRAFT_RECIPES[iid]={"name":name,"profession":"Jubilerstwo","tool_type":"jewelcrafting","stations":('jeweler_workshop',),"min_profession_level":lvl,"ingredients":{mat:2},"output":iid,"quantity":1,"profession_xp":max(30,lvl*3),"tool_xp":max(20,lvl*2),"generator_level":lvl,"desc":"Receptura Jubilerstwa 2.0."}

V03053_ENCHANTS={
 'sila':('Siła', 'strength',1, {'runestone_ore':1,'sage':2}),
 'zrecznosc':('Zręczność','dexterity',1,{'runestone_ore':1,'mint':2}),
 'kondycja':('Kondycja','constitution',1,{'runestone_ore':1,'nettle':2}),
 'inteligencja':('Inteligencja','intelligence',1,{'runestone_ore':1,'moonflower':1}),
 'wola':('Siła Woli','willpower',1,{'runestone_ore':1,'sage':2}),
 'hp':('Życie','hp',15,{'runestone_ore':1,'ginseng':1}),
 'mana':('Mana','mana',15,{'runestone_ore':1,'star_moss':1}),
}

# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.
