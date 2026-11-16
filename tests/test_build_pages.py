import gzip,io,json,struct,tempfile,unittest,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import build_pages as p

class TestPages(unittest.TestCase):
    def test_parse_complete_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"koreader--en-ru.zip"
            text=b"Long meaning A; long meaning B"
            idx=b"thoughtful\0"+struct.pack(">II",0,len(text))
            with zipfile.ZipFile(file,"w") as z:
                z.writestr("dictionary.idx",idx)
                z.writestr("dictionary.dict.dz",gzip.compress(text))
                z.writestr("dictionary.ifo","idxoffsetbits=32\n")
            self.assertEqual(list(p.extract_stardict(file)),
                [("thoughtful","Long meaning A; long meaning B")])
    def test_unicode_normalization_and_bucket(self):
        self.assertEqual(p.normalize("  СЛОВО  "),"слово")
        self.assertEqual(p.bucket("test",16),p.bucket("test",16))
    def test_separate_sources_and_meanings(self):
        data={"schema":1,"words":{"HELLO":{"translations":[
            {"source":"freedict","text":"sample short"}],"meanings":[
            {"source":"kaikki","text":"greeting","source_url":"https://example.org"}],
            "examples":[{"source":"tatoeba","text":"Hello world.","translation":"Привет, мир."}]}}}
        records={"hello":{"translations":{"freedict":["Full FreeDict definition"]},
                 "meanings":[],"examples":[]}}
        p.enrich_records(records,data)
        self.assertEqual(records["hello"]["translations"]["freedict"],["Full FreeDict definition"])
        self.assertEqual(records["hello"]["meanings"][0]["source"],"kaikki")
        self.assertEqual(records["hello"]["examples"][0]["source"],"tatoeba")
    def test_gzip_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"a.json.gz"
            p.write_gzip(output,{"words":{"hello":"привет"}})
            with gzip.open(output,"rt") as stream:
                self.assertEqual(json.load(stream)["words"]["hello"],"привет")

if __name__=="__main__":unittest.main()
