import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from build_source_directory import directory

class DirectoryTests(unittest.TestCase):
    def test_versions_and_retention(self):
        legal={"families":[{"id":x,"name":x} for x in ("freedict","wikdict","tatoeba","oewn","aggregate")]}
        main={"assets":[{"source":"freedict","name":"freedict--en-ru.zip","pair":"en-ru","version":"1.2"},
                         {"source":"wikdict","name":"wikdict--en-ru.zip","pair":"en-ru","version":"source version: online directory"}]}
        others={"tatoeba":{"created":"2026-10-01T00:00:00Z","sources":[{"original_url":"https://example.com/links.tar.bz2"}]},
                "oewn":{"version":"2025","assets":[{"name":"test","version":"2025"}]}}
        report={"previous_release":"v-old","sources":{"tatoeba":{"status":"retained"}}}
        result=directory("v-new","2026-11-17",legal,main,others,report)
        rows={r["id"]:r for r in result["sources"]}
        self.assertEqual(result["release_tag"],"v-new")
        self.assertNotIn("aggregate",rows)
        self.assertEqual(rows["freedict"]["versions"],["1.2"])
        self.assertEqual(rows["wikdict"]["versions"],[])
        self.assertIsNone(rows["wikdict"]["packages"][0]["version"])
        self.assertEqual(rows["tatoeba"]["snapshot_date"],"2026-10-01T00:00:00Z")
        self.assertEqual(rows["tatoeba"]["status"],"retained")
        self.assertEqual(rows["oewn"]["versions"],["2025"])
