"""Version policy is deliberately distinct from evidence of real testing."""
MIN_YEAR = 2017
LAST_REVIEWED_YEAR = 2027
TESTED_YEARS = {2022}


def version_info(major, display, expected_year=None, allow_future=False):
    year = int(major) + 1996
    if expected_year is not None and year != expected_year:
        raise RuntimeError(f'Expected Inventor {expected_year}; attached to {year}. '
                           'Close other Inventor instances and start the intended release.')
    if year < MIN_YEAR:
        raise RuntimeError(f'Inventor {year} is below the API baseline {MIN_YEAR}.')
    if year > LAST_REVIEWED_YEAR and not allow_future:
        raise RuntimeError(f'Inventor {year} is newer than the reviewed API range. '
                           'Set AI_CAD_ALLOW_FUTURE=1 only for explicit compatibility testing.')
    level = 'tested' if year in TESTED_YEARS else 'api_candidate' if year <= LAST_REVIEWED_YEAR else 'experimental'
    return {'year': year, 'major': int(major), 'display': str(display), 'support': level,
            'warnings': [] if level == 'tested' else [
                f'Inventor {year}: not live-tested by this release; run the compatibility suite.']}


def require_member(obj, name, label):
    try:
        value = getattr(obj, name)
    except Exception as exc:
        raise RuntimeError(f'Required Inventor API unavailable: {label}.{name}') from exc
    return value


def preflight(engine, command):
    """Probe actual installed COM members before starting the edit transaction."""
    groups = {
        'extrude': ('ExtrudeFeatures', 'CreateExtrudeDefinition'),
        'revolve': ('RevolveFeatures', 'AddByAngle'),
        'hole': ('HoleFeatures', 'CreateSketchPlacementDefinition'),
        'fillet': ('FilletFeatures', 'AddSimple'),
        'chamfer': ('ChamferFeatures', 'AddUsingDistance'),
        'linear_pattern': ('RectangularPatternFeatures', 'CreateDefinition'),
        'circular_pattern': ('CircularPatternFeatures', 'CreateDefinition'),
        'mirror': ('MirrorFeatures', 'CreateDefinition'),
    }
    for op in command['operations']:
        if op['type'] in groups:
            group, method = groups[op['type']]
            features = require_member(engine.cd, 'Features', 'ComponentDefinition')
            collection = require_member(features, group, 'Features')
            require_member(collection, method, group)
    if command.get('monolithic'):
        require_member(engine.cd.Features.NonParametricBaseFeatures, 'AddByDefinition', 'NonParametricBaseFeatures')
    if command.get('appearances'):
        require_member(engine.doc, 'Assets', 'Document')
