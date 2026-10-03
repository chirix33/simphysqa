"""Independent passive-motion bounds using observed inputs, not oracle endpoints."""
from ..contracts import ScenarioInput

CHECK_NAMES = ("speed_nonnegative", "no_speed_gain", "no_reverse_displacement", "reachable_displacement")


def passive_checks(scenario: ScenarioInput, values: tuple[float, ...]) -> list[dict] | None:
    facts = {fact.quantity_id: fact for fact in scenario.initial_facts}
    if (len(facts) != len(scenario.initial_facts) or not {"x0", "v0"} <= facts.keys()
            or facts["x0"].unit != "m" or facts["v0"].unit != "m/s"
            or type(facts["x0"].value) is not float or type(facts["v0"].value) is not float
            or facts["v0"].value < 0 or tuple(o.quantity_id for o in scenario.observables) != ("x", "v")
            or tuple(o.unit for o in scenario.observables) != ("m", "m/s")
            or any(not o.output_mask for o in scenario.observables)):
        return None
    x0, v0 = facts["x0"].value, facts["v0"].value
    x, v = values
    tolerances = (scenario.observables[1].absolute_tolerance,) * 2 + (scenario.observables[0].absolute_tolerance,) * 2
    excesses = (-v, v - v0, x0 - x, x - x0 - v0 * scenario.horizon)
    return [{"name": name, "violated": excess > tolerance, "excess": max(0.0, excess),
             "tolerance": tolerance, "unit": "m/s" if index < 2 else "m"}
            for index, (name, excess, tolerance) in enumerate(zip(CHECK_NAMES, excesses, tolerances))]
