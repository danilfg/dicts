import gzip
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from build_pages import bucket,write_gzip
from normalized_pack import write_json
from pair_pack import pack_application,build_pair_index,split_record

class PairPackTests(unittest.TestCase):
    def test_target_filter(self):
        for group,field in (("kaikki","translations"),("conceptnet","relations")):
            local,links=split_record(group,"en",{field:[{"language":"en"},{"language":"ru"},{"language":"de"}],"definitions":["test"]})
            self.assertEqual(local[field],[{"language":"en"}])
            self.assertEqual(links["ru"][field],[{"language":"ru"}])
            self.assertEqual(links["de"][field],[{"language":"de"}])
        local,links=split_record("tatoeba","en",{"examples":[{"language":"en","text":"Hi","translations":[{"language":"ru"},{"language":"de"}]}]})
        self.assertEqual(local["examples"][0]["translations"],[])
        self.assertEqual(links["ru"]["examples"][0]["translations"],[{"language":"ru"}])

    def test_ranges_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"root";out=Path(tmp)/"out"
            root.mkdir();out.mkdir()
            pairs=[]
            for lang in ("ru","de"):
                pair="en-"+lang
                path=root/"data"/pair/"00.json.gz"
                write_gzip(path,{"schema":1,"pair":pair,"words":{"car":{"translations":{"koreader":[lang]}}}})
                pairs.append({"pair":pair,"from":"en","to":lang,"buckets":1,"sources":[{"id":"koreader"}]})
            write_json(root/"data/catalog.json",{"pairs":pairs,"provenance":{}})
            doc=pack_application(root,"bilingual",out)
            lex=Path(tmp)/"lex";lex.mkdir()
            path="data/lexical/kaikki/en/edition"
            write_gzip(lex/path/"00.json.gz",{"schema":1,"source":"kaikki","language":"en","words":{"car":{"definitions":["vehicle"],"translations":[{"text":"машина","language":"ru"},{"text":"Auto","language":"de"}]}}})
            write_json(lex/"data/lexical/kaikki/catalog.json",{"languages":[{"language":"en","package":"edition","path":path,"buckets":1}]})
            kdoc=pack_application(lex,"kaikki",out)
            index=build_pair_index("v1",{"bilingual":doc,"kaikki":kdoc},"https://example.com/")
            def records(group,scope,key):
                result={}
                for r in index["groups"][group][scope][key]:
                    with (out/r["asset"]).open("rb") as stream:
                        stream.seek(r["offset"]);data=stream.read(r["bytes"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(),r["sha256"])
                    with zipfile.ZipFile(io.BytesIO(data)) as z:
                        for name in z.namelist():
                            if name.endswith(".gz"):result[name]=json.loads(gzip.decompress(z.read(name)))
                return result
            r=records("bilingual","pairs","en-ru")
            self.assertEqual(set(r),{"data/en-ru/00.json.gz"})
            self.assertEqual(r["data/en-ru/00.json.gz"]["words"]["car"]["translations"]["koreader"],["ru"])
            r=records("kaikki","pairs","en-ru")
            value=next(iter(r.values()))["words"]["car"][0]["record"]
            self.assertEqual(value["translations"],[{"text":"машина","language":"ru"}])
            r=records("kaikki","languages","en")
            self.assertEqual(next(iter(r.values()))["words"]["car"]["translations"],[])
