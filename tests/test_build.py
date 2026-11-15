import gzip
import hashlib
import io
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import build

class BuildTests(unittest.TestCase):
    def test_license_registry(self):
        self.assertEqual({x for x in ("koreader","freedict","wikdict","kaikki","tatoeba") if x not in build.LEGAL},set())
    def test_stardict_parse(self):
        raw={"demo.idx":b"hello\0"+struct.pack(">II",0,6),"demo.dict.dz":gzip.compress(b"world!")}
        self.assertEqual(build.extract_glossary(raw),{"hello":"world!"})
    def test_packaging_retains_notices(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"test.zip"
            build.package_zip(dest,{"demo.idx":b"123"},"CC-BY-SA-4.0","Original contributor")
            with zipfile.ZipFile(dest) as z:
                self.assertIn("ATTRIBUTION.txt",z.namelist())
                self.assertIn("LICENSE-SOURCE.txt",z.namelist())
    def test_manifest_requires_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"test.json"
            file.write_text("test")
            with self.assertRaises(ValueError):
                build.record(file,"koreader","en-ru","https://example.org","",attribution="")

if __name__=="__main__":unittest.main()
