"""Pure validation: runs before importing COM or touching documents."""
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA = json.loads(Path(__file__).with_name('command.schema.json').read_text(encoding='utf-8'))

def validate(command):
    errors=list(Draft202012Validator(SCHEMA).iter_errors(command))
    if errors:
        err=errors[0]
        raise ValueError('Schema '+ '/'.join(map(str,err.absolute_path))+': '+err.message)
    def finite(v):
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError('Non-finite numbers are forbidden')
        if isinstance(v, dict):
            for x in v.values(): finite(x)
        if isinstance(v, list):
            for x in v: finite(x)
    finite(command)
    action = command['action']
    if command.get('monolithic') and action != 'create_part':
        raise ValueError('monolithic is only supported for create_part; input appearances/history are never silently discarded')
    if action == 'inspect' and any(command.get(k) for k in ('monolithic','appearances','expected_size_mm')):
        raise ValueError('inspect cannot finish geometry')
    if action == 'create_assembly' and (command.get('appearances') or command.get('expected_size_mm')):
        raise ValueError('Part finishing options cannot be used on assemblies')
    appearance=command.get('appearances')
    if appearance:
        names=[p['name'] for p in appearance['palette']]
        if len(set(names)) != len(names): raise ValueError('Duplicate appearance name')
        if appearance.get('base') and appearance['base'] not in names: raise ValueError('Unknown base appearance')
        for region in appearance.get('regions',[]):
            if region['appearance'] not in names: raise ValueError('Unknown region appearance')
            if any(a>b for a,b in zip(region['box_mm']['min'],region['box_mm']['max'])): raise ValueError('Inverted appearance box')
            if region.get('min_faces',1)>region.get('max_faces',1000000): raise ValueError('Invalid face count range')
    if action in ('modify','inspect') and not command.get('input'):
        raise ValueError('input is required')
    if action != 'inspect' and not command.get('output'):
        raise ValueError('output is required; overwriting is forbidden')
    if action == 'inspect' and (command['operations'] or command.get('parameters') or command.get('exports') or command.get('snapshot')):
        raise ValueError('inspect cannot mutate or export')
    for m in command.get('observations',[]):
        if m['status'] == 'unknown' or m['value'] is None:
            raise ValueError('Reference measurement required: '+m['name'])
        if m['status'] == 'estimated' and not command.get('allow_estimates',False):
            raise ValueError('Estimated measurement requires allow_estimates: '+m['name'])
        if m['name'] in command.get('parameters',{}) and m['value'] != command['parameters'][m['name']]:
            raise ValueError('Measurement and parameter disagree: '+m['name'])
    seen = set()
    reference_fields = ('base','plane','sketch','axis','entity','entities','edges','features','first','second')
    builtin = {'XY','XZ','YZ','X','Y','Z'}
    for op in command['operations']:
        if op['id'] in seen: raise ValueError('Duplicate operation id: '+op['id'])
        if op['id'] in op['depends_on']: raise ValueError('Self dependency')
        if not set(op['depends_on']) <= seen: raise ValueError('Dependencies must precede operation')
        for key in reference_fields:
            values = op.get(key, [])
            if isinstance(values,str): values=[values]
            for value in values:
                root=value.split('/')[0]
                if root not in builtin and root not in op['depends_on']:
                    # persisted reference namespace explicitly distinguishes earlier documents
                    if not (action == 'modify' and root.startswith('@')):
                        raise ValueError(f'{op["id"]}: reference {value} must declare dependency')
        if op['type']=='sketch':
            ids=[g['id'] for g in op['geometry']]
            if len(ids)!=len(set(ids)): raise ValueError('Duplicate geometry id')
        if op['type']=='constraint':
            n=1 if op['kind'] in ('horizontal','vertical') else 2
            if len(op['entities'])!=n: raise ValueError('Incorrect constraint arity')
        if action=='create_assembly' and op['type'] not in ('occurrence','assembly_constraint','set_parameter'):
            raise ValueError('Part operation in assembly command')
        if action=='create_part' and op['type'] in ('occurrence','assembly_constraint'):
            raise ValueError('Assembly operation in part command')
        seen.add(op['id'])
    return command

class Workspace:
    def __init__(self, root): self.root=Path(root).resolve()
    def path(self, name, suffixes=None, existing=False):
        p=(self.root/name).resolve()
        if not p.is_relative_to(self.root): raise ValueError('Path outside workspace')
        if suffixes and p.suffix.lower() not in suffixes: raise ValueError('Invalid file extension')
        if existing and not p.is_file(): raise ValueError('Input file does not exist')
        if not existing and p.exists(): raise ValueError('Refusing to overwrite existing output')
        return p
