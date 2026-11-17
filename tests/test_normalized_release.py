import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from normalized_pack import pack,unpack
from release_plan import plan,SOURCES
from stage_source import belongs

class NormalizedReleaseTests(unittest.TestCase):
    def test_pack_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"root";root.mkdir()
            (root/"a.json.gz").write_bytes(b"test-data")
            (root/"b.json").write_bytes(b"index-data")
            out=Path(tmp)/"packs";dest=Path(tmp)/"dest"
            doc=pack(root,"omw",out)
            unpack(out,doc,dest)
            self.assertEqual((dest/"a.json.gz").read_bytes(),b"test-data")
            self.assertEqual(set(doc["members"]),{"a.json.gz","b.json"})
    def test_any_source_retention_does_not_block_other_updates(self):
        for source in SOURCES:
            with self.subTest(source=source):
                updated="wikdict" if source!="wikdict" else "freedict"
                name=updated+"--en-ru.zip"
                old={name:{"digest":"sha256:old"},"PAIR-INDEX.json":{}}
                new={name:{"digest":"sha256:new"}}
                report=plan(old,new,[name],{source:{"source":source,"retained":True,"reason":"unavailable","previous_release":"v1"}},"v2","v1")
                self.assertTrue(report["publish"])
                self.assertEqual(report["sources"][source]["status"],"retained")
                self.assertEqual(report["sources"][updated]["status"],"updated")
    def test_no_changes_no_release_after_bootstrap(self):
        self.assertFalse(plan({"PAIR-INDEX.json":{}},{},[],{},"v2","v1")["publish"])
        self.assertTrue(plan({}, {}, [], {}, "v2","v1")["publish"])
    def test_source_isolation(self):
        self.assertTrue(belongs("lexicon--oewn-en.json.gz","oewn"))
        self.assertFalse(belongs("omw--omw-en-2.0.tar.xz","oewn"))
