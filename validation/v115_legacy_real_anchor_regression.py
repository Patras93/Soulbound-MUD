"""v115: check original map anchor identifiers from the canonical authoring source."""
import ast
import pathlib
import unittest
from systems.v115.legacy_expareas import AREAS, expand
ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'world/expansion_frontier_fields_v407.py'

class RealAnchors(unittest.TestCase):
    def test_identifiers_in_actual_world_builder(self):
        code = SOURCE.read_text(encoding='utf-8')
        values = {n.value for n in ast.walk(ast.parse(code)) if isinstance(n, ast.Constant) and isinstance(n.value,str)}
        for key, name, anchor, enemies, level in AREAS:
            self.assertIn(anchor, values, msg=(key,anchor))
            for mob in enemies:
                self.assertIn(mob, values, msg=(key,mob))
    def test_missing_anchor_fails_without_mutation(self):
        rooms={anchor:{'exits':{}} for _,_,anchor,_,_ in AREAS[:-1]}
        mobs={mob:{} for _,_,_,enemies,_ in AREAS for mob in enemies}
        before=len(rooms)
        with self.assertRaises(ValueError):
            expand(rooms,mobs,[])
        self.assertEqual(len(rooms), before)
    def test_existing_graveyard_not_duplicated(self):
        self.assertNotIn('cmentarz',[area[0] for area in AREAS])
if __name__=='__main__': unittest.main()
