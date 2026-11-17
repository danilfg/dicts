import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from release_changes import diff_plan, zip_fingerprint

def item(value):
    return {"digest": "sha256:" + value}

class ReleaseChangesTests(unittest.TestCase):
    def test_generated_metadata_ignored(self):
        a = {"freedict--en-ru.zip": item("1"), "manifest.json": item("old"),
             "dicts-part-001.zip": item("old"), "enrichment--en-ru.json.gz": item("old")}
        b = dict(a, **{"manifest.json": item("new"), "dicts-part-001.zip": item("new"),
                       "enrichment--en-ru.json.gz": item("new")})
        self.assertEqual(diff_plan(a,b), ([], []))

    def test_one_changed_raw_source(self):
        a = {"tatoeba--sentences.part001": item("1")}
        b = {"tatoeba--sentences.part001": item("2")}
        self.assertEqual(diff_plan(a,b), (["tatoeba--sentences.part001"], []))

    def test_added_and_removed_dictionary(self):
        self.assertEqual(diff_plan({"wikdict--en-de.zip": item("1")},
                                   {"wikdict--en-ru.zip": item("1")}),
                         (["wikdict--en-de.zip", "wikdict--en-ru.zip"], []))

    def test_zip_timestamp_order_and_payload(self):
        name = "freedict--en-ru.zip"
        self.assertEqual(diff_plan({name:item("1")},{name:item("2")}), ([],[name]))
        with tempfile.TemporaryDirectory() as tmp:
            a,b,c = (Path(tmp)/n for n in ("a.zip","b.zip","c.zip"))
            for path, year, rows in [
                (a, 1980, [("word","definition"),("LICENSE","CC")]),
                (b, 2020, [("LICENSE","CC"),("word","definition")]),
                (c, 2020, [("word","new definition"),("LICENSE","CC")]),
            ]:
                with zipfile.ZipFile(path,"w") as z:
                    for member, value in rows:
                        z.writestr(zipfile.ZipInfo(member,(year,1,1,0,0,0)), value)
            self.assertEqual(zip_fingerprint(a),zip_fingerprint(b))
            self.assertNotEqual(zip_fingerprint(a),zip_fingerprint(c))
