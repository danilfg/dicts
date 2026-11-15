import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from mirror_raw import discover,EXPLICIT_TATOEBA
class ArchiveDiscoveryTests(unittest.TestCase):
 def test_kaikki_all_editions(self):
  page='<a href="/dictionary/raw-wiktextract-data.jsonl.gz">en</a><a href="/dictionary/downloads/ru/ru-extract.jsonl.gz">ru</a><a href="/dictionary/downloads/ja/ja-extract.jsonl.gz">ja</a>'
  pairs=discover("kaikki",page)
  self.assertEqual(set(pairs),{"en","ru","ja"})
 def test_tatoeba_source_files(self):
  page=''.join('<a href="'+x+'">'+x+'</a>' for x in EXPLICIT_TATOEBA)
  found=discover("tatoeba",page)
  self.assertEqual(set(found),set(EXPLICIT_TATOEBA))
 def test_no_unrelated_data(self):
  page='<a href="audio.tar">Audio</a><a href="error-data.jsonl.gz">Errors</a>'
  with self.assertRaises(ValueError):discover("kaikki",page)
if __name__=="__main__":unittest.main()
