import pytest
from cad_bridge.intake import prepare

def command():
 return {'schema_version':'1.0','request_id':'image','action':'create_part','units':'mm','output':'image.ipt','operations':[], 'observations':[{'name':'width','value':None,'status':'unknown','confidence':0,'source':'front photo'}]}
def test_missing_measurement(tmp_path):
 r=prepare(command(),tmp_path)
 assert r['required_measurements']==['width'] and not r['executable']
def test_estimated_requires_optin(tmp_path):
 c=command();c['observations'][0].update(value=10,status='estimated',confidence=0.4)
 assert prepare(c,tmp_path)['status']=='needs_estimate_acceptance'
 c['allow_estimates']=True
 assert prepare(c,tmp_path)['status']=='preliminary'
def test_source_hash(tmp_path):
 (tmp_path/'reference.png').write_bytes(b'reference image fixture')
 c=command();c['sources']=['reference.png']
 r=prepare(c,tmp_path)
 assert len(r['sources'][0]['sha256'])==64
 c['sources']=['../outside.png']
 with pytest.raises(ValueError): prepare(c,tmp_path)
