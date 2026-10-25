"""Local handoff from a multimodal agent to validated geometry; never invent measurements."""
import hashlib
from .validation import validate, Workspace

def prepare(command,root):
    workspace=Workspace(root)
    sources=[]
    for name in command.get('sources',[]):
        path=workspace.path(name,('.png','.jpg','.jpeg','.bmp','.tif','.tiff','.pdf','.webp'),True)
        with path.open('rb') as stream:
            digest=hashlib.sha256()
            for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
        sources.append({'path':str(path),'sha256':digest.hexdigest()})
    missing=[o['name'] for o in command.get('observations',[]) if o.get('status')=='unknown' or o.get('value') is None]
    estimates=[o['name'] for o in command.get('observations',[]) if o.get('status')=='estimated']
    if missing: return {'status':'needs_measurements','required_measurements':missing,'sources':sources,'executable':False}
    if estimates and not command.get('allow_estimates'):
        return {'status':'needs_estimate_acceptance','estimated_measurements':estimates,'sources':sources,'executable':False}
    validate(command)
    return {'status':'preliminary' if estimates else 'ready','sources':sources,'executable':True,'command':command}
