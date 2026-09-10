"""Parsing ISCF (Intel Schematic Connectivity Format).

Sekce: BEGIN_COMPPROPS, BEGIN_NETS, BEGIN_GROUND, BEGIN_POWER (BEGIN_BUSES a BEGIN_COMPPINS /
BEGIN_E-NETS nepoužíváme — viz Description.md kap. 2.1).

Hlavička řádku BEGIN_COMPPROPS (13 polí za ``RefDes:``, oddělovač ','):
  partName,partNumber,noMount,tolerance,value,maxV,powerDiss,maxP,elec_type,enetNonSeries,
  componentKind,power_supply,compComment
  - ``partName`` = A5E; ``componentKind`` = kód Function Type
    (číselník viz skills/cr8000-power-domain/SKILL.md).
  - ``power_supply`` = "VCC=P3V3;GND=GND" (interní název pinu -> rail/net); prázdné pole
    není chyba (jiný způsob připojení ve schématu).

Sekce BEGIN_POWER / BEGIN_NETS / BEGIN_GROUND mají shodný formát řádku:
  Name:RefDes(pin:pinLabel),RefDes(pin:pinLabel),...;   (prázdný seznam: "Name:;")

Viz Description.md kap. 2.1 a skills/cr8000-power-domain/SKILL.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# RefDes(pin:pinLabel) — hledáno přes celý řetězec entries (odolné vůči případným
# neočekávaným čárkám uvnitř pole; separátorem mezi entries je jinak ',').
_ENTRY_RE = re.compile(r"([^,()]+)\(([^:()]+):([^()]*)\)")


@dataclass
class CompProps:
    """Jeden řádek BEGIN_COMPPROPS (per RefDes)."""

    refdes: str
    a5e: str
    component_kind: int
    power_supply: dict[str, str] = field(default_factory=dict)
    comp_comment: str = ""


@dataclass
class Pin:
    """Jedno připojení ``RefDes(pin:pinLabel)`` v sekci POWER/NETS/GROUND."""

    refdes: str
    pin: str
    pin_label: str


def _extract_section(text: str, name: str) -> list[str]:
    """Vrátí datové řádky mezi ``BEGIN_<name>`` a ``END_<name>`` (bez '#' hlaviček)."""
    lines = text.splitlines()
    begin, end = f"BEGIN_{name}", f"END_{name}"
    try:
        start = lines.index(begin)
        stop = lines.index(end, start)
    except ValueError:
        return []
    return [
        ln for ln in lines[start + 1 : stop] if ln.strip() and not ln.lstrip().startswith("#")
    ]


def _parse_power_supply(field_value: str) -> dict[str, str]:
    """``"VCC=P3V3;GND=GND"`` -> ``{"VCC": "P3V3", "GND": "GND"}``. Prázdné -> ``{}``."""
    result: dict[str, str] = {}
    for part in field_value.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, val = part.partition("=")
        result[key.strip()] = val.strip()
    return result


def parse_compprops(text: str) -> dict[str, CompProps]:
    """RefDes -> CompProps ze sekce BEGIN_COMPPROPS."""
    result: dict[str, CompProps] = {}
    for line in _extract_section(text, "COMPPROPS"):
        refdes, sep, rest = line.partition(":")
        refdes = refdes.strip()
        if not sep or not refdes:
            continue
        fields = rest.split(",", 12)
        fields += [""] * (13 - len(fields))  # doplnit případná chybějící koncová pole
        a5e = fields[0].strip()
        kind_raw = fields[10].strip()
        try:
            component_kind = int(kind_raw)
        except ValueError:
            component_kind = -1
        result[refdes] = CompProps(
            refdes=refdes,
            a5e=a5e,
            component_kind=component_kind,
            power_supply=_parse_power_supply(fields[11]),
            comp_comment=fields[12].strip(),
        )
    return result


def _parse_pin_list_section(text: str, name: str) -> dict[str, list[Pin]]:
    """Společný parser pro POWER/NETS/GROUND: ``Name:RefDes(pin:pinLabel),...;``."""
    result: dict[str, list[Pin]] = {}
    for line in _extract_section(text, name):
        rail, sep, rest = line.partition(":")
        rail = rail.strip()
        if not sep or not rail:
            continue
        entries = rest.strip().rstrip(";")
        result[rail] = [
            Pin(refdes=m.group(1).strip(), pin=m.group(2).strip(), pin_label=m.group(3).strip())
            for m in _ENTRY_RE.finditer(entries)
        ]
    return result


def parse_power(text: str) -> dict[str, list[Pin]]:
    """Rail -> [Pin, ...] ze sekce BEGIN_POWER (hlavní zdroj railů a jejich pinů)."""
    return _parse_pin_list_section(text, "POWER")


def parse_nets(text: str) -> dict[str, list[Pin]]:
    """NetName -> [Pin, ...] ze sekce BEGIN_NETS (signálové nety; pro trasování topologie)."""
    return _parse_pin_list_section(text, "NETS")


def parse_ground(text: str) -> dict[str, list[Pin]]:
    """NetName -> [Pin, ...] ze sekce BEGIN_GROUND (zemní nety)."""
    return _parse_pin_list_section(text, "GROUND")
