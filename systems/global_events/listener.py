# -*- coding: utf-8 -*-
"""Opcjonalna subskrypcja istniejącego MobDefeatedEvent; nie dotyka walki."""
from .combat import record_defeat

def on_defeat(event):
    session=getattr(event,'killer_session',None)
    server=getattr(session,'server',None)
    if server is None or getattr(server,'db',None) is None:return None
    result=record_defeat(server.db,event.mob,event.template,event.recipients)
    if result:print('V110_EVENT: '+str(result),flush=True)
    return result
