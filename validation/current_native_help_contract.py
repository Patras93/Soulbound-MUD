# -*- coding: utf-8 -*-
"""Reviewed direct authoring of HELP methods retained from the v112 baseline.

The method bodies were byte-equal in the supplied v112 and v113 packages.
A new edit requires review and deliberate re-pinning; never silently accept it.
"""
from pathlib import Path
import ast
from hashlib import sha256

EXPECTED = {'aggro_cleanup_audit_v03015': 'c2f18def32dd39ada5105cb801277a5c09a7928259cfe1734be69a9c2d041d9a', 'apply_equipment_name_pass_v03016': 'f12390cf06e014b0e0ab77ec0017a8ea7623b2732790466d07a84fddf5d44a0a', 'equipment_name_audit_v03016': 'c212bfed040e76efb050a8a911773b3968694b69ace9db92bb66b076c3d55f0c', 'full_combat_scaling_audit_v03015': '20768ffcf4b3d1eb5e954d2be4be24e088a9c21f1b1700f2fc49d2b3af38ea97', 'full_game_audit_v03014': 'cb377709c661f7e6beeb7a57219b671924ea89a0116d0988208590bcd7063489', 'help_surface_audit_v11197': 'b7f769c80c7bfd2b94cc5f7f370f204f3ef4b9caa18a241966a2e22a0762452c', 'help_truth_audit_v11197': '5b5b9e61e57e330d005691cfff53582e1cc8692dbafd7f2bd2ad0d8e9b998e49', 'progression_combat_audit_v03017': 'c4acd4fc32cf2e76de59378552378393f8c5c049320442f78d387cdb43a87b34', 'refresh_generator_help_v0271': '443aa9658fba71ac8c149d9e0e76daac976599ff43fc4fd443f55899e022fa57', 'refresh_help_truth_v11197': 'b7ca93265170a0a41125ab2358939d096cd7d694fc062d14148842491e796d28', 'refresh_help_v03010': '3871f4391d9b1fcfefd281e5f9842d8ecc8f7ce3f01e848cd347e575a7cf58cf', 'refresh_help_v03011': 'b7b05fa7a4af0ae0e341ec0df39135da59b19d9702c2cf96114159d3c43cc05e', 'refresh_public_help_surface_v11197': 'dd282b67e90a663f117b320370bd9a95f675aee5c783942a7ca41c126e7e69e4'}

def verify_direct_help(source):
    tree=ast.parse(source)
    bodies={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    for name, expected in EXPECTED.items():
        body=bodies.get(name)
        if body is None or sha256(ast.dump(body,include_attributes=False).encode()).hexdigest()!=expected:
            raise AssertionError(('changed direct HELP implementation',name))
    return len(EXPECTED)
