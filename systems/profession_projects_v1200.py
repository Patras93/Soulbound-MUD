# -*- coding: utf-8 -*-
"""Soulbound 12.00.0: 22 real cross-profession masterworks.

Each project consumes existing products from TWO distinct professions.
Tiers increase material consumption, EXP and useful contracts. These are
additions, not substitutes for prior recipes, specialties or progress.
"""
from __future__ import annotations
from dataclasses import dataclass
import unicodedata

LEVELS=(25,200,400,600,700,775)

@dataclass(frozen=True)
class Project:
    code:str
    tool:str
    title:str
    primary:str
    partner:str
    partner_profession:str

PROJECTS = {
 'Wędkarstwo':Project('wedkarstwo','fishing','Przynęta Morskich Legend','small_fish','mint','Zielarstwo'),
 'Górnictwo':Project('gornictwo','mining','Wzorzec Żyły Pradawnej','iron_ore','stone_blocks','Murarstwo'),
 'Drwalstwo':Project('drwalstwo','woodcutting','Rdzeń Drzewa Strażnika','oak_log','iron_ingot','Kowalstwo'),
 'Zielarstwo':Project('zielarstwo','herbalism','Pęk Ziół Odnowy','mint','v600_milk','Hodowla zwierząt'),
 'Gotowanie':Project('gotowanie','cooking','Racja Długiej Wyprawy','hunt_meat','field_grain','Rolnictwo'),
 'Alchemia':Project('alchemia','alchemy','Esencja Mistycznego Wsparcia','sage','silver_ingot','Kowalstwo'),
 'Kowalstwo':Project('kowalstwo','crafting','Okucie Żelaznej Straży','iron_ingot','stone_blocks','Murarstwo'),
 'Jubilerstwo':Project('jubilerstwo','jewelcrafting','Soczewka Niebiańskiej Precyzji','silver_ingot','v600_nav_kit','Inżynieria'),
 'Krawiectwo':Project('krawiectwo','tailoring','Splot Tkackiej Harmonii','farm_wool','v600_yarn','Hodowla zwierząt'),
 'Garbarstwo':Project('garbarstwo','leatherworking','Runiczna Skóra Łowów','v600_hunting_hide','sage','Zielarstwo'),
 'Stolarstwo':Project('stolarstwo','carpentry','Rzeźbione Wzmocnienie Warsztatu','oak_plank','v600_yarn','Hodowla zwierząt'),
 'Zaklinanie':Project('zaklinanie','enchanting','Pieczęć Żywego Zaklęcia','silver_ingot','v600_mechanism','Inżynieria'),
 'Archeologia':Project('archeologia','archaeology','Oprawa Starego Reliktu','stone_chunk','v600_appraisal','Kupiectwo'),
 'Kartografia':Project('kartografia','cartography_profession','Mapa Tropiciela Tajemnic','navigation_chart','v600_tracks','Łowiectwo'),
 'Łowiectwo':Project('lowiectwo','hunting','Totem Zdobytej Zwierzyny','v600_hunting_hide','mint','Zielarstwo'),
 'Rolnictwo':Project('rolnictwo','farming','Plony Ocalenia','field_grain','v600_milk','Hodowla zwierząt'),
 'Hodowla zwierząt':Project('hodowla','animal_husbandry','Runo Opiekuna Stada','farm_wool','field_grain','Rolnictwo'),
 'Okrętownictwo':Project('okrety','shipbuilding','Pancerz Pokładu Legend','ship_parts','v600_masonry_support','Murarstwo'),
 'Murarstwo':Project('murarstwo','masonry','Fundament Niezłomnej Twierdzy','stone_blocks','iron_ingot','Kowalstwo'),
 'Inżynieria':Project('inzynieria','engineering','Autonomiczny Moduł Strażniczy','machine_gears','v600_masonry_support','Murarstwo'),
 'Kupiectwo':Project('kupiectwo','trading','Certyfikat Karawany Mistrza','trade_crate','v600_hunting_hide','Łowiectwo'),
 'Żeglarstwo':Project('zeglarstwo','sailing','Nawigacyjna Pieczęć Sztormów','v600_bearings','navigation_chart','Kartografia'),
}
assert len(PROJECTS)==22 and len({p.code for p in PROJECTS.values()})==22


def fold(text):
    s=str(text or '').casefold().replace('ł','l')
    return ''.join(x for x in unicodedata.normalize('NFKD',s) if not unicodedata.combining(x)).strip()


def resolve(text):
    key=fold(text)
    return next((prof for prof,project in PROJECTS.items()
                 if key in (fold(prof),project.code)),None)


def project_item_id(prof):
    return 'v1200_master_'+PROJECTS[prof].code


def recipe(prof,tier):
    if prof not in PROJECTS or tier not in LEVELS:
        return None
    p=PROJECTS[prof];stage=LEVELS.index(tier)
    # Different cross-professional materials, with scaling actual costs rather
    # than merely increasing the experience awarded for a fixed action.
    return ((p.primary,2+stage*2),(p.partner,1+stage))


def order_quantity(tier):
    return 2+LEVELS.index(tier)


def ensure_schema(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS prof12_contract_claims ('
                 'account_id INTEGER NOT NULL, profession TEXT NOT NULL, day INTEGER NOT NULL, '
                 'PRIMARY KEY(account_id,profession,day))')
    conn.execute('CREATE TABLE IF NOT EXISTS prof12_masterworks ('
                 'account_id INTEGER NOT NULL, profession TEXT NOT NULL, '
                 'made INTEGER NOT NULL DEFAULT 0, turned_in INTEGER NOT NULL DEFAULT 0, '
                 'PRIMARY KEY(account_id,profession))')


def crafted_items():
    return {project_item_id(prof): {
        'name':p.title,'type':'craft_material','price':None,'sell_silver':200,
        'desc':('Wyrób mistrzowski '+prof+'; może być użyty w kontrakcie v12 '
                'lub pozostawiony w ekwipunku jako opcjonalne wsparcie AI przywołań.')}
            for prof,p in PROJECTS.items()}
