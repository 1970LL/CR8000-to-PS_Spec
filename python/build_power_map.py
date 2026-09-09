"""Sestavení power_map: spojení ISCF + Partlist dle RefDes + křížová kontrola railů.

Vstup: výstupy parse_iscf + parse_partlist.
Výstup: power_map_xx (formát dle rozhodnutí — MD/XML, viz samples/).
Stub — implementace navazuje. Viz Description.md.
"""


def build_power_map(iscf_power: dict, compprops: dict, partlist: dict) -> list:
    """Vrátí seznam záznamů (RefDes, Rail, Pin) s dohledanými atributy. TODO."""
    raise NotImplementedError
