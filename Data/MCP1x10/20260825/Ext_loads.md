# Ext_loads.md — Externí zátěže (vstup uživatele)

> Data, která **nejsou** v podkladech (ISCF/Partlist) — typicky odběr přes konektor do externí
> zátěže. Vyplňuje **uživatel**. Slouží jako vstup pro výpočet sum a `power_tree`.

| refdes (konektor) | rail | rail_v [V] | curr_max [mA] | curr_typ [mA] | popis zátěže | poznámka |
|---|---|---|---|---|---|---|
| X120 | P5_USB_X12 | 5 | 500 |	200 | 1× USB port |	USB1 |
| X121 | P5_USB_X12 | 5 | 500 |	200 | 1× USB port |	USB2 |
| X130 | P5_USB_X13 | 5 | 0 | 0 | USB port / větev aktuálně bez budgetu | předpoklad vypuštění | 
| X131 | P5_USB_X13 | 5 | 0 | 0 | USB port / větev aktuálně bez budgetu | předpoklad vypuštění | 
| X200 | P5_NO_0 | 5 | 700 | 400 | Next Override | samostatná větev přes N3 |
| X201 | P5_NO_1 | 5 | 700 | 400 | Next Override | samostatná větev přes N4 |
| X60 |	P5_HW |	5 |	250	| 125 |	Handwheel |	symetrické rozdělení větve N5 mezi X60 a X61 |
| X61 |	P5_HW |	5 |	250	| 125 |	Handwheel |	symetrické rozdělení větve N5 mezi X60 a X61 |
| X30 |	P5_OV |	5 |	250 | 125 |	Override | symetrické rozdělení větve N6 mezi X30 a X31 |
| X31 |	P5_OV |	5 |	250 | 125 |	Override |	symetrické rozdělení větve N6 mezi X30 a X31 |
| X515 | P24 | 24 |	TBD | TBD |Customer Buttons přes high-side driver N1100 | proudy nejsou finálně uzavřené | 
