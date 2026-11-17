import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import build
import normalized_pack
import unified_release

class RateLimitRegression(unittest.TestCase):
    def test_previous_manifest_loaded_once(self):
        old_tag=build.PREVIOUS_TAG
        old=build.PREVIOUS.copy()
        old_assets=build.PREVIOUS_ASSETS.copy()
        try:
            build.PREVIOUS_TAG="v-test"
            snapshot={"manifest.json":{"published":True},"freedict--en-ru.zip":{"published":True}}
            with patch.object(unified_release,"inventory",return_value=snapshot) as inv, patch.object(normalized_pack,"pull") as pull:
                def manifest(tag,names,folder,assets):
                    self.assertEqual(assets,snapshot)
                    (folder/"manifest.json").write_text('{"assets":[]}')
                pull.side_effect=manifest
                build.load_previous(Path("."))
                inv.assert_called_once_with("v-test")
                self.assertEqual(build.PREVIOUS_ASSETS,snapshot)
        finally:
            build.PREVIOUS_TAG=old_tag;build.PREVIOUS.clear();build.PREVIOUS.update(old)
            build.PREVIOUS_ASSETS.clear();build.PREVIOUS_ASSETS.update(old_assets)

    def test_legacy_published_download_has_no_rest_queries(self):
        payload=b"verified archive"
        asset={"name":"sample.zip","size":len(payload),"digest":"sha256:"+hashlib.sha256(payload).hexdigest(),"published":True}
        with tempfile.TemporaryDirectory() as tmp:
            def fetch(item,path):path.write_bytes(payload)
            with patch.object(unified_release,"download",side_effect=fetch) as direct, patch.object(unified_release,"inventory",side_effect=AssertionError("unexpected inventory")), patch.object(normalized_pack.subprocess,"run",side_effect=AssertionError("unexpected REST download")):
                normalized_pack.pull("v1",["sample.zip"],Path(tmp),{"sample.zip":asset})
                normalized_pack.pull("v1",["sample.zip"],Path(tmp),{"sample.zip":asset})
                self.assertEqual(direct.call_count,1)
                self.assertEqual((Path(tmp)/"sample.zip").read_bytes(),payload)
