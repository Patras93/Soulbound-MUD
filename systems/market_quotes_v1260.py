# -*- coding: utf-8 -*-
"""Read-only, stable six-hour commodity board, accessible without a GUI."""
import time
from systems.market_dynamics_v1250 import CATEGORIES, market_demand_v1250

LABELS = {'fish': 'Ryby', 'ore': 'Rudy i minerały',
          'wood': 'Drewno', 'herb': 'Zioła'}

def market_quotes_v1260(now=None):
    now = time.time() if now is None else float(now)
    next_slot = ((int(now // 21600)+1)*21600)
    remaining = max(0,int(next_slot-now))
    lines=['RYNEK SOULBOUND: rzeczywisty popyt i ceny skupu. '
           'Notowania aktualizują się co 6 godzin, bez losowania po komendzie.']
    for cat in CATEGORIES:
        factor=market_demand_v1250(cat,now=now)
        direction = 'wysoki popyt' if factor > 1.05 else 'normalny popyt' if factor >= .98 else 'niski popyt'
        lines.append(f'{LABELS[cat]}: {round(factor*100,1)}% ceny podstawowej; {direction}.')
    lines.append(f'Pozostało {remaining//3600} godzin i {(remaining%3600)//60} minut do kolejnych notowań. '
                 'Rzadkie odmiany zachowują swój własny mnożnik wartości.')
    return lines
