"""Dekódování napětí railu (rail_v).

Strategie: 1) konvence PxVy, 2) prefix/suffix konvence, 3) trasování topologie,
4) dotaz na uživatele. Systém nehádá. Viz Description.md kap. 5.
Stub — implementace navazuje.
"""


def decode_rail_voltage(rail_name: str) -> float | None:
    """Vrátí napětí [V] dle konvence PxVy, nebo None (nutné trasování/dotaz). TODO."""
    raise NotImplementedError
