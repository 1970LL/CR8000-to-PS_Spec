"""Sumy spotřeb, přepočet energetických toků a generování power_tree.

Kroky 5–7: sumy ds_curr po railech, přepočet přes měniče (účinnost),
export Mermaid (.mmd) a draw.io (.drawio). Viz Description.md kap. 11.
Stub — implementace navazuje.
"""


def sum_rail_currents(entries: list) -> dict:
    """rail -> {sum_curr_max_mA, sum_curr_typ_mA} (jen PASS položky). TODO."""
    raise NotImplementedError


def build_power_tree(entries: list, ext_loads: list, threshold_mA: float = 30.0) -> str:
    """Vygeneruje Mermaid diagram napájecí soustavy. TODO."""
    raise NotImplementedError
