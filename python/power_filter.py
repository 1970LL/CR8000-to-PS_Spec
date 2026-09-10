"""Inteligentní filtr spotřeby (preprocessing -A-, Description.md kap. 6).

Klasifikuje součástky do tří stavů dle ``component_kind`` (Function Type, číselník viz
``skills/cr8000-power-domain/SKILL.md``) + BOM atributu ``value``:

- ``PASS`` (✅)  — reálný spotřebič, počítá se do sumy proudů railu (krok 5).
- ``SKIP`` (⛔)  — zanedbatelná/nulová spotřeba (blokovací kondenzátory, pull-up/down
  rezistory, testpointy, antény, propojky…).
- ``NODE`` ("uzel") — blok toku energie, ne prostý spotřebič (LDO/DC-DC, pojistky, cívky/
  feritové perly, konektory s externí zátěží, transformátory/měniče…); zpracuje se
  samostatně v ``build_power_tree.py`` (krok 6-7), nesčítá se jako spotřebič v kroku 5.

Filtr je konfigurovatelný přes ``FilterConfig`` (lze vypnout, přepsat výchozí klasifikaci
dle kódu, změnit práh "malého" sériového rezistoru). Vyfiltrované (⛔) položky se v HTML
nemažou, jen dostanou CSS třídu ``skip`` — zobrazení/potlačení řeší toolbar tlačítko
(viz ``build_power_map.py``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PASS = "✅"
SKIP = "⛔"
NODE = "uzel"

# component_kind (int, Function Type dle ISCF BEGIN_COMPPROPS) -> výchozí klasifikace.
# Zdroj: skills/cr8000-power-domain/SKILL.md, sloupec "Filtr (výchozí)".
KIND_DEFAULT: dict[int, str] = {
    12: NODE,   # Power box
    101: PASS,  # Sestava/modul (dle obsahu — defaultně PASS, HITL upřesní)
    102: PASS,  # Krystaly/oscilátory (malý spotřebič)
    103: SKIP,  # Kondenzátory (blokovací)
    104: PASS,  # Digitální IO
    106: NODE,  # Pojistky (sériový prvek)
    107: NODE,  # Power supply unit
    108: PASS,  # LED/žárovky (spotřebič)
    111: PASS,  # Relé (cívka)
    112: NODE,  # Cívky/tlumivky (feritové perly — sériový prvek)
    114: PASS,  # Analogové IO
    116: SKIP,  # Testpointy
    117: PASS,  # Ostatní (dle obsahu — defaultně PASS, HITL upřesní)
    118: SKIP,  # Rezistory — výchozí pull-up/down; "malý" sériový -> NODE (viz níže)
    119: PASS,  # Spínače (dle obsahu — defaultně PASS)
    120: NODE,  # Transformátory/měniče
    121: PASS,  # Optočleny
    122: PASS,  # Diody/tranzistory (dle role — defaultně PASS, HITL upřesní)
    123: SKIP,  # Antény
    124: NODE,  # Konektory (externí zátěž -> Ext_loads.md)
    126: NODE,  # Filtry (EMI)
    128: SKIP,  # Propojky (star points) — zkrat, ne spotřebič
}

_RESISTOR_KIND = 118
_RESISTOR_RE = re.compile(r"^(\d*)([RKM])(\d*)$")


@dataclass
class FilterConfig:
    """Konfigurace filtru (kap. 6: zapnout/vypnout, práh malého rezistoru, přepisy)."""

    enabled: bool = True
    small_resistor_max_ohm: float = 10.0
    kind_overrides: dict[int, str] = field(default_factory=dict)


DEFAULT_CONFIG = FilterConfig()


def _parse_resistor_ohms(value: str) -> float | None:
    """BOM ``Value`` rezistoru -> ohmy. ``"10R"``->10.0, ``"4K7"``->4700.0, ``"1M"``->1e6."""
    if not value:
        return None
    m = _RESISTOR_RE.match(value.strip().upper())
    if not m:
        try:
            return float(value)
        except ValueError:
            return None
    whole, unit, frac = m.groups()
    num = float(f"{whole or '0'}.{frac or '0'}")
    mult = {"R": 1.0, "K": 1e3, "M": 1e6}[unit]
    return num * mult


def classify_power_state(entry: dict, config: FilterConfig | None = None) -> str:
    """Vrátí ``PASS``/``SKIP``/``NODE`` dle ``entry['component_kind']`` (+ ``entry['value']``).

    ``entry`` potřebuje klíč ``component_kind`` (int dle ISCF, může být ``None``/chybět)
    a volitelně ``value`` (BOM Value — rozliší u rezistorů pull-up/down od "malého"
    sériového rezistoru). Vypnutý filtr (``config.enabled=False``) vrací vždy ``PASS``
    (nic se nefiltruje, kap. 6: "filtr lze zapnout/vypnout").
    """
    cfg = config or DEFAULT_CONFIG
    if not cfg.enabled:
        return PASS
    kind = entry.get("component_kind")
    state = cfg.kind_overrides.get(kind, KIND_DEFAULT.get(kind, PASS))
    if kind == _RESISTOR_KIND and state == SKIP:
        ohms = _parse_resistor_ohms(entry.get("value", ""))
        if ohms is not None and ohms <= cfg.small_resistor_max_ohm:
            state = NODE
    return state


def apply_power_filter(rows: list, compprops: dict, config: FilterConfig | None = None) -> None:
    """Doplní ``power_state`` do každého řádku power_map (in-place).

    ``rows``: list ``PowerMapRow`` (viz ``build_power_map.py``) — používá ``.refdes`` a
    ``.value``. ``compprops``: dict RefDes -> ``CompProps`` (viz ``parse_iscf.py``) —
    zdroj ``component_kind``.
    """
    for row in rows:
        cp = compprops.get(row.refdes)
        kind = cp.component_kind if cp else None
        row.power_state = classify_power_state({"component_kind": kind, "value": row.value}, config)
