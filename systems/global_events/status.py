# -*- coding: utf-8 -*-
"""Tylko odczyt statusu, w tym przed uruchomieniem pierwszego wydarzenia."""
import time
from .clock import rotation,REQUIRED_KILLS

def status(conn,now=None):
    current=rotation(time.time() if now is None else now)
    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v110_event_progress'").fetchone()
    row=conn.execute('SELECT kills,completed_at FROM v110_event_progress WHERE slot=?',
            (current['slot'],)).fetchone() if exists else None
    return {**current,'kills':int(row[0]) if row else 0,
            'completed':bool(row and int(row[1])>0)}

def text_status(conn,now=None):
    now=time.time() if now is None else now
    result=status(conn,now)
    remaining=max(0,int(result['expires_at']-now))
    label='ukończone' if result['completed'] else 'aktywne'
    return (f'WYDARZENIA GLOBALNE V110: {result["title"]}, {label}. '
            f'Kraina: {result["region"]}. Pokonane cele: {result["kills"]}/{REQUIRED_KILLS}. '
            f'Finałowy boss: {result["boss"]}. Rotacja za {(remaining+59)//60} minut.')
