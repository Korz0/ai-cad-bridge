"""One-body consolidation and visual face overrides. All coordinates are mm."""
import math
from .engine import cast, items, Engine


def flatten(cx, source):
    cd = source.ComponentDefinition
    if cd.SurfaceBodies.Count != 1 or not cd.SurfaceBodies.Item(1).IsSolid:
        raise ValueError('Monolithic output requires exactly one connected solid body')
    before = Engine(cx, source).verify()
    body = cx.app.TransientBRep.Copy(cd.SurfaceBodies.Item(1))
    doc = cast(cx.app.Documents.Add(cx.c.kPartDocumentObject,
        cx.app.FileManager.GetTemplateFile(cx.c.kPartDocumentObject,cx.c.kMetricSystemOfMeasure),True), 'PartDocument')
    try:
        doc.UnitsOfMeasure.LengthUnits = cx.c.kMillimeterLengthUnits
        features = doc.ComponentDefinition.Features.NonParametricBaseFeatures
        definition = features.CreateDefinition()
        definition.BRepEntities = cx.collection([body])
        definition.OutputType = cx.c.kSolidOutputType
        definition.IsAssociative = False
        features.AddByDefinition(definition).Name = 'Monolithic_body'
        after = Engine(cx, doc).verify()
        if (after['solid_bodies'] != 1 or after['features'] != 1 or after['sketches'] or
            not math.isclose(before['volume_mm3'], after['volume_mm3'], rel_tol=1e-9, abs_tol=1e-5) or
            not all(math.isclose(a,b,abs_tol=1e-6) for a,b in zip(before['size_mm'], after['size_mm']))):
            raise RuntimeError('Consolidation changed the geometry')
        return doc
    except BaseException:
        doc.Close(True)
        raise


def contains_point(point, box):
    return all(lo <= value <= hi for value,lo,hi in zip(point,box['min'],box['max']))


def paint(cx, doc, specification):
    if doc.DocumentType != cx.c.kPartDocumentObject:
        raise ValueError('Face appearances currently support parts only')
    assets = {}
    for entry in specification['palette']:
        # Names are scoped to this operation; conflict fails rather than mutating assets.
        asset = doc.Assets.Add(cx.c.kAssetTypeAppearance,'Generic','AI_'+entry['name'],'AI '+entry['name'])
        cast(asset.Item('generic_diffuse'),'ColorAssetValue').Value = cx.app.TransientObjects.CreateColor(*entry['rgb'])
        if 'gloss' in entry:
            cast(asset.Item('generic_glossiness'),'FloatAssetValue').Value = entry['gloss']
        if 'metallic' in entry:
            cast(asset.Item('generic_is_metal'),'BooleanAssetValue').Value = entry['metallic']
        assets[entry['name']] = asset
    if specification.get('base'): doc.ActiveAppearance = assets[specification['base']]
    faces = [face for body in items(doc.ComponentDefinition.SurfaceBodies) for face in items(body.Faces)]
    counts = [0] * len(specification.get('regions', []))
    old_update = cx.app.ScreenUpdating
    try:
        cx.app.ScreenUpdating = False
        for face in faces:
            p = face.PointOnFace
            point = [p.X*10,p.Y*10,p.Z*10]
            for index, region in enumerate(specification.get('regions', [])):
                if contains_point(point, region['box_mm']):
                    face.Appearance = assets[region['appearance']]
                    counts[index] += 1
        for region,count in zip(specification.get('regions', []), counts):
            if count < region.get('min_faces',1) or count > region.get('max_faces',1000000):
                raise ValueError(f'Appearance region {region["appearance"]} matched {count} faces outside expected limits')
    finally:
        cx.app.ScreenUpdating = old_update
    return {'palette': list(assets), 'region_matches': counts,
            'selection': 'Face.PointOnFace in box_mm; last matching region wins',
            'physical_material': 'unchanged; appearances are visual only'}
