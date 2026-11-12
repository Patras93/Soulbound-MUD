# -*- coding: utf-8 -*-
"""Izolowany most v111: potwierdzone zwyciestwo -> dziennik wyzwan.

Aktywny tylko w izolowanej kopii testowej. Po zatwierdzonym zabiciu
nalicza wyzwania i automatycznie wydaje gotowe nagrody, bez komend odbioru.
"""
from __future__ import annotations
from uuid import uuid4

from systems.runtime_activation import enabled
from systems.holiday.challenges import record_kill
from systems.holiday.prizes import claim


def on_confirmed_kill(db, mob, recipients, *, day=None):
    """Zapisz osiagniecia dopiero po zatwierdzeniu standardowej walki.

    Każde konto nadrzędne dostaje jeden zapis na rzeczywistą śmierć moba.
    Błąd dodatku jest raportowany wywołującemu, który musi go odizolować.
    """
    if not enabled() or mob is None:
        return ()
    template_id = getattr(mob, 'template_id', None)
    if not isinstance(template_id, str) or not template_id.startswith('v11100_holiday_'):
        return ()
    # Repeated callbacks of one death share an ID; respawn_at changes on
    # the next genuine death, even if the same MobState instance is reused.
    death_key = getattr(mob, 'respawn_at', None)
    if death_key != getattr(mob, 'v111_holiday_death_key', object()):
        mob.v111_holiday_fight_id = uuid4().hex
        mob.v111_holiday_death_key = death_key
    fight_id = mob.v111_holiday_fight_id
    conn = db.conn
    if conn.in_transaction:
        raise RuntimeError('Holiday credit requires confirmed committed kill')
    winners = {}
    for session in recipients:
        account = getattr(session, 'account_id', None)
        if type(account) is not int or account <= 0:
            continue
        master = int(db.master_account_for_character(account))
        if master > 0:
            # Do wypłaty wymagamy prawdziwej sesji z postacią; nie
            # zastępujemy jej sesją bez postaci z tego samego konta.
            if getattr(session, 'character', None) is not None and not getattr(session, 'closed', False):
                winners.setdefault(master, session)
    if not winners:
        return ()
    credited = []
    # The same DB abstraction as existing v109 daily gifts; never await here.
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v111_holiday_combat')
        try:
            for master in sorted(winners):
                state = record_kill(conn, master, template_id, fight_id, day=day)
                if state['credited']:
                    credited.append(master)
            conn.execute('RELEASE SAVEPOINT v111_holiday_combat')
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT v111_holiday_combat')
            conn.execute('RELEASE SAVEPOINT v111_holiday_combat')
            raise
    # Ukończone próby wypłacamy bez poleceń gracza, PO zapisaniu postępu.
    # Awaria pojedynczego przelewu nie cofa postępu ani zwykłej walki.
    # Niewypłacona nagroda pozostaje do ponownej próby przy kolejnej walce.
    # Również przy powtórnym callbacku można bezpiecznie ponowić nieudaną
    # wypłatę: klucz (konto, typ, okres) gwarantuje jednorazowość.
    for master in sorted(winners):
        session = winners[master]
        for kind, description in (('D', 'dzienna'), ('W', 'tygodniowa')):
            try:
                result = claim(session, kind, day=day)
                if result is None:
                    continue
                message = (f'SWIETA: automatyczna nagroda {description}: '
                           f'{result["silver"]} srebra i {result["exp"]} EXP.')
                messages = getattr(session, 'v111_holiday_auto_prize_messages', None)
                if messages is None:
                    messages = []
                    session.v111_holiday_auto_prize_messages = messages
                messages.append(message)
            except Exception as exc:
                print(f'V111_HOLIDAY_AUTO_PRIZE_ERROR: {type(exc).__name__}: {exc}', flush=True)
    return tuple(credited)
