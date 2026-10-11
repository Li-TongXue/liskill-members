from pathlib import Path
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import check_skills


class DefinitionTests(unittest.TestCase):
    def test_all_skill_contracts(self):
        self.assertEqual(check_skills.check(),[])

    def test_legacy_fixture_matches_recorded_official_hash(self):
        import hashlib
        manifest=json.loads((ROOT/'skills/li-update/references/legacy-installations.json').read_text())
        entry=next(e for e in manifest['skills'] if e['name']=='li')
        actual=hashlib.sha256((ROOT/'tests/fixtures/legacy/li.SKILL.txt').read_bytes()).hexdigest()
        self.assertEqual(actual,entry['files']['SKILL.md'])


if __name__=='__main__':unittest.main()
