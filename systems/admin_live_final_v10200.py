# -*- coding: utf-8 -*-
"""v102: safe local native-arena bridge, expanded declarative rules and truth audit."""
from __future__ import annotations
from systems.admin_live_bridge_v10200 import HELP as BRIDGE_HELP, connect, disconnect
from systems.admin_live_audit_v10200 import report

HELP=(
 'ADMIN LIVE POMOC 74: '+BRIDGE_HELP.split(': ',1)[1]+' '
 'POMOC 75: mechaniki v102 - dotychczasowe admin live mechaniki plan BOSS | JSON '
 'obsluguja teraz nowy efekt restore_health (leczy wybranych graczy), oraz opcjonalny '
 'conditions: {"target_hp_below":60,"target_mana_below":40,"min_party":2}. '
 'Progi procentowe 1..100, min_party 1..20; warunki stosowane do celow '
 'przed efektami. Plan, zatwierdz do DRAFT, sprawdz i aktywuj POTWIERDZAM. '
 'Mechaniki sa deklaratywne i bez dowolnego Pythona. '
 'POMOC 76: audyt raport / audyt komendy / audyt olc / audyt arena. '
 'Audyt tylko czyta; raport nie oznacza pelnego certyfikatu produkcji.')


async def dispatch_v10200(session,cmd,tail):
    raw=str(tail or '').strip();parts=raw.split()
    relevant=(cmd=='pomoc' and raw in ('74','75','76') or
              cmd=='arena' and parts[:2]==['real','tunel'] or
              cmd=='audyt')
    if not relevant:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if cmd=='pomoc':out=HELP
        elif cmd=='arena':
            if parts==['real','tunel','POTWIERDZAM']:
                out=await connect(session)
            elif parts==['real','tunel','status']:
                out=('ARENA REAL TUNEL: AKTYWNY' if getattr(session,'_v102_tunnel',None) is not None else 'ARENA REAL TUNEL: WYLACZONY')
            else:raise ValueError('arena real tunel POTWIERDZAM / status. Pomoc 74.')
        else:
            if len(parts)>1:raise ValueError('audyt raport/komendy/olc/arena')
            out=report(session,parts[0] if parts else 'raport')
            if not parts:
                # Historical 'admin live audyt' is read-only OLC5 validation.
                # Preserve the explicit draft verdict alongside the v102 audit.
                from systems.live_olc5_audit import live_audit_summary
                out += ' | ' + live_audit_summary(session.server.live_content_v1204)
    except (ValueError,OSError,TypeError,AttributeError,RuntimeError,OverflowError) as exc:
        out='ADMIN LIVE v102: '+str(exc)[:360]
    await session.send(out)
    return True
