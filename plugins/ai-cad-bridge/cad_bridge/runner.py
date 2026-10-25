import copy
import json
from pathlib import Path
import time
from .validation import validate, Workspace
from .engine import Engine, items, cast
from .intake import prepare
from .compatibility import preflight

def preflight_paths(command, workspace):
    """Fail before COM if any requested read/write escapes the configured boundary."""
    source = workspace.path(command['input'], ('.ipt', '.iam'), True) if command.get('input') else None
    paths = []
    if command['action'] != 'inspect':
        suffix = '.iam' if command['action'] == 'create_assembly' or (source and source.suffix.lower() == '.iam') else '.ipt'
        paths.extend([workspace.path(command['output'], (suffix,)),
                      workspace.path(command['output'] + '.bridge.json', ('.json',))])
    for export in command.get('exports', []):
        paths.append(workspace.path(export['path'], ('.step', '.stp') if export['format'] == 'step' else ('.stl',)))
    if command.get('snapshot'): paths.append(workspace.path(command['snapshot'], ('.png', '.bmp')))
    if len(set(paths)) != len(paths): raise ValueError('Output paths must be distinct')
    for op in command['operations']:
        if op['type'] == 'occurrence': workspace.path(op['path'], ('.ipt', '.iam'), True)
    return paths

