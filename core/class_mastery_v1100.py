# -*- coding: utf-8 -*-
"""Forty-four genuinely learnable dual-element techniques for the 22 classes.

The existing 5417 skills and all historical skill identifiers remain intact;
existing trainer/learning/skill-use mechanics consume the normal catalog rows.
"""

# Each two-skill chain is designed to lead into the mature party elemental
# reaction logic by applying the first and then the complementary element.
CLASS_ELEMENTS = (
    ('Wojownik', 'lightning', 'fire'),
    ('Berserker', 'fire', 'dark'),
    ('Łotrzyk', 'shadow', 'poison'),
    ('Łowca', 'ice', 'lightning'),
    ('Mnich', 'arcane', 'holy'),
    ('Strażnik', 'ice', 'holy'),
    ('Mag', 'ice', 'fire'),
    ('Nekromanta', 'dark', 'poison'),
    ('Kapłan', 'holy', 'fire'),
    ('Czarownik', 'dark', 'fire'),
    ('Druid', 'poison', 'water'),
    ('Psionik', 'arcane', 'lightning'),
    ('Mec', 'fire', 'ice'),
    ('Inżynier', 'lightning', 'fire'),
    ('Paladyn', 'holy', 'lightning'),
    ('Samuraj', 'fire', 'ice'),
    ('Korsarz', 'water', 'lightning'),
    ('Gladiator', 'fire', 'poison'),
    ('Chronomanta', 'arcane', 'ice'),
    ('Iluzjonista', 'shadow', 'arcane'),
    ('Bard', 'holy', 'arcane'),
    ('Szaman', 'lightning', 'poison'),
)
ELEMENT_NAMES = {
    'fire':'Ognia','ice':'Lodu','lightning':'Piorunów',
    'dark':'Mroku','shadow':'Cienia','poison':'Trucizny',
    'holy':'Światła','water':'Wody','arcane':'Arkanów',
}

# This map is used directly by the existing elemental combat system.
SKILL_ELEMENTS = {}
for _idx,(_klass,_first,_second) in enumerate(CLASS_ELEMENTS):
    for _stage,_element in enumerate((_first,_second),1):
        _name = (f'{_klass}: Przysięga {ELEMENT_NAMES[_element]}' if _stage == 1
                 else f'{_klass}: Sąd {ELEMENT_NAMES[_element]}')
        if _name.casefold() in SKILL_ELEMENTS:
            raise RuntimeError('v11 duplicate elemental skill name')
        SKILL_ELEMENTS[_name.casefold()] = _element


def install(catalogue, classes):
    kinds={row[0]:row[1] for row in classes}
    if set(catalogue)!=set(kinds) or len(kinds)!=22:
        raise RuntimeError('v11 skill mastery expected 22 real classes')
    total = 0
    for idx,(klass,first,second) in enumerate(CLASS_ELEMENTS):
        if klass not in kinds or klass not in catalogue:
            raise RuntimeError('v11 unknown class '+klass)
        magic = kinds[klass]=='magic'
        scale = ('intelligence' if magic else 'dexterity' if klass in
                 ('Łotrzyk','Łowca','Mnich','Inżynier','Samuraj','Korsarz') else 'strength')
        for stage,level,element in ((1,640,first),(2,780,second)):
            ident=f'v1100_tech_{idx:02d}_{stage}'
            name=(f'{klass}: Przysięga {ELEMENT_NAMES[element]}' if stage==1 else
                  f'{klass}: Sąd {ELEMENT_NAMES[element]}')
            row={
                'id':ident,'name':name,'aliases':[name.lower()],
                'natural_tags':['wieczna chwała','mistrzostwo','żywioły',element],
                'unlock':level,'kind':'damage' if stage==1 else 'aoe_damage',
                'cooldown':0,'mana':(95 if stage==1 else 135) if magic else 0,
                'desc':(f'Mistrzowska technika {klass} o żywiole {element}; '+
                        'łączy się z reakcjami żywiołów drużyny.'),
                'scale':scale,'mult':(4.15 if stage==1 else 3.50),
                'element':element,'v1100_dual_elements':(first,second),
            }
            if any(old['id']==ident or old['name']==name for old in catalogue[klass]):
                raise RuntimeError('v11 skill collision '+ident)
            catalogue[klass].append(row)
            total+=1
        catalogue[klass].sort(key=lambda skill:(int(skill.get('unlock',1)),skill.get('name','')))
    if total!=44:
        raise RuntimeError('v11 missing class techniques')
    return total


def run_regression(catalogue=None):
    if catalogue is None:
        from core.classes_skills import CLASS_SKILLS as catalogue
    assert len(CLASS_ELEMENTS)==22 and len(SKILL_ELEMENTS)==44
    checks=0
    all_ids=[s['id'] for skills in catalogue.values() for s in skills]
    assert len(all_ids)==len(set(all_ids))
    checks+=1
    for idx,(klass,first,second) in enumerate(CLASS_ELEMENTS):
        mastered=[s for s in catalogue[klass] if s.get('id','').startswith('v1100_tech_')]
        assert len(mastered)==2
        for stage,(level,element) in enumerate(((640,first),(780,second)),1):
            skill=next(s for s in mastered if s['id']==f'v1100_tech_{idx:02d}_{stage}')
            assert skill['unlock']==level and skill['element']==element
            assert skill['mult']>3 and skill['cooldown']==0
            assert SKILL_ELEMENTS[skill['name'].casefold()]==element
            assert skill['kind'] in ('damage','aoe_damage')
            checks+=4
        checks+=1
    return checks

if __name__=='__main__':
    print('V11 ALL CLASSES / DUAL ELEMENTS',run_regression(),'PASS')
