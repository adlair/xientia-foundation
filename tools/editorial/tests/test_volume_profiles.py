import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from volume_profiles import VOLUMES, load_profile, validate_profile, validate_numbers

class VolumeProfileTests(unittest.TestCase):
    def test_all_three_profiles(self):
        for volume in VOLUMES:
            with self.subTest(volume=volume):
                p=load_profile(ROOT / "config", volume)
                r=p["validation"]
                self.assertTrue(validate_numbers(p, range(1,r["last"]+1)))

    def test_missing_duplicate_out_of_order(self):
        p=load_profile(ROOT / "config", "XV-001")
        for bad in ([1,2,4], [1,2,2], list(reversed(range(1,16)))):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_numbers(p,bad)

    def test_wrong_volume_rule(self):
        p=load_profile(ROOT / "config", "XV-001")
        p["validation"]["kind"]="article_sequence"
        with self.assertRaisesRegex(ValueError, "incompatible"):
            validate_profile(p,"XV-001")

    def test_bad_editorial_contract(self):
        p=load_profile(ROOT / "config", "XEP-0000")
        p["validation"]["editorial"]["publication_status"]="adopted"
        with self.assertRaisesRegex(ValueError, "editorial"):
            validate_profile(p,"XEP-0000")

    def test_missing_chapter_and_wrong_order(self):
        p=load_profile(ROOT / "config", "XEP-0000")
        p["chapter_files"].pop()
        with self.assertRaises(ValueError): validate_profile(p,"XEP-0000")
        p=load_profile(ROOT / "config", "XEP-0000")
        p["chapter_files"][0],p["chapter_files"][1]=p["chapter_files"][1],p["chapter_files"][0]
        with self.assertRaises(ValueError): validate_profile(p,"XEP-0000")

if __name__ == "__main__":
    unittest.main()
