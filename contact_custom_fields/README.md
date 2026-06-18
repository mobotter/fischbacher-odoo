# Adds Custom Fields to Contacts

Kleines Odoo-Modul zur Erweiterung des Kontaktmodells `res.partner` um zusätzliche Stammdatenfelder.  
Das Modul ergänzt die Kontaktmaske in Odoo und fügt eigene Felder direkt im bestehenden Partnerformular ein.

## Funktionen

Das Modul ergänzt folgende Felder im Modell `res.partner`:

- `x_telefax` – Telefax
- `telefax` – Fax
- `supplier_customer_number` – Supplier Customer Number
- `dsp3_id` – DSP 3 ID

Zusätzlich wird die Standard-Kontaktansicht von Odoo erweitert:

- nach `website` werden `x_telefax` und `supplier_customer_number` eingefügt
- nach `ref` wird `dsp3_id` eingefügt

## Technische Details

- Odoo-Version: `19.0.1.0.0`
- Abhängigkeit: `base`
- Lizenz: `LGPL-3`
- Modell-Erweiterung: `res.partner`
- View-Inheritance über `base.view_partner_form` 

## Installation

1. Modul in das Odoo-Addons-Verzeichnis kopieren.
2. Apps-Liste in Odoo aktualisieren.
3. Nach dem Modul **Adds Custom Fields to Contacts** suchen.
4. Modul installieren. 

## Verzeichnisstruktur

```contact_custom_fields/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── res_partner.py
└── views/
    └── res_partner.xml
```

## Einsatzbereich

Geeignet für Installationen, in denen Kontakte um zusätzliche Kommunikations- oder Identifikationsdaten erweitert werden müssen, ohne das Standardmodell stark umzubauen. Die Erweiterung bleibt dabei nah an der Odoo-Standardstruktur. 

## Hinweise

Aktuell handelt es sich um eine sehr schlanke Erweiterung ohne Business-Logik, Validierungen oder Security-spezifische Zusatzregeln. Das Modul eignet sich daher gut als Basis für weitere kundenspezifische Anpassungen. 
