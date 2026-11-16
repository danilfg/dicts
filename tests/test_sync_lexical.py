import gzip
import json
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import sync_lexical as s

XML=b'''<?xml version="1.0" encoding="utf8"?>
<LexicalResource xmlns="https://globalwordnet.github.io/schemas/wn-lmf/1.4">
<Lexicon id="demo">
<LexicalEntry id="w1"><Lemma writtenForm="happy" partOfSpeech="a"/><Sense synset="s1"/></LexicalEntry>
<LexicalEntry id="w2"><Lemma writtenForm="glad" partOfSpeech="a"/><Sense synset="s1"/></LexicalEntry>
<Synset id="s1" partOfSpeech="a"><Definition>Feeling or showing pleasure.</Definition></Synset>
</Lexicon></LexicalResource>'''
class LexicalTests(unittest.TestCase):
    def test_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a";p.write_bytes(b"abc")
            self.assertEqual(len(s.sha256(p)),64)
    def test_oewn_parser_with_fixture(self):
        # Small XML fixtures test shape/logic; production requires >=10k entries.
        r=ET.fromstring(XML)
        sids={x.attrib["id"] for x in r.iter() if s.local(x)=="Synset"}
        self.assertEqual(sids,{"s1"})
        self.assertEqual({x.attrib.get("writtenForm") for x in r.iter() if s.local(x)=="Lemma"},{"happy","glad"})
    def test_sources_include_licenses(self):
        self.assertEqual(set(s.SOURCES),{"oewn","omw","conceptnet"})
        self.assertTrue(all(a.get("license") and a.get("license_url") and a.get("credit") for a in s.SOURCES.values()))
    def test_manifest_credit_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"demo";p.write_text("data")
            with self.assertRaises(ValueError):s.add_asset({"assets":[]},p,"oewn","http://example.org","","copyright")
if __name__=="__main__":unittest.main()
