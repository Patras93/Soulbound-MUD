"""Explicit two-phase HELP ownership: authored bootstrap, then live protocol.

Early authored equipment helpers retain their bootstrap catalogue. Consumers
that request current HELP get the live catalogue after protocol initialization.
No module dictionaries or arbitrary names are synchronized.
"""
from data.help_base_catalog_v405 import make_help_topics_v405, make_help_topic_aliases_v405
_topics = make_help_topics_v405()
_aliases = make_help_topic_aliases_v405()
_live = False

def get_help_catalogs():
    return _topics, _aliases

def begin_live_help():
    global _topics, _aliases, _live
    if _live:
        raise RuntimeError('Live HELP was already initialized')
    _topics = make_help_topics_v405()
    _aliases = make_help_topic_aliases_v405()
    _live = True
    return _topics, _aliases
