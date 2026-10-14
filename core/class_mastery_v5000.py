# -*- coding: utf-8 -*-
"""Additional real learnable arts for 14 existing classes, no class/skill resets."""
# class, focused technique (lvl 350), ultimate (lvl 700), first kind, last kind
ARTS = {
 'Wojownik': ('Przebicie Żelaznej Korony','Rozkaz Ostatecznej Szarży','execute','aoe_damage'),
 'Berserker': ('Rozdarcie Serca Kolosa','Furia Wygasłych Słońc','execute','damage'),
 'Łotrzyk': ('Przecięcie Niewidzialnej Nici','Noc Bez Śladów','damage','boost'),
 'Łowca': ('Strzała Gwiezdnego Tropu','Grad Łowcy Bogów','execute','aoe_damage'),
 'Mnich': ('Pęknięcie Siedmiu Bram','Stan Niewzruszonego Ducha','damage','guard'),
 'Strażnik': ('Cios Niezłomnej Cytadeli','Ostatni Bastion','damage','guard'),
 'Mag': ('Lanca Pradawnego Runu','Spadające Gwiazdy Eteru','damage','aoe_damage'),
 'Nekromanta': ('Cios Zagubionej Duszy','Szept Tysiąca Przodków','damage','aoe_damage'),
 'Kapłan': ('Wyrok Świetlistego Sądu','Krąg Oczyszczającego Świtu','damage','aoe_damage'),
 'Czarownik': ('Pęknięta Pieczęć Chaosu','Otchłań Bez Końca','damage','aoe_damage'),
 'Druid': ('Gniew Pierwszego Drzewa','Przebudzenie Korzeni','damage','boost'),
 'Psionik': ('Cięcie Wspomnień','Rezonans Tysiąca Umysłów','damage','aoe_damage'),
 'Mec': ('Przeładowanie Rdzenia V-MAX','Orbitalny Wyrok','damage','aoe_damage'),
 'Inżynier': ('Precyzyjny Ładunek Runiczny','Sieć Detonacyjna','execute','aoe_damage'),
}

def install(catalogue, classes):
    types = {name: kind for name, kind, *_ in classes}
    if set(catalogue) != set(ARTS):
        raise AssertionError('v5 mastery must cover exactly 14 existing classes')
    total = 0
    for name,(focused,ultimate,first_kind,second_kind) in ARTS.items():
        magic = types[name] == 'magic'
        scale = ('intelligence' if magic else 'dexterity' if name in
                 ('Łotrzyk','Łowca','Mnich','Inżynier') else 'strength')
        key = 'v500_'+str(list(ARTS).index(name))
        for level,title,kind,base in ((350,focused,first_kind,3.3),(700,ultimate,second_kind,4.5)):
            row = {'id':f'{key}_{level}', 'name':title,'aliases':[title.lower()],
                   'natural_tags':['wojna bogow','mistrzostwo','pradawni'],
                   'unlock':level,'kind':kind,'cooldown':17 if level==350 else 27,
                   'mana':(60 if level==350 else 115) if magic else 0,
                   'desc':f'Pradawna technika klasy {name}, odblokowana na poziomie biegłości {level}.',
                   'scale':scale}
            if kind in ('damage','aoe_damage','execute'):
                row['mult'] = base if kind != 'aoe_damage' else base * .84
                if kind == 'execute':row['execute_mult'] = 2.25
            elif kind == 'boost':
                row['boost'] = 1.65 if level==350 else 1.90
                row['duration'] = 17
            elif kind == 'guard':
                row['guard'] = 115 if level==350 else 330
            if any(old['id'] == row['id'] for old in catalogue[name]):
                raise AssertionError('Duplicate v5 art '+row['id'])
            catalogue[name].append(row)
            total += 1
    return total
