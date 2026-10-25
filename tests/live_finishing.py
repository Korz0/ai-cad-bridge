"""Opt-in integration test: creates files in a NEW directory only."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'plugins/ai-cad-bridge'))
from cad_bridge.connector import Connector
from cad_bridge.runner import Runner
from cad_bridge.engine import cast, items


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',required=True)
    args=parser.parse_args()
    root=Path(args.workspace).resolve()
    root.mkdir(parents=True,exist_ok=False)
    command=json.loads((Path(__file__).parents[1]/'examples/colored_block.json').read_text())
    cx=Connector()
    try:
        result=Runner(cx,root).execute(command)
        assert result['success'],result
        assert result['model']['features']==result['model']['solid_bodies']==1
        assert result['model']['sketches']==[]
        assert result['appearances']['region_matches']==[1]
        assert math.isclose(result['model']['volume_mm3'],12000,rel_tol=1e-9)
        doc=cast(cx.app.Documents.Open(str(root/'colored_block.ipt'),False),'PartDocument')
        try:
            body=doc.ComponentDefinition.SurfaceBodies.Item(1)
            top=[f for f in items(body.Faces) if abs(f.PointOnFace.Z-1)<1e-8]
            assert len(top)==1
            assert top[0].Appearance.DisplayName=='AI blue'
            rgb=cast(top[0].Appearance.Item('generic_diffuse'),'ColorAssetValue').Value
            assert [rgb.Red,rgb.Green,rgb.Blue]==[20,95,190]
            assert doc.ComponentDefinition.Features.Count==1
        finally:doc.Close(True)
        failure=json.loads(json.dumps(command));failure['request_id']='bad_envelope';failure['output']='bad.ipt';failure.pop('snapshot');failure['expected_size_mm']=[41,30,10]
        failed=Runner(cx,root).execute(failure)
        assert not failed['success'] and not (root/'bad.ipt').exists()
        failure['expected_size_mm']=[40,30,10]
        failure['appearances']['regions'][0]['box_mm']={'min':[500,500,500],'max':[510,510,510]}
        failed=Runner(cx,root).execute(failure)
        assert not failed['success'] and not (root/'bad.ipt').exists()
        report={'inventor':cx.version,'passed':True,'checks':['one_body_one_feature','volume','envelope','reopen_face_rgb','envelope_mismatch_rollback','unmatched_region_rollback']}
        (root/'summary.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report))
    finally:cx.close()

if __name__=='__main__':main()
