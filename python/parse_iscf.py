"""Parsing ISCF (Intel Schematic Connectivity Format).

Sekce: BEGIN_COMPPROPS, BEGIN_NETS, BEGIN_GROUND, BEGIN_POWER.
Stub — implementace navazuje po rozhodnutí formátu power_map. Viz Description.md.
"""


def parse_compprops(text: str) -> dict:
    """RefDes -> {a5e, component_kind, power_supply, value, ...}. TODO."""
    raise NotImplementedError


def parse_power(text: str) -> dict:
    """rail -> [(refdes, pin, pin_label), ...] ze sekce BEGIN_POWER. TODO."""
    raise NotImplementedError
