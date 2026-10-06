"""Shared Soulbound economy curve for authored and procedural systems.

One 1-600 stage anchor is the common point of reference. Procedural lanes use
explicit shares calibrated to the previous Generator Core values at the same
stage anchors, so architecture can be unified without surprise inflation.
"""
from __future__ import annotations

import math

ECONOMY_MAX_STAGE = 600

ECONOMY_STAGE_ANCHORS = (
    (1, 1_200), (50, 15_000), (100, 100_000), (150, 350_000),
    (200, 1_250_000), (250, 3_500_000), (300, 7_500_000),
    (350, 15_000_000), (400, 30_000_000), (500, 60_000_000),
    (600, 100_000_000),
)

# Shares of the same full-activity economy anchor. These are compatibility
# lanes, not a second independent economy curve.
ECONOMY_LANE_SHARE_ANCHORS = {
    "mob_currency": (
        (1, 0.0075000000), (50, 0.0281333333), (100, 0.0160900000),
        (150, 0.0104657143), (200, 0.0053192000), (250, 0.0030322857),
        (300, 0.0020792000), (350, 0.0014416667), (400, 0.0009578333),
        (500, 0.0007715167), (600, 0.0006844100),
    ),
    "item_price": (
        (1, 0.0191666667), (50, 0.0696666667), (100, 0.0373600000),
        (150, 0.0232885714), (200, 0.0114568000), (250, 0.0063634286),
        (300, 0.0042697333), (350, 0.0029060667), (400, 0.0018996333),
        (500, 0.0014887000), (600, 0.0012910400),
    ),
    "resource_sale": (
        (1, 0.0033333333), (50, 0.0066000000), (100, 0.0032200000),
        (150, 0.0019114286), (200, 0.0009088000), (250, 0.0004922857),
        (300, 0.0003237333), (350, 0.0002166667), (400, 0.0001396000),
        (500, 0.0001068333), (600, 0.0000908900),
    ),
}


def _clamp_stage(stage: int) -> int:
    return max(1, min(ECONOMY_MAX_STAGE, int(stage or 1)))


def _log_interpolate(stage: int, anchors) -> float:
    stage = _clamp_stage(stage)
    if stage <= anchors[0][0]:
        return float(anchors[0][1])
    if stage >= anchors[-1][0]:
        return float(anchors[-1][1])
    for (l0, v0), (l1, v1) in zip(anchors, anchors[1:]):
        if l0 <= stage <= l1:
            ratio = (stage - l0) / float(l1 - l0)
            return math.exp(
                math.log(max(1e-12, float(v0)))
                + (
                    math.log(max(1e-12, float(v1)))
                    - math.log(max(1e-12, float(v0)))
                )
                * ratio
            )
    return float(anchors[-1][1])


def economy_stage_anchor(stage: int) -> int:
    """Full-activity internal-silver value for economy stage 1-600."""
    return max(1, int(round(_log_interpolate(stage, ECONOMY_STAGE_ANCHORS))))


def economy_lane_share(stage: int, lane: str) -> float:
    anchors = ECONOMY_LANE_SHARE_ANCHORS[str(lane)]
    return max(0.0, float(_log_interpolate(stage, anchors)))


def economy_lane_amount(stage: int, lane: str, multiplier: float = 1.0) -> int:
    value = (
        economy_stage_anchor(stage)
        * economy_lane_share(stage, lane)
        * max(0.0, float(multiplier))
    )
    return max(1, int(round(value)))


# Compatibility exports used by v1.13.14 callers.
V11314_ECONOMY_STAGE_ANCHORS = ECONOMY_STAGE_ANCHORS


def economy_stage_anchor_v11314(stage: int) -> int:
    return economy_stage_anchor(stage)


# Anchor-preservation audit: procedural cleanup must not silently rebalance.
_EXPECTED_LANES = {
    1: {"mob_currency": 9, "item_price": 23, "resource_sale": 4},
    100: {"mob_currency": 1609, "item_price": 3736, "resource_sale": 322},
    200: {"mob_currency": 6649, "item_price": 14321, "resource_sale": 1136},
    400: {"mob_currency": 28735, "item_price": 56989, "resource_sale": 4188},
    600: {"mob_currency": 68441, "item_price": 129104, "resource_sale": 9089},
}
for _stage, _lanes in _EXPECTED_LANES.items():
    for _lane, _expected in _lanes.items():
        _actual = economy_lane_amount(_stage, _lane)
        if abs(_actual - _expected) > 1:
            raise RuntimeError(
                f"Economy lane audit failed: {_lane} stage {_stage}: "
                f"{_actual} != {_expected}"
            )
