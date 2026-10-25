"""Parametric operations. Length JSON values are mm; Inventor internal lengths are cm."""
import math

def cast(obj,name):
    import win32com.client
    return win32com.client.CastTo(obj,name)

def items(collection):
    return [collection.Item(i) for i in range(1,collection.Count+1)]

class Engine:
    def __init__(self, connector, document):
        self.cx=connector; self.app=connector.app; self.c=connector.c
        self.doc=document; self.cd=document.ComponentDefinition
        self.tg=self.app.TransientGeometry; self.refs={}
    def expr(self,value):
        if isinstance(value,(int,float)): return f'{value:.12g} mm'
        # Schema restricts to a parameter name; require an existing length parameter.
        p=self.cd.Parameters.Item(value)
        self.doc.UnitsOfMeasure.GetValueFromExpression(p.Expression,'mm')
        return value
    def length(self,value):
        return self.doc.UnitsOfMeasure.GetValueFromExpression(self.expr(value),'mm')
    def p2(self,xy): return self.tg.CreatePoint2d(xy[0]/10,xy[1]/10)
    def tag(self,obj,key):
        attrs=obj.AttributeSets
        aset=attrs.Item('AI_CAD') if attrs.NameIsUsed('AI_CAD') else attrs.Add('AI_CAD')
        if aset.NameIsUsed('id'): aset.Item('id').Value=key
        else: aset.Add('id',self.c.kStringType,key)
        self.refs[key]=obj
        return obj
    def ref(self,key):
        key=key.lstrip('@')
        if key in ('XY','XZ','YZ'): return self.cd.WorkPlanes.Item({'YZ':1,'XZ':2,'XY':3}[key])
        if key in ('X','Y','Z'): return self.cd.WorkAxes.Item({'X':1,'Y':2,'Z':3}[key])
        if key in self.refs: return self.refs[key]
        found=self.doc.AttributeManager.FindObjects('AI_CAD','id',key)
        if found.Count==1:
            self.refs[key]=found.Item(1)
            return self.refs[key]
        if found.Count>1: raise ValueError('Ambiguous stored reference: '+key)
        if '/' in key:
            parent,selector=key.rsplit('/',1)
            if selector in ('start','end','center'):
                entity=self.ref(parent)
                return getattr(entity,{'start':'StartSketchPoint','end':'EndSketchPoint','center':'CenterSketchPoint'}[selector])
            if selector in ('end_face','start_face','end_edges','start_edges'):
                feature=self.ref(parent)
                faces=feature.EndFaces if selector.startswith('end') else feature.StartFaces
                if faces.Count!=1: raise ValueError('Face selector is ambiguous: '+key)
                face=faces.Item(1)
                return items(face.Edges) if selector.endswith('edges') else face
        raise ValueError('Reference not found: '+key)
    def direction(self,op):
        return {'positive':self.c.kPositiveExtentDirection,'negative':self.c.kNegativeExtentDirection,'symmetric':self.c.kSymmetricExtentDirection}[op.get('direction','positive')]
    def operation(self,op):
        return {'join':self.c.kJoinOperation,'cut':self.c.kCutOperation,'new_body':self.c.kNewBodyOperation,'intersect':self.c.kIntersectOperation}[op['operation']]
    def run(self,op):
        self.cx.check_thread()
        result=getattr(self,'do_'+op['type'])(op)
        if result is not None:
            self.tag(result,op['id'])
            if op['type'] in ('sketch','workplane','extrude','revolve','hole','fillet','chamfer','linear_pattern','circular_pattern','mirror','occurrence'):
                result.Name='AI_'+op['id']
        return result
    def do_workplane(self,o):
        return self.cd.WorkPlanes.AddByPlaneAndOffset(self.ref(o['base']),f'{o["offset"]} mm')
    def do_sketch(self,o):
        s=self.cd.Sketches.Add(self.ref(o['plane']))
        for g in o['geometry']:
            key=o['id']+'/'+g['id']
            if g['type']=='rectangle':
                origin=g.get('origin',[0,0]); p=self.p2(origin)
                q=self.tg.CreatePoint2d(p.X+self.length(g['width']),p.Y+self.length(g['height']))
                lines=[cast(line,'SketchLine') for line in items(s.SketchLines.AddAsTwoPointRectangle(p,q))]
                for i,line in enumerate(lines): self.tag(line,key+'/'+str(i+1))
                # Driving dimensions preserve relations and make width/height editable.
                for line in lines[:2]:
                    horizontal=abs(line.StartSketchPoint.Geometry.Y-line.EndSketchPoint.Geometry.Y)<1e-8
                    d=s.DimensionConstraints.AddTwoPointDistance(line.StartSketchPoint,line.EndSketchPoint,self.c.kAlignedDim,self.tg.CreatePoint2d(q.X+1,q.Y+1))
                    d.Parameter.Expression=self.expr(g['width'] if horizontal else g['height'])
                s.GeometricConstraints.AddGround(lines[0].StartSketchPoint)
            elif g['type']=='circle':
                circle=s.SketchCircles.AddByCenterRadius(self.p2(g['center']),self.length(g['diameter'])/2)
                self.tag(circle,key)
                s.GeometricConstraints.AddGround(circle.CenterSketchPoint)
                d=s.DimensionConstraints.AddDiameter(circle,self.p2([g['center'][0]+10,g['center'][1]+10]))
                d.Parameter.Expression=self.expr(g['diameter'])
            elif g['type']=='line':
                line=s.SketchLines.AddByTwoPoints(self.p2(g['start']),self.p2(g['end']))
                line.Construction=g.get('construction',False); self.tag(line,key)
            elif g['type']=='arc':
                self.tag(s.SketchArcs.AddByThreePoints(self.p2(g['start']),self.p2(g['end']),self.p2(g['mid'])),key)
        return s
    def do_constraint(self,o):
        es=[self.ref(k) for k in o['entities']]
        methods={'horizontal':'AddHorizontal','vertical':'AddVertical','parallel':'AddParallel','perpendicular':'AddPerpendicular','equal':'AddEqualLength','coincident':'AddCoincident','concentric':'AddConcentric','tangent':'AddTangent'}
        if o['kind']=='equal' and es[0].Type in (self.c.kSketchCircleObject,self.c.kSketchArcObject): methods['equal']='AddEqualRadius'
        return getattr(es[0].Parent.GeometricConstraints,methods[o['kind']])(*es)
    def do_dimension(self,o):
        e=self.ref(o['entity']); ds=e.Parent.DimensionConstraints; p=self.p2(o['text'])
        if o['kind']=='length': d=ds.AddTwoPointDistance(e.StartSketchPoint,e.EndSketchPoint,self.c.kAlignedDim,p)
        elif o['kind']=='diameter': d=ds.AddDiameter(e,p)
        else: d=ds.AddRadius(e,p)
        d.Parameter.Expression=self.expr(o['value'])
        return d
    def do_extrude(self,o):
        profile=self.ref(o['sketch']).Profiles.AddForSolid()
        features=self.cd.Features.ExtrudeFeatures
        definition=features.CreateExtrudeDefinition(profile,self.operation(o))
        definition.SetDistanceExtent(self.expr(o['distance']),self.direction(o))
        return features.Add(definition)
    def do_revolve(self,o):
        profile=self.ref(o['sketch']).Profiles.AddForSolid()
        return self.cd.Features.RevolveFeatures.AddByAngle(profile,self.ref(o['axis']),f'{o["angle_deg"]} deg',self.c.kPositiveExtentDirection,self.operation(o))
    def do_hole(self,o):
        s=self.cd.Sketches.Add(self.ref(o['plane']))
        self.tag(s,o['id']+'/placement')
        points=self.cx.collection([s.SketchPoints.Add(self.p2(p)) for p in o['centers']])
        hs=self.cd.Features.HoleFeatures
        placement=hs.CreateSketchPlacementDefinition(points)
        if o['depth']=='through_all': return hs.AddDrilledByThroughAllExtent(placement,self.expr(o['diameter']),self.direction(o))
        return hs.AddDrilledByDistanceExtent(placement,self.expr(o['diameter']),self.expr(o['depth']),self.direction(o))
    def edges(self,o):
        edges=[]
        for key in o['edges']:
            e=self.ref(key); edges.extend(e if isinstance(e,list) else [e])
        result=self.app.TransientObjects.CreateEdgeCollection()
        for e in edges: result.Add(e)
        return result
    def do_fillet(self,o):
        return self.cd.Features.FilletFeatures.AddSimple(self.edges(o),self.expr(o['radius']))
    def do_chamfer(self,o):
        return self.cd.Features.ChamferFeatures.AddUsingDistance(self.edges(o),self.expr(o['distance']))
    def do_linear_pattern(self,o):
        fs=self.cd.Features.RectangularPatternFeatures
        d=fs.CreateDefinition(self.cx.collection([self.ref(x) for x in o['features']]),self.ref(o['axis']),True,o['count'],self.expr(o['spacing']))
        return fs.AddByDefinition(d)
    def do_circular_pattern(self,o):
        fs=self.cd.Features.CircularPatternFeatures
        d=fs.CreateDefinition(self.cx.collection([self.ref(x) for x in o['features']]),self.ref(o['axis']),True,o['count'],f'{o["angle_deg"]} deg',True)
        return fs.AddByDefinition(d)
    def do_mirror(self,o):
        fs=self.cd.Features.MirrorFeatures
        d=fs.CreateDefinition(self.cx.collection([self.ref(x) for x in o['features']]),self.ref(o['plane']))
        return fs.AddByDefinition(d)
    def do_set_parameter(self,o):
        p=self.cd.Parameters.Item(o['name'])
        p.Expression=self.expr(o['value'])
        return None
    def do_occurrence(self,o):
        transform=self.tg.CreateMatrix()
        transform.SetTranslation(self.tg.CreateVector(*[v/10 for v in o['translation']]))
        occ=self.cd.Occurrences.Add(o['path'],transform)
        occ.Grounded=o.get('grounded',False)
        return occ
    def assembly_plane(self,key):
        name,plane=key.rsplit('/',1)
        if plane not in ('XY','XZ','YZ'): raise ValueError('Assembly constraints require origin plane references')
        occ=self.ref(name)
        definition=cast(occ.Definition,'PartComponentDefinition' if occ.DefinitionDocumentType==self.c.kPartDocumentObject else 'AssemblyComponentDefinition')
        local=definition.WorkPlanes.Item({'YZ':1,'XZ':2,'XY':3}[plane])
        return occ.CreateGeometryProxy(local)
    def do_assembly_constraint(self,o):
        a=self.assembly_plane(o['first']); b=self.assembly_plane(o['second'])
        method=self.cd.Constraints.AddMateConstraint if o['kind']=='mate' else self.cd.Constraints.AddFlushConstraint
        return method(a,b,f'{o["offset"]} mm')

    def verify(self,update=True):
        if update and not self.doc.Update2(False): raise RuntimeError('Inventor Update2 reported failure')
        if self.doc.RequiresUpdate: raise RuntimeError('Document still requires update')
        assembly=self.doc.DocumentType==self.c.kAssemblyDocumentObject
        fs=items(self.cd.Constraints) if assembly else items(self.cd.Features)
        bad=[{'name':f.Name,'health':int(f.HealthStatus)} for f in fs if f.HealthStatus!=self.c.kUpToDateHealth]
        if bad: raise RuntimeError('Unhealthy operations: '+str(bad))
        result={'features':len(fs),'parameters':{p.Name:{'expression':p.Expression,'internal_value':p.Value,'units':p.Units} for p in items(self.cd.Parameters)}}
        if assembly:
            result['occurrences']=self.cd.Occurrences.Count
        else:
            bodies=items(self.cd.SurfaceBodies)
            result['solid_bodies']=sum(bool(b.IsSolid) for b in bodies)
            result['volume_mm3']=self.cd.MassProperties.Volume*1000 if bodies else 0.0
            if bodies:
                boxes=[body.RangeBox for body in bodies]
                result['size_mm']=[(max(getattr(b.MaxPoint,axis) for b in boxes)-min(getattr(b.MinPoint,axis) for b in boxes))*10 for axis in ('X','Y','Z')]
                result['faces']=sum(body.Faces.Count for body in bodies)
            result['sketches']=[{'name':s.Name,'constraint_status':int(s.ConstraintStatus),'entities':s.SketchEntities.Count} for s in items(self.cd.Sketches)]
        return result
