"""Authored exploration targets exposed to player progress and maps.

The world builder also refreshes a live spatial index for newly installed
rooms. Authored progress targets retain their finalized bootstrap identity;
refreshing the spatial index must not replace already imported progress data.
"""
TRACKED_EXPLORATION_ZONES = {}
ALL_EXPLORATION_ROOMS = ()

def install_authored_catalog(tracked, all_rooms):
    global ALL_EXPLORATION_ROOMS
    TRACKED_EXPLORATION_ZONES.clear()
    TRACKED_EXPLORATION_ZONES.update(tracked)
    ALL_EXPLORATION_ROOMS = tuple(all_rooms)
