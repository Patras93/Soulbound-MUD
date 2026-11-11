# -*- coding: utf-8 -*-
"""v53 tests — only private JSON, temporary catalog variants, no live DB."""
import asyncio, json, tempfile
from pathlib import Path
from core import live_level_caps_v5200 as caps
from core.equipment_growth_v5300 import infinite_equipment_requirement,stage_report
from systems.admin_live_level_caps_v5200 import _handle,dispatch_v52_caps
from systems import infinite_equipment as deep
from data.items import ITEMS


def run():
    n=0
    def check(value,why=''):
        nonlocal n
        assert value,why
        n+=1
    oldpath,oldstate,oldloaded=caps.CAP_FILE,caps.current(),caps._loaded
    created=[]
    with tempfile.TemporaryDirectory(prefix='soulbound_v53_eq_') as folder:
        caps.CAP_FILE=Path(folder)/'LIVE_CONTENT'/'admin_level_caps.json'
        try:
            caps.load()
            check(caps.cap('eq')==800)
            check(infinite_equipment_requirement(1200)==600)
            check('audyt' in _handle('pomoc'))
            check('etap EQ 900: biegłość 600' in _handle('audyt'))
            check('Tylko podglad' in _handle('eq prognoza krypta 901'))
            check('Etap 910' in _handle('eq prognoza krypta 901'))
            check('Zero oznacza blokade limitu' in _handle('progi 801'))
            check(not caps.CAP_FILE.exists())
            check('PLAN' in _handle('ustaw eq 1200'))
            check(infinite_equipment_requirement(1200)==600)
            check('ZAPISANO' in _handle('ustaw eq 1200 POTWIERDZAM'))
            check(caps.cap('eq')==1200)
            check(infinite_equipment_requirement(900)==800) # mastery still 800
            check(infinite_equipment_requirement(1200)==800)
            check('wymagana bieglosc 800' in _handle('eq prognoza krypta 901'))
            check('ZAPISANO' in _handle('ustaw bieglosc 2000 POTWIERDZAM'))
            for stage,required in ((600,600),(610,610),(800,800),(900,900),(1200,1200),(2000,1200)):
                check(infinite_equipment_requirement(stage)==required,str(stage))
            check('wymagana bieglosc 910' in _handle('eq prognoza krypta 901'))
            check('etap ponad limitem EQ' in _handle('eq prognoza krypta 2001'))
            check('wymagana bieglosc 1200' in _handle('eq prognoza krypta 2001'))
            check('ZAPISANO' in _handle('ustaw eq bezlimitu POTWIERDZAM'))
            check(infinite_equipment_requirement(2100)==2000)
            check('ZAPISANO' in _handle('ustaw bieglosc bezlimitu POTWIERDZAM'))
            check(infinite_equipment_requirement(2100)==2100)
            check(infinite_equipment_requirement(10**15)==caps.TECHNICAL_CEILING)
            profile=deep.infinite_source_profile({'crypt_floor':901})
            check(profile['effective_stage']==910)
            check(profile['rank']>0)
            check(deep.infinite_equipment_power_multiplier(100)>deep.infinite_equipment_power_multiplier(1))
            check(deep.infinite_equipment_audit_v11330()['error_count']==0)
            base=next(k for k,v in ITEMS.items() if isinstance(v,dict) and v.get('type') in ('armor','weapon','equipment'))
            original_keys=set(ITEMS)
            variant=deep.infinite_equipment_variant_id(base,'crypt','b',40)
            check(variant not in original_keys)
            made=deep.register_infinite_equipment_variant(base,'crypt','b',40,variant_id=variant)
            check(made==variant)
            created.append(variant)
            check(ITEMS[variant]['required_mastery']==1000)
            check(ITEMS[variant]['source_progression_stage']==1000)
            check(ITEMS[variant]['infinite_depth_variant'] is True)
            check(ITEMS[variant]['infinite_depth_base_item_id']==base)
            check(ITEMS[variant]['price']==ITEMS[base].get('price'))
            check(ITEMS[variant]['name']!=ITEMS[base].get('name'))
            check('ZAPISANO' in _handle('ustaw eq 800 POTWIERDZAM'))
            check(ITEMS[variant]['required_mastery']==600)
            check('ZAPISANO' in _handle('ustaw eq 2000 POTWIERDZAM'))
            check(ITEMS[variant]['required_mastery']==1000)
            check(ITEMS[base].get('required_mastery')==ITEMS[base].get('required_mastery'))
            check(deep.register_infinite_equipment_variant(base,'crypt','b',40,variant_id=variant)==variant)
            check(deep.ensure_infinite_equipment_variant(variant) is ITEMS[variant])
            check(deep.refresh_infinite_equipment_requirements_v5300()>=1)
            check('ZAPISANO' in _handle('ustaw bieglosc 800 POTWIERDZAM'))
            check(ITEMS[variant]['required_mastery']==800)
            check('ZAPISANO' in _handle('ustaw bieglosc 2000 POTWIERDZAM'))
            check(ITEMS[variant]['required_mastery']==1000)
            check('Wymaganie' in ITEMS[variant]['desc'])
            check(stage_report(2000)['required_mastery']==2000)
            check(stage_report(2001)['required_mastery']==2000)
            for src in ('krypta','mit_krypta','wieza','mit_wieza','magitek'):
                value=_handle('eq prognoza '+src+' 900')
                check(value.startswith('EQ PROGNOZA:') and 'bez zmian w grze' in value,src)
            for bad in ('eq prognoza krypta 0','eq prognoza brak 1000','eq prognoza krypta xyz',
                        'eq prognoza krypta 999999999999','progi 100001','progi foo'):
                try:_handle(bad)
                except ValueError:check(True)
                else:check(False,'bad accepted '+bad)
            check('postac ' in _handle('progi 800'))
            check('skille ' in _handle('progi 800'))
            check('postac ' in _handle('progi 801'))
            snapshot=caps.current()
            filedata=caps.CAP_FILE.read_bytes()
            _handle('audyt')
            _handle('eq prognoza krypta 10000')
            _handle('progi 900')
            check(caps.current()==snapshot)
            check(caps.CAP_FILE.read_bytes()==filedata)
            check(set(ITEMS)==original_keys|{variant})
            check(json.loads(filedata)['caps']['eq']==2000)
            class Session:
                def __init__(self,admin):self.admin=admin;self.out=[]
                def is_admin(self):return self.admin
                async def send(self,msg):self.out.append(msg)
            guest=Session(False)
            asyncio.run(dispatch_v52_caps(guest,'eq prognoza krypta 900'))
            check(guest.out[0].startswith('Nieznana komenda'))
            owner=Session(True)
            asyncio.run(dispatch_v52_caps(owner,'eq prognoza krypta 900'))
            check('EQ PROGNOZA' in owner.out[0])
            check('ZAPISANO' in _handle('reset wszystko POTWIERDZAM') or caps.current()==caps.DEFAULTS)
            check(infinite_equipment_requirement(1000)==600)
            check(ITEMS[variant]['required_mastery']==600)
            check(not any(key.endswith(('.db','.sqlite','.db-wal','.db-shm')) for key in ITEMS))
        finally:
            for ident in created:ITEMS.pop(ident,None)
            caps.CAP_FILE=oldpath
            caps._state.update(oldstate)
            caps._loaded=oldloaded
            caps._apply_to_runtime()
    print(f'v53 eq/progression/admin: {n} PASS')
    return n
if __name__=='__main__':run()
