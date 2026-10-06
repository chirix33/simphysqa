"""Deterministic shared event prose from public definitions/validated profiles only."""
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from .dataset import pointer
from .events import dec, signatures

RENDERER_VERSION = 'simphysqa-event-description/1.0.1'
DISPLAY_VERSION = 'decimal-six-significant-half-even/1.0.0'
FIELDS = ('event_description', 'event_description_bindings', 'event_description_status')

def versions():
    return {'event_description_renderer_version': RENDERER_VERSION,
            'event_description_renderer_sha256': sha256(Path(__file__).read_text(encoding='utf-8').encode()).hexdigest(),
            'event_description_display_version': DISPLAY_VERSION,
            'event_description_semantics': signatures()}

def number(value):
    """Presentation only: six significant digits, half even; never for matching."""
    value = value if isinstance(value, Decimal) else dec(value)
    if not value.is_finite():
        raise ValueError('nonfinite display value')
    if value == 0:
        return '0'
    # Decimal.__format__ uses the default ROUND_HALF_EVEN (explicit local context).
    from decimal import localcontext, ROUND_HALF_EVEN
    with localcontext() as context:
        context.rounding = ROUND_HALF_EVEN
        text = format(value, '.6g')
    mantissa, marker, exponent = text.lower().partition('e')
    if '.' in mantissa:
        mantissa = mantissa.rstrip('0').rstrip('.')
    return mantissa + ('e' + str(int(exponent)) if marker else '')

def interval(start, end):
    return f'[{number(start)}, {number(end)}) s'

def render(inp, descriptor, index):
    """One canonical annotation, no timestamps/measurements/private data needed."""
    event = inp['known_events'][index]
    if descriptor['event_id'] != event['event_id']:
        raise ValueError('description event identity mismatch')
    base = f'/known_events/{index}'
    bindings = [base + '/' + key for key in ('event_id', 'type', 'start_time', 'end_time')]
    bindings += [base + f'/parameters/{j}' for j in range(len(event['parameters']))]
    profile = descriptor['controller']
    kind = profile['kind']
    timing = interval(event['start_time'], event['end_time'])
    status = 'supported_declared_semantics'
    text = []
    def parameter(name):
        paths = [p for p in profile['bindings'] if p.startswith('/controller/parameters/')]
        return next(pointer(inp, p) for p in paths if pointer(inp, p)['name'] == name)
    if kind != 'unresolved_declared_law':
        bindings += profile['bindings']
    if kind == 'additive_joint_torque':
        mag = event['parameters'][0]
        text.append(f"Declared additive torque pulse on direct target joint_1: +{number(mag['value'])} {mag['unit']} during {timing}; this is an increment, not total or verified applied torque. Event magnitude frame: {mag['frame']}.")
        for j, control in enumerate(inp['controller']['controls']):
            if control['entity_id'] == 'joint_1' and control['channel'] == 'applied_torque':
                bindings.append(f'/controller/controls/{j}')
                text.append(f"Separate declared base torque: {number(control['value'])} {control['unit']} in {control['frame']} during {interval(control['start_time'], control['end_time'])}.")
                if control['frame'] != mag['frame']:
                    status = 'limited_unresolved_semantics'
                    text.append('The relationship between the event and base-control frames is unresolved; no frame conversion or total torque is inferred.')
    elif kind == 'brake_torque_limit':
        p = parameter('brake_torque_limit')
        text.append(f"Declared zero-velocity braking of direct target car on each axle during {timing}, opposing wheel motion, with maximum torque limit {number(p['value'])} {p['unit']} (declared parameter frame: {p['frame']}; event magnitude frame: {event['parameters'][0]['frame']}). The limit does not specify realized braking torque.")
    elif kind == 'force_at_center_of_mass':
        p = parameter('force')
        text.append(f"Declared +x force on direct target block_1 at its instantaneous center of mass during {timing}: {number(p['value'])} {p['unit']} in {p['frame']} (event magnitude frame: {event['parameters'][0]['frame']}). The declared controller supplies no force outside this interval; this does not establish that physical effects have ended.")
    elif kind == 'support_acceleration_phases':
        p = parameter('acceleration')
        text.append(f"Declared x-direction acceleration of direct target support during {timing}, with magnitude {number(p['value'])} {p['unit']} in {p['frame']} (event magnitude frame: {event['parameters'][0]['frame']}).")
        for phase in profile['phases']:
            bindings += phase['bindings']
            signed = ('+' if phase['value'] > 0 else '') + number(phase['value'])
            text.append(f"Declared {'positive' if phase['value'] > 0 else 'negative'} phase: {signed} {phase['unit']} during {interval(Decimal(phase['start_time_decimal']), Decimal(phase['end_time_decimal']))}.")
        text.append('The controller declares continuous support position and velocity, zero support position/velocity before onset and a stationary support afterward; load motion or causal effects are not asserted.')
    else:
        if descriptor['temporal_semantics'] == 'declared_point':
            text.append(f"Declared point event {event['type']} at {number(event['start_time'])} s: {descriptor['point_definition']}. This is a readout event, not a scheduled intervention; no direct intervention target is assigned.")
        else:
            status = 'limited_unresolved_semantics'
            scope = ', '.join(descriptor['target_entity_ids'])
            if descriptor['temporal_semantics'] == 'half_open_interval':
                bindings += profile['bindings'] + ['/controller/equations']
                text.append(f"Declared scheduled intervention on direct target(s) {scope or 'unspecified'} during {timing}. The action/application law is unresolved; no direction, applied value or phases are inferred.")
            else:
                text.append(f"Declared event type {event['type']}, source start {number(event['start_time'])} s and end {number(event['end_time'])} s. Temporal and application semantics are unresolved; no active interval or direct intervention target is inferred.")
        for p in event['parameters']:
            from .io import canonical
            value = number(p['value']) if type(p['value']) in (int, float) else canonical(p['value']).decode().strip()
            text.append(f"Declared parameter {p['name']} for {p['entity_id']}: {value} {p['unit']} (source frame: {p['frame']}); parameter scope is not evidence of physical application.")
    unknown_frames = {'unknown', 'unspecified', 'unresolved', ''}
    frames = [p['frame'] for p in event['parameters']]
    for binding in bindings:
        value = pointer(inp, binding)
        if isinstance(value, dict) and 'frame' in value:
            frames.append(value['frame'])
    if any(frame.lower() in unknown_frames for frame in frames):
        status = 'limited_unresolved_semantics'
        text.append('A declared parameter/control frame is unresolved and has not been inferred.')
    bindings = sorted(set(bindings))
    for binding in bindings:
        if binding.startswith('/states/'):
            raise ValueError('shared descriptions cannot use state-specific evidence')
        pointer(inp, binding)
    return {'event_description': ' '.join(text), 'event_description_bindings': bindings,
            'event_description_status': status}
