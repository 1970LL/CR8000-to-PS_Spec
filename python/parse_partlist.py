"""Parsing Partlist (Siemens Testway BOM), oddělovač '|'.

Hlavička: ARTIKEL|EPL|TYPE|COMMENT|Value|Tolerance|Voltage
- ARTIKEL -> a5e     (stabilní unikátní identifikátor komponenty)
- EPL     -> refdes  (B1, C1, D10, ...)
- TYPE    -> mpn/pouzdro (u IC bývá čisté MPN, u pasiv pouzdro; může být prázdné/nesmysl)
- COMMENT -> lidský Team Center název (KIND_..._package); zdroj klíče i labelu
- Value / Tolerance / Voltage: u pasiv vyplněné, u IC bývají prázdné

Klíč komponenty (per A5E): ``A5E<num>__<SLUG(COMMENT)>``. A5E nese unikátnost a řazení,
SLUG(COMMENT) je lidsky čitelný label. Fallback: COMMENT prázdný -> SLUG(TYPE) -> holé A5E.

Viz Description.md a diskuzi o pojmenování katalogu datasheetů.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SLUG_LIMIT = 48


@dataclass
class PartRow:
    """Jeden řádek Partlistu (per RefDes)."""

    a5e: str
    refdes: str
    type: str
    comment: str
    value: str = ""
    tolerance: str = ""
    voltage: str = ""


@dataclass
class Component:
    """Unikátní komponenta sloučená per A5E."""

    a5e: str
    mpn: str
    kind: str
    comment: str
    key: str
    refdes: list[str] = field(default_factory=list)

    @property
    def qty(self) -> int:
        return len(self.refdes)


def slugify(text: str, limit: int = SLUG_LIMIT) -> str:
    """ASCII slug: velká písmena, ne-[A-Z0-9] -> '_', sloučit '_', ořez na limit."""
    if not text:
        return ""
    s = re.sub(r"[^A-Z0-9]+", "_", text.upper())
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > limit:
        s = s[:limit].rstrip("_")
    return s


def comment_kind(comment: str) -> str:
    """KIND = vedoucí čistě alfabetické tokeny COMMENT (fazeta pro filtrování).

    ``IC_INTERFACE_74LVC244_...`` -> ``IC_INTERFACE``; ``CAP_CER_VS_0402_...`` -> ``CAP_CER_VS``.
    """
    slug = slugify(comment, limit=64)
    if not slug:
        return ""
    leading: list[str] = []
    for tok in slug.split("_"):
        if tok.isalpha():
            leading.append(tok)
        else:
            break
    return "_".join(leading) if leading else slug.split("_")[0]


def component_key(a5e: str, comment: str, type_: str) -> str:
    """``A5E<num>__<SLUG(COMMENT)>``; fallback SLUG(TYPE) -> holé A5E."""
    label = slugify(comment) or slugify(type_)
    return f"{a5e}__{label}" if label else a5e


# --- Function Type (CR8000 Design Editor) -----------------------------------------
# Prefix RefDes (písmeno) -> (kód componentKind, lidský štítek skupiny).
# Zdroj: skills/cr8000-power-domain/SKILL.md (ověřeno křížovou kontrolou proti ISCF).
# Partlist neobsahuje componentKind, proto ho odvozujeme z prefixu RefDes.
FUNCTION_TYPE: dict[str, tuple[int, str]] = {
    "A": (101, "Sestava"),
    "B": (102, "Krystal/Osc"),
    "C": (103, "Kondenzátor"),
    "D": (104, "Digitální IO"),
    "F": (106, "Pojistka"),
    "G": (107, "Napájení/Osc"),
    "H": (108, "LED/Žárovka"),
    "K": (111, "Relé"),
    "L": (112, "Cívka/Tlumivka"),
    "N": (114, "Analogové IO"),
    "P": (116, "Testpoint"),
    "Q": (117, "Ostatní"),
    "R": (118, "Rezistor"),
    "S": (119, "Spínač"),
    "T": (120, "Transformátor/Měnič"),
    "U": (121, "Optočlen"),
    "V": (122, "Dioda/Tranzistor"),
    "W": (123, "Anténa"),
    "X": (124, "Konektor"),
    "Z": (126, "Filtr"),
    "WS": (128, "Propojka"),
}


def refdes_prefix(refdes: str) -> str:
    """Vedoucí abecední část RefDes (velká písmena). ``R100`` -> ``R``; ``WS1`` -> ``WS``."""
    m = re.match(r"[A-Za-z]+", refdes or "")
    return m.group(0).upper() if m else ""


def function_type(refdes: str) -> tuple[int, str]:
    """Odvodí Function Type (kód, štítek) z prefixu RefDes. Neznámý -> (999, '?')."""
    pref = refdes_prefix(refdes)
    if pref in FUNCTION_TYPE:
        return FUNCTION_TYPE[pref]
    if pref[:1] in FUNCTION_TYPE:
        return FUNCTION_TYPE[pref[:1]]
    return (999, "?")


def parse_partlist(text: str) -> list[PartRow]:
    """Řádky Partlistu -> list PartRow. Komentáře '#' a prázdné řádky se ignorují."""
    rows: list[PartRow] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("|")
        parts += [""] * (7 - len(parts))  # doplnit chybějící pole
        a5e, refdes, type_, comment, value, tol, voltage = (p.strip() for p in parts[:7])
        if not a5e:
            continue
        rows.append(PartRow(a5e, refdes, type_, comment, value, tol, voltage))
    return rows


def aggregate_components(rows: list[PartRow]) -> list[Component]:
    """Sloučí řádky na unikátní komponenty per A5E (stejné A5E = stejná komponenta)."""
    by_a5e: dict[str, Component] = {}
    for r in rows:
        comp = by_a5e.get(r.a5e)
        if comp is None:
            comp = Component(
                a5e=r.a5e,
                mpn=r.type,
                kind=comment_kind(r.comment),
                comment=r.comment,
                key=component_key(r.a5e, r.comment, r.type),
            )
            by_a5e[r.a5e] = comp
        if r.refdes:
            comp.refdes.append(r.refdes)
    return sorted(by_a5e.values(), key=lambda c: c.a5e)
