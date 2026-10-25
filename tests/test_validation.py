import copy
import json
from pathlib import Path
import pytest
from cad_bridge.validation import validate, Workspace

@pytest.fixture
def command(): return json.loads((Path(__file__).parents[1]/'examples/bracket.json').read_text())

def test_valid(command): validate(command)

@pytest.mark.parametrize('mutation',[
 lambda c:c.update(schema_version='2.0'),
 lambda c:c.update(shell='calc.exe'),
 lambda c:c['operations'][1].update(depends_on=[]),
 lambda c:c['operations'][0].update(depends_on=['pad']),
 lambda c:c['operations'][1].update(id='base'),
 lambda c:c['parameters'].update(Width=float('nan')),
 lambda c:c['parameters'].update(Width=float('inf')),
 lambda c:c['operations'][1].update(distance=-1),
 lambda c:c['operations'][1].update(distance='__import__("os")'),
 lambda c:c.update(action='modify'),
 lambda c:c.update(action='inspect',input='models/a.ipt'),
 lambda c:c.update(action='create_assembly'),
])
def test_rejects(command,mutation):
 mutation(command)
 with pytest.raises(ValueError): validate(command)

def test_estimates(command):
 command['observations']=[{'name':'Width','value':100,'status':'estimated','confidence':0.6,'source':'photo/reference'}]
 with pytest.raises(ValueError): validate(command)
 command['allow_estimates']=True; validate(command)
 command['observations'][0]['status']='unknown'
 with pytest.raises(ValueError): validate(command)

def test_measurement_mismatch(command):
 command['observations']=[{'name':'Width','value':99,'status':'verified','confidence':1,'source':'caliper'}]
 with pytest.raises(ValueError): validate(command)

def test_paths(tmp_path):
 w=Workspace(tmp_path)
 with pytest.raises(ValueError): w.path('../escape.ipt')
 with pytest.raises(ValueError): w.path('file.exe',('.ipt',))
 with pytest.raises(ValueError): w.path('absent.ipt',existing=True)
 (tmp_path/'exists.ipt').write_bytes(b'original')
 with pytest.raises(ValueError): w.path('exists.ipt')
 assert (tmp_path/'exists.ipt').read_bytes()==b'original'

def test_persisted_reference(command):
 c={'schema_version':'1.0','request_id':'edit','action':'modify','units':'mm','input':'a.ipt','output':'b.ipt','operations':[{'id':'round','type':'fillet','depends_on':[],'edges':['@pad/end_edges'],'radius':1}]}
 validate(c)
 c['operations'][0]['edges']=['pad/end_edges']
 with pytest.raises(ValueError): validate(c)
