import gzip
import json
import tempfile
import unittest
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from build_pages import bucket,write_gzip
from expressions import build,BUCKETS,MAX_PER_KEY,keys_for
from normalized_pack import write_json
from pair_pack import pack_application,build_pair_index

class ExpressionTests(unittest.TestCase):
    def test_index_and_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"source";out=Path(tmp)/"expressions";packs=Path(tmp)/"packs"
            pairs=[]
            for lang in ("ru","de"):
                pair="en-"+lang
                pairs.append({"pair":pair,"from":"en","to":lang,"buckets":1,"sources":[{"id":"freedict"}]})
                words={"entitled to":{"translations":{"freedict":["имеющий право" if lang=="ru" else "berechtigt"]}},
                       "take care of":{"translations":{"freedict":["заботиться" if lang=="ru" else "sich kümmern"]}},
                       "single":{"translations":{"freedict":["one"]}},
                       "go for it":{"meanings":[{"source":"kaikki","text":"Try something.","license":"CC BY-SA 4.0"}]}}
                for i in range(80):words["take sample "+chr(97+i//26)+chr(97+i%26)]={"translations":{"freedict":["test"]}}
                write_gzip(root/"data"/pair/"00.json.gz",{"schema":1,"pair":pair,"words":words})
            write_json(root/"data/catalog.json",{"pairs":pairs,"provenance":{"en-ru":{"freedict":{"license":"GPL","source_url":"https://freedict.org/"}}}})
            build(root,out)
            def lookup(pair,key):
                p=out/"data/links/expressions"/pair/f"{bucket(key,BUCKETS):02x}.json.gz"
                if not p.exists():return []
                with gzip.open(p,"rt") as stream:doc=json.load(stream)
                return doc["words"].get(key,[{"record":{"expressions":[]}}])[0]["record"]["expressions"]
            entries=lookup("en-ru","entitled")
            self.assertTrue(any(x["text"]=="be entitled to + noun" for x in entries))
            self.assertTrue(any(x["text"]=="be entitled to + verb" for x in lookup("en-ru","entitle")))
            self.assertTrue(any(x["source"]=="dicts-curated" for x in entries if x.get("translation")))
            sourced=next(x for x in entries if x["text"]=="entitled to")
            self.assertEqual(sourced["articles"][0]["license"],"GPL")
            self.assertNotIn("translation",sourced)
            self.assertTrue(all(x["kind"]=="expression" for x in lookup("en-de","entitled")))
            self.assertEqual(lookup("en-de","single"),[])
            self.assertLessEqual(len(lookup("en-ru","take")),MAX_PER_KEY)
            self.assertTrue(any(x["text"]=="take care of" for x in lookup("en-ru","take")))
            bilingual=pack_application(root,"bilingual",packs)
            expressions=pack_application(out,"expressions",packs)
            self.assertEqual(expressions["pair_meta"],{})
            self.assertEqual(expressions["units"]["languages"],{})
            assets={m["name"]:{"size":m["bytes"],"digest":"sha256:"+m["sha256"],"oci":{"registry":"ghcr.io/danilfg/dicts-data","manifest":"sha256:"+"a"*64}} for d in (bilingual,expressions) for m in d["members"].values()}
            index=build_pair_index("v1",{"bilingual":bilingual,"expressions":expressions},"https://example.org/",assets)
            self.assertEqual(index["pairs"]["en-ru"]["sources"],["freedict"])
            self.assertIn("en-ru",index["groups"]["expressions"]["pairs"])
            for name in expressions["units"]["pairs"]["en-ru"]:
                with zipfile.ZipFile(packs/expressions["members"][name]["name"]) as z:
                    self.assertTrue(all(p=="UNIT.json" or p.startswith("data/links/expressions/en-ru/") for p in z.namelist()))
                    if "UNIT.json" in z.namelist():
                        unit=json.loads(z.read("UNIT.json"))
                        self.assertEqual(unit["kind"],"links")
                        self.assertEqual(unit["buckets"],BUCKETS)
    def test_word_aliases(self):
        self.assertIn("take",keys_for("took part in","en"))
        self.assertIn("entitle",keys_for("entitled to","en"))
        self.assertEqual(keys_for("single","en"),[])
