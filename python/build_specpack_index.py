"""DEPRECATED driver: per-DATASHEET (`--per-doc`) build/index SpecPack indexu.

⚠  NEPOUŽÍVAT PRO NOVÉ BĚHY. Nahrazeno per-KOMPONENTNÍM driverem
    ``build_datasheet_workspaces.py`` (1 workspace = 1 A5E komponenta, čistá jména
    ``A5E<num>__<SLUG(COMMENT)>``). ``--per-doc`` vyráběl ošklivá lit-number jména
    (JESD36, SLLS413, …), která jsme opustili.

Tento modul zůstává jen kvůli **znovupoužitelným symbolům**, které importuje nový
driver: ``DEFAULT_COMPONENTS``, ``DEFAULT_ROOT``, ``DEFAULT_CONFIG``,
``resolve_specpack()`` a ``run()``. Spouštění ``main()`` je záměrně ponecháno funkční
pro nouzové případy, ale vypíše varování.

Určeno ke spouštění z terminálu — nepotřebuje žádný jazykový model.

Použití (DEPRECATED):
    python build_specpack_index.py                      # incremental build + index
    python build_specpack_index.py --full               # plný rebuild
    python build_specpack_index.py --no-index           # jen build

Viz build_datasheet_workspaces.py (výchozí workflow), Description.md kap. 9
(SpecPack) a python/README.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- Výchozí cesty (lze přepsat argumenty) --------------------------------------
# Junction na externí zdroj datasheetů (viz .gitignore).
DEFAULT_COMPONENTS = Path(__file__).resolve().parent.parent / "Data" / "MCP1x10" / "Components"
# Sdílený multi-workspace root (globální, napříč projekty).
DEFAULT_ROOT = Path(r"D:\Code\Tools\specPack\workspaces")
# Konfigurace extrakce dodávaná se SpecPackem.
DEFAULT_CONFIG = Path(r"D:\Code\Tools\specPack\specPack\config\specpack.yml")
# pipx-instalovaný příkaz (fallback: PATH).
DEFAULT_SPECPACK = Path(r"C:\Users\z003z5xd\.local\bin\specpack.exe")


def resolve_specpack(explicit: str | None) -> str:
    """Najde spustitelný specpack: explicitní > výchozí pipx cesta > PATH."""
    if explicit:
        return explicit
    if DEFAULT_SPECPACK.exists():
        return str(DEFAULT_SPECPACK)
    found = shutil.which("specpack")
    if found:
        return found
    sys.exit(
        "CHYBA: specpack nenalezen. Zadej --specpack <cesta> nebo přidej na PATH.\n"
        f"Zkoušeno: {DEFAULT_SPECPACK} a PATH."
    )


def run(cmd: list[str], env: dict[str, str]) -> None:
    """Spustí příkaz, streamuje výstup, při chybě ukončí skript."""
    print(">>> " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        sys.exit(f"CHYBA: příkaz skončil s kódem {result.returncode}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build & index SpecPack datasheet index.")
    parser.add_argument("--components", type=Path, default=DEFAULT_COMPONENTS,
                        help=f"Složka s PDF datasheety (rekurzivně). Výchozí: {DEFAULT_COMPONENTS}")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help=f"Sdílený workspace root pro index. Výchozí: {DEFAULT_ROOT}")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help=f"SpecPack YAML config. Výchozí: {DEFAULT_CONFIG}")
    parser.add_argument("--specpack", default=None,
                        help="Cesta ke specpack(.exe). Výchozí: pipx cesta nebo PATH.")
    parser.add_argument("--full", action="store_true",
                        help="Plný rebuild (bez --incremental).")
    parser.add_argument("--no-index", action="store_true",
                        help="Jen build, přeskočit indexaci.")
    args = parser.parse_args()

    if not args.components.exists():
        sys.exit(f"CHYBA: složka s datasheety neexistuje: {args.components}")
    if not args.config.exists():
        sys.exit(f"CHYBA: config neexistuje: {args.config}")

    print(
        "VAROVÁNÍ: build_specpack_index.py (--per-doc) je DEPRECATED. "
        "Použij build_datasheet_workspaces.py (per-komponenta).",
        file=sys.stderr, flush=True,
    )

    specpack = resolve_specpack(args.specpack)

    # PyMuPDF jinak tiskne "fitz API deprecated" na stdout; fd:2 -> stderr.
    env = dict(os.environ)
    env["PYMUPDF_MESSAGE"] = "fd:2"

    build_cmd = [specpack, "build", str(args.components),
                 "--out", str(args.root), "--config", str(args.config), "--per-doc"]
    if not args.full:
        build_cmd.append("--incremental")
    run(build_cmd, env)

    if not args.no_index:
        run([specpack, "index", str(args.root), "--per-doc"], env)

    print("\nHOTOVO. Index je v:", args.root, flush=True)


if __name__ == "__main__":
    main()