class Runner:
    def __init__(self,connector,root): self.cx=connector; self.workspace=Workspace(root)
    def execute(self,command):
        command=copy.deepcopy(command)
        validate(command)
        preflight_paths(command, self.workspace)
        cx=self.cx; cx.check_thread(); app=cx.app; c=cx.c
        output=None; doc=None; transaction=None; saved=False
        results=[]; current=None
        response={'request_id':command['request_id'],'schema_version':'1.0','success':False,'operations':results,'warnings':list(cx.version['warnings']), 'inventor':cx.version}
        try:
            response['sources']=prepare(command,self.workspace.root)['sources']
            source=self.workspace.path(command['input'],('.ipt','.iam'),True) if command.get('input') else None
            if command['action']!='inspect':
                suffix='.iam' if command['action']=='create_assembly' or (source and source.suffix.lower()=='.iam') else '.ipt'
                output=self.workspace.path(command['output'],(suffix,))
                report=self.workspace.path(str(output)+'.bridge.json',('.json',))
            exports=[]
            for export in command.get('exports',[]):
                ext=('.step','.stp') if export['format']=='step' else ('.stl',)
                exports.append((export['format'],self.workspace.path(export['path'],ext)))
            snapshot=self.workspace.path(command['snapshot'],('.png','.bmp')) if command.get('snapshot') else None
            paths=[p for p in [output,snapshot,*[p for _,p in exports]] if p]
            if len(set(paths))!=len(paths): raise ValueError('Output paths must be distinct')
            for op in command['operations']:
                if op['type']=='occurrence': op['path']=str(self.workspace.path(op['path'],('.ipt','.iam'),True))
            if source:
                if any(d.FullFileName and Path(d.FullFileName).resolve()==source for d in items(app.Documents)):
                    raise ValueError('Input is already open in Inventor; close it first to isolate edits')
                # An invisible document has no view to activate for a snapshot.
                doc=app.Documents.Open(str(source),bool(command.get('snapshot')))
            else:
                kind=c.kAssemblyDocumentObject if command['action']=='create_assembly' else c.kPartDocumentObject
                template=app.FileManager.GetTemplateFile(kind,c.kMetricSystemOfMeasure)
                doc=app.Documents.Add(kind,template,True)
                doc.DisplayName=command.get('name',command['request_id'])
            import win32com.client
            doc=win32com.client.CastTo(doc,'AssemblyDocument' if doc.DocumentType==c.kAssemblyDocumentObject else 'PartDocument')
            engine=Engine(cx,doc)
            if command['action']=='inspect':
                # Inspection reports existing state without calling Update2.
                response.update(success=True,model=engine.verify(update=False))
                return response
            preflight(engine, command)
            transaction=app.TransactionManager.StartTransaction(doc,'AI CAD '+command['request_id'])
            doc.UnitsOfMeasure.LengthUnits=c.kMillimeterLengthUnits
            for name,value in command.get('parameters',{}).items():
                if any(p.Name==name for p in items(engine.cd.Parameters)):
                    raise ValueError('Parameter already exists; use set_parameter: '+name)
                engine.cd.Parameters.UserParameters.AddByExpression(name,f'{value} mm',c.kMillimeterLengthUnits)
            before=engine.verify()
            for op in command['operations']:
                current=op['id']; start=time.monotonic()
                # Reusing ids would make persistent references ambiguous.
                if doc.AttributeManager.FindObjects('AI_CAD','id',current).Count:
                    raise ValueError('Operation id already exists: '+current)
                obj=engine.run(op)
                after=engine.verify()
                typ=op['type']
                if typ in ('extrude','revolve','hole','fillet','chamfer','linear_pattern','circular_pattern','mirror'):
                    if after['solid_bodies']<1: raise RuntimeError('No expected solid body')
                    delta=after['volume_mm3']-before['volume_mm3']
                    if abs(delta)<1e-6: raise RuntimeError('Operation produced no measurable volume change')
                    if (typ=='hole' or op.get('operation')=='cut') and delta>=0:
                        raise RuntimeError('Cut did not remove material')
                    if op.get('operation') in ('join','new_body') and delta<=0:
                        raise RuntimeError('Additive feature did not add material')
                if typ=='occurrence' and after['occurrences']!=before['occurrences']+1:
                    raise RuntimeError('Occurrence was not added')
                if obj is not None and doc.AttributeManager.FindObjects('AI_CAD','id',current).Count!=1:
                    raise RuntimeError('Operation identity could not be verified')
                results.append({'id':current,'type':typ,'verified':True,'elapsed_seconds':round(time.monotonic()-start,3),'model':after})
                before=after
            if command.get('monolithic'):
                from .finishing import flatten
                transaction.End(); transaction=None
                old_doc=doc
                doc=flatten(cx, old_doc)
                old_doc.Close(True)
                engine=Engine(cx,doc)
                transaction=app.TransactionManager.StartTransaction(doc,'AI CAD finish')
                response['warnings'].append('Monolithic output has no editable construction history; rebuild from the JSON command.')
            if command.get('appearances'):
                from .finishing import paint
                response['appearances']=paint(cx, doc, command['appearances'])
            response['model']=engine.verify()
            if command.get('expected_size_mm'):
                import math
                actual=response['model'].get('size_mm')
                if actual is None or not all(math.isclose(a,b,abs_tol=0.01,rel_tol=0) for a,b in zip(actual,command['expected_size_mm'])):
                    raise RuntimeError('Envelope mismatch: '+str(actual))
            if command.get('allow_estimates') and any(m['status']=='estimated' for m in command.get('observations',[])):
                response['warnings'].append('PRELIMINARY: contains estimated dimensions; see observations')
            provenance=doc.AttributeSets.Add('AI_CAD_PROVENANCE') if not doc.AttributeSets.NameIsUsed('AI_CAD_PROVENANCE') else doc.AttributeSets.Item('AI_CAD_PROVENANCE')
            if provenance.NameIsUsed('request'): provenance.Item('request').Value=json.dumps(command)
            else: provenance.Add('request',c.kStringType,json.dumps(command))
            transaction.End(); transaction=None
            output.parent.mkdir(parents=True,exist_ok=True)
            if command.get('monolithic'):
                try: doc.ComponentDefinition.CompactModelHistoryOnNextSave=True
                except Exception: response['warnings'].append('CompactModelHistoryOnNextSave unavailable; geometry retained.')
            doc.SaveAs(str(output),False); saved=True
            if not output.is_file() or output.stat().st_size==0: raise RuntimeError('Native output missing')
            response['native_output']=str(output)
            response['exports']=[]
            for fmt,path in exports:
                path.parent.mkdir(parents=True,exist_ok=True)
                self.export(doc,fmt,path)
                response['exports'].append(str(path))
            if snapshot:
                snapshot.parent.mkdir(parents=True,exist_ok=True)
                doc.Activate(); view=app.ActiveView
                camera=view.Camera; camera.ViewOrientationType=c.kIsoTopRightViewOrientation; camera.Fit(); camera.Apply()
                view.SaveAsBitmap(str(snapshot),1200,900)
                if not snapshot.is_file() or not snapshot.stat().st_size: raise RuntimeError('Snapshot missing')
                response['snapshot']=str(snapshot)
            response['success']=True
            response['command']=command
            report.write_text(json.dumps(response,indent=2,ensure_ascii=False),encoding='utf-8')
        except Exception as exc:
            response['error']={'operation_id':current,'type':type(exc).__name__,'message':str(exc)}
            response['native_saved']=saved
            if transaction:
                try: transaction.Abort(); response['rolled_back']=True
                except Exception as rollback: response['rollback_error']=str(rollback)
        finally:
            if doc:
                try: doc.Close(True)
                except Exception as close: response['warnings'].append('Could not close bridge document: '+str(close))
        return response
    def export(self,doc,fmt,path):
        app=self.cx.app; c=self.cx.c
        translator_id={'step':'{90AF7F40-0C01-11D5-8E83-0010B541CD80}','stl':'{533E9A98-FC3B-11D4-8E7E-0010B541CD80}'}[fmt]
        addin=cast(app.ApplicationAddIns.ItemById(translator_id),'TranslatorAddIn')
        if not addin.Activated: addin.Activate()
        context=app.TransientObjects.CreateTranslationContext(); context.Type=c.kFileBrowseIOMechanism
        options=app.TransientObjects.CreateNameValueMap()
        if not addin.HasSaveCopyAsOptions(doc,context,options): raise RuntimeError('Translator does not support document')
        if fmt=='step': options.SetValue('ApplicationProtocolType',4)
        else:
            # Translator options use their own enum, not UnitsTypeEnum.
            options.SetValue('ExportUnits',5)
            options.SetValue('OutputFileType',0)
            options.SetValue('ExportFileStructure',0)
            options.SetValue('Resolution',0)
        data=app.TransientObjects.CreateDataMedium(); data.FileName=str(path)
        addin.SaveCopyAs(doc,context,options,data)
        if not path.is_file() or path.stat().st_size==0: raise RuntimeError('Export file is empty or missing')
        data=path.read_bytes()
        if fmt=='step' and not data.lstrip().startswith(b'ISO-10303-21;'):
            raise RuntimeError('Invalid STEP signature')
        if fmt=='stl':
            import struct
            binary=len(data)>=84 and len(data)==84+50*struct.unpack_from('<I',data,80)[0]
            ascii_stl=data.lstrip().startswith(b'solid') and b'facet normal' in data and b'endsolid' in data
            if not (binary or ascii_stl): raise RuntimeError('Invalid STL structure')
