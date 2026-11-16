import pathlib,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"src"))
import select_compact_pages as p

class CompactPagesTest(unittest.TestCase):
 def test_selects_only_redundant_koreader_pairs(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d); downloads=root/"downloads";downloads.mkdir()
   extras=downloads/"enrichments-extra--001.zip"
   with zipfile.ZipFile(extras,"w") as z:
    for i in range(430):z.writestr(f"enrichment--aa-{i:02d}.json.gz","x")
    z.writestr("enrichment--en-ru.json.gz","x")
    z.writestr("enrichment--en-fr.json.gz","x")
   for pair in ("en-ru","en-fr","en-zz"):
    (downloads/f"koreader--{pair}.zip").write_text("archive")
   with self.assertRaisesRegex(ValueError,"expected KOReader"):
    p.select_compact(downloads,root/"skip")
   # Same core should never be removed even if a compact index exists.
   self.assertTrue((downloads/"koreader--en-ru.zip").exists())
   self.assertFalse((downloads/"koreader--en-fr.zip").exists())
   self.assertTrue((downloads/"koreader--en-zz.zip").exists())
if __name__=="__main__":unittest.main()
