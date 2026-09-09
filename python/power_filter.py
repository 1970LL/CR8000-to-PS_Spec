"""Inteligentní filtr spotřeby (preprocessing -A-).

Označí zanedbatelné součástky (blokovací C, pull-up/down R) jako SKIP (⛔),
ostatní jako PASS (✅). Primární signál: component_kind + BOM. Konfigurovatelné.
Viz Description.md kap. 6. Stub — implementace navazuje.
"""


def classify_power_state(entry: dict, config: dict) -> str:
    """Vrátí 'PASS' nebo 'SKIP'. TODO (číselník component_kind — otevřený bod)."""
    raise NotImplementedError
