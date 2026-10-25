import copy
import json
import os
from pathlib import Path
import pytest
from cad_bridge.compatibility import version_info, require_member
from cad_bridge.validation import validate, Workspace
from cad_bridge.runner import preflight_paths
from cad_bridge.finishing import contains_point

ROOT=Path(__file__).parents[1]

@pytest.mark.parametrize('year',range(2017,2028))
def test_version_policy(year):
    result=version_info(year-1996,str(year))
    assert result['year']==year
    assert result['support']==('tested' if year==2022 else 'api_candidate')

def test_unsupported_and_wrong_release():
    for kwargs in ({'major':20,'display':'2016'},{'major':32,'display':'2028'},
                   {'major':26,'display':'2022','expected_year':2025}):
        with pytest.raises(RuntimeError):version_info(**kwargs)
    assert version_info(32,'2028',allow_future=True)['support']=='experimental'
    with pytest.raises(RuntimeError,match='Required Inventor API'):require_member(object(),'Unknown','Test')

@pytest.fixture
def colored():return json.loads((ROOT/'examples/colored_block.json').read_text())

def test_finishing_schema(colored):validate(colored)

@pytest.mark.parametrize('mutate',[
 lambda c:c['appearances']['palette'][0].update(rgb=[-1,0,0]),
 lambda c:c['appearances']['palette'][0].update(gloss=2),
 lambda c:c['appearances'].update(base='missing'),
 lambda c:c['appearances']['regions'][0].update(appearance='missing'),
 lambda c:c['appearances']['regions'][0]['box_mm'].update(min=[100,100,100]),
 lambda c:c.update(action='modify',input='a.ipt'),
 lambda c:c.update(expected_size_mm=[1,2]),
 lambda c:c['appearances']['regions'][0].update(min_faces=10,max_faces=1),
])
def test_reject_finishing(colored,mutate):
    mutate(colored)
    with pytest.raises(ValueError):validate(colored)

def test_source_and_output_validation_before_com(tmp_path,colored):
    w=Workspace(tmp_path)
    preflight_paths(colored,w)
    for field in ('output','snapshot'):
        c=copy.deepcopy(colored);c[field]='../escape.'+('ipt' if field=='output' else 'png')
        with pytest.raises(ValueError):preflight_paths(c,w)
    (tmp_path/'colored_block.ipt.bridge.json').write_text('keep')
    with pytest.raises(ValueError,match='overwrite'):preflight_paths(colored,w)
    assert (tmp_path/'colored_block.ipt.bridge.json').read_text()=='keep'

def test_face_region_boundaries():
    box={'min':[0,0,10],'max':[40,30,10]}
    assert contains_point([20,15,10],box)
    assert not contains_point([20,15,9],box)

def test_server_requires_explicit_workspace(monkeypatch):
    from cad_bridge.server import workspace
    monkeypatch.delenv('AI_CAD_WORKSPACE',raising=False)
    with pytest.raises(RuntimeError,match='not configured'):workspace()

def test_plugin_identity_and_launch_target():
    plugin=ROOT/'plugins/ai-cad-bridge'
    portable=json.loads((plugin/'plugin.json').read_text())
    legacy=json.loads((plugin/'.codex-plugin/plugin.json').read_text())
    assert portable['name']==legacy['name']=='ai-cad-bridge'
    assert portable['version']==legacy['version']=='0.2.0'
    assert len(portable['extensions']['com.openai']['interface']['shortDescription'])<=30
    launch=json.loads((plugin/'mcp.json').read_text())['mcpServers']['inventor']['args'][-1]
    assert (plugin/launch.replace('${PLUGIN_ROOT}/','')).is_file()
    assert (plugin/'skills/inventor-modeling/SKILL.md').is_file()
