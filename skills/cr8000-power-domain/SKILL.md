---
name: cr8000-power-domain
description: >-
  Doménová znalost pro CR8000-to-PS_Spec — formáty ISCF a Testway Partlist, konvence názvů railů
  (PxVy), pravidla inteligentního filtru spotřeby a metodika derating proudů. Použij při parsingu
  podkladů, dekódování napětí railů, klasifikaci spotřebičů a návrhu datasheetových hodnot.
---

# CR8000 Power Domain — doménová znalost

> Detailní a závazné zadání: `Description.md`. Tento skill shrnuje pravidla pro agenty.

## Formát ISCF
- Sekce `BEGIN_COMPPROPS` … `END_COMPPROPS`: `RefDes:partName,partNumber,noMount,tolerance,value,
  maxV,powerDiss,maxP,elec_type,enetNonSeries,componentKind,power_supply,compComment`.
  - `partName` = A5E, `componentKind` = kód třídy (číselník viz níže), `power_supply` =
    `VCC=P3V3;GND=GND` (pro křížovou kontrolu; může být prázdné — není chyba).
- Sekce `BEGIN_POWER` … `END_POWER`: `RailName:RefDes(pin:pinLabel),...;` — zdroj railů a pinů.
- `BEGIN_NETS`, `BEGIN_GROUND` — signálové/zemní nety.

## Číselník `componentKind` (Function Type v CR8000 Design Editor)
Ověřeno křížovou kontrolou proti ISCF (prefix RefDes ↔ kód). Zdroj: strom „Function Type" v CR8000
Design Editoru. Písmeno = prefix RefDes. Kódy 105/109/110/113/115/125 jsou volné (nepřiřazená písmena).

| Kód | RefDes | DE (originál) | EN | CZ | Filtr (výchozí) |
|---|---|---|---|---|---|
| 12 | — | POWER BOX | Power box | Napájecí box | uzel |
| 101 | A | Baugruppe | Assembly / module | Sestava (modul) | dle obsahu |
| 102 | B | Quarze | Crystals / oscillators | Krystaly (oscilátory) | ✅ malý |
| 103 | C | Kondensatoren | Capacitors | Kondenzátory | ⛔ (blokovací) |
| 104 | D | Digital ICs | Digital ICs | Digitální IO | ✅ spotřebič |
| 105 | E | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 106 | F | Sicherungen | Fuses | Pojistky | uzel (série) |
| 107 | G | Netzgerät | Power supply unit | Napájecí zdroj | uzel (zdroj) |
| 108 | H | Lampen, LED | Lamps, LEDs | Žárovky, LED | ✅ spotřebič |
| 109 | I | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 110 | J | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 111 | K | Relais | Relays | Relé | ✅ (cívka) |
| 112 | L | Spulen | Inductors (coils) | Cívky (tlumivky/ferity) | uzel (série) |
| 113 | M | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 114 | N | Analog ICs | Analog ICs | Analogové IO | ✅ spotřebič |
| 115 | O | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 116 | P | Prüfpunkte | Test points | Zkušební body (testpointy) | ⛔ |
| 117 | Q | Sonstige | Miscellaneous / other | Ostatní | dle obsahu |
| 118 | R | Widerstände | Resistors | Rezistory | ⛔ (pull-up/down) / uzel (malý série) |
| 119 | S | Schalter | Switches | Spínače / přepínače | dle obsahu |
| 120 | T | Trafos, Wandler | Transformers, converters | Transformátory, měniče | uzel (měnič) |
| 121 | U | Optokoppler | Optocouplers | Optočleny | ✅ spotřebič |
| 122 | V | Dioden, Transistoren | Diodes, transistors | Diody, tranzistory | uzel/✅ dle role |
| 123 | W | Antennen | Antennas | Antény | ⛔ |
| 124 | X | Stecker | Connectors | Konektory | externí zátěž (`Ext_loads.md`) |
| 125 | Y | — | (nepřiřazeno) | (nepřiřazeno) | — |
| 126 | Z | Filter | Filters | Filtry | uzel (série) |
| 127 | — | Hierarchical Block | Hierarchical block | Hierarchický blok | — |
| 128 | WS | Sternpunkte | Star points | Propojky | — |

> Sloupec „Filtr (výchozí)" je jen návodné výchozí chování (kap. Inteligentní filtr); je
> konfigurovatelné a rozhoduje i hodnota/typ z BOM (např. „malý" sériový R = uzel toku, ne ⛔).


## Formát Partlist (Testway BOM)
- Oddělovač `|`, hlavička `ARTIKEL|EPL|TYPE|COMMENT|Value|Tolerance|Voltage`.
- `EPL` = RefDes (klíč spojení s ISCF), `ARTIKEL` = A5E, `COMMENT` = Item.
- Normalizace kódování/diakritiky (`+95A??C` → `+95°C`).

## Konvence napětí railu (rail_v)
- `PxVy`: `P5`→5, `P12`→12, `P3V3`→3.3, `P0V85`→0.85 [V].
- Konvence i ve složených názvech: `NVCC_BBSM_P1V8`→1.8, `SNVS_P0V8`→0.8.
- Bez konvence (`VDDAH_PHY`) → trasování přes feritovou perlu/spínač/malý R na napájecí rail.
- Nedeterministické (`VDD2`, `VDDQ`) → dotaz na uživatele. **Nehádat.**

## Inteligentní filtr (✅/⛔)
- ⛔ zanedbatelné: blokovací kondenzátory, pull-up/pull-down rezistory.
- ✅ spotřebiče: IC, LED (přes driver/OC), aktivní prvky.
- Uzly toku (bloky, ne prostý spotřebič): LDO, DC/DC, spínače napájení, feritové perly, pojistky,
  „malé" rezistory, konektory (externí zátěž → `Ext_loads.md`).

## Metodika proudů (datasheet)
- `ds_v_min/max` z **Operating conditions** (ne Absolute Max).
- `ds_curr_max/typ` [mA]; typ = derating dle režimu (např. standby/aktivní u EEPROM).
- Při nejednoznačnosti: AI navrhne hodnotu + metodiku, uživatel verifikuje.
