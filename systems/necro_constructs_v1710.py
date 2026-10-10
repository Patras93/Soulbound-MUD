# -*- coding: utf-8 -*-
"""v1.70.10: Necromancer constructs & undead; distinct from soulstone skeletons.

Inspired by Alter Aeon minion archetypes; progression, recipes and balance are
Soulbound originals. All ingredient IDs are real mine, logging or loot items.
"""
NECRO_MINIONS = {
 # name, level, MP, ingredients, element, attack ratio, health ratio, role, upkeep
 'gliniany_sluga': ('Gliniany Sługa',1,35,{'stone_chunk':4},'physical',.34,.90,'obrona',2),
 'drewniany_straznik': ('Drewniany Strażnik',15,55,{'oak_log':4},'physical',.41,1.05,'obrona',3),
 'kostny_straznik': ('Kościany Strażnik',25,75,{'v1700_common_tooth':4},'physical',.53,1.15,'obrona',4),
 'bestia_ciala': ('Bestia Ciała',40,90,{'v1700_common_tooth':6,'leather_vest':1},'physical',.62,1.18,'atak',5),
 'konstrukt_miedzi': ('Miedziany Konstrukt',50,110,{'copper_ore':12,'iron_ingot':2},'physical',.70,1.32,'obrona',6),
 'konstrukt_zelaza': ('Żelazny Konstrukt',75,145,{'iron_ingot':12},'physical',.82,1.56,'obrona',8),
 'konstrukt_stali': ('Stalowy Konstrukt',110,195,{'iron_ingot':20,'silver_ingot':2},'physical',.95,1.75,'obrona',10),
 'krysztalowa_czaszka': ('Kryształowa Czaszka',120,210,{'stone_chunk':12,'soul_shard':2},'magic',1.00,.90,'wsparcie',11),
 'zombie': ('Zombie',25,75,{'v1700_common_tooth':3,'leather_vest':1},'physical',.47,1.20,'obrona',3),
 'ghul': ('Ghul',70,130,{'v1700_common_tooth':6,'soul_shard':1},'physical',.83,1.08,'atak',6),
 'widmo': ('Widmo',95,170,{'soul_shard':3},'magic',.98,.88,'wsparcie',8),
 'mumia': ('Mumia',170,240,{'soul_shard':4,'v1700_common_tooth':10},'magic',1.13,1.27,'atak',11),
 'wampir': ('Wampirzy Sługa',250,310,{'soul_shard':8,'v1700_dragon_tooth':1},'magic',1.32,1.31,'wsparcie',14),
 'demon_cienia': ('Demon Cienia',310,370,{'soul_shard':12,'v1700_dragon_tooth':2},'magic',1.50,1.30,'atak',17),
 'konstrukt_mithrilu': ('Mithrilowy Konstrukt',400,460,{'mithril_ore':12,'iron_ingot':15,'soul_shard':6},'physical',1.62,2.30,'obrona',20),
 'straznik_obsydianu': ('Obsydianowy Strażnik',475,520,{'stone_chunk':30,'soul_shard':12},'magic',1.75,2.05,'obrona',22),
 'runiczny_tytan': ('Runiczny Tytan',600,700,{'mithril_ore':22,'soul_shard':20,'worldtree_wood':2},'magic',2.0,2.8,'obrona',30),
}

ALIASES = {
 'clay man':'gliniany_sluga','gliniany':'gliniany_sluga','wood woad':'drewniany_straznik',
 'woad':'drewniany_straznik','bone guardian':'kostny_straznik',
 'flesh beast':'bestia_ciala','metal construct':'konstrukt_zelaza',
 'metalowy':'konstrukt_zelaza','metal':'konstrukt_zelaza',
 'konstrukt':'konstrukt_zelaza','zelazny':'konstrukt_zelaza',
 'miedziany':'konstrukt_miedzi','stalowy':'konstrukt_stali',
 'mithrilowy':'konstrukt_mithrilu','crystal skull':'krysztalowa_czaszka',
 'czaszka':'krysztalowa_czaszka','bone beast':'bestia_ciala',
 'zombi':'zombie','wampirzy':'wampir','tytan':'runiczny_tytan',
}

def summon_key(value):
    value=str(value).strip().casefold().replace(' ','_')
    return ALIASES.get(value.replace('_',' '), value)
