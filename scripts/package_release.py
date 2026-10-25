"""Create redistributable source/plugin archives without local CAD or caches."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_ROOTS={'.agents','.github','docs','examples','plugins','scripts','tests'}
EXCLUDED={'__pycache__','.pytest_cache','.git','.venv','build','dist','test-results'}
ROOT_FILES={'.gitignore','.gitattributes','README.md','README.es.md','LICENSE','CHANGELOG.md','CONTRIBUTING.md',
            'PRIVACY.md','SECURITY.md','THIRD_PARTY_NOTICES.md','install.ps1','INSTALL.cmd',
            'uninstall.ps1','doctor.ps1','pytest.ini','requirements-lock.txt'}
EXTENSIONS={'.py','.json','.md','.toml','.ps1','.cmd','.txt','.yml','.yaml','.svg'}


def sources():
    for path in sorted(ROOT.rglob('*')):
        if path.is_symlink(): raise ValueError(f'Symlink not permitted: {path}')
        if not path.is_file():continue
        relative=path.relative_to(ROOT)
        if any(p in EXCLUDED or p.endswith('.egg-info') for p in relative.parts):continue
        if len(relative.parts)==1:
            if relative.name in ROOT_FILES:yield path,relative
        elif relative.parts[0] in ALLOWED_ROOTS and (path.suffix in EXTENSIONS or path.name=='LICENSE'):
            yield path,relative


def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    plugin=ROOT/'plugins/ai-cad-bridge'
    manifest=json.loads((plugin/'plugin.json').read_text())
    version=manifest['version']
    source_files=list(sources())
    archives=[]
    for name,plugin_only in [('ai-cad-bridge-source',False),('ai-cad-bridge-plugin',True)]:
        archive=output/f'{name}-{version}.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for path,relative in source_files:
                if plugin_only:
                    if not path.is_relative_to(plugin):continue
                    arc=Path('ai-cad-bridge')/path.relative_to(plugin)
                else:arc=Path('ai-cad-bridge')/relative
                # Stable timestamps/modes make local and CI downloads reproducible.
                info=zipfile.ZipInfo(arc.as_posix(),date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.create_system=3
                info.external_attr=0o100644 << 16
                z.writestr(info,path.read_bytes())
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names=z.namelist()
            required='ai-cad-bridge/plugin.json' if plugin_only else 'ai-cad-bridge/install.ps1'
            assert required in names
            assert not any(n.endswith(('.ipt','.iam','.pyc','.pyd','.dll')) for n in names)
        archives.append(archive)
    checksums=output/'SHA256SUMS.txt'
    checksums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in archives))
    return archives


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print('\n'.join(map(str,build(parser.parse_args().output))))
