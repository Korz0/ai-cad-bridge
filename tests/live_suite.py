"""Explicit opt-in real Inventor tests; creates new files only in supplied folder.
Run: python tests/live_suite.py --workspace <empty testing directory>
"""
import argparse,json,math,sys,shutil,time,hashlib,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'plugins/ai-cad-bridge'))
from cad_bridge.connector import Connector
from cad_bridge.runner import Runner

def op(operation_type,id,depends=(),**kwargs): return dict(type=operation_type,id=id,depends_on=list(depends),**kwargs)
def sketch(id='base',origin=None,width=100,height=60):
 return op('sketch',id,plane='XY',geometry=[dict(id='outline',type='rectangle',origin=origin or [0,0],width=width,height=height)])
def pad(): return op('extrude','pad',['base'],sketch='base',distance=10,operation='join')

def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);args=p.parse_args()
 root=Path(args.workspace).resolve();root.mkdir(parents=True,exist_ok=False)
 cx=Connector();run=Runner(cx,root);reports=[]
 def case(name,ops,action='create_part',expected=None,expect_failure=False,**kw):
  command=dict(schema_version='1.0',request_id=name,action=action,units='mm',operations=ops,output=name+('.iam' if action=='create_assembly' else '.ipt'),**kw)
  result=run.execute(command)
  passed=result['success']!=expect_failure
  if expected is not None and result['success']: passed=passed and math.isclose(result['model']['volume_mm3'],expected,rel_tol=1e-6,abs_tol=1e-5)
  result['test_passed']=passed;result['expected_volume_mm3']=expected
  (root/(name+'.result.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
  reports.append({'case':name,'passed':passed,'error':result.get('error'),'volume':result.get('model',{}).get('volume_mm3')})
  print(json.dumps(reports[-1]),flush=True)
  return result
 try:
  case('box',[sketch(),pad()],expected=60000)
  case('holes',[sketch(),pad(),op('hole','bore',['pad'],plane='XY',centers=[[20,20]],diameter=8,depth='through_all',direction='negative')],expected=60000-math.pi*16*10)
  case('blind',[sketch(),pad(),op('hole','bore',['pad'],plane='XY',centers=[[20,20]],diameter=8,depth=5,direction='negative')])
  case('cut',[sketch(),pad(),op('sketch','cutSketch',['pad'],plane='XY',geometry=[dict(type='circle',id='c',center=[20,20],diameter=8)]),op('extrude','cut',['cutSketch'],sketch='cutSketch',distance=10,operation='cut')],expected=60000-math.pi*16*10)
  case('fillet',[sketch(),pad(),op('fillet','round',['pad'],edges=['pad/end_edges'],radius=1)])
  case('chamfer',[sketch(),pad(),op('chamfer','bevel',['pad'],edges=['pad/end_edges'],distance=1)])
  case('revolve',[sketch(origin=[10,0],width=10,height=20),op('revolve','turn',['base'],sketch='base',axis='Y',angle_deg=360,operation='join')],expected=math.pi*(400-100)*20)
  bore=op('hole','bore',['pad'],plane='XY',centers=[[20,20]],diameter=8,depth='through_all',direction='negative')
  case('linear',[sketch(),pad(),bore,op('linear_pattern','repeat',['bore'],features=['bore'],axis='X',count=3,spacing=20)],expected=60000-3*math.pi*16*10)
  case('circular',[sketch(origin=[-50,-50],width=100,height=100),pad(),op('hole','bore',['pad'],plane='XY',centers=[[20,0]],diameter=8,depth='through_all',direction='negative'),op('circular_pattern','repeat',['bore'],features=['bore'],axis='Z',count=4,angle_deg=360)],expected=100000-4*math.pi*16*10)
  case('mirror',[sketch(origin=[-50,-30]),pad(),op('hole','bore',['pad'],plane='XY',centers=[[20,0]],diameter=8,depth='through_all',direction='negative'),op('mirror','symmetry',['bore'],features=['bore'],plane='YZ')],expected=60000-2*math.pi*16*10)
  case('workplane',[op('workplane','offset',base='XY',offset=20),op('sketch','base',['offset'],plane='offset',geometry=[dict(type='circle',id='c',center=[0,0],diameter=20)]),pad()],expected=math.pi*100*10)
  case('constraints',[op('sketch','base',plane='XY',geometry=[dict(type='line',id='line',start=[0,0],end=[10,0])]),op('constraint','horizontal',['base'],kind='horizontal',entities=['base/line']),op('dimension','length',['base'],kind='length',entity='base/line',value=30,text=[10,10])])
  case('arc',[op('sketch','base',plane='XY',geometry=[dict(type='arc',id='arc',start=[0,0],mid=[10,10],end=[20,0])])])
  case('params',[sketch(width='Width'),pad()],parameters={'Width':100},expected=60000)
  digest=hashlib.sha256((root/'params.ipt').read_bytes()).hexdigest()
  case('modified',[op('set_parameter','resize',name='Width',value=120)],action='modify',input='params.ipt',expected=72000,snapshot='modified.png')
  assert hashlib.sha256((root/'params.ipt').read_bytes()).hexdigest()==digest
  case('persisted',[op('fillet','newRound',edges=['@pad/end_edges'],radius=1)],action='modify',input='box.ipt')
  case('assembly',[op('occurrence','first',path='box.ipt',translation=[0,0,0],grounded=True),op('occurrence','second',path='box.ipt',translation=[0,0,30]),op('assembly_constraint','mate',['first','second'],kind='flush',first='first/XY',second='second/XY',offset=30)],action='create_assembly')
  case('rollback',[sketch(),pad(),op('hole','miss',['pad'],plane='XY',centers=[[500,500]],diameter=8,depth='through_all',direction='negative')],expect_failure=True)
  assert not (root/'rollback.ipt').exists()
  case('export',[sketch(),pad()],exports=[{'format':'step','path':'box.step'},{'format':'stl','path':'box.stl'}],snapshot='box.png',expected=60000)
  data=(root/'box.stl').read_bytes();n=struct.unpack_from('<I',data,80)[0]
  points=[struct.unpack_from('<3f',data,84+50*i+12+12*j) for i in range(n) for j in range(3)]
  bounds=[max(p[a] for p in points)-min(p[a] for p in points) for a in range(3)]
  passed=all(math.isclose(a,b,rel_tol=1e-5) for a,b in zip(bounds,[100,60,10]))
  reports.append({'case':'stl_mm_scale','passed':passed,'bounds_mm':bounds})
  print(json.dumps(reports[-1]),flush=True)
  inspected=run.execute({'schema_version':'1.0','request_id':'inspect','action':'inspect','units':'mm','input':'export.ipt','operations':[]})
  reports.append({'case':'native_reopen','passed':inspected['success'] and math.isclose(inspected['model']['volume_mm3'],60000,rel_tol=1e-6)})
 finally:
  cx.close()
  (root/'summary.json').write_text(json.dumps({'inventor':cx.version,'cases':reports},indent=2),encoding='utf-8')
 return 0 if all(r['passed'] for r in reports) else 1
if __name__=='__main__':raise SystemExit(main())
