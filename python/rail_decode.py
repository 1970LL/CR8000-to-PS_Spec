"""Dekódování napětí railu (rail_v).

Strategie v pořadí priorit (Description.md kap. 5):
  1. Konvence ``PxVy`` v názvu -> deterministicky (``P5``->5V, ``P3V3``->3.3V, ``P0V85``->0.85V).
  2. Prefix/suffix konvence i ve složitějších názvech (``NVCC_BBSM_P1V8``->1.8V,
     ``SNVS_P0V8``->0.8V, ``VDDIO_P1V8``->1.8V, ``P5_USB``->5V).
  3. Trasování topologie pro názvy bez konvence (např. ``VDDAH_PHY``) -- NEIMPLEMENTOVÁNO
     (MVP dle repo-memory next-steps: jen konvence, viz body 1-2). Otevřený bod pro další krok.
  4. Dotaz na uživatele, pokud vazba není nalezena / není deterministická (např. ``VDD2``,
     ``VDDQ``) -- systém nehádá. V MVP se takové raily nechají prázdné (``rail_v == ""``) pro
     doplnění uživatelem při HITL kontrole.
"""

from __future__ import annotations

import re

# Token oddělený '_', který přesně odpovídá tvaru P<int> nebo P<int>V<int>.
_TOKEN_RE = re.compile(r"^P(\d+)(?:V(\d+))?$")


def decode_rail_voltage(rail_name: str) -> tuple[float | None, str]:
    """Vrátí ``(napětí ve V, metoda)`` dle konvence ``PxVy`` (kap. 5, body 1-2).

    Název railu se rozdělí na tokeny podle ``_`` a hledá se token přesně ve tvaru
    ``P<int>`` (např. ``P5``, ``P24``) nebo ``P<int>V<int>`` (např. ``P3V3``, ``P0V85``).
    Konvence se uplatní jak pro prostý název, tak jako prefix/suffix ve složitějším názvu.

    Je-li nalezen právě jeden takový token -> ``(hodnota, "convention")``.
    Jinak (žádný token / víc nejednoznačných kandidátů) -> ``(None, "")`` -- vyžaduje
    trasování topologie (bod 3) nebo dotaz na uživatele (bod 4); systém nehádá.
    """
    if not rail_name:
        return None, ""
    matches = [m for token in rail_name.split("_") if (m := _TOKEN_RE.match(token))]
    if len(matches) != 1:
        return None, ""
    int_part, frac = matches[0].groups()
    value = float(int_part)
    if frac:
        value += int(frac) / (10 ** len(frac))
    return value, "convention"


def format_voltage(value: float) -> str:
    """Formátuje napětí pro zápis do sloupce ``rail_v`` (bez zbytečných nul: ``3.3``, ``5``)."""
    return f"{value:g}"


def decode_rails(rail_names) -> dict[str, tuple[float | None, str]]:
    """Dekóduje kolekci názvů railů -> dict ``rail -> (hodnota, metoda)``."""
    return {name: decode_rail_voltage(name) for name in rail_names}


def apply_rail_decode(rows) -> None:
    """Doplní ``PowerMapRow.rail_v`` pro řádky, jejichž rail lze dekódovat dle konvence.

    Nedekódovatelné raily (nutné trasování topologie nebo dotaz na uživatele, kap. 5
    body 3-4 -- zatím neimplementováno) zůstávají prázdné, k doplnění při HITL kontrole.
    Přijímá libovolné objekty s atributy ``rail``/``rail_v`` (typicky ``PowerMapRow``).
    """
    cache: dict[str, tuple[float | None, str]] = {}
    for row in rows:
        if row.rail not in cache:
            cache[row.rail] = decode_rail_voltage(row.rail)
        value, _method = cache[row.rail]
        if value is not None:
            row.rail_v = format_voltage(value)
