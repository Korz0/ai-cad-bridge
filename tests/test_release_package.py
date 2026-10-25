import importlib.util
from pathlib import Path
import zipfile

ROOT=Path(__file__).parents[1]

def test_release_includes_license_and_is_reproducible(tmp_path):
    spec=importlib.util.spec_from_file_location('package_release',ROOT/'scripts/package_release.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    first=module.build(tmp_path/'first')
    second=module.build(tmp_path/'second')
    assert [p.read_bytes() for p in first]==[p.read_bytes() for p in second]
    with zipfile.ZipFile(first[0]) as archive:
        assert 'ai-cad-bridge/plugins/ai-cad-bridge/LICENSE' in archive.namelist()
        assert 'ai-cad-bridge/.github/workflows/release.yml' in archive.namelist()
    with zipfile.ZipFile(first[1]) as archive:
        assert 'ai-cad-bridge/LICENSE' in archive.namelist()
