# -*- coding: utf-8 -*-
from datetime import date
from systems.holiday.events import festival,holiday_reward,calendar_text
from systems.v11100_holiday_activation import enabled

def check():
    from systems.v11100_holiday_activation import production_approved
    assert not production_approved(), 'Nie wolno uruchomić produkcji bez manifestu'
    # W PREDEPLOY aktywacja na odizolowanej bazie jest celowa.
    # Sama flaga nie zatwierdza jednak prawdziwej instalacji.
    for month in range(1,13):
        day=date(2027,month,15)
        a=festival(day)
        assert a['month']==month and 1.25<=a['bonus']<=2
        mid=f'v11100_holiday_{month:02d}_mob_1'
        assert holiday_reward(mid,100,day)>=125
        assert holiday_reward('v11000_realm_mob_1',100,day)==100
        assert holiday_reward(f'v11100_holiday_{month%12+1:02d}_mob_1',100,day)==100
        assert holiday_reward(mid,100,day,exact=True)==100
        assert holiday_reward(mid,0,day)==0
        assert calendar_text(day).startswith('SWIETA V111:')
    from pathlib import Path
    src=(Path(__file__).resolve().parents[1]/'player/session_mixins/combat_rewards.py').read_text(encoding='utf-8')
    assert src.index("if template.get('v11100'):") < src.index('settle_combat_full_progression_v10400(', src.index("if template.get('v11100'):"))
    assert festival(date(2027,10,31))['bonus']==2
    assert festival(date(2027,12,25))['bonus']==2
    assert festival(date(2027,3,28))['bonus']==2
    assert festival(date(2027,2,4))['bonus']==1.5
    print('V111 HOLIDAY EVENTS REGRESSION PASS: 12 miesięcy, święta ruchome, izolacja XP, brak aktywacji produkcyjnej')
if __name__=='__main__':check()
