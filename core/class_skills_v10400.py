# -*- coding: utf-8 -*-
"""Three new endgame skills per existing class, in the canonical trainer catalog.

Higher unlocks require successful high-level progression integration; until
that is verified this is a non-production gameplay extension.
"""
from __future__ import annotations

NAMES={
'Wojownik':('Cięcie Gwiezdnego Tronu','Szturm Nieskończonej Armii','Przysięga Królewskiej Stali'),
'Berserker':('Gniew Pierwotnego Tytana','Huragan Krwi Eonów','Szał Ostatniej Bitwy'),
'Łotrzyk':('Sztylet Zagubionych Światów','Taniec Tysiąca Cieni','Maska Wiecznej Nocy'),
'Łowca':('Strzała Poza Horyzont','Deszcz Smoczych Strzał','Oko Wiecznego Tropiciela'),
'Mnich':('Dłoń Nieba i Ziemi','Krąg Siedmiu Dusz','Medytacja Źródła'),
'Strażnik':('Uderzenie Niezniszczalnej Tarczy','Fala Bastionów','Przymierze Obrońcy'),
'Mag':('Promień Pierwszego Słońca','Kataklizm Kręgów','Koncentracja Run Stworzenia'),
'Nekromanta':('Pieczęć Milczącego Grobu','Legion Dusz Otchłani','Rytuał Wiecznego Cienia'),
'Kapłan':('Sąd Krystalicznego Światła','Deszcz Uświęcenia','Modlitwa Pierwszej Gwiazdy'),
'Czarownik':('Pakt Rozbitego Nieba','Otchłań Królewskich Cieni','Przysięga Zakazanej Runy'),
'Druid':('Cios Korzeni Wieczności','Szał Pierwszego Lasu','Pieśń Pradawnej Natury'),
'Psionik':('Pęknięcie Myśli Absolutu','Burza Wspomnień','Skupienie Nieskończoności'),
'Mec':('Ostrzał Gwiezdnej Cytadeli','Salwa Oblężenia','Przeciążenie Gwiezdnego Rdzenia'),
'Inżynier':('Ładunek Ostatecznej Precyzji','Drony Starego Świata','Kalibracja Bez Końca'),
'Paladyn':('Ostrze Sądu','Świetlisty Krąg','Przysięga Wiecznego Świtu'),
'Samuraj':('Cięcie Przecinające Niebo','Taniec Tysiąca Ostrzy','Spokój Ostatniego Ronina'),
'Korsarz':('Atak Króla Burz','Kanonnada Nieskończonej Floty','Flaga Wiecznych Mórz'),
'Gladiator':('Cios Areny Bogów','Wir Żelaznej Chwały','Ryk Niepokonanego'),
'Chronomanta':('Dotyk Pękniętej Sekundy','Wicher Czasów','Krąg Nieskończonej Chwili'),
'Iluzjonista':('Prawda Tysiąca Masek','Lustrzane Oblężenie','Zasłona Pierwszego Snu'),
'Bard':('Akord Królewskiego Świtu','Hymn Tysiąca Głosów','Pieśń Wieloświata'),
'Szaman':('Dotyk Najstarszych Przodków','Burza Duchów Natury','Przymierze Duchów'),
}

def install(catalog, classes):
    if set(NAMES)!={row[0] for row in classes}:
        raise RuntimeError('Katalog umiejętności v104 nie pokrywa wszystkich klas')
    added=0
    for index,(name,klass_type,*_) in enumerate(classes,1):
        old=catalog.setdefault(name,[])
        existing={x.get('id') for x in old}
        base=f'v10400_skill_{index:02d}'
        if {f'{base}_{i}' for i in (1,2,3)} <= existing:
            continue
        if any(f'{base}_{i}' in existing for i in (1,2,3)):
            raise RuntimeError(f'Niekompletna instalacja umiejętności: {name}')
        magic=(klass_type=='magic')
        stat='intelligence' if magic else 'dexterity' if name in ('Łotrzyk','Łowca','Mnich','Samuraj','Korsarz','Inżynier') else 'strength'
        titles=NAMES[name]
        skills=(
            dict(id=f'{base}_1',name=titles[0],aliases=[titles[0].lower()],kind='damage',
                 unlock=5200,cooldown=14,mana=80 if magic else 0,scale=stat,mult=3.0,
                 desc=f'Zaawansowana umiejętność klasy {name}, biegłość 5200.'),
            dict(id=f'{base}_2',name=titles[1],aliases=[titles[1].lower()],kind='aoe_damage',
                 unlock=7600,cooldown=20,mana=110 if magic else 0,scale=stat,mult=2.65,
                 desc=f'Atak obszarowy klasy {name}, biegłość 7600.'),
            dict(id=f'{base}_3',name=titles[2],aliases=[titles[2].lower()],kind='boost',
                 unlock=9800,cooldown=28,mana=75 if magic else 0,boost=1.55,duration=16,
                 desc=f'Wzmocnienie klasy {name}, biegłość 9800.'),
        )
        old.extend(skills);added+=3
    return added


def is_authored_endgame_unlock_v104(skill, class_name=None):
    """True ONLY for original class-matched 5200/7600/9800 v104 abilities.

    Prevents the historical 800-level auditors from hiding a damaged or
    arbitrary new skill. Older skill IDs retain their old hard cap.
    """
    if not isinstance(skill, dict):
        return False
    sid = skill.get('id')
    if type(sid) is not str:
        return False
    import re
    match = re.fullmatch(r'v10400_skill_(\d{2})_([123])', sid)
    if not match:
        return False
    idx, n = map(int, match.groups())
    names = tuple(NAMES)
    if not 1 <= idx <= len(names) or (class_name is not None and names[idx-1] != class_name):
        return False
    expected = (5200, 7600, 9800)[n-1]
    return type(skill.get('unlock')) is int and skill['unlock'] == expected
