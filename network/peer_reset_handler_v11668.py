# -*- coding: utf-8 -*-
"""Narrow, privacy-safe reporting for expected Windows TCP peer resets.

Only the transport's already-failed socket cleanup callback is filtered.
Application exceptions, Windows errors other than 10054, and other asyncio
callbacks continue to the existing/default exception handler.
"""

def is_peer_reset_cleanup(context):
    exc = context.get('exception')
    if not isinstance(exc, ConnectionResetError) or (
            getattr(exc, 'winerror', None) != 10054
            and getattr(exc, 'errno', None) != 10054):
        return False
    callback = getattr(context.get('handle'), '_callback', None)
    return (getattr(callback, '__name__', '') == '_call_connection_lost'
            and type(getattr(callback, '__self__', None)).__module__.startswith('asyncio.'))


def install_peer_reset_handler(loop):
    if getattr(loop, '_soulbound_peer_reset_v11668', False):
        return
    previous = loop.get_exception_handler()

    def on_exception(event_loop, context):
        if is_peer_reset_cleanup(context):
            print('[TCP] Klient gwałtownie przerwał połączenie (WinError 10054); '
                  'serwer działa dalej.', flush=True)
            return
        if previous is not None:
            previous(event_loop, context)
        else:
            event_loop.default_exception_handler(context)

    loop.set_exception_handler(on_exception)
    loop._soulbound_peer_reset_v11668 = True
