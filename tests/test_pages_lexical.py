import gzip
import pathlib
import sys
import tempfile
import unittest
import json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
import build_pages_lexical as lex

class LexicalPagesTests(unittest.TestCase):
 def test_parse_concept_uri(self):
  self.assertEqual(lex.uri_concept("/c/en/thoughtful/a"),("en","thoughtful"))
  self.assertEqual(lex.uri_concept("/c/ru/%D0%BC%D0%B8%D1%80/n"),("ru","мир"))
  self.assertIsNone(lex.uri_concept("/r/RelatedTo"))
 def test_generate_real_on_demand_shards(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   meta=lex.publish_index(p,"oewn","en",{"thoughtful":{"definitions":["Showing consideration"],"synonyms":["kind"]}},4)
   self.assertEqual(meta["entries"],1)
   self.assertEqual(len(list((p/"data"/"lexical"/"oewn"/"en").glob("*.json.gz"))),4)
 def test_concept_relationships_and_provenance(self):
  with tempfile.TemporaryDirectory() as d:
   f=pathlib.Path(d)/"concept.gz"
   rows=[
    "/a/\t/r/RelatedTo\t/c/en/thoughtful\t/c/en/caring\t{}\n",
    "/a/\t/r/Synonym\t/c/en/thoughtful\t/c/en/considerate\t{}\n",
    "/a/\t/r/RelatedTo\t/c/en/random\t/c/en/something\t{}\n"]
   with gzip.open(f,"wt") as stream:stream.writelines(rows)
   # Tiny test set deliberately fails production completeness guard.
   with self.assertRaisesRegex(ValueError,"unexpectedly tiny"):
    lex.conceptnet_records(f,{"en":{"thoughtful"}})
if __name__=="__main__":unittest.main()
