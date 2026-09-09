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
  - `partName` = A5E, `componentKind` = kód třídy (číselník = otevřený bod), `power_supply` =
    `VCC=P3V3;GND=GND` (pro křížovou kontrolu; může být prázdné — není chyba).
- Sekce `BEGIN_POWER` … `END_POWER`: `RailName:RefDes(pin:pinLabel),...;` — zdroj railů a pinů.
- `BEGIN_NETS`, `BEGIN_GROUND` — signálové/zemní nety.

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
