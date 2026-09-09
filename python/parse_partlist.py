"""Parsing Partlist (Testway BOM), oddělovač '|'.

Hlavička: ARTIKEL|EPL|TYPE|COMMENT|Value|Tolerance|Voltage
Pozor na kódování/diakritiku (COMMENT: '+95A??C' -> '+95°C').
Stub — implementace navazuje. Viz Description.md.
"""


def parse_partlist(text: str) -> dict:
    """RefDes(EPL) -> {a5e, type, item, value, tolerance, voltage}. TODO."""
    raise NotImplementedError
