# -*- coding: utf-8 -*-
"""v108 offline EQ history classification; aggregates only, never selects a copy.

The v105 legacy evolution record describes a template, not a physical item.
There is no defensible way to infer which of several indistinguishable
historical pieces was upgraded. Report the cases instead of guessing.
"""
from __future__ import annotations

from systems.equipment_instances_v10600 import snapshot, _manual_row


_FIELDS = (
    'legacy_verified_single', 'legacy_verified_plain_duplicates',
    'legacy_manual_verified', 'legacy_evolved_duplicates_review',
    'legacy_orphan_evolution_review', 'legacy_zero_quantity_review',
    'legacy_stale_manual_review', 'legacy_other_review',
)


def reconciliation_summary(conn, catalog, *, rows=None):
    """Count unresolved physical identities without returning private row data.

    `rows` is a pre-migration read-only snapshot. A manual review record does
    not resolve a conflict unless a matching, exact physical ledger is present.
    """
    if rows is None:
        rows = snapshot(conn, catalog)
    summary = dict.fromkeys(_FIELDS, 0)
    for row in rows:
        account, item = row['account_id'], row['item_id']
        qty, stage, status = row['quantity'], row['legacy_stage'], row['status']
        if status == 'verified_manual':
            key = 'legacy_manual_verified'
        elif status == 'verified':
            key = ('legacy_verified_plain_duplicates' if qty > 1 else
                   'legacy_verified_single')
        elif _manual_row(conn, account, item) is not None:
            key = 'legacy_stale_manual_review'
        elif qty == 0 and stage > 0:
            key = 'legacy_orphan_evolution_review'
        elif qty == 0:
            key = 'legacy_zero_quantity_review'
        elif qty > 1 and stage > 0:
            key = 'legacy_evolved_duplicates_review'
        else:
            key = 'legacy_other_review'
        summary[key] += 1
    summary['legacy_review_total'] = sum(value for name, value in summary.items()
                                         if name.endswith('_review'))
    summary['legacy_groups_scanned'] = len(rows)
    assert sum(summary[field] for field in _FIELDS) == len(rows)
    summary['automatic_ordinal_selection'] = False
    summary['production_approved'] = False
    return summary
