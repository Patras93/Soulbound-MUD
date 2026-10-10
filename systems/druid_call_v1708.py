# -*- coding: utf-8 -*-
"""v1.70.9: diverse terrain calls, rarity progression and forest squirrel."""
import unicodedata

def fold(value):
    t=''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold()) if not unicodedata.combining(c))
    return t.replace('ł','l').replace('-',' ').strip()

ANIMALS={
 'wilk':dict(name='Wilk Runiczny',call='wilk',mana=50,damage=.44,damage_kind='physical',hp_factor=.50,role='atak'),
 'sowa':dict(name='Sowa Gwiezdna',call='sowa',mana=55,damage=.46,damage_kind='magic',hp_factor=.42,role='wsparcie'),
 'niedzwiedz':dict(name='Niedźwiedź Runiczny',call='niedzwiedz',mana=110,damage=.66,damage_kind='physical',hp_factor=1.1,role='obrona'),
 'zw_lis':dict(name='Leśny Lis',call='lis',mana=40,damage=.36,damage_kind='physical',hp_factor=.42,role='atak'),
 'zw_dzik':dict(name='Dziki Odyniec',call='dzik',mana=65,damage=.54,damage_kind='physical',hp_factor=.8,role='obrona'),
 'zw_jastrzab':dict(name='Jastrząb Wiatru',call='jastrzab',mana=55,damage=.53,damage_kind='physical',hp_factor=.4,role='atak'),
 'zw_jelen':dict(name='Jeleń Strażnik',call='jelen',mana=55,damage=.35,damage_kind='physical',hp_factor=.78,role='wsparcie'),
 'zw_orzel':dict(name='Orzeł Górski',call='orzel',mana=70,damage=.61,damage_kind='physical',hp_factor=.54,role='atak'),
 'zw_kozica':dict(name='Kozica Górska',call='kozica',mana=45,damage=.4,damage_kind='physical',hp_factor=.55,role='obrona'),
 'zw_zaba':dict(name='Żaba Bagienna',call='zaba',mana=35,damage=.32,damage_kind='magic',hp_factor=.37,role='wsparcie'),
 'zw_czapla':dict(name='Czapla',call='czapla',mana=45,damage=.40,damage_kind='physical',hp_factor=.43,role='atak'),
 'zw_delfin':dict(name='Delfin',call='delfin',mana=70,damage=.55,damage_kind='physical',hp_factor=.70,role='wsparcie'),
 'zw_foka':dict(name='Foka',call='foka',mana=65,damage=.44,damage_kind='physical',hp_factor=.75,role='obrona'),
 'zw_nietoperz':dict(name='Nietoperz Jaskiniowy',call='nietoperz',mana=40,damage=.37,damage_kind='physical',hp_factor=.33,role='wsparcie'),
 'zw_pajak':dict(name='Pająk Jaskiniowy',call='pajak',mana=55,damage=.46,damage_kind='physical',hp_factor=.42,role='atak'),
 'zw_golab':dict(name='Gołąb Miejski',call='golab',mana=30,damage=.25,damage_kind='physical',hp_factor=.30,role='wsparcie'),
 'zw_kot':dict(name='Kot',call='kot',mana=35,damage=.31,damage_kind='physical',hp_factor=.37,role='atak'),
 'zw_skorpion':dict(name='Skorpion Pustynny',call='skorpion',mana=70,damage=.56,damage_kind='physical',hp_factor=.35,role='atak'),
}
# v1.70.9: authored fauna; each call is a distinct, persistent companion.
ANIMALS['zw_borsuk']=dict(name='Borsuk Leśny',call='borsuk',mana=42,damage=0.38,damage_kind='physical',hp_factor=0.56,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_rys']=dict(name='Ryś Leśny',call='rys',mana=65,damage=0.52,damage_kind='physical',hp_factor=0.48,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_dzieciol']=dict(name='Dzięcioł Zielony',call='dzieciol',mana=45,damage=0.35,damage_kind='physical',hp_factor=0.35,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_bialy_jelen']=dict(name='Biały Jeleń',call='bialy jelen',mana=125,damage=0.76,damage_kind='magic',hp_factor=0.82,role='wsparcie',rarity='rzadkie',min_level=100)
ANIMALS['zw_duch_lasu']=dict(name='Pradawny Duch Lasu',call='duch lasu',mana=250,damage=0.96,damage_kind='magic',hp_factor=1.1,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_zajac']=dict(name='Zając Łąkowy',call='zajac',mana=30,damage=0.27,damage_kind='physical',hp_factor=0.29,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_bawol']=dict(name='Bawół Stepowy',call='bawol',mana=67,damage=0.53,damage_kind='physical',hp_factor=0.92,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_sokol']=dict(name='Sokół Łąkowy',call='sokol',mana=115,damage=0.74,damage_kind='physical',hp_factor=0.5,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_jednorozec']=dict(name='Jednorożec Świetlisty',call='jednorozec',mana=245,damage=0.94,damage_kind='magic',hp_factor=1.02,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_kruk_gorski']=dict(name='Kruk Szczytów',call='kruk gorski',mana=45,damage=0.4,damage_kind='physical',hp_factor=0.32,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_puma']=dict(name='Puma Skalna',call='puma',mana=75,damage=0.61,damage_kind='physical',hp_factor=0.57,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_pantera_sniezna']=dict(name='Pantera Śnieżna',call='pantera sniezna',mana=145,damage=0.82,damage_kind='physical',hp_factor=0.68,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_gryf']=dict(name='Gryf Szczytów',call='gryf',mana=265,damage=0.99,damage_kind='physical',hp_factor=1.02,role='atak',rarity='legendarne',min_level=300)
ANIMALS['zw_bobor']=dict(name='Bóbr Bagienny',call='bobor',mana=40,damage=0.35,damage_kind='physical',hp_factor=0.68,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_waz']=dict(name='Wąż Wodny',call='waz wodny',mana=55,damage=0.5,damage_kind='physical',hp_factor=0.41,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_krokodyl']=dict(name='Krokodyl Bagienny',call='krokodyl',mana=135,damage=0.79,damage_kind='physical',hp_factor=0.94,role='obrona',rarity='rzadkie',min_level=100)
ANIMALS['zw_bazyliszek']=dict(name='Bazyliszek Bagien',call='bazyliszek',mana=260,damage=0.97,damage_kind='magic',hp_factor=1.05,role='atak',rarity='legendarne',min_level=300)
ANIMALS['zw_mewa']=dict(name='Mewa Sztormowa',call='mewa',mana=35,damage=0.34,damage_kind='physical',hp_factor=0.32,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_zolw']=dict(name='Żółw Morski',call='zolw',mana=65,damage=0.41,damage_kind='physical',hp_factor=0.94,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_rekin']=dict(name='Rekin Głębinowy',call='rekin',mana=165,damage=0.86,damage_kind='physical',hp_factor=0.72,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_wieloryb']=dict(name='Wieloryb Przypływów',call='wieloryb',mana=285,damage=0.92,damage_kind='magic',hp_factor=1.18,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_kret']=dict(name='Kret Jaskiniowy',call='kret',mana=30,damage=0.33,damage_kind='physical',hp_factor=0.47,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_salamandra']=dict(name='Salamandra Jaskiniowa',call='salamandra',mana=70,damage=0.55,damage_kind='magic',hp_factor=0.5,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_cien_pajaka']=dict(name='Cienisty Pająk',call='cienisty pajak',mana=140,damage=0.8,damage_kind='magic',hp_factor=0.53,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_pradawny_nietoperz']=dict(name='Pradawny Nietoperz',call='pradawny nietoperz',mana=250,damage=0.97,damage_kind='magic',hp_factor=0.9,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_kruk']=dict(name='Kruk Miejski',call='kruk',mana=40,damage=0.38,damage_kind='physical',hp_factor=0.35,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_szczur']=dict(name='Szczur Zaułków',call='szczur',mana=30,damage=0.29,damage_kind='physical',hp_factor=0.34,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_sokol_krolewski']=dict(name='Sokół Królewski',call='sokol krolewski',mana=130,damage=0.79,damage_kind='physical',hp_factor=0.55,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_zloty_kruk']=dict(name='Złoty Kruk',call='zloty kruk',mana=235,damage=0.92,damage_kind='magic',hp_factor=0.85,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_fenek']=dict(name='Fenek',call='fenek',mana=45,damage=0.37,damage_kind='physical',hp_factor=0.36,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_waran']=dict(name='Waran Pustynny',call='waran',mana=63,damage=0.54,damage_kind='physical',hp_factor=0.7,role='obrona',rarity='zwykle',min_level=0)
ANIMALS['zw_kobra']=dict(name='Kobra Piasków',call='kobra',mana=130,damage=0.78,damage_kind='physical',hp_factor=0.48,role='atak',rarity='rzadkie',min_level=100)
ANIMALS['zw_feniks_pustyni']=dict(name='Feniks Pustyni',call='feniks pustyni',mana=265,damage=0.99,damage_kind='magic',hp_factor=0.88,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_jerzyk']=dict(name='Jerzyk Wysokich Chmur',call='jerzyk',mana=45,damage=0.4,damage_kind='physical',hp_factor=0.3,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_kruk_burzowy']=dict(name='Kruk Burzowy',call='kruk burzowy',mana=72,damage=0.56,damage_kind='magic',hp_factor=0.45,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_pegaz']=dict(name='Pegaz',call='pegaz',mana=140,damage=0.8,damage_kind='magic',hp_factor=0.9,role='obrona',rarity='rzadkie',min_level=100)
ANIMALS['zw_feniks_nieba']=dict(name='Feniks Zorzy',call='feniks zorzy',mana=290,damage=1.0,damage_kind='magic',hp_factor=1.07,role='wsparcie',rarity='legendarne',min_level=300)
ANIMALS['zw_lis_polarny']=dict(name='Lis Polarny',call='lis polarny',mana=45,damage=0.39,damage_kind='physical',hp_factor=0.42,role='wsparcie',rarity='zwykle',min_level=0)
ANIMALS['zw_wilk_polarny']=dict(name='Wilk Polarny',call='wilk polarny',mana=75,damage=0.62,damage_kind='physical',hp_factor=0.65,role='atak',rarity='zwykle',min_level=0)
ANIMALS['zw_biala_sowa']=dict(name='Biała Sowa',call='biala sowa',mana=135,damage=0.8,damage_kind='magic',hp_factor=0.56,role='wsparcie',rarity='rzadkie',min_level=100)
ANIMALS['zw_gryf_lodowy']=dict(name='Gryf Lodowy',call='gryf lodowy',mana=275,damage=0.97,damage_kind='magic',hp_factor=1.03,role='obrona',rarity='legendarne',min_level=300)
for _animal in ANIMALS.values():
    _animal.setdefault('rarity','zwykle')
    _animal.setdefault('min_level',0)

BIOMES={'las': ('wilk', 'sowa', 'niedzwiedz', 'zw_lis', 'zw_borsuk', 'zw_rys', 'zw_dzieciol', 'zw_bialy_jelen', 'zw_duch_lasu'), 'łąka': ('zw_dzik', 'zw_jastrzab', 'zw_jelen', 'zw_zajac', 'zw_bawol', 'zw_sokol', 'zw_jednorozec'), 'góry': ('zw_orzel', 'zw_kozica', 'zw_jastrzab', 'zw_kruk_gorski', 'zw_puma', 'zw_pantera_sniezna', 'zw_gryf'), 'bagno': ('zw_zaba', 'zw_czapla', 'zw_dzik', 'zw_bobor', 'zw_waz', 'zw_krokodyl', 'zw_bazyliszek'), 'woda': ('zw_delfin', 'zw_foka', 'zw_mewa', 'zw_zolw', 'zw_rekin', 'zw_wieloryb'), 'jaskinia': ('zw_nietoperz', 'zw_pajak', 'zw_kret', 'zw_salamandra', 'zw_cien_pajaka', 'zw_pradawny_nietoperz'), 'miasto': ('zw_golab', 'zw_kot', 'zw_kruk', 'zw_szczur', 'zw_sokol_krolewski', 'zw_zloty_kruk'), 'pustynia': ('zw_skorpion', 'zw_jastrzab', 'zw_fenek', 'zw_waran', 'zw_kobra', 'zw_feniks_pustyni'), 'niebo': ('zw_jerzyk', 'zw_kruk_burzowy', 'zw_pegaz', 'zw_feniks_nieba'), 'śnieg': ('zw_lis_polarny', 'zw_wilk_polarny', 'zw_biala_sowa', 'zw_gryf_lodowy')}

def biome_for_room(room, room_id=''):
    full=fold(' '.join((str(room_id),str(room.get('zone','')),str(room.get('name','')))))
    if any(x in full for x in ('v1700_sky','podniebn','przystan sterow','niebo','niebios','wysokie chmur','zorz nieba')):return 'niebo'
    if any(x in full for x in ('lodowa kraina','kraina lodu','tundr','wieczny snieg','lodowiec','zamarznieta')):return 'śnieg'
    if any(x in full for x in ('woda','ocean','morze','jezior','rzeka','podwod','wyspa','port morski')):return 'woda'
    if any(x in full for x in ('jaskin','krypt','loch','piwnic','katakumb','podziem','tunel','kopal','labirynt')):return 'jaskinia'
    if any(x in full for x in ('gaj','las','lesn','puszcz','bor ','grove','forest','zagaj','wood','ogrod','park ')):return 'las'
    if any(x in full for x in ('bagno','bagn','bagien','torf','mokra','trzcin')):return 'bagno'
    if any(x in full for x in ('gor ','gora','gory','skal','szczyt','przelecz','mountain')):return 'góry'
    if any(x in full for x in ('pustyn','wydm','piasek','desert')):return 'pustynia'
    if any(x in full for x in ('miasto','tawern','rynek','swia tyn','swiatyn','sala','zamek','karczm','ulica','plac ','gild')):return 'miasto'
    return 'łąka'

def terrain_animals(biome, level=None):
    # Squirrels provide cones only in woods, groves and meadows.
    pool=(('squirrel',) if biome in ('las','łąka') else ()) + BIOMES.get(biome,BIOMES['łąka'])
    if level is None:
        return pool
    return tuple(key for key in pool if key=='squirrel' or int(level)>=int(ANIMALS[key]['min_level']))

def normalize_animal(name):
    name=fold(name)
    if name in ('squirrel','wiewiorka','wiewiorke','wiewiora','szyszki','acorn'):return 'squirrel'
    for key,value in ANIMALS.items():
        if name in (fold(key),fold(value['call']),fold(value['name'])):return key
    return name
